#!/usr/bin/env python3
# cc_recipdef.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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

import configparser
import datetime
from typing import List, Optional

import cardinal_pythonlib.rnc_db as rnc_db
from cardinal_pythonlib.rnc_lang import AttrDict

from .cc_configfile import get_config_parameter, get_config_parameter_boolean
from .cc_constants import NUMBER_OF_IDNUMS, VALUE
from . import cc_dt
from . import cc_filename
from .cc_logger import log
from . import cc_policy


# =============================================================================
# Constants
# =============================================================================

DEFAULT_HL7_PORT = 2575
RECIPIENT_TYPE = AttrDict({
    "HL7": "hl7",
    "FILE": "file",
})
RIO_MAX_USER_LEN = 10


# =============================================================================
# RecipientDefinition class
# =============================================================================

class RecipientDefinition(object):
    """Class representing HL7/file recipient.

    Full details of parameters are in the demonstration config file.
    """
    FIELDSPECS = [
        # common
        dict(name="recipient", cctype="HOSTNAME", indexed=True,
             comment="Recipient definition name (determines uniqueness)"),
        dict(name="type", cctype="SENDINGFORMAT",
             comment="Recipient type (e.g. hl7, file)"),
        dict(name="primary_idnum", cctype="INT_UNSIGNED",
             comment="Which ID number was used as the primary ID?"),
        dict(name="require_idnum_mandatory", cctype="BOOL",
             comment="Must the primary ID number be mandatory in the relevant "
             "policy?"),
        dict(name="start_date", cctype="DATETIME",
             comment="Start date for tasks (UTC)"),
        dict(name="end_date", cctype="DATETIME",
             comment="End date for tasks (UTC)"),
        dict(name="finalized_only", cctype="BOOL",
             comment="Send only finalized tasks"),
        dict(name="task_format", cctype="SENDINGFORMAT",
             comment="Format that task information was sent in (e.g. PDF)"),
        dict(name="xml_field_comments", cctype="BOOL",
             comment="Whether to include field comments in XML output"),
        # HL7
        dict(name="host", cctype="HOSTNAME",
             comment="(HL7) Destination host name/IP address"),
        dict(name="port", cctype="INT_UNSIGNED",
             comment="(HL7) Destination port number"),
        dict(name="divert_to_file", cctype="TEXT",
             comment="(HL7) Divert to file"),
        dict(name="treat_diverted_as_sent", cctype="BOOL",
             comment="(HL7) Treat messages diverted to file as sent"),
        # File
        dict(name="include_anonymous", cctype="BOOL",
             comment="(FILE) Include anonymous tasks"),
        dict(name="overwrite_files", cctype="BOOL",
             comment="(FILE) Overwrite existing files"),
        dict(name="rio_metadata", cctype="BOOL",
             comment="(FILE) Export RiO metadata file along with main file?"),
        dict(name="rio_idnum", cctype="INT",
             comment="(FILE) RiO metadata: which ID number is the RiO ID?"),
        dict(name="rio_uploading_user", cctype="TEXT",
             comment="(FILE) RiO metadata: name of automatic upload user"),
        dict(name="rio_document_type", cctype="TEXT",
             comment="(FILE) RiO metadata: document type for RiO"),
        dict(name="script_after_file_export", cctype="TEXT",
             comment="(FILE) Command/script to run after file export")
    ]
    # ... fieldspecs are actually used by HL7Run class
    FIELDS = [x["name"] for x in FIELDSPECS]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize. Possible methods:

            RecipientDefinition()
            RecipientDefinition(config, section)

        Args:
            config: configparser INI file object
            section: name of recipient and of INI file section
        """
        rnc_db.blank_object(self, RecipientDefinition.FIELDS)
        # HL7 fields not copied to database
        self.ping_first = None
        self.network_timeout_ms = None
        self.idnum_type_list = [None] * NUMBER_OF_IDNUMS
        self.idnum_aa_list = [None] * NUMBER_OF_IDNUMS
        self.keep_message = None
        self.keep_reply = None
        # File fields not copied to database (because actual filename stored):
        self.patient_spec_if_anonymous = None
        self.patient_spec = None
        self.filename_spec = None
        self.make_directory = None
        # Some default values we never want to be None
        self.include_anonymous = False
        # Internal use
        self.valid = False

        # Variable constructor...
        nargs = len(args)
        if nargs == 0:
            # dummy one
            self.type = RECIPIENT_TYPE.FILE
            self.primary_idnum = 1
            self.require_idnum_mandatory = False
            self.finalized_only = False
            self.task_format = VALUE.OUTPUTTYPE_XML
            # File
            self.include_anonymous = True
            self.patient_spec_if_anonymous = "anonymous"
            self.patient_spec = "{surname}_{forename}_{idshortdesc1}{idnum1}"
            self.filename_spec = (
                "/tmp/camcops_debug_testing/"
                "TestCamCOPS_{patient}_{created}_{tasktype}-{serverpk}"
                ".{filetype}"
            )
            self.overwrite_files = False
            self.make_directory = True
            return
        elif nargs != 2:
            raise AssertionError("RecipientDefinition: bad __init__ call")

        # Standard constructor
        config = args[0]
        section = args[1]

        self.recipient = section
        try:
            self.type = get_config_parameter(
                config, section, "TYPE", str, "hl7")
            self.primary_idnum = get_config_parameter(
                config, section, "PRIMARY_IDNUM", int, None)
            self.require_idnum_mandatory = get_config_parameter_boolean(
                config, section, "REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY",
                True)
            sd = get_config_parameter(
                config, section, "START_DATE", str, None)
            self.start_date = cc_dt.get_date_from_string(sd)
            ed = get_config_parameter(
                config, section, "END_DATE", str, None)
            self.end_date = cc_dt.get_date_from_string(ed)
            self.finalized_only = get_config_parameter_boolean(
                config, section, "FINALIZED_ONLY", True)
            self.task_format = get_config_parameter(
                config, section, "TASK_FORMAT", str, VALUE.OUTPUTTYPE_PDF)
            self.xml_field_comments = get_config_parameter_boolean(
                config, section, "XML_FIELD_COMMENTS", True)

            # HL7
            if self.using_hl7():
                self.host = get_config_parameter(
                    config, section, "HOST", str, None)
                self.port = get_config_parameter(
                    config, section, "PORT", int, DEFAULT_HL7_PORT)
                self.ping_first = get_config_parameter_boolean(
                    config, section, "PING_FIRST", True)
                self.network_timeout_ms = get_config_parameter(
                    config, section, "NETWORK_TIMEOUT_MS", int, 10000)
                for n in range(1, NUMBER_OF_IDNUMS + 1):
                    i = n - 1
                    nstr = str(n)
                    self.idnum_type_list[i] = get_config_parameter(
                        config, section, "IDNUM_TYPE_" + nstr, str, "")
                    self.idnum_aa_list[i] = get_config_parameter(
                        config, section, "IDNUM_AA_" + nstr, str, "")
                self.keep_message = get_config_parameter_boolean(
                    config, section, "KEEP_MESSAGE", False)
                self.keep_reply = get_config_parameter_boolean(
                    config, section, "KEEP_REPLY", False)
                self.divert_to_file = get_config_parameter(
                    config, section, "DIVERT_TO_FILE", str, None)
                self.treat_diverted_as_sent = get_config_parameter_boolean(
                    config, section, "TREAT_DIVERTED_AS_SENT", False)
                if self.divert_to_file:
                    self.host = None
                    self.port = None
                    self.ping_first = None
                    self.network_timeout_ms = None
                    self.keep_reply = None
                self.include_anonymous = False

            # File
            if self.using_file():
                self.include_anonymous = get_config_parameter_boolean(
                    config, section, "INCLUDE_ANONYMOUS", False)
                self.patient_spec_if_anonymous = get_config_parameter(
                    config, section, "PATIENT_SPEC_IF_ANONYMOUS", str,
                    "anonymous")
                self.patient_spec = get_config_parameter(
                    config, section, "PATIENT_SPEC", str, None)
                self.filename_spec = get_config_parameter(
                    config, section, "FILENAME_SPEC", str, None)
                self.overwrite_files = get_config_parameter_boolean(
                    config, section, "OVERWRITE_FILES", False)
                self.make_directory = get_config_parameter_boolean(
                    config, section, "MAKE_DIRECTORY", False)
                self.rio_metadata = get_config_parameter_boolean(
                    config, section, "RIO_METADATA", False)
                self.rio_idnum = get_config_parameter(
                    config, section, "RIO_IDNUM", int, None)
                self.rio_uploading_user = get_config_parameter(
                    config, section, "RIO_UPLOADING_USER", str, None)
                self.rio_document_type = get_config_parameter(
                    config, section, "RIO_DOCUMENT_TYPE", str, None)
                self.script_after_file_export = get_config_parameter(
                    config, section, "SCRIPT_AFTER_FILE_EXPORT", str, None)

            self.check_valid()

        except configparser.NoSectionError:
            log.warning("Config file section missing: [{}]".format(
                section
            ))
            self.valid = False

    @staticmethod
    def report_error(msg) -> None:
        log.error("RecipientDefinition: {}".format(msg))

    def check_valid(self) -> None:
        """Performs validity check and sets self.valid"""
        self.valid = False
        if self.type not in RECIPIENT_TYPE.values():
            self.report_error("missing/invalid type: {}".format(self.type))
            return
        if not self.primary_idnum and self.using_hl7():
            self.report_error("missing primary_idnum")
            return
        if self.primary_idnum < 1 or self.primary_idnum > NUMBER_OF_IDNUMS:
            self.report_error("invalid primary_idnum: {}".format(
                self.primary_idnum))
            return
        if self.primary_idnum and self.require_idnum_mandatory:
            # (a) ID number must be mandatory in finalized records
            if not cc_policy.is_idnum_mandatory_in_finalize_policy(
                    self.primary_idnum):
                self.report_error(
                    "primary_idnum ({}) not mandatory in finalizing policy, "
                    "but needs to be".format(self.primary_idnum))
                return
            if not self.finalized_only:
                # (b) ID number must also be mandatory in uploaded,
                # non-finalized records
                if not cc_policy.is_idnum_mandatory_in_upload_policy(
                        self.primary_idnum):
                    self.report_error(
                        "primary_idnum ({}) not mandatory in upload policy, "
                        "but needs to be".format(self.primary_idnum))
                    return
        if not self.task_format or \
                self.task_format not in [
                    VALUE.OUTPUTTYPE_PDF,
                    VALUE.OUTPUTTYPE_HTML,
                    VALUE.OUTPUTTYPE_XML,
                ]:
            self.report_error(
                "missing/invalid task_format: {}".format(self.task_format))
            return
        if not self.task_format == VALUE.OUTPUTTYPE_XML:
            self.xml_field_comments = None
        # HL7
        if self.type == RECIPIENT_TYPE.HL7:
            if not self.divert_to_file:
                if not self.host:
                    self.report_error("missing host")
                    return
                if not self.port or self.port <= 0:
                    self.report_error(
                        "missing/invalid port: {}".format(self.port))
                    return
            if not self.idnum_type_list[self.primary_idnum - 1]:
                self.report_error(
                    "missing IDNUM_TYPE_{} (for primary ID)".format(
                        self.primary_idnum))
                return
        # File
        if self.type == RECIPIENT_TYPE.FILE:
            if not self.patient_spec_if_anonymous:
                self.report_error("missing patient_spec_if_anonymous")
                return
            if not self.patient_spec:
                self.report_error("missing patient_spec")
                return
            if not cc_filename.patient_spec_for_filename_is_valid(
                    self.patient_spec):
                self.report_error(
                    "invalid patient_spec: {}".format(self.patient_spec))
                return
            if not self.filename_spec:
                self.report_error("missing filename_spec")
                return
            if not cc_filename.filename_spec_is_valid(self.filename_spec):
                self.report_error(
                    "invalid filename_spec: {}".format(self.filename_spec))
                return
            # RiO metadata
            if self.rio_metadata:
                if not (1 <= self.rio_idnum <= NUMBER_OF_IDNUMS):
                    # ... test handles None values; 1 < None < 3 is False
                    self.report_error(
                        "invalid rio_idnum: {}".format(self.rio_idnum))
                    return
                if (not self.rio_uploading_user or
                        " " in self.rio_uploading_user or
                        len(self.rio_uploading_user) > RIO_MAX_USER_LEN):
                    self.report_error(
                        "missing/invalid rio_uploading_user: {} (must be "
                        "present, contain no spaces, and max length "
                        "{})".format(
                            self.rio_uploading_user,
                            RIO_MAX_USER_LEN))
                    return
                if not self.rio_document_type:
                    self.report_error("missing rio_document_type")
                    return

        # This section would be BETTER with a try/raise/except block, rather
        # than a bunch of return statements.

        # Done
        self.valid = True

    def using_hl7(self) -> bool:
        """Is the recipient an HL7 recipient?"""
        return self.type == RECIPIENT_TYPE.HL7

    def using_file(self) -> bool:
        """Is the recipient a filestore?"""
        return self.type == RECIPIENT_TYPE.FILE

    def get_id_type(self, idnum: int) -> str:
        """Get HL7 ID type for a specific ID number.

        Args:
            idnum: From 1 to NUMBER_OF_IDNUMS inclusive.
        """
        if idnum is None or idnum < 1 or idnum > NUMBER_OF_IDNUMS:
            return None
        return self.idnum_type_list[idnum - 1]

    def get_id_aa(self, idnum: int) -> str:
        """Get HL7 ID type for a specific ID number.

        Args:
            idnum: From 1 to NUMBER_OF_IDNUMS inclusive.
        """
        if idnum is None or idnum < 1 or idnum > NUMBER_OF_IDNUMS:
            return None
        return self.idnum_aa_list[idnum - 1]

    def get_filename(self,
                     is_anonymous: bool = False,
                     surname: str = None,
                     forename: str = None,
                     dob: datetime.datetime = None,
                     sex: str = None,
                     idnums: List[Optional[int]] = [None]*NUMBER_OF_IDNUMS,
                     idshortdescs: List[str] = [""]*NUMBER_OF_IDNUMS,
                     creation_datetime: datetime.datetime = None,
                     basetable: str = None,
                     serverpk: int = None) -> str:
        """Get filename, for file transfers."""
        return cc_filename.get_export_filename(
            self.patient_spec_if_anonymous,
            self.patient_spec,
            self.filename_spec,
            self.task_format,
            is_anonymous=is_anonymous,
            surname=surname,
            forename=forename,
            dob=dob,
            sex=sex,
            idnums=idnums,
            idshortdescs=idshortdescs,
            creation_datetime=creation_datetime,
            basetable=basetable,
            serverpk=serverpk)

    def __str__(self):
        """String representation."""
        return (
            "RecipientDefinition: " + ", ".join([
                "{}={}".format(key, str(getattr(self, key)))
                for key in self.__dict__ if not key.startswith('_')
            ])
        )
