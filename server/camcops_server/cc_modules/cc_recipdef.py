#!/usr/bin/env python
# camcops_server/cc_modules/cc_recipdef.py

"""
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
"""

import configparser
import logging
from typing import Dict, List, TYPE_CHECKING

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
)
from cardinal_pythonlib.datetimefunc import coerce_to_pendulum_date
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import simple_repr
from pendulum import DateTime as Pendulum

from .cc_filename import (
    filename_spec_is_valid,
    FileType,
    get_export_filename,
    patient_spec_for_filename_is_valid,
)
from .cc_group import Group

if TYPE_CHECKING:
    from .cc_patientidnum import PatientIdNum
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DEFAULT_HL7_PORT = 2575
RIO_MAX_USER_LEN = 10


class Hl7RecipientType(object):
    HL7 = "hl7"
    FILE = "file"


ALL_RECIPIENT_TYPES = [
    Hl7RecipientType.HL7,
    Hl7RecipientType.FILE,
]


class ConfigParamRecipient(object):
    DIVERT_TO_FILE = "DIVERT_TO_FILE"
    END_DATE = "END_DATE"
    FILENAME_SPEC = "FILENAME_SPEC"
    FINALIZED_ONLY = "FINALIZED_ONLY"
    GROUP_ID = "GROUP_ID"
    HOST = "HOST"
    IDNUM_AA_PREFIX = "IDNUM_AA_"  # unusual
    IDNUM_TYPE_PREFIX = "IDNUM_TYPE_"  # unusual
    INCLUDE_ANONYMOUS = "INCLUDE_ANONYMOUS"
    KEEP_MESSAGE = "KEEP_MESSAGE"
    KEEP_REPLY = "KEEP_REPLY"
    MAKE_DIRECTORY = "MAKE_DIRECTORY"
    NETWORK_TIMEOUT_MS = "NETWORK_TIMEOUT_MS"
    OVERWRITE_FILES = "OVERWRITE_FILES"
    PATIENT_SPEC = "PATIENT_SPEC"
    PATIENT_SPEC_IF_ANONYMOUS = "PATIENT_SPEC_IF_ANONYMOUS"
    PING_FIRST = "PING_FIRST"
    PORT = "PORT"
    PRIMARY_IDNUM = "PRIMARY_IDNUM"
    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = "REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY"  # noqa
    RIO_DOCUMENT_TYPE = "RIO_DOCUMENT_TYPE"
    RIO_IDNUM = "RIO_IDNUM"
    RIO_METADATA = "RIO_METADATA"
    RIO_UPLOADING_USER = "RIO_UPLOADING_USER"
    SCRIPT_AFTER_FILE_EXPORT = "SCRIPT_AFTER_FILE_EXPORT"
    START_DATE = "START_DATE"
    TASK_FORMAT = "TASK_FORMAT"
    TREAT_DIVERTED_AS_SENT = "TREAT_DIVERTED_AS_SENT"
    TYPE = "TYPE"
    XML_FIELD_COMMENTS = "XML_FIELD_COMMENTS"


# =============================================================================
# RecipientDefinition class
# =============================================================================

class RecipientDefinition(object):
    """
    Class representing HL7/file recipient.

    Full details of parameters are in the demonstration config file.
    """

    def __init__(self,
                 config: configparser.ConfigParser = None,
                 section: str = None) -> None:
        """
        Initialize. Possible methods:

            RecipientDefinition()  # FOR TESTING ONLY
            RecipientDefinition(config, section)

        Args:
            config: configparser INI file object
            section: name of recipient and of INI file section
        """
        # Some attributes will be copied to HL7Run:
        # ... common
        self.recipient = None  # type: str
        self.type = None  # type: str
        self.group_id = None  # type: int
        self.primary_idnum = None  # type: int
        self.require_idnum_mandatory = True
        self.start_date = None  # type: Pendulum
        self.end_date = None  # type: Pendulum
        self.finalized_only = True
        self.task_format = None  # type: str
        self.xml_field_comments = True

        # ... HL7
        self.host = ''
        self.port = None  # type: int
        self.divert_to_file = None  # type: str
        self.treat_diverted_as_sent = False

        # ... File
        self.include_anonymous = False
        self.overwrite_files = False
        self.rio_metadata = True
        self.rio_idnum = None  # type: int
        self.rio_uploading_user = None  # type: str
        self.rio_document_type = None  # type: str
        self.script_after_file_export = None  # type: str

        # HL7 fields not copied to database
        self.ping_first = True
        self.network_timeout_ms = None  # type: int
        self.idnum_type_list = {}  # type: Dict[int, str]
        self.idnum_aa_list = {}  # type: Dict[int, str]
        self.keep_message = True
        self.keep_reply = True
        # File fields not copied to database (because actual filename stored):
        self.patient_spec_if_anonymous = None  # type: str
        self.patient_spec = None  # type: str
        self.filename_spec = None  # type: str
        self.make_directory = True
        # Some default values we never want to be None
        self.include_anonymous = False

        # Variable constructor...
        if config is None and section is None:
            # dummy one
            self.type = Hl7RecipientType.FILE
            self.group_id = 1
            self.primary_idnum = 1
            self.require_idnum_mandatory = False
            self.finalized_only = False
            self.task_format = FileType.XML
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

        assert config and section, "RecipientDefinition: bad __init__ call"

        # Standard constructor
        self.recipient = section
        cpr = ConfigParamRecipient
        try:
            self.type = get_config_parameter(
                config, section, cpr.TYPE, str, "hl7")
            self.type = str(self.type).lower()
            self.group_id = get_config_parameter(
                config, section, cpr.GROUP_ID, int, None)
            self.primary_idnum = get_config_parameter(
                config, section, cpr.PRIMARY_IDNUM, int, None)
            self.require_idnum_mandatory = get_config_parameter_boolean(
                config, section, cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY,
                True)
            sd = get_config_parameter(
                config, section, cpr.START_DATE, str, None)
            self.start_date = coerce_to_pendulum_date(sd)
            ed = get_config_parameter(
                config, section, cpr.END_DATE, str, None)
            self.end_date = coerce_to_pendulum_date(ed)
            self.finalized_only = get_config_parameter_boolean(
                config, section, cpr.FINALIZED_ONLY, True)
            self.task_format = get_config_parameter(
                config, section, cpr.TASK_FORMAT, str, FileType.PDF)
            self.xml_field_comments = get_config_parameter_boolean(
                config, section, cpr.XML_FIELD_COMMENTS, True)

            # HL7
            if self.using_hl7():
                self.host = get_config_parameter(
                    config, section, cpr.HOST, str, None)
                self.port = get_config_parameter(
                    config, section, cpr.PORT, int, DEFAULT_HL7_PORT)
                self.ping_first = get_config_parameter_boolean(
                    config, section, cpr.PING_FIRST, True)
                self.network_timeout_ms = get_config_parameter(
                    config, section, cpr.NETWORK_TIMEOUT_MS, int, 10000)
                self.keep_message = get_config_parameter_boolean(
                    config, section, cpr.KEEP_MESSAGE, False)
                self.keep_reply = get_config_parameter_boolean(
                    config, section, cpr.KEEP_REPLY, False)
                self.divert_to_file = get_config_parameter(
                    # a filename:
                    config, section, cpr.DIVERT_TO_FILE, str, None)
                self.treat_diverted_as_sent = get_config_parameter_boolean(
                    config, section, cpr.TREAT_DIVERTED_AS_SENT, False)
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
                    config, section, cpr.INCLUDE_ANONYMOUS, False)
                self.patient_spec_if_anonymous = get_config_parameter(
                    config, section, cpr.PATIENT_SPEC_IF_ANONYMOUS, str,
                    "anonymous")
                self.patient_spec = get_config_parameter(
                    config, section, cpr.PATIENT_SPEC, str, None)
                self.filename_spec = get_config_parameter(
                    config, section, cpr.FILENAME_SPEC, str, None)
                self.overwrite_files = get_config_parameter_boolean(
                    config, section, cpr.OVERWRITE_FILES, False)
                self.make_directory = get_config_parameter_boolean(
                    config, section, cpr.MAKE_DIRECTORY, False)
                self.rio_metadata = get_config_parameter_boolean(
                    config, section, cpr.RIO_METADATA, False)
                self.rio_idnum = get_config_parameter(
                    config, section, cpr.RIO_IDNUM, int, None)
                self.rio_uploading_user = get_config_parameter(
                    config, section, cpr.RIO_UPLOADING_USER, str, None)
                self.rio_document_type = get_config_parameter(
                    config, section, cpr.RIO_DOCUMENT_TYPE, str, None)
                self.script_after_file_export = get_config_parameter(
                    config, section, cpr.SCRIPT_AFTER_FILE_EXPORT, str, None)

        except configparser.NoSectionError:
            log.warning("Config file section missing: [{}]", section)

    @staticmethod
    def report_error(msg) -> None:
        log.error("RecipientDefinition: {}", msg)

    def valid(self, req: "CamcopsRequest") -> bool:
        """Is this definition valid?"""
        if self.type not in ALL_RECIPIENT_TYPES:
            self.report_error("missing/invalid type: {}".format(self.type))
            return False
        if not self.group_id:
            self.report_error("missing group_id")
            return False
        group = Group.get_group_by_id(req.dbsession, self.group_id)
        if not group:
            self.report_error("invalid group_id: {}".format(self.group_id))
            return False
        if not self.primary_idnum and self.using_hl7():
            self.report_error("missing primary_idnum")
            return False

        valid_which_idnums = req.valid_which_idnums

        if self.primary_idnum not in valid_which_idnums:
            self.report_error("invalid primary_idnum: {}".format(
                self.primary_idnum))
            return False
        if self.primary_idnum and self.require_idnum_mandatory:
            # (a) ID number must be mandatory in finalized records
            finalize_policy = group.tokenized_finalize_policy()
            if not finalize_policy.is_idnum_mandatory_in_policy(
                    which_idnum=self.primary_idnum,
                    valid_which_idnums=valid_which_idnums):
                self.report_error(
                    "primary_idnum ({}) not mandatory in finalizing policy, "
                    "but needs to be".format(self.primary_idnum))
                return False
            if not self.finalized_only:
                # (b) ID number must also be mandatory in uploaded,
                # non-finalized records
                upload_policy = group.tokenized_upload_policy()
                if not upload_policy.is_idnum_mandatory_in_policy(
                        which_idnum=self.primary_idnum,
                        valid_which_idnums=valid_which_idnums):
                    self.report_error(
                        "primary_idnum ({}) not mandatory in upload policy, "
                        "but needs to be".format(self.primary_idnum))
                    return False
        if not self.task_format or self.task_format not in [FileType.HTML,
                                                            FileType.PDF,
                                                            FileType.XML]:
            self.report_error(
                "missing/invalid task_format: {}".format(self.task_format))
            return False
        if not self.task_format == FileType.XML:
            self.xml_field_comments = None
        # HL7
        if self.type == Hl7RecipientType.HL7:
            if not self.divert_to_file:
                if not self.host:
                    self.report_error("missing host")
                    return False
                if not self.port or self.port <= 0:
                    self.report_error(
                        "missing/invalid port: {}".format(self.port))
                    return False
            if not self.idnum_type_list.get(self.primary_idnum, None):
                self.report_error(
                    "missing IDNUM_TYPE_{} (for primary ID)".format(
                        self.primary_idnum))
                return False
        # File
        if self.type == Hl7RecipientType.FILE:
            if not self.patient_spec_if_anonymous:
                self.report_error("missing patient_spec_if_anonymous")
                return False
            if not self.patient_spec:
                self.report_error("missing patient_spec")
                return False
            if not patient_spec_for_filename_is_valid(
                    patient_spec=self.patient_spec,
                    valid_which_idnums=valid_which_idnums):
                self.report_error(
                    "invalid patient_spec: {}".format(self.patient_spec))
                return False
            if not self.filename_spec:
                self.report_error("missing filename_spec")
                return False
            if not filename_spec_is_valid(
                    filename_spec=self.filename_spec,
                    valid_which_idnums=valid_which_idnums):
                self.report_error(
                    "invalid filename_spec: {}".format(self.filename_spec))
                return False
            # RiO metadata
            if self.rio_metadata:
                if self.rio_idnum not in valid_which_idnums:
                    self.report_error(
                        "invalid rio_idnum: {}".format(self.rio_idnum))
                    return False
                if (not self.rio_uploading_user or
                        " " in self.rio_uploading_user or
                        len(self.rio_uploading_user) > RIO_MAX_USER_LEN):
                    self.report_error(
                        "missing/invalid rio_uploading_user: {} (must be "
                        "present, contain no spaces, and max length "
                        "{})".format(
                            self.rio_uploading_user,
                            RIO_MAX_USER_LEN))
                    return False
                if not self.rio_document_type:
                    self.report_error("missing rio_document_type")
                    return False

        # This section would be BETTER with a try/raise/except block, rather
        # than a bunch of return statements.

        # Done
        return True

    def using_hl7(self) -> bool:
        """Is the recipient an HL7 recipient?"""
        return self.type == Hl7RecipientType.HL7

    def using_file(self) -> bool:
        """Is the recipient a filestore?"""
        return self.type == Hl7RecipientType.FILE

    @staticmethod
    def get_id_type(req: "CamcopsRequest", which_idnum: int) -> str:
        """Get HL7 ID type for a specific ID number."""
        iddef = req.get_idnum_definition(which_idnum)
        return (iddef.hl7_id_type or '') if iddef else ''

    @staticmethod
    def get_id_aa(req: "CamcopsRequest", which_idnum: int) -> str:
        """Get HL7 ID type for a specific ID number."""
        iddef = req.get_idnum_definition(which_idnum)
        return (iddef.hl7_assigning_authority or '') if iddef else ''

    def get_filename(self,
                     req: "CamcopsRequest",
                     is_anonymous: bool = False,
                     surname: str = None,
                     forename: str = None,
                     dob: Pendulum = None,
                     sex: str = None,
                     idnum_objects: List['PatientIdNum'] = None,
                     creation_datetime: Pendulum = None,
                     basetable: str = None,
                     serverpk: int = None) -> str:
        """Get filename, for file transfers."""
        return get_export_filename(
            req=req,
            patient_spec_if_anonymous=self.patient_spec_if_anonymous,
            patient_spec=self.patient_spec,
            filename_spec=self.filename_spec,
            task_format=self.task_format,
            is_anonymous=is_anonymous,
            surname=surname,
            forename=forename,
            dob=dob,
            sex=sex,
            idnum_objects=idnum_objects,
            creation_datetime=creation_datetime,
            basetable=basetable,
            serverpk=serverpk
        )

    def __str__(self):
        """String representation."""
        attrnames = [key for key in self.__dict__ if not key.startswith('_')]
        return simple_repr(self, attrnames)
