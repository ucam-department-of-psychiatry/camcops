#!/usr/bin/env python
# camcops_server/cc_modules/cc_constants.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

# Helpful UTF-8 characters: ‘’ “” – — × • ≤ ≥ ≠ ± →

import os
import string
from cardinal_pythonlib.dicts import merge_dicts

from .cc_baseconstants import CAMCOPS_SERVER_DIRECTORY

# =============================================================================
# Number of ID numbers. Don't alter this lightly; influences database fields.
# =============================================================================

NUMBER_OF_IDNUMS_DEFUNCT = 8  # Determines number of ID number fields

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE_MAIN_SECTION = "server"
CONFIG_FILE_RECIPIENTLIST_SECTION = "recipients"

DEFAULT_DB_PORT = 3306
DEFAULT_DB_SERVER = "localhost"
DEFAULT_DATABASE_TITLE = "CamCOPS database"
DEFAULT_LOCAL_INSTITUTION_URL = "http://www.camcops.org/"
DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES = 10
DEFAULT_LOCKOUT_THRESHOLD = 10
DEFAULT_MYSQLDUMP = "/usr/bin/mysqldump"
DEFAULT_MYSQL = "/usr/bin/mysql"
DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS = 0  # zero for never

# SERVER_BASE_DIRECTORY = os.path.join(PROJECT_BASE_DIRECTORY, "server")
# DEFAULT_STRING_FILE = os.path.join(
#     TABLET_SOURCE_COPY_DIR, "tablet_titanium", "i18n", "en", "strings.xml")
# DEFAULT_EXTRA_STRING_SPEC = os.path.join(
#     PROJECT_BASE_DIRECTORY, "server", "extra_strings", "*")
DEFAULT_TIMEOUT_MINUTES = 30
DEFAULT_PLOT_FONTSIZE = 8

# =============================================================================
# URLs, filenames, etc. for interaction with the hosting web server
# =============================================================================

# As sent to the client, using relative URLS:
STATIC_URL_PREFIX = "static/"
CAMCOPS_LOGO_FILE_WEBREF = STATIC_URL_PREFIX + "logo_camcops.png"
LOCAL_LOGO_FILE_WEBREF = STATIC_URL_PREFIX + "logo_local.png"
CAMCOPS_FAVICON_FILE = STATIC_URL_PREFIX + "favicon_camcops.png"

URL_RELATIVE_WEBVIEW = "webview"

# As seen in the WSGI PATH_INFO variable:
URL_ROOT_WEBVIEW = "/" + URL_RELATIVE_WEBVIEW
URL_ROOT_DATABASE = "/database"
URL_ROOT_STATIC = "/static"  # only for development environments

# =============================================================================
# More filenames
# =============================================================================

DEFAULT_CAMCOPS_LOGO_FILE = os.path.join(CAMCOPS_SERVER_DIRECTORY,
                                         CAMCOPS_LOGO_FILE_WEBREF)
DEFAULT_LOCAL_LOGO_FILE = os.path.join(CAMCOPS_SERVER_DIRECTORY,
                                       LOCAL_LOGO_FILE_WEBREF)

# =============================================================================
# Introspection
# =============================================================================

INTROSPECTION_BASE_DIRECTORY = CAMCOPS_SERVER_DIRECTORY


# =============================================================================
# HTTP actions, parameters, values
# =============================================================================

class ACTION(object):
    ADD_SPECIAL_NOTE = "add_special_note"
    ADD_USER = "add_user"
    AGREE_TERMS = "agree_terms"
    APPLY_FILTER_COMPLETE = "apply_filter_complete"
    APPLY_FILTER_DEVICE = "apply_filter_device"
    APPLY_FILTER_DOB = "apply_filter_dob"
    APPLY_FILTER_END_DATETIME = "apply_filter_end_datetime"
    APPLY_FILTER_FORENAME = "apply_filter_forename"
    APPLY_FILTER_IDNUMS = "apply_filter_idnums"
    APPLY_FILTER_INCLUDE_OLD_VERSIONS = "apply_filter_include_old_versions"
    APPLY_FILTERS = "apply_filters"
    APPLY_FILTER_SEX = "apply_filter_sex"
    APPLY_FILTER_START_DATETIME = "apply_filter_start_datetime"
    APPLY_FILTER_SURNAME = "apply_filter_surname"
    APPLY_FILTER_TASK = "apply_filter_task"
    APPLY_FILTER_TEXT = "apply_filter_text"
    APPLY_FILTER_USER = "apply_filter_user"
    ASK_DELETE_USER = "ask_delete_user"
    ASK_TO_ADD_USER = "ask_to_add_user"
    BASIC_DUMP = "basic_dump"
    CHANGE_NUMBER_TO_VIEW = "change_number_to_view"
    CHANGE_PASSWORD = "change_password"
    CHANGE_USER = "change_user"
    CHOOSE_CLINICALTEXTVIEW = "choose_clinicaltextview"
    CHOOSE_TRACKER = "choose_tracker"
    CLEAR_FILTER_COMPLETE = "clear_filter_complete"
    CLEAR_FILTER_DEVICE = "clear_filter_device"
    CLEAR_FILTER_DOB = "clear_filter_dob"
    CLEAR_FILTER_END_DATETIME = "clear_filter_end_datetime"
    CLEAR_FILTER_FORENAME = "clear_filter_forename"
    CLEAR_FILTER_IDNUMS = "clear_filter_idnums"
    CLEAR_FILTER_INCLUDE_OLD_VERSIONS = "clear_filter_include_old_versions"
    CLEAR_FILTERS = "clear_filters"
    CLEAR_FILTER_SEX = "clear_filter_sex"
    CLEAR_FILTER_START_DATETIME = "clear_filter_start_datetime"
    CLEAR_FILTER_SURNAME = "clear_filter_surname"
    CLEAR_FILTER_TASK = "clear_filter_task"
    CLEAR_FILTER_TEXT = "clear_filter_text"
    CLEAR_FILTER_USER = "clear_filter_user"
    CLINICALTEXTVIEW = "clinicaltextview"
    CRASH = "crash"
    DELETE_PATIENT = "delete_patient"
    DELETE_USER = "delete_user"
    EDIT_PATIENT = "edit_patient"
    EDIT_USER = "edit_user"
    ENABLE_USER = "enable_user"
    ENTER_NEW_PASSWORD = "enter_new_password"
    ERASE_TASK = "erase_task"
    FILTER = "filter"
    FIRST_PAGE = "first_page"
    FORCIBLY_FINALIZE = "forcibly_finalize"
    INSPECT_TABLE_DEFS = "view_table_definitions"
    INSPECT_TABLE_VIEW_DEFS = "view_table_and_view_definitions"
    INTROSPECT = "introspect"
    LAST_PAGE = "last_page"
    LOGIN = "login"
    LOGOUT = "logout"
    MAIN_MENU = "main_menu"
    MANAGE_USERS = "manage_users"
    NEXT_PAGE = "next_page"
    OFFER_BASIC_DUMP = "offer_basic_dump"
    OFFER_HL7_LOG_OPTIONS = "offer_hl7_log"
    OFFER_HL7_RUN_OPTIONS = "offer_hl7_run"
    OFFER_INTROSPECTION = "offer_introspect"
    OFFER_REGENERATE_SUMMARIES = "offer_regenerate_summary_tables"
    OFFER_REPORT = "offer_report"
    OFFER_TABLE_DUMP = "offer_table_dump"
    PREVIOUS_PAGE = "previous_page"
    PROVIDE_REPORT = "report"
    REGENERATE_SUMMARIES = "regenerate_summary_tables"
    REPORTS_MENU = "reports_menu"
    TABLE_DUMP = "table_dump"
    TASK = "task"
    TRACKER = "tracker"
    VIEW_AUDIT_TRAIL = "view_audit_trail"
    VIEW_HL7_LOG = "view_hl7_log"
    VIEW_HL7_RUN = "view_hl7_run"
    VIEW_POLICIES = "view_policies"
    VIEW_TASKS = "view_tasks"


class PARAM(object):
    ACTION = "action"
    ADDRESS = "address"
    AGREE = "agree"
    ANONYMISE = "anonymise"
    BASIC_DUMP_TYPE = "basic_dump_type"
    COMPLETE = "complete"
    CONFIRMATION_SEQUENCE = "confirmation_sequence"
    DEVICE = "device"
    DOB = "dob"
    END_DATETIME = "end_datetime"
    FILENAME = "filename"
    FORENAME = "forename"
    GP = "gp"
    HL7RUNID = "hl7runid"
    IDNUM_VALUE = "idnum_value"
    IDNUM_PREFIX = "idnum_prefix"
    INCLUDE_BLOBS = "include_blobs"
    INCLUDE_CALCULATED = "include_calculated"
    INCLUDE_COMMENTS = "include_comments"
    INCLUDE_OLD_VERSIONS = "include_old_versions"
    INCLUDE_PATIENT = "include_patient"
    IPADDR = "ipaddr"
    LABEL = "label"
    MAY_ADD_NOTES = "may_add_notes"
    MAY_DUMP_DATA = "may_dump_data"
    MAY_REGISTER_DEVICES = "may_register_devices"
    MAY_RUN_REPORTS = "may_run_reports"
    MAY_UPLOAD = "may_upload"
    MAY_USE_WEBSTORAGE = "may_use_webstorage"
    MAY_USE_WEBVIEWER = "may_use_webviewer"
    MAY_VIEW_OTHER_USERS_RECORDS = "may_view_other_users_records"
    MUST_CHANGE_PASSWORD = "must_change_password"
    NAME = "name"
    NEW_PASSWORD_1 = "new_password_1"
    NEW_PASSWORD_2 = "new_password_2"
    NOTE = "note"
    NROWS = "nrows"
    NTASKS = "ntasks"
    NUMBER_TO_VIEW = "number_to_view"
    OLD_PASSWORD = "old_password"
    OTHER = "other"
    OUTPUTTYPE = "outputtype"
    PASSWORD_1 = "password_1"
    PASSWORD_2 = "password_2"
    PASSWORD = "password"
    REDIRECT_URL = "redirect_url"
    REPORT_ID = "report_id"
    SERVERPK = "serverpk"
    SEX = "sex"
    SHOWMESSAGE = "show_message"
    SHOWREPLY = "show_reply"
    START_DATETIME = "start_datetime"
    SOURCE = "source"
    SUPERUSER = "superuser"
    SURNAME = "surname"
    TABLENAME = "tablename"
    TABLES_BLOB = "tables_blob"
    TABLES = "tables"
    TASK = "task"
    TASKTYPES = "tasktypes"
    TEXT = "text"
    TRUNCATE = "truncate"
    TYPE = "type"
    USERNAME = "username"
    USER = "user"
    VIEW_ALL_PTS_WHEN_UNFILTERED = "view_all_patients_when_unfiltered"
    VIEWS = "views"
    WHICH_IDNUM = "which_idnum"


class VALUE(object):
    DUMPTYPE_AS_TASK_FILTER = "as_task_filter"
    DUMPTYPE_EVERYTHING = "everything"
    DUMPTYPE_SPECIFIC_TASKS = "specific_tasks"
    OUTPUTTYPE_PDF = "pdf"
    OUTPUTTYPE_HTML = "html"
    OUTPUTTYPE_PDFHTML = "pdfhtml"  # debugging: HTML used to make PDF
    OUTPUTTYPE_TSV = "tsv"
    OUTPUTTYPE_SQL = "sql"
    OUTPUTTYPE_XML = "xml"


class TABLET_PARAM(object):
    CAMCOPS_VERSION = "camcops_version"
    DATEVALUES = "datevalues"
    DEVICE = "device"
    FIELDS = "fields"
    NRECORDS = "nrecords"
    OPERATION = "operation"
    PASSWORD = "password"
    PKNAME = "pkname"
    PKVALUES = "pkvalues"
    RESULT = "result"   # server to tablet
    SESSION_ID = "session_id"   # bidirectional
    SESSION_TOKEN = "session_token"   # bidirectional
    SUCCESS = "success"   # server to tablet
    ERROR = "error"   # server to tablet
    TABLE = "table"
    TABLES = "tables"
    USER = "user"
    WHEREFIELDS = "wherefields"
    WHERENOTFIELDS = "wherenotfields"
    WHERENOTVALUES = "wherenotvalues"
    WHEREVALUES = "wherevalues"
    VALUES = "values"


DEFAULT_ROWS_PER_PAGE = 25


# =============================================================================
# Date formats
# =============================================================================

class DateFormat(object):
    SHORT_DATE = "%d %b %Y"  # e.g. 24 Jul 2013
    LONG_DATE = "%d %B %Y"  # e.g. 24 July 2013
    LONG_DATE_WITH_DAY = "%a %d %B %Y"  # e.g. Wed 24 July 2013
    LONG_DATETIME = "%d %B %Y, %H:%M %z"  # ... e.g. 24 July 2013, 20:04 +0100
    LONG_DATETIME_WITH_DAY = "%a %d %B %Y, %H:%M %z"  # ... e.g. Wed 24 July 2013, 20:04 +0100  # noqa
    LONG_DATETIME_WITH_DAY_NO_TZ = "%a %d %B %Y, %H:%M"  # ... e.g. Wed 24 July 2013, 20:04  # noqa
    SHORT_DATETIME_WITH_DAY_NO_TZ = "%a %d %b %Y, %H:%M"  # ... e.g. Wed 24 Jul 2013, 20:04  # noqa
    LONG_DATETIME_SECONDS = "%d %B %Y, %H:%M:%S %z"
    SHORT_DATETIME = "%d %b %Y, %H:%M %z"
    SHORT_DATETIME_SECONDS = "%d %b %Y, %H:%M:%S %z"
    HOURS_MINUTES = "%H:%M"
    ISO8601 = "%Y-%m-%dT%H:%M:%S%z"  # e.g. 2013-07-24T20:04:07+0100
    ISO8601_DATE_ONLY = "%Y-%m-%d"  # e.g. 2013-07-24
    FILENAME = "%Y-%m-%dT%H%M"  # e.g. 20130724T2004
    FILENAME_DATE_ONLY = "%Y-%m-%d"  # e.g. 20130724
    HL7_DATETIME = "%Y%m%d%H%M%S%z"  # e.g. 20130724200407+0100
    HL7_DATE = "%Y%m%d"  # e.g. 20130724
    ERA = "%Y-%m-%dT%H:%M:%SZ"  # e.g. 2013-07-24T20:03:07Z
    # http://www.hl7standards.com/blog/2008/07/25/hl7-time-zone-qualification/
    RIO_EXPORT_UK = "%d/%m/%Y %H:%M"  # e.g. 01/12/2014 09:45


# =============================================================================
# Permitted values in fields: some common settings
# =============================================================================

class PV(object):
    BIT = [0, 1]


NO_CHAR = 'N'
YES_CHAR = 'Y'

# =============================================================================
# Field names/specifications
# =============================================================================

PKNAME = "_pk"
TABLET_ID_FIELD = "id"
MOVE_OFF_TABLET_FIELD = "_move_off_tablet"
CLIENT_DATE_FIELD = "when_last_modified"

# Field prefixes, for Patient table (here to avoid circular imports)
FP_ID_NUM = "idnum"
FP_ID_DESC = "iddesc"
FP_ID_SHORT_DESC = "idshortdesc"

CRIS_CLUSTER_KEY_FIELDSPEC = dict(
    name="_task_main_pk", cctype="INT_UNSIGNED",
    comment="(CRIS) Server primary key for task and linked records"
)

# DEFUNCT NOTE ABOUT FIELDSPEC LISTS:
#
# BEWARE when using these, esp. if you perform modifications. For example:
#
#   x = [{"a": 1}]
#   y = [{"b": 2}]
#   z = x + y
#   for i in z:
#       i["modify"] = 99
#
# ... modifies x, y as well. And so does this:
#
#   x = [{"a": 1}]
#   y = [{"b": 2}]
#   z = list(x) + list(y)
#   for i in z:
#       i["modify"] = 99
#
# So you'd need a deep copy.
# http://stackoverflow.com/questions/8913026/list-copy-not-working
# http://stackoverflow.com/questions/2612802
# http://stackoverflow.com/questions/6993531/copy-list-in-python
#
# However, our problem comes about when we modify comments; it'll be OK if we
# never modify a comment when there's an existing comment.


# =============================================================================
# Other special values
# =============================================================================

CAMCOPS_URL = "http://www.camcops.org/"
ERA_NOW = "NOW"  # defines the current era in database records

# =============================================================================
# PDF engine: now always "pdfkit".
# =============================================================================

# PDF_ENGINE = "xhtml2pdf"  # working
PDF_ENGINE = "pdfkit"  # working
# PDF_ENGINE = "weasyprint"  # working but table <tr> element bugs
# ... must use double quotes; read by a Perl regex in MAKE_PACKAGE
# ... value must be one of: xhtml2pdf, weasyprint, pdfkit

# =============================================================================
# Simple constants for HTML/plots/display
# =============================================================================

WHOLE_PANEL = 111  # as in: ax = fig.add_subplot(111)

DEFAULT_PLOT_DPI = 300

# Debugging option
USE_SVG_IN_HTML = True  # set to False for PNG debugging

RESTRICTED_WARNING = """
    <div class="warning">
        You are restricted to viewing records uploaded by you. Other records
        may exist for the same patient(s), uploaded by others.
    </div>"""
RESTRICTED_WARNING_SINGULAR = """
    <div class="warning">
        You are restricted to viewing records uploaded by you. Other records
        may exist for the same patient, uploaded by others.
    </div>"""

MIMETYPE_PNG = "image/png"

# =============================================================================
# CSS/HTML constants
# =============================================================================

CSS_PAGED_MEDIA = (PDF_ENGINE != "pdfkit")


WKHTMLTOPDF_OPTIONS = {  # dict for pdfkit
    "page-size": "A4",
    "margin-left": "20mm",
    "margin-right": "20mm",
    "margin-top": "21mm",  # from paper edge down to top of content?
    # ... inaccurate
    "margin-bottom": "24mm",  # from paper edge up to bottom of content?
    # ... inaccurate
    "header-spacing": "3",  # mm, from content up to bottom of header
    "footer-spacing": "3",  # mm, from content down to top of footer
}

# =============================================================================
# Other
# =============================================================================

SEPARATOR_HYPHENS = "-" * 79
SEPARATOR_EQUALS = "=" * 79

# =============================================================================
# Table names used by modules that would otherwise have an interdependency, or
# are defined elsewhere
# =============================================================================

HL7MESSAGE_TABLENAME = "_hl7_message_log"
ALEMBIC_VERSION_TABLENAME = "alembic_version"

# =============================================================================
# Task constants
# =============================================================================

ANON_PATIENT = "XXXX"
COMMENT_IS_COMPLETE = "Task complete?"
DATA_COLLECTION_ONLY_DIV = """
    <div class="copyright">
        Reproduction of the original task/scale is not permitted.
        This is a data collection tool only; use it only in conjunction with
        a licensed copy of the original task.
    </div>
"""
DATA_COLLECTION_UNLESS_UPGRADED_DIV = """
    <div class="copyright">
        Reproduction of the original task/scale is not permitted as part of
        CamCOPS. This is a data collection tool only, unless the hosting
        institution has supplied task text via its own permissions. <b>Any such
        text, if shown here, is not part of CamCOPS, and copyright in
        it belongs to the original task’s copyright holder.</b> Use this data
        collection tool only in conjunction with a licensed copy of the
        original task.
    </div>
"""
FULLWIDTH_PLOT_WIDTH = 6.7  # inches: full width is ~170mm
ICD10_COPYRIGHT_DIV = """
    <div class="copyright">
        ICD-10 criteria: Copyright © 1992 World Health Organization.
        Used here with permission.
    </div>
"""
INVALID_VALUE = "[invalid_value]"

TSV_PATIENT_FIELD_PREFIX = "_patient_"
CRIS_PATIENT_COMMENT_PREFIX = "(PATIENT) "
CRIS_SUMMARY_COMMENT_PREFIX = "(SUMMARY) "
CRIS_TABLENAME_PREFIX = "camcops_"

QUESTION = "Question"
