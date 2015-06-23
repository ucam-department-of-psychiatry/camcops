#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from __future__ import print_function

import base64
import errno
import codecs
import hl7
import lockfile
import os
import ping
import socket
import subprocess
import sys

import pythonlib.rnc_db as rnc_db
import pythonlib.rnc_web as ws

from cc_constants import ACTION, DATEFORMAT, ERA_NOW, PARAM, VALUE
import cc_db
import cc_dt
import cc_filename
import cc_html
from cc_logger import logger
from cc_pls import pls
import cc_recipdef
import cc_task


# =============================================================================
# General HL7 sources
# =============================================================================
# http://python-hl7.readthedocs.org/en/latest/
# http://www.interfaceware.com/manual/v3gen_python_library_details.html
# http://www.interfaceware.com/hl7_video_vault.html#how
# http://www.interfaceware.com/hl7-standard/hl7-segments.html
# http://www.hl7.org/special/committees/vocab/v26_appendix_a.pdf
# http://www.ncbi.nlm.nih.gov/pmc/articles/PMC130066/

# =============================================================================
# HL7 design
# =============================================================================

# WHICH RECORDS TO SEND?
# Most powerful mechanism is not to have a sending queue (which would then
# require careful multi-instance locking), but to have a "sent" log. That way:
# - A record needs sending if it's not in the sent log (for an appropriate
#   server).
# - You can add a new server and the system will know about the (new) backlog
#   automatically.
# - You can specify criteria, e.g. don't upload records before 1/1/2014, and
#   modify that later, and it would catch up with the backlog.
# - Successes and failures are logged in the same table.
# - Multiple recipients are handled with ease.
# - No need to alter database.pl code that receives from tablets.
# - Can run with a simple cron job.

# LOCKING
# - Don't use database locking:
#   https://blog.engineyard.com/2011/5-subtle-ways-youre-using-mysql-as-a-queue-and-why-itll-bite-you  # noqa
# - Locking via UNIX lockfiles:
#       https://pypi.python.org/pypi/lockfile
#       http://pythonhosted.org/lockfile/

# CALLING THE HL7 PROCESSOR
# - Use "camcops -7 ..." or "camcops --hl7 ..."
# - Call it via a cron job, e.g. every 5 minutes.

# CONFIG FILE
# q.v.

# TO CONSIDER
# - batched messages (HL7 batching protocol)
#   http://docs.oracle.com/cd/E23943_01/user.1111/e23486/app_hl7batching.htm
# - note: DG1 segment = diagnosis

# BASIC MESSAGE STRUCTURE
# - package into HL7 2.X message as encapsulated PDF
#   http://www.hl7standards.com/blog/2007/11/27/pdf-attachment-in-hl7-message/
# - message ORU^R01
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-messages
#   MESSAGES: http://www.interfaceware.com/hl7-standard/hl7-messages.html
# - OBX segment = observation/result segment
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-obx-segment  # noqa
#   http://www.interfaceware.com/hl7-standard/hl7-segment-OBX.html
# - SEGMENTS:
#   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-segments
# - ED field (= encapsulated data)
#   http://www.interfaceware.com/hl7-standard/hl7-fields.html
# - base-64 encoding
# - Option for structure (XML), HTML, PDF export.


# =============================================================================
# Constants
# =============================================================================


# STRUCTURE OF HL7 MESSAGES
# MESSAGE = list of segments, separated by carriage returns
SEGMENT_SEPARATOR = u"\r"
# SEGMENT = list of fields (= composites), separated by pipes
FIELD_SEPARATOR = u"|"
# FIELD (= COMPOSITE) = string, or list of components separated by carets
COMPONENT_SEPARATOR = u"^"
# Component = string, or lists of subcomponents separated by ampersands
SUBCOMPONENT_SEPARATOR = u"&"
# Subcomponents must be primitive data types (i.e. strings).
# ... http://www.interfaceware.com/blog/hl7-composites/

REPETITION_SEPARATOR = u"~"
ESCAPE_CHARACTER = u"\\"

# Fields are specified in terms of DATA TYPES:
# http://www.corepointhealth.com/resource-center/hl7-resources/hl7-data-types

# Some of those are COMPOSITE TYPES:
# http://amisha.pragmaticdata.com/~gunther/oldhtml/composites.html#COMPOSITES


# =============================================================================
# Main functions
# =============================================================================

def send_all_pending_hl7_messages(show_queue_only=False):
    """Sends all pending HL7 or file messages.

    Obtains a file lock, then iterates through all recipients.
    """
    queue_stdout = sys.stdout
    if not pls.HL7_LOCKFILE:
        logger.error("send_all_pending_hl7_messages: No HL7_LOCKFILE specified"
                     " in config; can't proceed")
        return
    # On UNIX, lockfile uses LinkLockFile
    # https://github.com/smontanaro/pylockfile/blob/master/lockfile/
    #         linklockfile.py
    lock = lockfile.FileLock(pls.HL7_LOCKFILE)
    if lock.is_locked():
        logger.warning("send_all_pending_hl7_messages: locked by another"
                       " process; aborting")
        return
    with lock:
        if show_queue_only:
            print("recipient,basetable,_pk,when_created", file=queue_stdout)
        for recipient_def in pls.HL7_RECIPIENT_DEFS:
            send_pending_hl7_messages(recipient_def, show_queue_only,
                                      queue_stdout)
        pls.db.commit()  # HL7 commit (prior to releasing file lock)


def send_pending_hl7_messages(recipient_def, show_queue_only, queue_stdout):
    """Pings recipient if necessary, opens any files required, creates an
    HL7Run, then sends all pending HL7/file messages to a specific
    recipient."""
    # Called once per recipient.
    logger.debug("send_pending_hl7_messages: " + str(recipient_def))

    use_ping = (recipient_def.using_hl7()
                and not recipient_def.divert_to_file
                and recipient_def.ping_first)
    if use_ping:
        # No HL7 PING method yet. Proposal is:
        # http://hl7tsc.org/wiki/index.php?title=FTSD-ConCalls-20081028
        # So use TCP/IP ping.
        try:
            if not ping.do_one(
                dest_addr=recipient_def.host,
                timeout=recipient_def.network_timeout_ms,
                psize=32  # ping standard, not that it matters
            ):
                logger.error("Failed to ping {}".format(recipient_def.host))
                return
        except socket.error:
            logger.error("Socket error trying to ping {}; likely need to "
                         "run as root".format(recipient_def.host))
            return

    if show_queue_only:
        hl7run = None
    else:
        hl7run = HL7Run(recipient_def)

    # Do things, but with safe file closure if anything goes wrong
    use_divert = (recipient_def.using_hl7() and recipient_def.divert_to_file)
    if use_divert:
        try:
            with codecs.open(recipient_def.divert_to_file, "a", "utf8") as f:
                send_pending_hl7_messages_2(recipient_def, show_queue_only,
                                            queue_stdout, hl7run, f)
        except Exception as e:
            logger.error("Couldn't open file {} for appending: {}".format(
                recipient_def.divert_to_file, e))
            return
    else:
        send_pending_hl7_messages_2(recipient_def, show_queue_only,
                                    queue_stdout, hl7run, None)


def send_pending_hl7_messages_2(recipient_def, show_queue_only, queue_stdout,
                                hl7run, divert_file):
    """Sends all pending HL7/file messages to a specific recipient."""
    # Also called once per recipient, but after diversion files safely
    # opened and recipient pinged successfully (if desired).
    n_hl7_sent = 0
    n_hl7_successful = 0
    n_file_sent = 0
    n_file_successful = 0
    files_exported = []
    basetables = cc_task.get_base_tables(recipient_def.include_anonymous)
    for bt in basetables:
        # Current records...
        args = []
        sql = """
            SELECT _pk
            FROM {basetable}
            WHERE _current
        """.format(basetable=bt)

        # Having an appropriate date...
        # Best to use when_created, or _when_added_batch_utc?
        # The former. Because nobody would want a system that would miss
        # amendments to records, and records are defined (date-wise) by
        # when_created.
        if recipient_def.start_date:
            sql += """
                AND {} >= ?
            """.format(
                cc_db.mysql_select_utc_date_field_from_iso8601_field(
                    "when_created")
            )
            args.append(recipient_def.start_date)
        if recipient_def.end_date:
            sql += """
                AND {} <= ?
            """.format(
                cc_db.mysql_select_utc_date_field_from_iso8601_field(
                    "when_created")
            )
            args.append(recipient_def.end_date)

        # That haven't already had a successful HL7 message sent to this
        # server...
        sql += """
            AND _pk NOT IN (
                SELECT m.serverpk
                FROM {hl7table} m
                INNER JOIN {hl7runtable} r
                ON m.run_id = r.run_id
                WHERE m.basetable = ?
                AND r.recipient = ?
                AND m.success
                AND (NOT m.cancelled OR m.cancelled IS NULL)
            )
        """.format(hl7table=HL7Message.TABLENAME, hl7runtable=HL7Run.TABLENAME)
        args.append(bt)
        args.append(recipient_def.recipient)
        # http://explainextended.com/2009/09/18/not-in-vs-not-exists-vs-left-join-is-null-mysql/  # noqa

        # That are finalized (i.e. aren't still on the tablet and potentially
        # subject to modification)?
        if recipient_def.finalized_only:
            sql += """
                AND _era <> ?
            """
            args.append(ERA_NOW)

        # OK. Fetch PKs and send information.
        # logger.debug("{}, args={}".format(sql, args))
        pklist = pls.db.fetchallfirstvalues(sql, *args)
        for serverpk in pklist:
            msg = HL7Message(bt, serverpk, hl7run, recipient_def,
                             show_queue_only=show_queue_only)
            tried, succeeded = msg.send(queue_stdout, divert_file)
            if not tried:
                continue
            if recipient_def.using_hl7():
                n_hl7_sent += 1
                n_hl7_successful += 1 if succeeded else 0
            else:
                n_file_sent += 1
                n_file_successful += 1 if succeeded else 0
                if succeeded:
                    files_exported.append(msg.filename)
                    if msg.rio_metadata_filename:
                        files_exported.append(msg.rio_metadata_filename)

    if hl7run:
        hl7run.call_script(files_exported)
        hl7run.finish()
    logger.info("{} HL7 messages sent, {} successful, {} failed".format(
        n_hl7_sent, n_hl7_successful, n_hl7_sent - n_hl7_successful))
    logger.info("{} files sent, {} successful, {} failed".format(
        n_file_sent, n_file_successful, n_file_sent - n_file_successful))


# =============================================================================
# File-handling functions
# =============================================================================

def make_sure_path_exists(path):
    """Creates a directory/directories if the path doesn't already exist."""
    # http://stackoverflow.com/questions/273192
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


# =============================================================================
# HL7 helper functions
# =============================================================================

def get_mod11_checkdigit(strnum):
    """Input: string containing integer. Output: MOD11 check digit (string)."""
    # http://www.mexi.be/documents/hl7/ch200025.htm
    # http://stackoverflow.com/questions/7006109
    # http://www.pgrocer.net/Cis51/mod11.html
    total = 0
    multiplier = 2  # 2 for units digit, increases to 7, then resets to 2
    try:
        for i in reversed(range(len(strnum))):
            total += int(strnum[i]) * multiplier
            multiplier += 1
            if multiplier == 8:
                multiplier = 2
        c = str(11 - (total % 11))
        if c == "11":
            c = "0"
        elif c == "10":
            c = "X"
        return c
    except (TypeError, ValueError):
        # garbage in...
        return ""


def make_msh_segment(message_datetime,
                     message_control_id):
    """Creates an HL7 message header (MSH) segment."""
    # We're making an ORU^R01 message = unsolicited result.
    # ORU = Observational Report - Unsolicited
    # ORU^R01 = Unsolicited transmission of an observation message
    # http://www.corepointhealth.com/resource-center/hl7-resources/hl7-oru-message  # noqa
    # http://www.hl7kit.com/joomla/index.php/hl7resources/examples/107-orur01  # noqa

    # -------------------------------------------------------------------------
    # Message header (MSH)
    # -------------------------------------------------------------------------
    # http://www.hl7.org/documentcenter/public/wg/conf/HL7MSH.htm

    segment_id = u"MSH"
    encoding_characters = (COMPONENT_SEPARATOR + REPETITION_SEPARATOR +
                           ESCAPE_CHARACTER + SUBCOMPONENT_SEPARATOR)
    sending_application = u"CamCOPS"
    sending_facility = ""
    receiving_application = ""
    receiving_facility = ""
    date_time_of_message = cc_dt.format_datetime(message_datetime,
                                                 DATEFORMAT.HL7_DATETIME)
    security = ""
    message_type = hl7.Field(COMPONENT_SEPARATOR, [
        "ORU",  # message type ID = Observ result/unsolicited
        "R01"   # trigger event ID = ORU/ACK - Unsolicited transmission
                # of an observation message
    ])
    processing_id = "P"  # production (processing mode: current)
    version_id = "2.3"  # HL7 version
    sequence_number = ""
    continuation_pointer = ""
    accept_acknowledgement_type = ""
    application_acknowledgement_type = "AL"  # always
    country_code = ""
    character_set = "UNICODE UTF-8"
    # http://wiki.hl7.org/index.php?title=Character_Set_used_in_v2_messages
    principal_language_of_message = ""

    fields = [
        segment_id,
        # field separator inserted automatically; HL7 standard considers it a
        # field but the python-hl7 processor doesn't when it parses
        encoding_characters,
        sending_application,
        sending_facility,
        receiving_application,
        receiving_facility,
        date_time_of_message,
        security,
        message_type,
        message_control_id,
        processing_id,
        version_id,
        sequence_number,
        continuation_pointer,
        accept_acknowledgement_type,
        application_acknowledgement_type,
        country_code,
        character_set,
        principal_language_of_message,
    ]
    segment = hl7.Segment(FIELD_SEPARATOR, fields)
    return segment


def make_pid_segment(forename,
                     surname,
                     dob,
                     sex,
                     address,
                     patient_id_tuple_list=[]):
    """Creates an HL7 patient identification (PID) segment."""
    # -------------------------------------------------------------------------
    # Patient identification (PID)
    # -------------------------------------------------------------------------
    # http://www.corepointhealth.com/resource-center/hl7-resources/hl7-pid-segment  # noqa
    # http://www.hl7.org/documentcenter/public/wg/conf/Msgadt.pdf (s5.4.8)

    # ID numbers...
    # http://www.cdc.gov/vaccines/programs/iis/technical-guidance/downloads/hl7guide-1-4-2012-08.pdf  # noqa

    segment_id = u"PID"
    set_id = ""

    # External ID
    patient_external_id = ""
    # ... this one is deprecated
    # http://www.j4jayant.com/articles/hl7/16-patient-id

    # Internal ID
    internal_id_element_list = []
    for i in range(len(patient_id_tuple_list)):
        if not patient_id_tuple_list[i].id:
            continue
        id = patient_id_tuple_list[i].id
        check_digit = get_mod11_checkdigit(id)
        check_digit_scheme = "M11"  # Mod 11 algorithm
        type_id = patient_id_tuple_list[i].id_type
        assigning_authority = patient_id_tuple_list[i].assigning_authority
        internal_id_element = hl7.Field(COMPONENT_SEPARATOR, [
            id,
            check_digit,
            check_digit_scheme,
            assigning_authority,
            type_id
        ])
        internal_id_element_list.append(internal_id_element)
    patient_internal_id = hl7.Field(REPETITION_SEPARATOR,
                                    internal_id_element_list)

    # Alternate ID
    alternate_patient_id = ""
    # ... this one is deprecated
    # http://www.j4jayant.com/articles/hl7/16-patient-id

    patient_name = hl7.Field(COMPONENT_SEPARATOR, [
        forename,  # surname
        surname,  # forename
        "",  # middle initial/name
        "",  # suffix (e.g. Jr, III)
        "",  # prefix (e.g. Dr)
        "",  # degree (e.g. MD)
    ])
    mothers_maiden_name = ""
    date_of_birth = cc_dt.format_datetime(dob, DATEFORMAT.HL7_DATE)
    alias = ""
    race = ""
    country_code = ""
    home_phone_number = ""
    business_phone_number = ""
    language = ""
    marital_status = ""
    religion = ""
    account_number = ""
    social_security_number = ""
    drivers_license_number = ""
    mother_identifier = ""
    ethnic_group = ""
    birthplace = ""
    birth_order = ""
    citizenship = ""
    veterans_military_status = ""

    fields = [
        segment_id,
        set_id,  # PID.1
        patient_external_id,  # PID.2
        patient_internal_id,  # known as "PID-3" or "PID.3"
        alternate_patient_id,  # PID.4
        patient_name,
        mothers_maiden_name,
        date_of_birth,
        sex,
        alias,
        race,
        address,
        country_code,
        home_phone_number,
        business_phone_number,
        language,
        marital_status,
        religion,
        account_number,
        social_security_number,
        drivers_license_number,
        mother_identifier,
        ethnic_group,
        birthplace,
        birth_order,
        citizenship,
        veterans_military_status,
    ]
    segment = hl7.Segment(FIELD_SEPARATOR, fields)
    return segment


def make_obr_segment(task):
    """Creates an HL7 observation request (OBR) segment."""
    # -------------------------------------------------------------------------
    # Observation request segment (OBR)
    # -------------------------------------------------------------------------
    # http://hl7reference.com/HL7%20Specifications%20ORM-ORU.PDF
    # Required in ORU^R01 message:
    #   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-oru-message  # noqa
    #   http://www.corepointhealth.com/resource-center/hl7-resources/hl7-obr-segment  # noqa

    segment_id = u"OBR"
    set_id = "1"
    placer_order_number = "CamCOPS"
    filler_order_number = "CamCOPS"
    universal_service_id = hl7.Field(COMPONENT_SEPARATOR, [
        "CamCOPS",
        "CamCOPS psychiatric/cognitive assessment"
    ])
    # unused below here, apparently
    priority = ""
    requested_date_time = ""
    observation_date_time = ""
    observation_end_date_time = ""
    collection_volume = ""
    collector_identifier = ""
    specimen_action_code = ""
    danger_code = ""
    relevant_clinical_information = ""
    specimen_received_date_time = ""
    ordering_provider = ""
    order_callback_phone_number = ""
    placer_field_1 = ""
    placer_field_2 = ""
    filler_field_1 = ""
    filler_field_2 = ""
    results_report_status_change_date_time = ""
    charge_to_practice = ""
    diagnostic_service_section_id = ""
    result_status = ""
    parent_result = ""
    quantity_timing = ""
    result_copies_to = ""
    parent = ""
    transportation_mode = ""
    reason_for_study = ""
    principal_result_interpreter = ""
    assistant_result_interpreter = ""
    technician = ""
    transcriptionist = ""
    scheduled_date_time = ""
    number_of_sample_containers = ""
    transport_logisticts_of_collected_samples = ""
    collectors_comment = ""
    transport_arrangement_responsibility = ""
    transport_arranged = ""
    escort_required = ""
    planned_patient_transport_comment = ""

    fields = [
        segment_id,
        set_id,
        placer_order_number,
        filler_order_number,
        universal_service_id,
        priority,
        requested_date_time,
        observation_date_time,
        observation_end_date_time,
        collection_volume,
        collector_identifier,
        specimen_action_code,
        danger_code,
        relevant_clinical_information,
        specimen_received_date_time,
        ordering_provider,
        order_callback_phone_number,
        placer_field_1,
        placer_field_2,
        filler_field_1,
        filler_field_2,
        results_report_status_change_date_time,
        charge_to_practice,
        diagnostic_service_section_id,
        result_status,
        parent_result,
        quantity_timing,
        result_copies_to,
        parent,
        transportation_mode,
        reason_for_study,
        principal_result_interpreter,
        assistant_result_interpreter,
        technician,
        transcriptionist,
        scheduled_date_time,
        number_of_sample_containers,
        transport_logisticts_of_collected_samples,
        collectors_comment,
        transport_arrangement_responsibility,
        transport_arranged,
        escort_required,
        planned_patient_transport_comment,
    ]
    segment = hl7.Segment(FIELD_SEPARATOR, fields)
    return segment


def make_obx_segment(task,
                     task_format,
                     observation_identifier,
                     observation_datetime,
                     responsible_observer,
                     xml_field_comments=True):
    """Creates an HL7 observation result (OBX) segment."""
    # -------------------------------------------------------------------------
    # Observation result segment (OBX)
    # -------------------------------------------------------------------------
    # http://www.hl7standards.com/blog/2006/10/18/how-do-i-send-a-binary-file-inside-of-an-hl7-message  # noqa
    # http://www.hl7standards.com/blog/2007/11/27/pdf-attachment-in-hl7-message/  # noqa
    # http://www.hl7standards.com/blog/2006/12/01/sending-images-or-formatted-documents-via-hl7-messaging/  # noqa
    # www.hl7.org/documentcenter/public/wg/ca/HL7ClmAttIG.PDF
    # type of data:
    #   http://www.hl7.org/implement/standards/fhir/v2/0191/index.html
    # subtype of data:
    #   http://www.hl7.org/implement/standards/fhir/v2/0291/index.html
    segment_id = u"OBX"
    set_id = unicode(1)

    source_application = u"CamCOPS"
    if task_format == VALUE.OUTPUTTYPE_PDF:
        value_type = "ED"  # Encapsulated data (ED) field
        observation_value = hl7.Field(COMPONENT_SEPARATOR, [
            source_application,
            u"Application",  # type of data
            u"PDF",  # data subtype
            u"Base64",  # base 64 encoding
            base64.standard_b64encode(task.get_pdf())  # data
        ])
    elif task_format == VALUE.OUTPUTTYPE_HTML:
        value_type = "ED"  # Encapsulated data (ED) field
        observation_value = hl7.Field(COMPONENT_SEPARATOR, [
            source_application,
            u"TEXT",  # type of data
            u"HTML",  # data subtype
            u"A",  # no encoding (see table 0299), but need to escape
            escape_hl7_text(task.get_html())  # data
        ])
    elif task_format == VALUE.OUTPUTTYPE_XML:
        value_type = "ED"  # Encapsulated data (ED) field
        observation_value = hl7.Field(COMPONENT_SEPARATOR, [
            source_application,
            u"TEXT",  # type of data
            u"XML",  # data subtype
            u"A",  # no encoding (see table 0299), but need to escape
            escape_hl7_text(task.get_xml(
                indent_spaces=0, eol="",
                include_comments=xml_field_comments
            ))  # data
        ])
    else:
        raise AssertionError(
            "make_obx_segment: invalid task_format: {}".format(task_format))

    observation_sub_id = ""
    units = ""
    reference_range = ""
    abnormal_flags = ""
    probability = ""
    nature_of_abnormal_test = ""
    observation_result_status = ""
    date_of_last_observation_normal_values = ""
    user_defined_access_checks = ""
    date_and_time_of_observation = cc_dt.format_datetime(
        observation_datetime, DATEFORMAT.HL7_DATETIME)
    producer_id = ""
    observation_method = ""
    equipment_instance_identifier = ""
    date_time_of_analysis = ""

    fields = [
        segment_id,
        set_id,
        value_type,
        observation_identifier,
        observation_sub_id,
        observation_value,
        units,
        reference_range,
        abnormal_flags,
        probability,
        nature_of_abnormal_test,
        observation_result_status,
        date_of_last_observation_normal_values,
        user_defined_access_checks,
        date_and_time_of_observation,
        producer_id,
        responsible_observer,
        observation_method,
        equipment_instance_identifier,
        date_time_of_analysis,
    ]
    segment = hl7.Segment(FIELD_SEPARATOR, fields)
    return segment


def make_dg1_segment(set_id,
                     diagnosis_datetime,
                     coding_system,
                     diagnosis_identifier,
                     diagnosis_text,
                     alternate_coding_system="",
                     alternate_diagnosis_identifier="",
                     alternate_diagnosis_text="",
                     diagnosis_type="F",
                     diagnosis_classification="D",
                     confidential_indicator="N",
                     clinician_id_number=None,
                     clinician_surname="",
                     clinician_forename="",
                     clinician_middle_name_or_initial="",
                     clinician_suffix="",
                     clinician_prefix="",
                     clinician_degree="",
                     clinician_source_table="",
                     clinician_assigning_authority="",
                     clinician_name_type_code="",
                     clinician_identifier_type_code="",
                     clinician_assigning_facility="",
                     attestation_datetime=None):
    """Creates an HL7 diagnosis (DG1) segment.

    Args:
        set_id: Diagnosis sequence number, starting with 1 (use higher numbers
            for >1 diagnosis).
        diagnosis_datetime: Date/time diagnosis was made.

        coding_system: E.g. "I9C" for ICD9-CM; "I10" for ICD10.
        diagnosis_identifier: Code.
        diagnosis_text: Text.

        alternate_coding_system: Optional alternate coding system.
        alternate_diagnosis_identifier: Optional alternate code.
        alternate_diagnosis_text: Optional alternate text.

        diagnosis_type: A admitting, W working, F final.
        diagnosis_classification: C consultation, D diagnosis, M medication,
            O other, R radiological scheduling, S sign and symptom,
            T tissue diagnosis, I invasive procedure not classified elsewhere.
        confidential_indicator: Y yes, N no

        clinician_id_number:              } Diagnosing clinician.
        clinician_surname:                }
        clinician_forename:               }
        clinician_middle_name_or_initial: }
        clinician_suffix:                 }
        clinician_prefix:                 }
        clinician_degree:                 }
        clinician_source_table:           }
        clinician_assigning_authority:    }
        clinician_name_type_code:         }
        clinician_identifier_type_code:   }
        clinician_assigning_facility:     }

        attestation_datetime: Date/time the diagnosis was attested.
    """
    # -------------------------------------------------------------------------
    # Diagnosis segment (DG1)
    # -------------------------------------------------------------------------
    # http://www.mexi.be/documents/hl7/ch600012.htm
    # https://www.hl7.org/special/committees/vocab/V26_Appendix_A.pdf
    segment_id = u"DG1"
    try:
        int(set_id)
        set_id = unicode(set_id)
    except:
        raise AssertionError("make_dg1_segment: set_id invalid")
    diagnosis_coding_method = ""
    diagnosis_code = hl7.Field(COMPONENT_SEPARATOR, [
        diagnosis_identifier,
        diagnosis_text,
        coding_system,
        alternate_diagnosis_identifier,
        alternate_diagnosis_text,
        alternate_coding_system,
    ])
    diagnosis_description = ""
    diagnosis_datetime = cc_dt.format_datetime(diagnosis_datetime,
                                               DATEFORMAT.HL7_DATETIME)
    if diagnosis_type not in ["A", "W", "F"]:
        raise AssertionError("make_dg1_segment: diagnosis_type invalid")
    major_diagnostic_category = ""
    diagnostic_related_group = ""
    drg_approval_indicator = ""
    drg_grouper_review_code = ""
    outlier_type = ""
    outlier_days = ""
    outlier_cost = ""
    grouper_version_and_type = ""
    diagnosis_priority = ""

    try:
        clinician_id_number = (
            unicode(int(clinician_id_number))
            if clinician_id_number is not None else ""
        )
    except:
        raise AssertionError("make_dg1_segment: diagnosing_clinician_id_number"
                             " invalid")
    if clinician_id_number:
        clinician_id_check_digit = get_mod11_checkdigit(clinician_id_number)
        clinician_checkdigit_scheme = "M11"  # Mod 11 algorithm
    else:
        clinician_id_check_digit = ""
        clinician_checkdigit_scheme = ""
    diagnosing_clinician = hl7.Field(COMPONENT_SEPARATOR, [
        clinician_id_number,
        clinician_surname or "",
        clinician_forename or "",
        clinician_middle_name_or_initial or "",
        clinician_suffix or "",
        clinician_prefix or "",
        clinician_degree or "",
        clinician_source_table or "",
        clinician_assigning_authority or "",
        clinician_name_type_code or "",
        clinician_id_check_digit or "",
        clinician_checkdigit_scheme or "",
        clinician_identifier_type_code or "",
        clinician_assigning_facility or "",
    ])

    if diagnosis_classification not in ["C", "D", "M", "O", "R", "S", "T",
                                        "I"]:
        raise AssertionError(
            "make_dg1_segment: diagnosis_classification invalid")
    if confidential_indicator not in ["Y", "N"]:
        raise AssertionError(
            "make_dg1_segment: confidential_indicator invalid")
    attestation_datetime = (
        cc_dt.format_datetime(attestation_datetime, DATEFORMAT.HL7_DATETIME)
        if attestation_datetime else ""
    )

    fields = [
        segment_id,
        set_id,
        diagnosis_coding_method,
        diagnosis_code,
        diagnosis_description,
        diagnosis_datetime,
        diagnosis_type,
        major_diagnostic_category,
        diagnostic_related_group,
        drg_approval_indicator,
        drg_grouper_review_code,
        outlier_type,
        outlier_days,
        outlier_cost,
        grouper_version_and_type,
        diagnosis_priority,
        diagnosing_clinician,
        diagnosis_classification,
        confidential_indicator,
        attestation_datetime,
    ]
    segment = hl7.Segment(FIELD_SEPARATOR, fields)
    return segment


def escape_hl7_text(s):
    """Escapes HL7 special characters."""
    # http://www.mexi.be/documents/hl7/ch200034.htm
    # http://www.mexi.be/documents/hl7/ch200071.htm
    esc_escape = ESCAPE_CHARACTER + ESCAPE_CHARACTER + ESCAPE_CHARACTER
    esc_fieldsep = ESCAPE_CHARACTER + u"F" + ESCAPE_CHARACTER
    esc_componentsep = ESCAPE_CHARACTER + u"S" + ESCAPE_CHARACTER
    esc_subcomponentsep = ESCAPE_CHARACTER + u"T" + ESCAPE_CHARACTER
    esc_repetitionsep = ESCAPE_CHARACTER + u"R" + ESCAPE_CHARACTER

    # Linebreaks:
    # http://www.healthintersections.com.au/?p=344
    # https://groups.google.com/forum/#!topic/ensemble-in-healthcare/wP2DWMeFrPA  # noqa
    # http://www.hermetechnz.com/documentation/sqlschema/index.html?hl7_escape_rules.htm  # noqa
    esc_linebreak = ESCAPE_CHARACTER + u".br" + ESCAPE_CHARACTER

    s = s.replace(ESCAPE_CHARACTER, esc_escape)  # this one first!
    s = s.replace(FIELD_SEPARATOR, esc_fieldsep)
    s = s.replace(COMPONENT_SEPARATOR, esc_componentsep)
    s = s.replace(SUBCOMPONENT_SEPARATOR, esc_subcomponentsep)
    s = s.replace(REPETITION_SEPARATOR, esc_repetitionsep)
    s = s.replace("\n", esc_linebreak)
    return s


def msg_is_successful_ack(msg):
    """Checks whether msg represents a successful acknowledgement message."""
    # http://hl7reference.com/HL7%20Specifications%20ORM-ORU.PDF

    if msg is None:
        return False, "Reply is None"

    # Get segments (MSH, MSA)
    if len(msg) != 2:
        return False, "Reply doesn't have 2 segments (has {})".format(len(msg))
    msh_segment = msg[0]
    msa_segment = msg[1]

    # Check MSH segment
    if len(msh_segment) < 9:
        return False, "First (MSH) segment has <9 fields (has {})".format(
            len(msh_segment))
    msh_segment_id = msh_segment[0]
    msh_message_type = msh_segment[8]
    if msh_segment_id != [u"MSH"]:
        return False, "First (MSH) segment ID is not 'MSH' (is {})".format(
            msh_segment_id)
    if msh_message_type != [u"ACK"]:
        return False, "MSH message type is not 'ACK' (is {})".format(
            msh_message_type)

    # Check MSA segment
    if len(msa_segment) < 2:
        return False, "Second (MSA) segment has <2 fields (has {})".format(
            len(msa_segment))
    msa_segment_id = msa_segment[0]
    msa_acknowledgment_code = msa_segment[1]
    if msa_segment_id != [u"MSA"]:
        return False, "Second (MSA) segment ID is not 'MSA' (is {})".format(
            msa_segment_id)
    if msa_acknowledgment_code != [u"AA"]:
        # AA for success, AE for error
        return False, "MSA acknowledgement code is not 'AA' (is {})".format(
            msa_acknowledgment_code)

    return True, None


# =============================================================================
# HL7Run class
# =============================================================================

class HL7Run(object):
    """Class representing an HL7/file run for a specific recipient.

    May be associated with multiple HL7/file messages.
    """
    TABLENAME = "_hl7_run_log"
    FIELDSPECS = [
        dict(name="run_id", cctype="BIGINT_UNSIGNED", pk=True,
             autoincrement=True, comment="Arbitrary primary key"),
        # 4294967296 values, so at 1/minute, 8165 years.
        dict(name="start_at_utc", cctype="DATETIME",
             comment="Time run was started (UTC)"),
        dict(name="finish_at_utc", cctype="DATETIME",
             comment="Time run was finished (UTC)"),
    ] + cc_recipdef.RecipientDefinition.FIELDSPECS + [
        dict(name="script_retcode", cctype="INT",
             comment="Return code from the script_after_file_export script"),
        dict(name="script_stdout", cctype="TEXT",
             comment="stdout from the script_after_file_export script"),
        dict(name="script_stderr", cctype="TEXT",
             comment="stderr from the script_after_file_export script"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns=False):
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, param):
        if isinstance(param, cc_recipdef.RecipientDefinition):
            rnc_db.blank_object(self, HL7Run.FIELDS)
            # Copy all attributes from the RecipientDefinition
            self.__dict__.update(param.__dict__)

            self.start_at_utc = cc_dt.get_now_utc_notz()
            self.finish_at_utc = None
            self.save()
        else:
            pls.db.fetch_object_from_db_by_pk(self, HL7Run.TABLENAME,
                                              HL7Run.FIELDS, param)

    def save(self):
        pls.db.save_object_to_db(self, HL7Run.TABLENAME, HL7Run.FIELDS,
                                 self.run_id is None)

    def call_script(self, files_exported):
        if not self.script_after_file_export:
            # No script to call
            return
        if not files_exported:
            # Didn't export any files; nothing to do.
            self.script_after_file_export = None  # wasn't called
            return
        args = [self.script_after_file_export] + files_exported
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            self.script_stdout, self.script_stderr = p.communicate()
            self.script_retcode = p.returncode
        except Exception as e:
            self.script_stdout = "Failed to run script"
            self.script_stderr = str(e)

    def finish(self):
        self.finish_at_utc = cc_dt.get_now_utc_notz()
        self.save()

    @classmethod
    def get_html_header_row(cls):
        html = u"<tr>"
        for fs in cls.FIELDSPECS:
            html += u"<th>{}</th>".format(fs["name"])
        html += u"</tr>\n"
        return html

    def get_html_data_row(self):
        html = u"<tr>"
        for fs in self.FIELDSPECS:
            name = fs["name"]
            value = ws.webify(getattr(self, name))
            html += u"<td>{}</td>".format(value)
        html += u"</tr>\n"
        return html


# =============================================================================
# HL7Message class
# =============================================================================

class HL7Message(object):
    TABLENAME = "_hl7_message_log"
    FIELDSPECS = [
        dict(name="msg_id", cctype="INT_UNSIGNED", pk=True,
             autoincrement=True, comment="Arbitrary primary key"),
        dict(name="run_id", cctype="INT_UNSIGNED",
             comment="FK to _hl7_run_log.run_id"),
        dict(name="basetable", cctype="TABLENAME", indexed=True,
             comment="Base table of task concerned"),
        dict(name="serverpk", cctype="INT_UNSIGNED", indexed=True,
             comment="Server PK of task in basetable (_pk field)"),
        dict(name="sent_at_utc", cctype="DATETIME",
             comment="Time message was sent at (UTC)"),
        dict(name="reply_at_utc", cctype="DATETIME",
             comment="(HL7) Time message was replied to (UTC)"),
        dict(name="success", cctype="BOOL",
             comment="Message sent successfully (and, for HL7, acknowledged)"),
        dict(name="failure_reason", cctype="TEXT",
             comment="Reason for failure"),
        dict(name="message", cctype="LONGTEXT",
             comment="(HL7) Message body, if kept"),
        dict(name="reply", cctype="TEXT",
             comment="(HL7) Server's reply, if kept"),
        dict(name="filename", cctype="TEXT",
             comment="(FILE) Destination filename"),
        dict(name="rio_metadata_filename", cctype="TEXT",
             comment="(FILE) RiO metadata filename, if used"),
        dict(name="cancelled", cctype="BOOL",
             comment="Message subsequently invalidated (may trigger resend)"),
        dict(name="cancelled_at_utc", cctype="DATETIME",
             comment="Time message was cancelled at (UTC)"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns=False):
        """Creates underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, *args, **kwargs):
        """Initializes.

        Use either:
            HL7Message(msg_id)
        or:
            HL7Message(basetable, serverpk, hl7run, recipient_def)
        """
        nargs = len(args)
        if nargs == 1:
            # HL7Message(msg_id)
            msg_id = args[0]
            pls.db.fetch_object_from_db_by_pk(self, HL7Message.TABLENAME,
                                              HL7Message.FIELDS, msg_id)
            self.hl7run = HL7Run(self.run_id)

        elif nargs == 4:
            # HL7Message(basetable, serverpk, hl7run, recipient_def)
            rnc_db.blank_object(self, HL7Message.FIELDS)
            self.basetable = args[0]
            self.serverpk = args[1]
            self.hl7run = args[2]
            if self.hl7run:
                self.run_id = self.hl7run.run_id
            self.recipient_def = args[3]
            self.show_queue_only = kwargs.get("show_queue_only", False)
            self.no_saving = self.show_queue_only
            self.task = cc_task.TaskFactory(self.basetable, self.serverpk)

        else:
            raise AssertionError("Bad call to HL7Message.__init__")

    def valid(self):
        """Checks for internal validity; returns Boolean."""
        if not self.recipient_def or not self.recipient_def.valid:
            return False
        if not self.basetable or self.serverpk is None:
            return False
        if not self.task:
            return False
        anonymous_ok = (self.recipient_def.using_file()
                        and self.recipient_def.include_anonymous)
        task_is_anonymous = self.task.is_anonymous()
        if task_is_anonymous and not anonymous_ok:
            return False
        # After this point, all anonymous tasks must be OK. So:
        task_has_primary_id = self.task.get_patient_idnum(
            self.recipient_def.primary_idnum) is not None
        if not task_is_anonymous and not task_has_primary_id:
            return False
        return True

    def save(self):
        """Writes to database, unless saving is prohibited."""
        if self.no_saving:
            return
        if self.basetable is None or self.serverpk is None:
            return
        is_new_record = self.msg_id is None
        pls.db.save_object_to_db(self, HL7Message.TABLENAME,
                                 HL7Message.FIELDS, is_new_record)

    def divert_to_file(self, f):
        """Write an HL7 message to a file."""
        infomsg = (
            "OUTBOUND MESSAGE DIVERTED FROM RECIPIENT {} AT {}\n".format(
                self.recipient_def.recipient,
                cc_dt.format_datetime(self.sent_at_utc, DATEFORMAT.ISO8601)
            )
        )
        print(infomsg, file=f)
        print(unicode(self.msg), file=f)
        print("\n", file=f)
        logger.debug(infomsg)
        self.host = self.recipient_def.divert_to_file
        if self.recipient_def.treat_diverted_as_sent:
            self.success = True

    def send(self, queue_file=None, divert_file=None):
        """Send an outbound HL7/file message, by the appropriate method."""
        # returns: tried, succeeded
        if not self.valid():
            return False, False

        if self.show_queue_only:
            print("{},{},{},{},{}".format(
                self.recipient_def.recipient,
                self.recipient_def.type,
                self.basetable,
                self.serverpk,
                self.task.when_created
            ), file=queue_file)
            return False, True

        if not self.hl7run:
            return True, False

        self.save()  # creates self.msg_id
        now = cc_dt.get_now_localtz()
        self.sent_at_utc = cc_dt.convert_datetime_to_utc_notz(now)

        if self.recipient_def.using_hl7():
            self.make_hl7_message(now)  # will write its own error msg/flags
            if self.recipient_def.divert_to_file:
                self.divert_to_file(divert_file)
            else:
                self.transmit_hl7()
        elif self.recipient_def.using_file():
            self.send_to_filestore()
        else:
            raise AssertionError("HL7Message.send: invalid recipient_def.type")
        self.save()

        logger.debug(
            "HL7Message.send: recipient={}, basetable={}, "
            "serverpk={}".format(
                self.recipient_def.recipient,
                self.basetable,
                self.serverpk
            )
        )
        return True, self.success

    def send_to_filestore(self):
        """Send a file to a filestore."""
        self.filename = self.recipient_def.get_filename(
            is_anonymous=self.task.is_anonymous(),
            surname=self.task.get_patient_surname(),
            forename=self.task.get_patient_forename(),
            dob=self.task.get_patient_dob(),
            sex=self.task.get_patient_sex(),
            idnums=self.task.get_patient_idnum_array(),
            idshortdescs=self.task.get_patient_idshortdesc_array(),
            creation_datetime=self.task.get_creation_datetime(),
            basetable=self.basetable,
            serverpk=self.serverpk,
        )

        filename = self.filename
        directory = os.path.dirname(filename)
        task = self.task
        task_format = self.recipient_def.task_format
        allow_overwrite = self.recipient_def.overwrite_files

        if task_format == VALUE.OUTPUTTYPE_PDF:
            data = task.get_pdf()
        elif task_format == VALUE.OUTPUTTYPE_HTML:
            data = task.get_html()
        elif task_format == VALUE.OUTPUTTYPE_XML:
            data = task.get_xml()
        else:
            raise AssertionError("write_to_filestore_file: bug")

        if not allow_overwrite and os.path.isfile(filename):
            self.failure_reason = "File already exists"
            return

        if self.recipient_def.make_directory:
            try:
                make_sure_path_exists(directory)
            except Exception as e:
                self.failure_reason = "Couldn't make directory {} ({})".format(
                    directory, e)
                return

        try:
            if task_format == VALUE.OUTPUTTYPE_PDF:
                # binary for PDF
                with open(filename, mode="wb") as f:
                    f.write(data)
            else:
                # UTF-8 for HTML, XML
                with codecs.open(filename, mode="w", encoding="utf8") as f:
                    f.write(data)
        except Exception as e:
            self.failure_reason = "Failed to open or write file: {}".format(e)
            return

        # RiO metadata too?
        if self.recipient_def.rio_metadata:
            # No spaces in filename
            self.rio_metadata_filename = cc_filename.change_filename_ext(
                self.filename, ".metadata").replace(" ", "")
            self.rio_metadata_filename = self.rio_metadata_filename
            metadata = task.get_rio_metadata(
                self.recipient_def.rio_idnum,
                self.recipient_def.rio_uploading_user,
                self.recipient_def.rio_document_type
            )
            try:
                DOS_NEWLINE = "\r\n"
                # ... Servelec say CR = "\r", but DOS is \r\n.
                with codecs.open(self.rio_metadata_filename, mode="w",
                                 encoding="ascii") as f:
                    # codecs.open() means that file writing is in binary mode,
                    # so newline conversion has to be manual:
                    f.write(metadata.replace("\n", DOS_NEWLINE))
                # UTF-8 is NOT supported by RiO for metadata.
            except Exception as e:
                self.failure_reason = ("Failed to open or write RiO metadata "
                                       "file: {}".format(e))
                return

        self.success = True

    def make_hl7_message(self, now):
        """Stores HL7 message in self.msg.

        May also store it in self.message (which is saved to the database), if
        we're saving HL7 messages.
        """
        # http://python-hl7.readthedocs.org/en/latest/index.html

        msh_segment = make_msh_segment(
            message_datetime=now,
            message_control_id=unicode(self.msg_id)
        )
        pid_segment = self.task.get_patient_hl7_pid_segment(self.recipient_def)
        other_segments = self.task.get_hl7_data_segments(self.recipient_def)

        # ---------------------------------------------------------------------
        # Whole message
        # ---------------------------------------------------------------------
        segments = [msh_segment, pid_segment] + other_segments
        self.msg = hl7.Message(SEGMENT_SEPARATOR, segments)
        if self.recipient_def.keep_message:
            self.message = unicode(self.msg)

    def transmit_hl7(self):
        """Sends HL7 message over TCP/IP."""
        # Default MLLP/HL7 port is 2575
        # ... MLLP = minimum lower layer protocol
        # ... http://www.cleo.com/support/byproduct/lexicom/usersguide/mllp_configuration.htm  # noqa
        # ... http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=hl7  # noqa
        # Essentially just a TCP socket with a minimal wrapper:
        #   http://stackoverflow.com/questions/11126918

        self.host = self.recipient_def.host
        self.port = self.recipient_def.port
        self.success = False

        # http://python-hl7.readthedocs.org/en/latest/api.html
        # ... but we've modified that
        try:
            with MLLPTimeoutClient(self.recipient_def.host,
                                   self.recipient_def.port,
                                   self.recipient_def.network_timeout_ms) \
                    as client:
                server_replied, reply = client.send_message(self.msg)
        except socket.timeout:
            self.failure_reason = "Failed to send message via MLLP: timeout"
            return
        except Exception as e:
            self.failure_reason = "Failed to send message via MLLP: {}".format(
                str(e))
            return

        if not server_replied:
            self.failure_reason = "No response from server"
            return
        self.reply_at_utc = cc_dt.get_now_utc_notz()
        if self.recipient_def.keep_reply:
            self.reply = reply
        try:
            replymsg = hl7.parse(reply)
        except Exception as e:
            self.failure_reason = "Malformed reply: {}".format(e)
            return

        self.success, self.failure_reason = msg_is_successful_ack(replymsg)

    @classmethod
    def get_html_header_row(cls, showmessage=False, showreply=False):
        """Returns HTML table header row for this class."""
        html = u"<tr>"
        for fs in cls.FIELDSPECS:
            if fs["name"] == "message" and not showmessage:
                continue
            if fs["name"] == "reply" and not showreply:
                continue
            html += u"<th>{}</th>".format(fs["name"])
        html += u"</tr>\n"
        return html

    def get_html_data_row(self, showmessage=False, showreply=False):
        """Returns HTML table data row for this instance."""
        html = u"<tr>"
        for fs in self.FIELDSPECS:
            name = fs["name"]
            if name == "message" and not showmessage:
                continue
            if name == "reply" and not showreply:
                continue
            value = ws.webify(getattr(self, name))
            if name == "serverpk":
                contents = u"<a href={}>{}</a>".format(
                    cc_task.get_url_task_html(self.basetable, self.serverpk),
                    value
                )
            elif name == "run_id":
                contents = u"<a href={}>{}</a>".format(
                    get_url_hl7_run(value),
                    value
                )
            else:
                contents = unicode(value)
            html += u"<td>{}</td>".format(contents)
        html += u"</tr>\n"
        return html

# =============================================================================
# MLLPTimeoutClient
# =============================================================================
# Modification of MLLPClient from python-hl7, to allow timeouts and failure.

SB = '\x0b'  # <SB>, vertical tab
EB = '\x1c'  # <EB>, file separator
CR = '\x0d'  # <CR>, \r
FF = '\x0c'  # <FF>, new page form feed

RECV_BUFFER = 4096


class MLLPTimeoutClient(object):
    """Class for MLLP TCP/IP transmission that implements timeouts."""

    def __init__(self, host, port, timeout_ms=None):
        """Creates MLLP client and opens socket."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        timeout_s = float(timeout_ms) / float(1000) \
            if timeout_ms is not None else None
        self.socket.settimeout(timeout_s)
        self.socket.connect((host, port))

    def __enter__(self):
        """For use with "with" statement."""
        return self

    def __exit__(self, exc_type, exc_val, trackeback):
        """For use with "with" statement."""
        self.close()

    def close(self):
        """Release the socket connection"""
        self.socket.close()

    def send_message(self, message):
        """Wraps a str, unicode, or :py:class:`hl7.Message` in a MLLP container
        and send the message to the server
        """
        if isinstance(message, hl7.Message):
            message = unicode(message)
        # wrap in MLLP message container
        data = SB + message + CR + EB + CR
        # ... the CR immediately after the message is my addition, because
        # HL7 Inspector otherwise says: "Warning: last segment have no segment
        # termination char 0x0d !" (sic).
        return self.send(data.encode('utf-8'))

    def send(self, data):
        """Low-level, direct access to the socket.send (data must be already
        wrapped in an MLLP container).  Blocks until the server returns.
        """
        # upload the data
        self.socket.send(data)
        # wait for the ACK/NACK
        try:
            ack_msg = self.socket.recv(RECV_BUFFER)
            return True, ack_msg
        except socket.timeout:
            return False, None


# =============================================================================
# URLs
# =============================================================================

def get_url_hl7_run(run_id):
    """URL to view an HL7Run instance."""
    url = cc_html.get_generic_action_url(ACTION.VIEW_HL7_RUN)
    url += cc_html.get_url_field_value_pair(PARAM.HL7RUNID, run_id)
    return url


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests():
    """Unit tests for cc_hl7 module."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    import cc_namedtuples
    from cc_unittest import unit_test_ignore
    import phq9

    # skip: send_all_pending_hl7_messages
    # skip: send_pending_hl7_messages

    current_pks = pls.db.fetchallfirstvalues(
        "SELECT _pk FROM {} WHERE _current".format(phq9.Phq9.get_tablename())
    )
    pk = current_pks[0] if current_pks else None
    task = phq9.Phq9(pk)
    pitlist = [
        cc_namedtuples.PatientIdentifierTuple(
            id="1", id_type="TT", assigning_authority="AA")
    ]
    now = cc_dt.get_now_localtz()

    unit_test_ignore("", get_mod11_checkdigit, "12345")
    unit_test_ignore("", get_mod11_checkdigit, "badnumber")
    unit_test_ignore("", get_mod11_checkdigit, None)
    unit_test_ignore("", make_msh_segment, now, "control_id")
    unit_test_ignore("", make_pid_segment, "fname", "sname", now, "sex",
                     "addr", pitlist)
    unit_test_ignore("", make_obr_segment, task)
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_PDF,
                     "obs_id", now, "responsible_observer")
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_HTML,
                     "obs_id", now, "responsible_observer")
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_XML,
                     "obs_id", now, "responsible_observer",
                     xml_field_comments=True)
    unit_test_ignore("", make_obx_segment, task, VALUE.OUTPUTTYPE_XML,
                     "obs_id", now, "responsible_observer",
                     xml_field_comments=False)
    unit_test_ignore("", escape_hl7_text, "blahblah")
    # not yet tested: HL7Message class
    # not yet tested: MLLPTimeoutClient class
