#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_exportrecipient.py

===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

**ExportRecipient class.**

"""

import configparser
import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_multiline,
)
from cardinal_pythonlib.datetimefunc import coerce_to_pendulum
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import simple_repr
from cardinal_pythonlib.sqlalchemy.list_types import IntListType
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_columns
from sqlalchemy.event.api import listens_for
from sqlalchemy.orm import (
    reconstructor,
    relationship,
    Session as SqlASession,
)
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Text,
)

from camcops_server.cc_modules.cc_filename import (
    filename_spec_is_valid,
    FileType,
    get_export_filename,
    patient_spec_for_filename_is_valid,
)
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_sqla_coltypes import (
    EmailAddressColType,
    ExportRecipientNameColType,
    ExportTransmissionMethodColType,
    FileSpecColType,
    HostnameColType,
    UrlColType,
    UserNameExternalColType,
)
from camcops_server.cc_modules.cc_sqlalchemy import Base

if TYPE_CHECKING:
    from sqlalchemy.engine.base import Connection
    from sqlalchemy.orm.mapper import Mapper
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DEFAULT_HL7_MLLP_PORT = 2575
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
    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = "REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY"  # noqa
    RIO_DOCUMENT_TYPE = "RIO_DOCUMENT_TYPE"
    RIO_IDNUM = "RIO_IDNUM"
    RIO_UPLOADING_USER = "RIO_UPLOADING_USER"
    START_DATETIME_UTC = "START_DATETIME_UTC"
    TASK_FORMAT = "TASK_FORMAT"
    TRANSMISSION_METHOD = "TRANSMISSION_METHOD"
    XML_FIELD_COMMENTS = "XML_FIELD_COMMENTS"


class InvalidExportRecipient(ValueError):
    """
    Exception for invalid export recipients.
    """
    pass


# Internal shorthand:
_Invalid = InvalidExportRecipient


class _Missing(_Invalid):
    """
    Exception for missing config parameters
    """
    def __init__(self, paramname: str) -> None:
        super().__init__("Missing {}".format(paramname))


# =============================================================================
# ExportRecipient class
# =============================================================================

class ExportRecipient(Base):
    """
    Class representing an export recipient.

    Full details of parameters are in the docs for the config file.
    """

    __tablename__ = "_export_recipients"

    # -------------------------------------------------------------------------
    # Identifying this object, and whether it's the "live" version
    # -------------------------------------------------------------------------
    id = Column(
        "id", BigInteger,
        primary_key=True, autoincrement=True, index=True,
        comment="Export recipient ID (arbitrary primary key)"
    )
    recipient_name = Column(
        "recipient_name", ExportRecipientNameColType, nullable=False,
        comment="Name of export recipient"
    )
    current = Column(
        "current", Boolean, default=False, nullable=False,
        comment="Is this the current record for this recipient? (If not, it's "
                "a historical record for audit purposes.)"
    )

    # -------------------------------------------------------------------------
    # How to export
    # -------------------------------------------------------------------------
    transmission_method = Column(
        "transmission_method", ExportTransmissionMethodColType, nullable=False,
        comment="Export transmission method (e.g. hl7, file)"
    )
    task_format = Column(
        "task_format", ExportTransmissionMethodColType,
        comment="Format that task information should be sent in (e.g. PDF), "
                "if not predetermined by the transmission method"
    )
    xml_field_comments = Column(
        "xml_field_comments", Boolean, default=True, nullable=False,
        comment="Whether to include field comments in XML output"
    )

    # -------------------------------------------------------------------------
    # What to export
    # -------------------------------------------------------------------------
    all_groups = Column(
        "active", Boolean, default=False, nullable=False,
        comment="Export all groups? (If not, see group_ids.)"
    )
    group_ids = Column(
        "group_ids", IntListType,
        comment="Integer IDs of CamCOPS group to export data from (as CSV)"
    )
    start_datetime_utc = Column(
        "start_datetime_utc", DateTime,
        comment="Start date/time for tasks (UTC)"
    )
    end_datetime_utc = Column(
        "end_datetime_utc", DateTime,
        comment="End date/time for tasks (UTC)"
    )
    finalized_only = Column(
        "finalized_only", Boolean, default=True, nullable=False,
        comment="Send only finalized tasks"
    )
    include_anonymous = Column(
        "include_anonymous", Boolean, default=False, nullable=False,
        comment="Include anonymous tasks? "
                "Not applicable to some methods (e.g. HL7)"
    )
    primary_idnum = Column(
        "primary_idnum", Integer, nullable=False,
        comment="Which ID number is used as the primary ID?"
    )
    require_idnum_mandatory = Column(
        "require_idnum_mandatory", Boolean,
        comment="Must the primary ID number be mandatory in the relevant "
                "policy?"
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    db_url = Column(
        "db_url", UrlColType,
        comment="(DATABASE) SQLAlchemy database URL for export"
    )
    db_echo = Column(
        "db_echo", Boolean, default=False, nullable=False,
        comment="(DATABASE) Echo SQL applied to destination database?"
    )
    db_include_blobs = Column(
        "db_include_blobs", Boolean, default=True, nullable=False,
        comment="(DATABASE) Include BLOBs?"
    )
    db_add_summaries = Column(
        "db_add_summaries", Boolean, default=True, nullable=False,
        comment="(DATABASE) Add summary information?"
    )
    db_patient_id_per_row = Column(
        "db_patient_id_per_row", Boolean, default=True, nullable=False,
        comment="(DATABASE) Add patient ID information per row?"
    )

    # -------------------------------------------------------------------------
    # Email
    # -------------------------------------------------------------------------
    email_host = Column(
        "email_host", HostnameColType,
        comment="(EMAIL) E-mail (SMTP) server host name/IP address"
    )
    email_port = Column(
        "email_port", Integer,
        comment="(EMAIL) E-mail (SMTP) server port number"
    )
    email_use_tls = Column(
        "email_use_tls", Boolean, default=True, nullable=False,
        comment="(EMAIL) Use explicit TLS connection?"
    )
    email_host_username = Column(
        "email_host_username", UserNameExternalColType,
        comment="(EMAIL) Username on e-mail server"
    )
    # email_host_password: not stored in database
    email_from = Column(
        "email_from", EmailAddressColType,
        comment='(EMAIL) "From:" address(es)'
    )
    email_sender = Column(
        "email_sender", EmailAddressColType,
        comment='(EMAIL) "Sender:" address(es)'
    )
    email_reply_to = Column(
        "email_reply_to", EmailAddressColType,
        comment='(EMAIL) "Reply-To:" address(es)'
    )
    email_to = Column(
        "email_to", Text,
        comment='(EMAIL) "To:" recipient(s), as a CSV list'
    )
    email_cc = Column(
        "email_cc", Text,
        comment='(EMAIL) "CC:" recipient(s), as a CSV list'
    )
    email_bcc = Column(
        "email_bcc", Text,
        comment='(EMAIL) "BCC:" recipient(s), as a CSV list'
    )
    email_patient_spec = Column(
        "email_patient", FileSpecColType,
        comment="(EMAIL) Patient specification"
    )
    email_patient_spec_if_anonymous = Column(
        "email_patient_spec_if_anonymous", FileSpecColType,
        comment="(EMAIL) Patient specification for anonymous tasks"
    )
    email_subject = Column(
        "email_subject", FileSpecColType,
        comment="(EMAIL) Subject specification"
    )
    email_body_as_html = Column(
        "email_body_as_html", Boolean, default=False, nullable=False,
        comment="(EMAIL) Is the body HTML, rather than plain text?"
    )
    email_body = Column(
        "email_body", Text,
        comment="(EMAIL) Body contents"
    )
    email_keep_message = Column(
        "email_keep_message", Boolean, default=False, nullable=False,
        comment="(EMAIL) Keep entire message?"
    )

    # -------------------------------------------------------------------------
    # HL7
    # -------------------------------------------------------------------------
    hl7_host = Column(
        "hl7_host", HostnameColType,
        comment="(HL7) Destination host name/IP address"
    )
    hl7_port = Column(
        "hl7_port", Integer,
        comment="(HL7) Destination port number"
    )
    hl7_ping_first = Column(
        "hl7_ping_first", Boolean, default=False, nullable=False,
        comment="(HL7) Ping via TCP/IP before sending HL7 messages?"
    )
    hl7_network_timeout_ms = Column(
        "hl7_network_timeout_ms", Integer,
        comment="(HL7) Network timeout (ms)."
    )
    hl7_keep_message = Column(
        "hl7_keep_message", Boolean, default=False, nullable=False,
        comment="(HL7) Keep copy of message in database? (May be large!)"
    )
    hl7_keep_reply = Column(
        "hl7_keep_reply", Boolean, default=False, nullable=False,
        comment="(HL7) Keep copy of server's reply in database?"
    )
    hl7_debug_divert_to_file = Column(
        "hl7_debug_divert_to_file", Text,
        comment="(HL7 debugging option) Divert to file with this name"
    )
    hl7_debug_treat_diverted_as_sent = Column(
        "hl7_debug_treat_diverted_as_sent", Boolean,
        default=False, nullable=False,
        comment="(HL7 debugging option) Treat messages diverted to file as sent"  # noqa
    )

    # -------------------------------------------------------------------------
    # File
    # -------------------------------------------------------------------------
    file_patient_spec = Column(
        "file_patient_spec", FileSpecColType,
        comment="(FILE) Patient part of filename specification"
    )
    file_patient_spec_if_anonymous = Column(
        "file_patient_spec_if_anonymous", FileSpecColType,
        comment="(FILE) Patient part of filename specification for anonymous tasks"  # noqa
    )
    file_filename_spec = Column(
        "file_filename_spec", FileSpecColType,
        comment="(FILE) Filename specification"
    )
    file_make_directory = Column(
        "file_make_directory", Boolean, default=True, nullable=False,
        comment="(FILE) Make destination directory if it doesn't already exist"
    )
    file_overwrite_files = Column(
        "file_overwrite_files", Boolean, default=False, nullable=False,
        comment="(FILE) Overwrite existing files"
    )
    file_export_rio_metadata = Column(
        "file_export_rio_metadata", Boolean, default=False, nullable=False,
        comment="(FILE) Export RiO metadata file along with main file?"
    )
    file_script_after_export = Column(
        "file_script_after_export", Text,
        comment="(FILE) Command/script to run after file export"
    )

    # -------------------------------------------------------------------------
    # File/RiO
    # -------------------------------------------------------------------------
    rio_idnum = Column(
        "rio_idnum", Integer,
        comment="(FILE / RiO) RiO metadata: which ID number is the RiO ID?"
    )
    rio_uploading_user = Column(
        "rio_uploading_user", Text,
        comment="(FILE / RiO) RiO metadata: name of automatic upload user"
    )
    rio_document_type = Column(
        "rio_document_type", Text,
        comment="(FILE / RiO) RiO metadata: document type for RiO"
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    export_runs = relationship("ExportRun")

    def __init__(self, *args, **kwargs) -> None:
        """
        Creates a blank :class:`ExportRecipient` object.

        NB not called when SQLAlchemy objects loaded from database; see
        :meth:`init_on_load` instead.
        """
        super().__init__(*args, **kwargs)

        # We need to initialize these explicitly, because if we create an
        # instance via "x = ExportRecipient()", they will be initialized to
        # None, without any recourse to our database to-and-fro conversion code
        # for each fieldtype.
        # (If we load from a database, things will be fine.)
        self.group_ids = []  # type: List[int]

        # *** todo: check HL7 ones below
        # HL7
        self.idnum_type_list = {}  # type: Dict[int, str]
        self.idnum_aa_list = {}  # type: Dict[int, str]

        # E-mail
        self.email_host_password = ""

    @reconstructor
    def init_on_load(self) -> None:
        """
        Called when SQLAlchemy recreates an object; see
        https://docs.sqlalchemy.org/en/latest/orm/constructors.html.
        """
        # *** todo: check HL7 ones below
        # HL7
        self.idnum_type_list = {}  # type: Dict[int, str]
        self.idnum_aa_list = {}  # type: Dict[int, str]

        # Email
        self.email_host_password = ""

    def __repr__(self):
        attrnames = set([attrname for attrname, _ in gen_columns(self)])
        attrnames.update(key for key in self.__dict__ if not key.startswith('_'))  # noqa
        return simple_repr(self, sorted(list(attrnames)))

    def __str__(self) -> str:
        return repr(self.recipient_name)

    def __eq__(self, other: "ExportRecipient") -> bool:
        """
        Does this object equal another -- meaning "sufficiently equal that we
        can use the same one, rather than making a new database copy"?
        """
        skip_attrs = ["id", "current"]  # mismatch on these is OK
        for attrname, _ in gen_columns(self):
            if attrname not in skip_attrs:
                if getattr(self, attrname) != getattr(other, attrname):
                    return False
        return True

    @classmethod
    def get_existing_matching_recipient(cls,
                                        dbsession: SqlASession,
                                        recipient: "ExportRecipient") \
            -> Optional["ExportRecipient"]:
        """
        Retrieves an active instance from the database that matches ``other``,
        if there is one.

        Args:
            dbsession: a :class:`sqlalchemy.orm.session.Session`
            recipient: an :class:`ExportRecipient`

        Returns:
            a database instance of :class:`ExportRecipient` that matches, or
            ``None``.
        """
        # noinspection PyPep8
        q = dbsession.query(cls).filter(
            cls.recipient_name == recipient.recipient_name,
            cls.current == True)
        results = q.all()
        if len(results) > 1:
            raise ValueError(
                "Database has gone wrong: more than one active record for "
                "{t}.{c} = {r}".format(
                    t=cls.__tablename__,
                    c=cls.recipient_name.name,  # ***
                    r=recipient.recipient_name,
                )
            )
        if results:
            r = results[0]
            if r == recipient:
                return r
        return None

    @staticmethod
    def create_dummy_recipient() -> "ExportRecipient":
        """
        Creates and returns a dummy :class:`ExportRecipient`.
        """
        d = ExportRecipient()

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

    @staticmethod
    def read_from_config(req: "CamcopsRequest",
                         parser: configparser.ConfigParser,
                         recipient_name: str) -> "ExportRecipient":
        """
        Reads from the config file and writes this instance's attributes.

        Args:
            req: a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
            parser: configparser INI file object
            recipient_name: name of recipient and of INI file section

        Returns:
            an :class:`ExportRecipient` object
        """
        assert parser and recipient_name

        dbsession = req.dbsession
        section = recipient_name
        cpr = ConfigParamExportRecipient
        r = ExportRecipient()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Identity
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.recipient_name = recipient_name

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # How to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.transmission_method = get_config_parameter(
            parser, section, cpr.TRANSMISSION_METHOD, str, "hl7")
        r.transmission_method = str(r.transmission_method).lower()
        r.task_format = get_config_parameter(
            parser, section, cpr.TASK_FORMAT, str, FileType.PDF)
        r.xml_field_comments = get_config_parameter_boolean(
            parser, section, cpr.XML_FIELD_COMMENTS, True)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.all_groups = get_config_parameter_boolean(
            parser, section, cpr.ALL_GROUPS, False)
        groupnames = get_config_parameter_multiline(
            parser, section, cpr.GROUPS, [])
        r.group_ids = []  # type: List[int]
        for groupname in groupnames:
            group = Group.get_group_by_name(dbsession, groupname)
            if not group:
                raise ValueError("No such group: {!r}".format(groupname))
            r.group_ids.append(group.id)
        r.group_ids.sort()
        sd = get_config_parameter(
            parser, section, cpr.START_DATETIME_UTC, str, None)
        r.start_datetime_utc = coerce_to_pendulum(sd, assume_local=False)
        ed = get_config_parameter(
            parser, section, cpr.END_DATETIME_UTC, str, None)
        r.end_datetime_utc = coerce_to_pendulum(ed, assume_local=False)
        r.finalized_only = get_config_parameter_boolean(
            parser, section, cpr.FINALIZED_ONLY, True)
        r.include_anonymous = get_config_parameter_boolean(
            parser, section, cpr.INCLUDE_ANONYMOUS, False)
        r.primary_idnum = get_config_parameter(
            parser, section, cpr.PRIMARY_IDNUM, int, None)
        r.require_idnum_mandatory = get_config_parameter_boolean(
            parser, section, cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY,
            True)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Database
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.db_url = get_config_parameter(
            parser, section, cpr.DB_URL, str, None)
        r.db_echo = get_config_parameter_boolean(
            parser, section, cpr.DB_ECHO, False)
        r.db_include_blobs = get_config_parameter_boolean(
            parser, section, cpr.DB_INCLUDE_BLOBS, True)
        r.db_add_summaries = get_config_parameter_boolean(
            parser, section, cpr.DB_ADD_SUMMARIES, True)
        r.db_patient_id_per_row = get_config_parameter_boolean(
            parser, section, cpr.DB_PATIENT_ID_PER_ROW, False)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Email
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def _make_email_csv_list(paramname: str) -> str:
            return ", ".join(
                x for x in get_config_parameter_multiline(
                    parser, section, paramname, [])
            )

        r.email_host = get_config_parameter(
            parser, section, cpr.EMAIL_HOST, str, None)
        r.email_port = get_config_parameter(
            parser, section, cpr.EMAIL_PORT, int, 25)
        r.email_use_tls = get_config_parameter_boolean(
            parser, section, cpr.EMAIL_USE_TLS, False)
        r.email_host_username = get_config_parameter(
            parser, section, cpr.EMAIL_HOST_USERNAME, str, None)
        r.email_host_password = get_config_parameter(
            parser, section, cpr.EMAIL_HOST_PASSWORD, str, "")
        r.email_from = get_config_parameter(
            parser, section, cpr.EMAIL_FROM, str, "")
        r.email_sender = get_config_parameter(
            parser, section, cpr.EMAIL_SENDER, str, "")
        r.email_reply_to = get_config_parameter(
            parser, section, cpr.EMAIL_REPLY_TO, str, "")
        r.email_to = _make_email_csv_list(cpr.EMAIL_TO)
        r.email_cc = _make_email_csv_list(cpr.EMAIL_CC)
        r.email_bcc = _make_email_csv_list(cpr.EMAIL_BCC)
        r.email_patient_spec_if_anonymous = get_config_parameter(
            parser, section, cpr.EMAIL_PATIENT_SPEC_IF_ANONYMOUS, str, "")
        r.email_patient_spec = get_config_parameter(
            parser, section, cpr.EMAIL_PATIENT_SPEC, str, "")
        r.email_subject = get_config_parameter(
            parser, section, cpr.EMAIL_SUBJECT, str, "")
        r.email_body_as_html = get_config_parameter_boolean(
            parser, section, cpr.EMAIL_BODY_IS_HTML, False)
        r.email_body = get_config_parameter(
            parser, section, cpr.EMAIL_BODY, str, "")
        r.email_keep_message = get_config_parameter_boolean(
            parser, section, cpr.EMAIL_KEEP_MESSAGE, False)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # HL7
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.hl7_host = get_config_parameter(
            parser, section, cpr.HL7_HOST, str, None)
        r.hl7_port = get_config_parameter(
            parser, section, cpr.HL7_PORT, int, DEFAULT_HL7_MLLP_PORT)
        r.hl7_ping_first = get_config_parameter_boolean(
            parser, section, cpr.HL7_PING_FIRST, True)
        r.hl7_network_timeout_ms = get_config_parameter(
            parser, section, cpr.HL7_NETWORK_TIMEOUT_MS, int, 10000)
        r.hl7_keep_message = get_config_parameter_boolean(
            parser, section, cpr.HL7_KEEP_MESSAGE, False)
        r.hl7_keep_reply = get_config_parameter_boolean(
            parser, section, cpr.HL7_KEEP_REPLY, False)
        r.hl7_debug_divert_to_file = get_config_parameter(
            # a filename:
            parser, section, cpr.HL7_DEBUG_DIVERT_TO_FILE, str, None)
        r.hl7_debug_treat_diverted_as_sent = get_config_parameter_boolean(
            parser, section, cpr.HL7_DEBUG_TREAT_DIVERTED_AS_SENT, False)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # File
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.file_patient_spec = get_config_parameter(
            parser, section, cpr.FILE_PATIENT_SPEC, str, None)
        r.file_patient_spec_if_anonymous = get_config_parameter(
            parser, section, cpr.FILE_PATIENT_SPEC_IF_ANONYMOUS, str,
            "anonymous")
        r.file_filename_spec = get_config_parameter(
            parser, section, cpr.FILE_FILENAME_SPEC, str, None)
        r.file_make_directory = get_config_parameter_boolean(
            parser, section, cpr.FILE_MAKE_DIRECTORY, False)
        r.file_overwrite_files = get_config_parameter_boolean(
            parser, section, cpr.FILE_OVERWRITE_FILES, False)
        r.file_export_rio_metadata = get_config_parameter_boolean(
            parser, section, cpr.FILE_EXPORT_RIO_METADATA, False)
        r.file_script_after_export = get_config_parameter(
            parser, section, cpr.FILE_SCRIPT_AFTER_EXPORT, str, None)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # RiO metadata
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.rio_idnum = get_config_parameter(
            parser, section, cpr.RIO_IDNUM, int, None)
        r.rio_uploading_user = get_config_parameter(
            parser, section, cpr.RIO_UPLOADING_USER, str, None)
        r.rio_document_type = get_config_parameter(
            parser, section, cpr.RIO_DOCUMENT_TYPE, str, None)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Validate and return
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        r.validate(req)
        return r

    @staticmethod
    def report_error(msg: str) -> None:
        """
        Report an error to the log.
        """
        log.error("ExportRecipient: {}", msg)

    def valid(self, req: "CamcopsRequest") -> bool:
        """
        Is this definition valid?
        """
        try:
            self.validate(req)
        except InvalidExportRecipient as e:
            self.report_error(str(e))
            return False

    def validate(self, req: "CamcopsRequest") -> None:
        """
        Validates, or raises :exc:`InvalidExportRecipient`.
        """
        dbsession = req.dbsession
        valid_which_idnums = req.valid_which_idnums

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Export type
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method not in ALL_TRANSMISSION_METHODS:
            raise _Invalid("Missing/invalid {}: {}".format(
                ConfigParamExportRecipient.TRANSMISSION_METHOD,
                self.transmission_method))

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.all_groups:
            groups = Group.get_all_groups(dbsession)
        else:
            groups = []  # type: List[Group]
            if not self.group_ids:
                raise _Invalid("Missing group_ids (from {})".format(
                    ConfigParamExportRecipient.GROUPS))
            for gid in self.group_ids:
                group = Group.get_group_by_id(dbsession, gid)
                if not group:
                    raise _Invalid("Invalid group ID: {}".format(gid))
                groups.append(group)

        if (self.transmission_method == ExportTransmissionMethod.HL7 and
                not self.primary_idnum):
            raise _Invalid("Must specify {} with {} = {}".format(
                ConfigParamExportRecipient.PRIMARY_IDNUM,
                ConfigParamExportRecipient.TRANSMISSION_METHOD,
                ExportTransmissionMethod.HL7
            ))

        if self.primary_idnum:
            if self.primary_idnum not in valid_which_idnums:
                raise _Invalid("Invalid {}: {}".format(
                    ConfigParamExportRecipient.PRIMARY_IDNUM,
                    self.primary_idnum))

            if self.require_idnum_mandatory:
                # (a) ID number must be mandatory in finalized records
                for group in groups:
                    finalize_policy = group.tokenized_finalize_policy()
                    if not finalize_policy.is_idnum_mandatory_in_policy(
                            which_idnum=self.primary_idnum,
                            valid_idnums=valid_which_idnums):
                        raise _Invalid(
                            "primary_idnum ({}) must be mandatory in "
                            "finalizing policy, but is not for group "
                            "{}".format(self.primary_idnum, group)
                        )
                    if not self.finalized_only:
                        # (b) ID number must also be mandatory in uploaded,
                        # non-finalized records
                        upload_policy = group.tokenized_upload_policy()
                        if not upload_policy.is_idnum_mandatory_in_policy(
                                which_idnum=self.primary_idnum,
                                valid_idnums=valid_which_idnums):
                            raise _Invalid(
                                "primary_idnum ({}) must be mandatory in "
                                "upload policy, but is not for group "
                                "{}".format(self.primary_idnum, group))

        if not self.task_format or self.task_format not in ALL_TASK_FORMATS:
            raise _Invalid("Missing/invalid {}: {}".format(
                ConfigParamExportRecipient.TASK_FORMAT,
                self.task_format))

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Database
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.DATABASE:
            if not self.db_url:
                raise _Missing(ConfigParamExportRecipient.DB_URL)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Email
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.EMAIL:
            if not self.email_host:
                raise _Missing(ConfigParamExportRecipient.EMAIL_HOST)
            if not self.email_host_username:
                raise _Missing(ConfigParamExportRecipient.EMAIL_HOST_USERNAME)
            if not self.email_from:
                raise _Missing(ConfigParamExportRecipient.EMAIL_FROM)
            if not any([self.email_to, self.email_cc, self.email_bcc]):
                raise _Invalid("Must specify some of: {}, {}, {}".format(
                    ConfigParamExportRecipient.EMAIL_TO,
                    ConfigParamExportRecipient.EMAIL_CC,
                    ConfigParamExportRecipient.EMAIL_BCC,
                ))
            if not self.email_subject:
                raise _Missing(ConfigParamExportRecipient.EMAIL_SUBJECT)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # HL7
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.HL7:
            if self.hl7_debug_divert_to_file:
                if not self.hl7_debug_treat_diverted_as_sent:
                    raise _Missing(ConfigParamExportRecipient.HL7_DEBUG_TREAT_DIVERTED_AS_SENT)  # noqa
            if not self.hl7_debug_divert_to_file:
                if not self.hl7_host:
                    raise _Missing(ConfigParamExportRecipient.HL7_HOST)
                if not self.hl7_port or self.hl7_port <= 0:
                    raise _Invalid("Missing/invalid {}: {}".format(
                        ConfigParamExportRecipient.HL7_PORT,
                        self.hl7_port))
            if not self.primary_idnum:
                raise _Missing(ConfigParamExportRecipient.PRIMARY_IDNUM)
            if not self.idnum_type_list.get(self.primary_idnum, None):
                raise _Invalid(
                    "Missing IDNUM_TYPE_{} (for primary ID)".format(
                        self.primary_idnum))
            if self.include_anonymous:
                raise _Invalid("Can't include anonymous tasks for HL7")

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # File
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if self.transmission_method == ExportTransmissionMethod.FILE:
            if not self.file_patient_spec_if_anonymous:
                raise _Missing(ConfigParamExportRecipient.FILE_PATIENT_SPEC_IF_ANONYMOUS)  # noqa
            if not self.file_patient_spec:
                raise _Missing(ConfigParamExportRecipient.FILE_PATIENT_SPEC)
            if not patient_spec_for_filename_is_valid(
                    patient_spec=self.file_patient_spec,
                    valid_which_idnums=valid_which_idnums):
                raise _Invalid("Invalid {}: {}".format(
                    ConfigParamExportRecipient.FILE_PATIENT_SPEC,
                    self.file_patient_spec))
            if not self.file_filename_spec:
                raise _Missing(ConfigParamExportRecipient.FILE_FILENAME_SPEC)  # noqa
            if not filename_spec_is_valid(
                    filename_spec=self.file_filename_spec,
                    valid_which_idnums=valid_which_idnums):
                raise _Invalid("Invalid {}: {}".format(
                    ConfigParamExportRecipient.FILE_FILENAME_SPEC,
                    self.file_filename_spec))
            # RiO metadata
            if self.file_export_rio_metadata:
                if self.rio_idnum not in valid_which_idnums:
                    raise _Invalid("Invalid {}: {}".format(
                        ConfigParamExportRecipient.RIO_IDNUM,
                        self.rio_idnum))
                if (not self.rio_uploading_user or
                        " " in self.rio_uploading_user or
                        len(self.rio_uploading_user) > RIO_MAX_USER_LEN):
                    raise _Invalid(
                        "Missing/invalid {}: {} (must be "
                        "present, contain no spaces, and max length "
                        "{})".format(
                            ConfigParamExportRecipient.RIO_UPLOADING_USER,
                            self.rio_uploading_user,
                            RIO_MAX_USER_LEN))
                if not self.rio_document_type:
                    raise _Missing(ConfigParamExportRecipient.RIO_DOCUMENT_TYPE)  # noqa

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
                            treat_as_filename: bool) -> str:
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

        Returns:
            a processed string specification (e.g. a filename; an e-mail
            subject)
        """
        return get_export_filename(
            req=req,
            patient_spec_if_anonymous=patient_spec_if_anonymous,
            patient_spec=patient_spec,
            filename_spec=spec,
            task_format=self.task_format,
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

    def get_filename(self, req: "CamcopsRequest", task: "Task") -> str:
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


# noinspection PyUnusedLocal
@listens_for(ExportRecipient, "after_insert")
@listens_for(ExportRecipient, "after_update")
def _check_current(mapper: "Mapper",
                   connection: "Connection",
                   target: ExportRecipient) -> None:
    """
    Ensures that only one :class:`ExportRecipient` is marked as ``current``
    per ``recipient_name``.

    As per
    https://stackoverflow.com/questions/6269469/mark-a-single-row-in-a-table-in-sqlalchemy.
    """  # noqa
    if target.current:
        # noinspection PyUnresolvedReferences
        connection.execute(
            ExportRecipient.__table__.update()
            .values(current=False)
            .where(ExportRecipient.recipient_name == target.recipient_name)
            .where(ExportRecipient.id != target.id)
        )
