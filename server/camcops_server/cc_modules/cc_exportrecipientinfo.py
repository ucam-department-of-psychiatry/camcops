#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_exportrecipient.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**ExportRecipientInfo class.**

The purpose of this is to capture information without using an SQLAlchemy
class. The :class:`camcops_server.cc_modules.cc_config.CamcopsConfig` class
uses this, as it needs to be readable in the absence of a database connection
(q.v.).

"""

import configparser
import datetime
import logging
from typing import List, Optional, TYPE_CHECKING

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_multiline,
)
from cardinal_pythonlib.datetimefunc import (
    coerce_to_pendulum,
    pendulum_to_utc_datetime_without_tz,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import simple_repr

from camcops_server.cc_modules.cc_filename import (
    filename_spec_is_valid,
    FileType,
    get_export_filename,
    patient_spec_for_filename_is_valid,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

COMMA = ","
DEFAULT_HL7_MLLP_PORT = 2575
DEFAULT_HL7_TIMEOUT_MS = 10000
DEFAULT_PATIENT_SPEC_IF_ANONYMOUS = "anonymous"
DEFAULT_SMTP_PORT = 25
CONFIG_RECIPIENT_PREFIX = "recipient:"
RIO_MAX_USER_LEN = 10


class ExportTransmissionMethod(object):
    """
    Possible export transmission methods.
    """
    DATABASE = "database"
    EMAIL = "email"
    HL7 = "hl7"
    FILE = "file"


ALL_TRANSMISSION_METHODS = [
    v for k, v in vars(ExportTransmissionMethod).items()
    if not k.startswith("_")
]  # ... the values of all the relevant attributes

ALL_TASK_FORMATS = [FileType.HTML, FileType.PDF, FileType.XML]


class ConfigParamExportRecipient(object):
    """
    Possible configuration file parameters that relate to "export recipient"
    definitions.
    """
    ALL_GROUPS = "ALL_GROUPS"
    DB_ADD_SUMMARIES = "DB_ADD_SUMMARIES"
    DB_ECHO = "DB_ECHO"
    DB_INCLUDE_BLOBS = "DB_INCLUDE_BLOBS"
    DB_PATIENT_ID_PER_ROW = "DB_PATIENT_ID_PER_ROW"
    DB_URL = "DB_URL"
    EMAIL_BCC = "EMAIL_BCC"
    EMAIL_BODY = "EMAIL_BODY"
    EMAIL_BODY_IS_HTML = "EMAIL_BODY_IS_HTML"
    EMAIL_CC = "EMAIL_CC"
    EMAIL_FROM = "EMAIL_FROM"
    EMAIL_HOST = "EMAIL_HOST"
    EMAIL_HOST_PASSWORD = "EMAIL_HOST_PASSWORD"
    EMAIL_HOST_USERNAME = "EMAIL_HOST_USERNAME"
    EMAIL_KEEP_MESSAGE = "EMAIL_KEEP_MESSAGE"
    EMAIL_PORT = "EMAIL_PORT"
    EMAIL_RECIPIENTS = "EMAIL_RECIPIENTS"
    EMAIL_REPLY_TO = "EMAIL_REPLY_TO"
    EMAIL_SENDER = "EMAIL_SENDER"
    EMAIL_PATIENT_SPEC = "EMAIL_PATIENT_SPEC"
    EMAIL_PATIENT_SPEC_IF_ANONYMOUS = "EMAIL_PATIENT_SPEC_IF_ANONYMOUS"
    EMAIL_SUBJECT = "EMAIL_SUBJECT"
    EMAIL_TIMEOUT = "EMAIL_TIMEOUT"
    EMAIL_TO = "EMAIL_TO"
    EMAIL_USE_TLS = "EMAIL_USE_TLS"
    END_DATETIME_UTC = "END_DATETIME_UTC"
    FILE_EXPORT_RIO_METADATA = "FILE_EXPORT_RIO_METADATA"
    FILE_FILENAME_SPEC = "FILE_FILENAME_SPEC"
    FILE_MAKE_DIRECTORY = "FILE_MAKE_DIRECTORY"
    FILE_OVERWRITE_FILES = "FILE_OVERWRITE_FILES"
    FILE_PATIENT_SPEC = "FILE_PATIENT_SPEC"
    FILE_PATIENT_SPEC_IF_ANONYMOUS = "FILE_PATIENT_SPEC_IF_ANONYMOUS"
    FILE_SCRIPT_AFTER_EXPORT = "FILE_SCRIPT_AFTER_EXPORT"
    FINALIZED_ONLY = "FINALIZED_ONLY"
    GROUPS = "GROUPS"
    HL7_DEBUG_DIVERT_TO_FILE = "HL7_DEBUG_DIVERT_TO_FILE"
    HL7_DEBUG_TREAT_DIVERTED_AS_SENT = "HL7_DEBUG_TREAT_DIVERTED_AS_SENT"
    HL7_HOST = "HL7_HOST"
    HL7_KEEP_MESSAGE = "HL7_KEEP_MESSAGE"
    HL7_KEEP_REPLY = "HL7_KEEP_REPLY"
    HL7_NETWORK_TIMEOUT_MS = "HL7_NETWORK_TIMEOUT_MS"
    HL7_PING_FIRST = "HL7_PING_FIRST"
    HL7_PORT = "HL7_PORT"
    IDNUM_AA_PREFIX = "IDNUM_AA_"  # unusual; prefix not parameter
    IDNUM_TYPE_PREFIX = "IDNUM_TYPE_"  # unusual; prefix not parameter
    INCLUDE_ANONYMOUS = "INCLUDE_ANONYMOUS"
    PRIMARY_IDNUM = "PRIMARY_IDNUM"
    PUSH = "PUSH"
    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = "REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY"  # noqa
    RIO_DOCUMENT_TYPE = "RIO_DOCUMENT_TYPE"
    RIO_IDNUM = "RIO_IDNUM"
    RIO_UPLOADING_USER = "RIO_UPLOADING_USER"
    START_DATETIME_UTC = "START_DATETIME_UTC"
    TASK_FORMAT = "TASK_FORMAT"
    TASKS = "TASKS"
    TRANSMISSION_METHOD = "TRANSMISSION_METHOD"
    XML_FIELD_COMMENTS = "XML_FIELD_COMMENTS"


class InvalidExportRecipient(ValueError):
    """
    Exception for invalid export recipients.
    """
    def __init__(self, recipient_name: str, msg: str) -> None:
        super().__init__(
            f"For export recipient [{recipient_name}]: {msg}")


# Internal shorthand:
_Invalid = InvalidExportRecipient


class _Missing(_Invalid):
    """
    Exception for missing config parameters
    """
    def __init__(self, recipient_name: str, paramname: str) -> None:
        super().__init__(recipient_name,
                         f"Missing parameter {paramname}")


# =============================================================================
# ExportRecipientInfo class
# =============================================================================

class ExportRecipientInfo(object):
    """
    Class representing an export recipient, that is not an SQLAlchemy ORM
    object.

    This has an unfortunate close relationship with
    :class:`camcops_server.cc_modules.cc_exportrecipient.ExportRecipient`
    (q.v.).

    Full details of parameters are in the docs for the config file.
    """
    IGNORE_FOR_EQ_ATTRNAMES = [
        # Attribute names to ignore for equality comparison
        "email_host_password",
    ]

    def __init__(self, other: "ExportRecipientInfo" = None) -> None:
        """
        Initializes, optionally copying attributes from ``other``.
        """
        self.recipient_name = ""

        # How to export

        self.transmission_method = ExportTransmissionMethod.EMAIL
        self.push = False
        self.task_format = FileType.XML
        self.xml_field_comments = False

        # What to export

        self.all_groups = False
        self.group_names = []  # type: List[str]  # not in database; see group_ids  # noqa
        self.group_ids = []  # type: List[int]
        self.tasks = []  # type: List[str]
        self.start_datetime_utc = None  # type: Optional[datetime.datetime]
        self.end_datetime_utc = None  # type: Optional[datetime.datetime]
        self.finalized_only = True
        self.include_anonymous = False
        self.primary_idnum = None  # type: Optional[int]
        self.require_idnum_mandatory = True

        # Database

        self.db_url = ""
        self.db_echo = False
        self.db_include_blobs = False
        self.db_add_summaries = True
        self.db_patient_id_per_row = True

        # Email

        self.email_host = ""
        self.email_port = DEFAULT_SMTP_PORT
        self.email_use_tls = False
        self.email_host_username = ""
        self.email_host_password = ""  # not in database for security
        self.email_from = ""
        self.email_sender = ""
        self.email_reply_to = ""
        self.email_to = ""  # CSV list
        self.email_cc = ""  # CSV list
        self.email_bcc = ""  # CSV list
        self.email_patient_spec = ""
        self.email_patient_spec_if_anonymous = DEFAULT_PATIENT_SPEC_IF_ANONYMOUS  # noqa
        self.email_subject = ""
        self.email_body_as_html = False
        self.email_body = ""
        self.email_keep_message = False

        # HL7

        self.hl7_host = ""
        self.hl7_port = DEFAULT_HL7_MLLP_PORT
        self.hl7_ping_first = False
        self.hl7_network_timeout_ms = DEFAULT_HL7_TIMEOUT_MS
        self.hl7_keep_message = False
        self.hl7_keep_reply = False
        self.hl7_debug_divert_to_file = False
        self.hl7_debug_treat_diverted_as_sent = False

        # File

        self.file_patient_spec = ""
        self.file_patient_spec_if_anonymous = DEFAULT_PATIENT_SPEC_IF_ANONYMOUS
        self.file_filename_spec = ""
        self.file_make_directory = True
        self.file_overwrite_files = False
        self.file_export_rio_metadata = False
        self.file_script_after_export = ""

        # File/RiO

        self.rio_idnum = None  # type: Optional[int]
        self.rio_uploading_user = ""
        self.rio_document_type = ""

        # Copy from other?
        if other is not None:
            assert isinstance(other, ExportRecipientInfo)
            for attrname in self.get_attrnames():
                # Note that both "self" and "other" may be an ExportRecipient
                # rather than an ExportRecipientInfo.
                if hasattr(other, attrname):
                    setattr(self, attrname, getattr(other, attrname))

    def get_attrnames(self) -> List[str]:
        """
        Returns all relevant attribute names.
        """
        return sorted([key for key in self.__dict__
                       if not key.startswith('_')])

    def get_eq_attrnames(self) -> List[str]:
        """
        Returns attribute names to use for equality comparison.
        """
        return [x for x in self.get_attrnames()
                if x not in self.IGNORE_FOR_EQ_ATTRNAMES]

    def __repr__(self):
        return simple_repr(self, self.get_attrnames())

    def __str__(self) -> str:
        return repr(self.recipient_name)

    def __eq__(self, other: "ExportRecipientInfo") -> bool:
        """
        Does this object equal another -- meaning "sufficiently equal that we
        can use the same one, rather than making a new database copy"?
        """
        for attrname in self.get_attrnames():
            if attrname not in self.IGNORE_FOR_EQ_ATTRNAMES:
                selfattr = getattr(self, attrname)
                otherattr = getattr(other, attrname)
                # log.critical("{}.{}: {} {} {}",
                #              self.__class__.__name__,
                #              attrname,
                #              selfattr,
                #              "==" if selfattr == otherattr else "!=",
                #              otherattr)
                if selfattr != otherattr:
                    log.debug(
                        "{}: For {!r}, new export recipient mismatches "
                        "previous copy on {}: {!r} != {!r}",
                        self.__class__.__name__,
                        self.recipient_name,
                        attrname,
                        selfattr,
                        otherattr)
                    return False
        return True

    @classmethod
    def create_dummy_recipient(cls) -> "ExportRecipientInfo":
        """
        Creates and returns a dummy :class:`ExportRecipientInfo`.
        """
        d = cls()

        d.recipient_name = "_dummy_export_recipient_"
        d.current = True

        d.transmission_method = ExportTransmissionMethod.FILE

        d.all_groups = True
        d.primary_idnum = 1
        d.require_idnum_mandatory = False
        d.finalized_only = False
        d.task_format = FileType.XML

        # File
        d.include_anonymous = True
        d.file_patient_spec_if_anonymous = "anonymous"
        d.file_patient_spec = "{surname}_{forename}_{idshortdesc1}{idnum1}"
        d.file_filename_spec = (
            "/tmp/camcops_debug_testing/"
            "TestCamCOPS_{patient}_{created}_{tasktype}-{serverpk}"
            ".{filetype}"
        )
        d.file_overwrite_files = False
        d.file_make_directory = True

        return d

    @classmethod
    def read_from_config(cls,
                         parser: configparser.ConfigParser,
                         recipient_name: str) -> "ExportRecipientInfo":
        """
        Reads from the config file and writes this instance's attributes.

        Args:
            parser: configparser INI file object
            recipient_name: name of recipient and of INI file section

        Returns:
            an :class:`ExportRecipient` object, which is **not** currently in
            a database session
        """
        assert recipient_name
        log.debug("Loading export config for recipient {!r}", recipient_name)

        section = CONFIG_RECIPIENT_PREFIX + recipient_name
        cpr = ConfigParamExportRecipient
        r = cls()

        def _get_str(paramname: str, default: str = None) -> Optional[str]:
            return get_config_parameter(
                parser, section, paramname, str, default)

        def _get_bool(paramname: str, default: bool) -> bool:
            return get_config_parameter_boolean(
                parser, section, paramname, default)

        def _get_int(paramname: str, default: int = None) -> Optional[int]:
            return get_config_parameter(
                parser, section, paramname, int, default)

        def _get_multiline(paramname: str) -> List[str]:
            return get_config_parameter_multiline(
                parser, section, paramname, [])

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Identity
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.recipient_name = recipient_name

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # How to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.transmission_method = _get_str(cpr.TRANSMISSION_METHOD)
        r.transmission_method = str(r.transmission_method).lower()
        # Check this one immediately, since we use it in conditions below
        if r.transmission_method not in ALL_TRANSMISSION_METHODS:
            raise _Invalid(
                r.recipient_name,
                f"Missing/invalid "
                f"{ConfigParamExportRecipient.TRANSMISSION_METHOD}: "
                f"{r.transmission_method}"
            )
        r.push = _get_bool(cpr.PUSH, False)
        r.task_format = _get_str(cpr.TASK_FORMAT, FileType.PDF)
        r.xml_field_comments = _get_bool(cpr.XML_FIELD_COMMENTS, True)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.all_groups = _get_bool(cpr.ALL_GROUPS, False)
        r.group_names = _get_multiline(cpr.GROUPS)
        r.group_ids = []  # type: List[int]
        # ... read later by validate_db_dependent()
        r.tasks = sorted([x.lower() for x in _get_multiline(cpr.TASKS)])
        sd = _get_str(cpr.START_DATETIME_UTC)
        r.start_datetime_utc = pendulum_to_utc_datetime_without_tz(
            coerce_to_pendulum(sd, assume_local=False)) if sd else None
        ed = _get_str(cpr.END_DATETIME_UTC)
        r.end_datetime_utc = pendulum_to_utc_datetime_without_tz(
            coerce_to_pendulum(ed, assume_local=False)) if ed else None
        r.finalized_only = _get_bool(cpr.FINALIZED_ONLY, True)
        r.include_anonymous = _get_bool(cpr.INCLUDE_ANONYMOUS, False)
        r.primary_idnum = _get_int(cpr.PRIMARY_IDNUM)
        r.require_idnum_mandatory = _get_bool(cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY, True)  # noqa

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Database
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if r.transmission_method == ExportTransmissionMethod.DATABASE:
            r.db_url = _get_str(cpr.DB_URL)
            r.db_echo = _get_bool(cpr.DB_ECHO, False)
            r.db_include_blobs = _get_bool(cpr.DB_INCLUDE_BLOBS, True)
            r.db_add_summaries = _get_bool(cpr.DB_ADD_SUMMARIES, True)
            r.db_patient_id_per_row = _get_bool(cpr.DB_PATIENT_ID_PER_ROW, False)  # noqa

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Email
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def _make_email_csv_list(paramname: str) -> str:
            return ", ".join(x for x in _get_multiline(paramname))

        if r.transmission_method == ExportTransmissionMethod.EMAIL:
            r.email_host = _get_str(cpr.EMAIL_HOST)
            r.email_port = _get_int(cpr.EMAIL_PORT, DEFAULT_SMTP_PORT)
            r.email_use_tls = _get_bool(cpr.EMAIL_USE_TLS, False)
            r.email_host_username = _get_str(cpr.EMAIL_HOST_USERNAME, "")
            r.email_host_password = _get_str(cpr.EMAIL_HOST_PASSWORD, "")
            r.email_from = _get_str(cpr.EMAIL_FROM, "")
            r.email_sender = _get_str(cpr.EMAIL_SENDER, "")
            r.email_reply_to = _get_str(cpr.EMAIL_REPLY_TO, "")
            r.email_to = _make_email_csv_list(cpr.EMAIL_TO)
            r.email_cc = _make_email_csv_list(cpr.EMAIL_CC)
            r.email_bcc = _make_email_csv_list(cpr.EMAIL_BCC)
            r.email_patient_spec_if_anonymous = _get_str(cpr.EMAIL_PATIENT_SPEC_IF_ANONYMOUS, "")  # noqa
            r.email_patient_spec = _get_str(cpr.EMAIL_PATIENT_SPEC, "")
            r.email_subject = _get_str(cpr.EMAIL_SUBJECT, "")
            r.email_body_as_html = _get_bool(cpr.EMAIL_BODY_IS_HTML, False)
            r.email_body = _get_str(cpr.EMAIL_BODY, "")
            r.email_keep_message = _get_bool(cpr.EMAIL_KEEP_MESSAGE, False)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # HL7
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if r.transmission_method == ExportTransmissionMethod.HL7:
            r.hl7_host = _get_str(cpr.HL7_HOST)
            r.hl7_port = _get_int(cpr.HL7_PORT, DEFAULT_HL7_MLLP_PORT)
            r.hl7_ping_first = _get_bool(cpr.HL7_PING_FIRST, True)
            r.hl7_network_timeout_ms = _get_int(cpr.HL7_NETWORK_TIMEOUT_MS, DEFAULT_HL7_TIMEOUT_MS)  # noqa
            r.hl7_keep_message = _get_bool(cpr.HL7_KEEP_MESSAGE, False)
            r.hl7_keep_reply = _get_bool(cpr.HL7_KEEP_REPLY, False)
            r.hl7_debug_divert_to_file = _get_bool(cpr.HL7_DEBUG_DIVERT_TO_FILE, False)  # noqa
            r.hl7_debug_treat_diverted_as_sent = _get_bool(cpr.HL7_DEBUG_TREAT_DIVERTED_AS_SENT, False)  # noqa

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # File
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if r._need_file_name():
            r.file_patient_spec = _get_str(cpr.FILE_PATIENT_SPEC)
            r.file_patient_spec_if_anonymous = _get_str(cpr.FILE_PATIENT_SPEC_IF_ANONYMOUS, "anonymous")  # noqa
            r.file_filename_spec = _get_str(cpr.FILE_FILENAME_SPEC)

        if r._need_file_disk_options():
            r.file_make_directory = _get_bool(cpr.FILE_MAKE_DIRECTORY, False)
            r.file_overwrite_files = _get_bool(cpr.FILE_OVERWRITE_FILES, False)

        if r.transmission_method == ExportTransmissionMethod.FILE:
            r.file_export_rio_metadata = _get_bool(cpr.FILE_EXPORT_RIO_METADATA, False)  # noqa
            r.file_script_after_export = _get_str(cpr.FILE_SCRIPT_AFTER_EXPORT)

        if r._need_rio_metadata_options():
            # RiO metadata
            r.rio_idnum = _get_int(cpr.RIO_IDNUM)
            r.rio_uploading_user = _get_str(cpr.RIO_UPLOADING_USER)
            r.rio_document_type = _get_str(cpr.RIO_DOCUMENT_TYPE)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Validate the basics and return
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.validate_db_independent()
        return r

    @classmethod
    def report_error(cls, msg: str) -> None:
        """
        Report an error to the log.
        """
        log.error("{}: {}", cls.__name__, msg)

    def valid(self, req: "CamcopsRequest") -> bool:
        """
        Is this definition valid?

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        try:
            self.validate(req)
            return True
        except InvalidExportRecipient as e:
            self.report_error(str(e))
            return False

    def validate(self, req: "CamcopsRequest") -> None:
        """
        Validates all aspects.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`

        Raises:
            :exc:`InvalidExportRecipient` if invalid
        """
        self.validate_db_independent()
        self.validate_db_dependent(req)

    def validate_db_independent(self) -> None:
        """
        Validates the database-independent aspects of the
        :class:`ExportRecipient`, or raises :exc:`InvalidExportRecipient`.
        """
        # noinspection PyUnresolvedReferences
        import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa
        from camcops_server.cc_modules.cc_task import all_task_tablenames  # delayed import # noqa

        def fail_invalid(msg: str) -> None:
            raise _Invalid(self.recipient_name, msg)

        def fail_missing(paramname: str) -> None:
            raise _Missing(self.recipient_name, paramname)

        cpr = ConfigParamExportRecipient

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Export type
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method not in ALL_TRANSMISSION_METHODS:
            fail_invalid(
                f"Missing/invalid {cpr.TRANSMISSION_METHOD}: "
                f"{self.transmission_method}")
        no_push = [ExportTransmissionMethod.DATABASE]
        if self.push and self.transmission_method in no_push:
            fail_invalid(f"Push notifications not supported for these "
                         f"transmission methods: {no_push!r}")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if not self.all_groups and not self.group_names:
            fail_invalid(f"Missing group names (from {cpr.GROUPS})")

        all_basetables = all_task_tablenames()
        for basetable in self.tasks:
            if basetable not in all_basetables:
                fail_invalid(f"Task {basetable!r} doesn't exist")

        if (self.transmission_method == ExportTransmissionMethod.HL7 and
                not self.primary_idnum):
            fail_invalid(
                f"Must specify {cpr.PRIMARY_IDNUM} with "
                f"{cpr.TRANSMISSION_METHOD} = {ExportTransmissionMethod.HL7}"
            )

        if not self.task_format or self.task_format not in ALL_TASK_FORMATS:
            fail_invalid(
                f"Missing/invalid {cpr.TASK_FORMAT}: {self.task_format}")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Database
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.DATABASE:
            if not self.db_url:
                fail_missing(cpr.DB_URL)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Email
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.EMAIL:
            if not self.email_host:
                # You can't send an e-mail without knowing which server to send
                # it to.
                fail_missing(cpr.EMAIL_HOST)
            # Username is *not* required by all servers!
            if not self.email_from:
                # From is mandatory in all e-mails.
                # (Sender and Reply-To are optional.)
                fail_missing(cpr.EMAIL_FROM)
            if COMMA in self.email_from:
                # RFC 5322 permits multiple addresses in From, but Python
                # sendmail doesn't.
                fail_invalid(
                    f"Only a single 'From:' address permitted; was "
                    f"{self.email_from!r}")
            if not any([self.email_to, self.email_cc, self.email_bcc]):
                # At least one destination is required (obviously).
                fail_invalid(
                    f"Must specify some of: {cpr.EMAIL_TO}, {cpr.EMAIL_CC}, "
                    f"{cpr.EMAIL_BCC}")
            if COMMA in self.email_sender:
                # RFC 5322 permits multiple addresses in From and Reply-To,
                # but only one in Sender.
                fail_invalid(
                    f"Only a single 'Sender:' address permitted; was "
                    f"{self.email_sender!r}")
            if not self.email_subject:
                # A subject is not obligatory for e-mails in general, but we
                # will require one for e-mails sent from CamCOPS.
                fail_missing(cpr.EMAIL_SUBJECT)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # HL7
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.HL7:
            if not self.hl7_debug_divert_to_file:
                if not self.hl7_host:
                    fail_missing(cpr.HL7_HOST)
                if not self.hl7_port or self.hl7_port <= 0:
                    fail_invalid(
                        f"Missing/invalid {cpr.HL7_PORT}: {self.hl7_port}")
            if not self.primary_idnum:
                fail_missing(cpr.PRIMARY_IDNUM)
            if self.include_anonymous:
                fail_invalid("Can't include anonymous tasks for HL7")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # File
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self._need_file_name():
            # Filename options
            if not self.file_patient_spec_if_anonymous:
                fail_missing(cpr.FILE_PATIENT_SPEC_IF_ANONYMOUS)
            if not self.file_patient_spec:
                fail_missing(cpr.FILE_PATIENT_SPEC)
            if not self.file_filename_spec:
                fail_missing(cpr.FILE_FILENAME_SPEC)

        if self._need_rio_metadata_options():
            # RiO metadata
            if (not self.rio_uploading_user or
                    " " in self.rio_uploading_user or
                    len(self.rio_uploading_user) > RIO_MAX_USER_LEN):
                fail_invalid(
                    f"Missing/invalid {cpr.RIO_UPLOADING_USER}: "
                    f"{self.rio_uploading_user} (must be present, contain no "
                    f"spaces, and max length {RIO_MAX_USER_LEN})")
            if not self.rio_document_type:
                fail_missing(cpr.RIO_DOCUMENT_TYPE)

    def validate_db_dependent(self, req: "CamcopsRequest") -> None:
        """
        Validates the database-dependent aspects of the
        :class:`ExportRecipient`, or raises :exc:`InvalidExportRecipient`.

        :meth:`validate_db_independent` should have been called first; this
        function presumes that those checks have been passed.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        from camcops_server.cc_modules.cc_group import Group  # delayed import  # noqa

        def fail_invalid(msg: str) -> None:
            raise _Invalid(self.recipient_name, msg)

        dbsession = req.dbsession
        valid_which_idnums = req.valid_which_idnums
        cpr = ConfigParamExportRecipient

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Set group IDs from group names
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.group_ids = []  # type: List[int]
        for groupname in self.group_names:
            group = Group.get_group_by_name(dbsession, groupname)
            if not group:
                raise ValueError(f"No such group: {groupname!r}")
            self.group_ids.append(group.id)
        self.group_ids.sort()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.all_groups:
            groups = Group.get_all_groups(dbsession)
        else:
            groups = []  # type: List[Group]
            for gid in self.group_ids:
                group = Group.get_group_by_id(dbsession, gid)
                if not group:
                    fail_invalid(f"Invalid group ID: {gid}")
                groups.append(group)

        if self.primary_idnum:
            if self.primary_idnum not in valid_which_idnums:
                fail_invalid(
                    f"Invalid {cpr.PRIMARY_IDNUM}: {self.primary_idnum}")

            if self.require_idnum_mandatory:
                # (a) ID number must be mandatory in finalized records
                for group in groups:
                    finalize_policy = group.tokenized_finalize_policy()
                    if not finalize_policy.is_idnum_mandatory_in_policy(
                            which_idnum=self.primary_idnum,
                            valid_idnums=valid_which_idnums):
                        fail_invalid(
                            f"primary_idnum ({self.primary_idnum}) must be "
                            f"mandatory in finalizing policy, but is not for "
                            f"group {group}"
                        )
                    if not self.finalized_only:
                        # (b) ID number must also be mandatory in uploaded,
                        # non-finalized records
                        upload_policy = group.tokenized_upload_policy()
                        if not upload_policy.is_idnum_mandatory_in_policy(
                                which_idnum=self.primary_idnum,
                                valid_idnums=valid_which_idnums):
                            fail_invalid(
                                f"primary_idnum ({self.primary_idnum}) must "
                                f"be mandatory in upload policy (because "
                                f"{cpr.FINALIZED_ONLY} is false), but is not "
                                f"for group {group}")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # File
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self._need_file_name():
            # Filename options
            if not patient_spec_for_filename_is_valid(
                    patient_spec=self.file_patient_spec,
                    valid_which_idnums=valid_which_idnums):
                fail_invalid(f"Invalid {cpr.FILE_PATIENT_SPEC}: "
                             f"{self.file_patient_spec}")
            if not filename_spec_is_valid(
                    filename_spec=self.file_filename_spec,
                    valid_which_idnums=valid_which_idnums):
                fail_invalid(f"Invalid {cpr.FILE_FILENAME_SPEC}: "
                             f"{self.file_filename_spec}")

        if self._need_rio_metadata_options():
            # RiO metadata
            if self.rio_idnum not in valid_which_idnums:
                fail_invalid(f"Invalid ID number type for "
                             f"{cpr.RIO_IDNUM}: {self.rio_idnum}")

    def _need_file_name(self) -> bool:
        """
        Do we need to know about filenames?
        """
        return (
            self.transmission_method == ExportTransmissionMethod.FILE or
            (self.transmission_method == ExportTransmissionMethod.HL7 and
             self.hl7_debug_divert_to_file) or
            self.transmission_method == ExportTransmissionMethod.EMAIL
        )

    def _need_file_disk_options(self) -> bool:
        """
        Do we need to know about how to write to disk (e.g. overwrite, make
        directories)?
        """
        return (
            self.transmission_method == ExportTransmissionMethod.FILE or
            (self.transmission_method == ExportTransmissionMethod.HL7 and
             self.hl7_debug_divert_to_file)
        )

    def _need_rio_metadata_options(self) -> bool:
        """
        Do we need to know about RiO metadata?
        """
        return (
            self.transmission_method == ExportTransmissionMethod.FILE and
            self.file_export_rio_metadata
        )

    def using_db(self) -> bool:
        """
        Is the recipient a database?
        """
        return self.transmission_method == ExportTransmissionMethod.DATABASE

    def using_email(self) -> bool:
        """
        Is the recipient an e-mail system?
        """
        return self.transmission_method == ExportTransmissionMethod.EMAIL

    def using_file(self) -> bool:
        """
        Is the recipient a filestore?
        """
        return self.transmission_method == ExportTransmissionMethod.FILE

    def using_hl7(self) -> bool:
        """
        Is the recipient an HL7 recipient?
        """
        return self.transmission_method == ExportTransmissionMethod.HL7

    def anonymous_ok(self) -> bool:
        """
        Does this recipient permit/want anonymous tasks?
        """
        return self.include_anonymous and not (
            # Methods that require patient identification:
            self.using_hl7()
        )

    def is_incremental(self) -> bool:
        """
        Is this an incremental export? (That's the norm, except for database
        exports.)
        """
        return not self.using_db()

    @staticmethod
    def get_hl7_id_type(req: "CamcopsRequest", which_idnum: int) -> str:
        """
        Get the HL7 ID type for a specific CamCOPS ID number type.
        """
        iddef = req.get_idnum_definition(which_idnum)
        return (iddef.hl7_id_type or '') if iddef else ''

    @staticmethod
    def get_hl7_id_aa(req: "CamcopsRequest", which_idnum: int) -> str:
        """
        Get the HL7 Assigning Authority for a specific CamCOPS ID number type.
        """
        iddef = req.get_idnum_definition(which_idnum)
        return (iddef.hl7_assigning_authority or '') if iddef else ''

    def _get_processed_spec(self,
                            req: "CamcopsRequest",
                            task: "Task",
                            patient_spec_if_anonymous: str,
                            patient_spec: str,
                            spec: str,
                            treat_as_filename: bool,
                            override_task_format: str = "") -> str:
        """
        Returns a
        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            task: a :class:`camcops_server.cc_modules.cc_task.Task`
        patient_spec_if_anonymous:
            patient specification to be used for anonymous tasks
        patient_spec:
            patient specification to be used for patient-identifiable tasks
        spec:
            specification to use to create the string (may include
            patient information from the patient specification)
        treat_as_filename:
            convert the resulting string to be a safe filename
        override_task_format:
            format to use to override the default (typically to force an
            extension e.g. for HL7 debugging)

        Returns:
            a processed string specification (e.g. a filename; an e-mail
            subject)
        """
        return get_export_filename(
            req=req,
            patient_spec_if_anonymous=patient_spec_if_anonymous,
            patient_spec=patient_spec,
            filename_spec=spec,
            filetype=(override_task_format if override_task_format
                      else self.task_format),
            is_anonymous=task.is_anonymous,
            surname=task.get_patient_surname(),
            forename=task.get_patient_forename(),
            dob=task.get_patient_dob(),
            sex=task.get_patient_sex(),
            idnum_objects=task.get_patient_idnum_objects(),
            creation_datetime=task.get_creation_datetime(),
            basetable=task.tablename,
            serverpk=task.get_pk(),
            skip_conversion_to_safe_filename=not treat_as_filename,
        )

    def get_filename(self, req: "CamcopsRequest", task: "Task",
                     override_task_format: str = "") -> str:
        """
        Get the export filename, for file transfers.
        """
        return self._get_processed_spec(
            req=req,
            task=task,
            patient_spec_if_anonymous=self.file_patient_spec_if_anonymous,
            patient_spec=self.file_patient_spec,
            spec=self.file_filename_spec,
            treat_as_filename=True,
            override_task_format=override_task_format,
        )

    def get_email_subject(self, req: "CamcopsRequest", task: "Task") -> str:
        """
        Gets a substituted e-mail subject.
        """
        return self._get_processed_spec(
            req=req,
            task=task,
            patient_spec_if_anonymous=self.email_patient_spec_if_anonymous,
            patient_spec=self.email_patient_spec,
            spec=self.email_subject,
            treat_as_filename=False,
        )

    def get_email_body(self, req: "CamcopsRequest", task: "Task") -> str:
        """
        Gets a substituted e-mail body.
        """
        return self._get_processed_spec(
            req=req,
            task=task,
            patient_spec_if_anonymous=self.email_patient_spec_if_anonymous,
            patient_spec=self.email_patient_spec,
            spec=self.email_body,
            treat_as_filename=False,
        )
