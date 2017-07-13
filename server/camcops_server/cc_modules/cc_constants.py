#!/usr/bin/env python
# cc_constants.py

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
from cardinal_pythonlib.rnc_lang import merge_dicts
from camcops_server.cc_modules.cc_baseconstants import (
    CAMCOPS_SERVER_DIRECTORY,
    TABLET_SOURCE_COPY_DIR,
)

# =============================================================================
# Number of ID numbers. Don't alter this lightly; influences database fields.
# =============================================================================

NUMBER_OF_IDNUMS = 8  # Determines number of ID number fields

# =============================================================================
# Configuration
# =============================================================================

ENVVAR_CONFIG_FILE = "CAMCOPS_CONFIG_FILE"

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
STATIC_ROOT_DIR = os.path.join(CAMCOPS_SERVER_DIRECTORY, 'static')


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
    OFFER_AUDIT_TRAIL_OPTIONS = "offer_audit_trail_options"
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
    REDIRECT = "redirect"
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


# =============================================================================
# Date formats
# =============================================================================

class DATEFORMAT(object):
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

ISO8601_STRING_LENGTH = 32
# ... max length e.g. 2013-07-24T20:04:07.123456+01:00
# (microseconds, colon in timezone).

PKNAME = "_pk"
MOVE_OFF_TABLET_FIELD = "_move_off_tablet"
CLIENT_DATE_FIELD = "when_last_modified"

# Field prefixes, for Patient table (here to avoid circular imports)
FP_ID_NUM = "idnum"
FP_ID_DESC = "iddesc"
FP_ID_SHORT_DESC = "idshortdesc"

# VALID KEYS FOR FIELDSPECS:
# - all those listed in rnc_db.py
# - cctype
# - identifies_patient (Boolean)
STANDARD_GENERIC_FIELDSPECS = [
    # server side:
    dict(name=PKNAME, cctype="INT_UNSIGNED", pk=True,
         autoincrement=True, comment="(SERVER) Primary key (on the server)"),
    # ... server PK; must always be first in the fieldlist
    dict(name="_device_id", cctype="INT_UNSIGNED", notnull=True,
         comment="(SERVER) ID of the source tablet device",
         indexed=True),
    dict(name="_era", cctype="ISO8601", notnull=True,
         comment="(SERVER) 'NOW', or when this row was preserved and removed "
                 "from the source device (UTC ISO 8601)",
         indexed=True, index_nchar=ISO8601_STRING_LENGTH),
    # ... note that _era is textual so that plain comparison
    # with "=" always works, i.e. no NULLs -- for USER comparison too, not
    # just in CamCOPS code
    dict(name="_current", cctype="BOOL", notnull=True,
         comment="(SERVER) Is the row current (1) or not (0)?", indexed=True),
    dict(name="_when_added_exact", cctype="ISO8601",
         comment="(SERVER) Date/time this row was added (ISO 8601)"),
    dict(name="_when_added_batch_utc", cctype="DATETIME",
         comment="(SERVER) Date/time of the upload batch that added this "
                 "row (DATETIME in UTC)"),
    dict(name="_adding_user_id", cctype="INT_UNSIGNED",
         comment="(SERVER) ID of user that added this row"),
    dict(name="_when_removed_exact", cctype="ISO8601",
         comment="(SERVER) Date/time this row was removed, i.e. made "
                 "not current (ISO 8601)"),
    dict(name="_when_removed_batch_utc", cctype="DATETIME",
         comment="(SERVER) Date/time of the upload batch that removed "
                 "this row (DATETIME in UTC)"),
    dict(name="_removing_user_id", cctype="INT_UNSIGNED",
         comment="(SERVER) ID of user that removed this row"),
    dict(name="_preserving_user_id", cctype="INT_UNSIGNED",
         comment="(SERVER) ID of user that preserved this row"),
    dict(name="_forcibly_preserved", cctype="BOOL",
         comment="(SERVER) Forcibly preserved by superuser (rather than "
                 "normally preserved by tablet)?"),
    dict(name="_predecessor_pk", cctype="INT_UNSIGNED",
         comment="(SERVER) PK of predecessor record, prior to modification"),
    dict(name="_successor_pk", cctype="INT_UNSIGNED",
         comment="(SERVER) PK of successor record  (after modification) "
                 "or NULL (after deletion)"),
    dict(name="_manually_erased", cctype="BOOL",
         comment="(SERVER) Record manually erased (content destroyed)?"),
    dict(name="_manually_erased_at", cctype="ISO8601",
         comment="(SERVER) Date/time of manual erasure (ISO 8601)"),
    dict(name="_manually_erasing_user_id", cctype="INT_UNSIGNED",
         comment="(SERVER) ID of user that erased this row manually"),
    dict(name="_camcops_version", cctype="SEMANTICVERSIONTYPE",
         comment="(SERVER) CamCOPS version number of the uploading device"),
    dict(name="_addition_pending", cctype="BOOL",
         notnull=True, comment="(SERVER) Addition pending?"),
    dict(name="_removal_pending", cctype="BOOL",
         notnull=True, comment="(SERVER) Removal pending?"),
    dict(name=MOVE_OFF_TABLET_FIELD, cctype="BOOL",
         comment="(SERVER/TABLET) Record-specific preservation pending?"),
    # fields that *all* client tables have:
    dict(name=CLIENT_DATE_FIELD, cctype="ISO8601",
         comment="(STANDARD) Date/time this row was last modified on the "
                 "source tablet device (ISO 8601)"),
]

STANDARD_TASK_COMMON_FIELDSPECS = [
    dict(name="when_created", cctype="ISO8601", notnull=True,
         comment="(TASK) Date/time this task instance was created (ISO 8601)"),
    dict(name="when_firstexit", cctype="ISO8601",
         comment="(TASK) Date/time of the first exit from this "
                 "task (ISO 8601)"),
    dict(name="firstexit_is_finish", cctype="BOOL",
         comment="(TASK) Was the first exit from the task because it was "
                 "finished (1)?"),
    dict(name="firstexit_is_abort", cctype="BOOL",
         comment="(TASK) Was the first exit from this task because it was "
                 "aborted (1)?"),
    dict(name="editing_time_s", cctype="FLOAT",
         comment="(TASK) Time spent editing (s)"),
]

STANDARD_TASK_FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
    dict(name="id", cctype="INT_UNSIGNED", notnull=True,
         comment="(TASK) Primary key (task ID) on the tablet device",
         indexed=True),
    dict(name="patient_id", cctype="INT_UNSIGNED", notnull=True,
         comment="(TASK) Foreign key to patient.id for this device",
         indexed=True),
] + STANDARD_TASK_COMMON_FIELDSPECS

STANDARD_ANONYMOUS_TASK_FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
    dict(name="id", cctype="INT_UNSIGNED", notnull=True,
         comment="(TASK) Primary key (task ID) on the tablet device",
         indexed=True),
] + STANDARD_TASK_COMMON_FIELDSPECS

STANDARD_ANCILLARY_FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
    dict(name="id", cctype="INT_UNSIGNED", notnull=True,
         comment="(ANCILLARY) Primary key on the tablet device",
         indexed=True),
]

CLINICIAN_FIELDSPECS = [  # see also has_clinician
    dict(name="clinician_specialty", cctype="TEXT", anon=True,
         comment="(CLINICIAN) Clinician's specialty (e.g. Liaison "
                 "Psychiatry)"),
    dict(name="clinician_name", cctype="TEXT", anon=True,
         comment="(CLINICIAN) Clinician's name (e.g. Dr X)"),
    dict(name="clinician_professional_registration", cctype="TEXT",
         comment="(CLINICIAN) Clinician's professional registration (e.g. "
                 "GMC# 12345)"),
    dict(name="clinician_post", cctype="TEXT", anon=True,
         comment="(CLINICIAN) Clinician's post (e.g. Consultant)"),
    dict(name="clinician_service", cctype="TEXT", anon=True,
         comment="(CLINICIAN) Clinician's service (e.g. Liaison Psychiatry "
                 "Service)"),
    dict(name="clinician_contact_details", cctype="TEXT", anon=True,
         comment="(CLINICIAN) Clinician's contact details (e.g. bleep, "
                 "extension)"),
]
RESPONDENT_FIELDSPECS = [  # see also has_respondent
    dict(name="respondent_name", cctype="TEXT",
         comment="(RESPONDENT) Respondent's name"),
    dict(name="respondent_relationship", cctype="TEXT",
         comment="(RESPONDENT) Respondent's relationship to patient"),
]

CRIS_CLUSTER_KEY_FIELDSPEC = dict(
    name="_task_main_pk", cctype="INT_UNSIGNED",
    comment="(CRIS) Server primary key for task and linked records"
)

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

TEXT_FILTER_EXEMPT_FIELDS = [
    item["name"] for item in (
        STANDARD_GENERIC_FIELDSPECS +
        STANDARD_TASK_COMMON_FIELDSPECS +
        CLINICIAN_FIELDSPECS
    ) if item["cctype"] == "TEXT" or item["name"].startswith("_")
]

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

# =============================================================================
# CSS/HTML constants
# =============================================================================

PDF_LOGO_HEIGHT = "20mm"

CSS_PAGED_MEDIA = (PDF_ENGINE != "pdfkit")

COMMON_DEFINITIONS = {  # dict for CSS substitutions
    "SMALLFONTSIZE": "0.85em",
    "TINYFONTSIZE": "0.7em",
    "LARGEFONTSIZE": "1.2em",
    "GIANTFONTSIZE": "1.4em",
    "BANNERFONTSIZE": "1.6em",

    # Rules: line height is 1.1-1.2 * font size
    # ... but an em is related to the calculated font-size of the element,
    #   http://www.impressivewebs.com/understanding-em-units-css/
    # so it can always be 1.2:
    "MAINLINEHEIGHT": "1.1em",
    "SMALLLINEHEIGHT": "1.1em",
    "TINYLINEHEIGHT": "1.0em",  # except this one
    "LARGELINEHEIGHT": "1.1em",
    "GIANTLINEHEIGHT": "1.1em",
    "BANNERLINEHIGHT": "1.1em",
    "TABLELINEHEIGHT": "1.1em",

    "VSPACE_NORMAL": "0.5em",
    "VSPACE_LARGE": "0.8em",

    "SIGNATUREHEIGHT": "3em",

    # Specific to PDFs:
    "PDF_LOGO_HEIGHT": PDF_LOGO_HEIGHT,
}

WEB_SIZES = {  # dict for CSS substitutions
    "MAINFONTSIZE": "medium",
    "SMALLGAP": "2px",
    "ELEMENTGAP": "5px",
    "NORMALPAD": "2px",
    "TABLEPAD": "2px",
    "INDENT_NORMAL": "20px",
    "INDENT_LARGE": "75px",
    "THINLINE": "1px",
    "ZERO": "0px",
    "PDFEXTRA": "",
    "MAINMARGIN": "10px",
    "BODYPADDING": "5px",
    "BANNER_PADDING": "25px",
}

# Hard page margins for A4:
# - left/right: most printers can cope; hole punches to e.g. 13 mm; so 20mm
#   reasonable.
# - top: HP Laserjet 1100 e.g. clips at about 17.5mm
# - bottom: HP Laserjet 1100 e.g. clips at about 15mm
# ... so 20mm all round about right

PDF_SIZES = {  # dict for CSS substitutions
    "MAINFONTSIZE": "10pt",
    "SMALLGAP": "0.2mm",
    "ELEMENTGAP": "1mm",
    "NORMALPAD": "0.5mm",
    "TABLEPAD": "0.5mm",
    "INDENT_NORMAL": "5mm",
    "INDENT_LARGE": "10mm",
    "THINLINE": "0.2mm",
    "ZERO": "0mm",
    "MAINMARGIN": "2cm",
    "BODYPADDING": "0mm",
    "BANNER_PADDING": "0.5cm",
}

# Sequences of 4: top, right, bottom, left
# margin is outside, padding is inside
# #identifier
# .class
# http://www.w3schools.com/cssref/css_selectors.asp
# http://stackoverflow.com/questions/4013604
# http://stackoverflow.com/questions/6023419

# Avoid both {} and % substitution by using string.Template and $
CSS_BASE = string.Template("""

/* Display PNG fallback image... */
svg img.svg {
    display: none;
}
img.pngfallback {
    display: inline;
}
/* ... unless our browser supports SVG */
html.svg svg img.svg {
    display: inline;
}
html.svg img.pngfallback {
    display: none;
}

/* Overall defaults */

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: $MAINFONTSIZE;
    line-height: $MAINLINEHEIGHT;
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
    padding: $BODYPADDING;
}
code {
    font-size: 0.8em;
    font-family: Consolas, Monaco, 'Lucida Console', 'Liberation Mono',
        'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Courier New';
    background-color: #eeeeee;
    padding: 1px 5px 1px 5px;
}
div {
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
    padding: $NORMALPAD;
}
em {
    color: rgb(0, 0, 255);
    font-style: normal;
}
h1 {
    font-size: $GIANTFONTSIZE;
    line-height: $GIANTLINEHEIGHT;
    font-weight: bold;
    margin: $ZERO;
}
h2 {
    font-size: $LARGEFONTSIZE;
    line-height: $LARGELINEHEIGHT;
    font-weight: bold;
    margin: $ZERO;
}
h3 {
    font-size: $LARGEFONTSIZE;
    line-height: $LARGELINEHEIGHT;
    font-weight: bold;
    font-style: italic;
    margin: $ZERO;
}
img {
    max-width: 100%;
    max-height: 100%;
}
p {
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
}
sup, sub {
    font-size: 0.7em; /* 1 em is the size of the parent font */
    vertical-align: baseline;
    position: relative;
    top: -0.5em;
}
sub {
    top: 0.5em;
}
table {
    width: 100%; /* particularly for PDFs */
    vertical-align: top;
    border-collapse: collapse;
    border: $THINLINE solid black;
    padding: $ZERO;
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
}
tr, th, td {
    vertical-align: top;
    text-align: left;
    margin: $ZERO;
    padding: $TABLEPAD;
    border: $THINLINE solid black;
    line-height: $TABLELINEHEIGHT;
}

/* Specific classes */

.badidpolicy_mild {
    background-color: rgb(255, 255, 153);
}
.badidpolicy_severe {
    background-color: rgb(255, 255, 0);
}
.banner {
    text-align: center;
    font-size: $BANNERFONTSIZE;
    line-height: $BANNERLINEHIGHT;
    padding: $BANNER_PADDING;
    margin: $ZERO;
}
.banner_referral_general_adult {
    background-color: rgb(255, 165, 0);
}
.banner_referral_old_age {
    background-color: rgb(0, 255, 127);
}
.banner_referral_substance_misuse {
    background-color: rgb(0, 191, 255);
}
.clinician {
    background-color: rgb(200, 255, 255);
}
table.clinician, table.clinician th, table.clinician td {
    border: $THINLINE solid black;
}
.copyright {
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(227, 227, 227);
}
.ctv_datelimit_start {
    /* line below */
    text-align: right;
    border-style: none none solid none;
    border-width: $THINLINE;
    border-color: black;
}
.ctv_datelimit_end {
    /* line above */
    text-align: right;
    border-style: solid none none none;
    border-width: $THINLINE;
    border-color: black;
}
.ctv_taskheading {
    background-color: rgb(200, 200, 255);
    font-weight: bold;
}
.ctv_fieldheading {
    background-color: rgb(200, 200, 200);
    font-weight: bold;
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fieldsubheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fielddescription {
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fieldcontent {
    font-weight: bold;
    margin: $SMALLGAP $ZERO $ELEMENTGAP $INDENT_NORMAL;
}
.ctv_warnings {
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.error {
    color: rgb(255, 0, 0);
}
.explanation {
    background-color: rgb(200, 255, 200);
}
table.extradetail {
    border: $THINLINE solid black;
    background-color: rgb(210, 210, 210);
}
table.extradetail th {
    border: $THINLINE solid black;
    font-style: italic;
    font-weight: bold;
    font-size: $TINYFONTSIZE;
}
table.extradetail td {
    border: $THINLINE solid black;
    font-size: $TINYFONTSIZE;
}
tr.extradetail2 {
    background-color: rgb(240, 240, 240);
}
td.figure {
    padding: $ZERO;
    background-color: rgb(255, 255, 255);
}
div.filter {
    /* for task filters */
    margin-left: $INDENT_LARGE;
    padding: $ZERO;
}
form.filter {
    /* for task filters */
    display: inline;
    margin: $ZERO;
}
.footnotes {
    /* font-style: italic; */
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}
.formtitle {
    font-size: $LARGEFONTSIZE;
    color: rgb(34, 139, 34);
}
table.general, table.general th, table.general td {
    border: $THINLINE solid black;
}
table.general th.col1, table.general td.col1 {
    width: 22%;
}
table.general th.col2, table.general td.col2 {
    width: 78%;
}
.green {
    color: rgb(34, 139, 34);
}
p.hangingindent {
    padding-left: $INDENT_NORMAL;
    text-indent: -$INDENT_NORMAL;
}
.heading {
    background-color: rgb(0, 0, 0);
    color: rgb(255, 255, 255);
    font-style: italic;
}
.highlight {
    background-color: rgb(255, 250, 205);
}
.important {
    color: rgb(64, 0, 192);
    font-weight: bold;
}
.specialnote {
    background-color: rgb(255, 255, 153);
}
.live_on_tablet {
    background-color: rgb(216, 208, 245);
}
.incomplete {
    background-color: rgb(255, 165, 0);
}
.superuser {
    background-color: rgb(255, 192, 203);
}
p.indent {
    margin-left: $INDENT_NORMAL;
}
div.indented {
    margin-left: $INDENT_LARGE;
}
.navigation {
    background-color: rgb(200, 255, 200);
}
.noborder {
    border: none;
    /* NB also: hidden overrides none with border-collapse */
}
.noborderphoto {
    padding: $ZERO;
    border: none;
}
.office {
    background-color: rgb(227, 227, 227);
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
}
.patient {
    background-color: rgb(255, 200, 200);
}
.pdf_logo_header {
    width: 100%;
    border: none;
}
.pdf_logo_header table, .pdf_logo_header tr {
    width: 100%;
    border: none;
}
.pdf_logo_header .image_td {
    width: 45%;
    border: none;
}
.pdf_logo_header .centregap_td {
    width: 10%;
    border: none;
}
.pdf_logo_header .logo_left {
    float: left;
    max-width: 100%;
    max-height: $PDF_LOGO_HEIGHT;
    height: auto;
    width: auto;
}
.pdf_logo_header .logo_right {
    float: right;
    max-width: 100%;
    max-height: $PDF_LOGO_HEIGHT;
    height: auto;
    width: auto;
}
.photo {
    padding: $ZERO;
}
.respondent {
    background-color: rgb(189, 183, 107);
}
table.respondent, table.respondent th, table.respondent td {
    border: $THINLINE solid black;
}
.signature_label {
    border: none;
    text-align: center;
}
.signature {
    line-height: $SIGNATUREHEIGHT;
    border: $THINLINE solid black;
}
.smallprint {
    font-style: italic;
    font-size: $SMALLFONTSIZE;
}
.subheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
}
.subsubheading {
    font-style: italic;
}
.summary {
    background-color: rgb(200, 200, 255);
}
table.summary, .summary th, .summary td {
    border: $THINLINE solid black;
}
table.taskconfig, .taskconfig th, .taskconfig td {
    border: $THINLINE solid black;
    background-color: rgb(230, 230, 230);
}
table.taskconfig th {
    font-style: italic; font-weight: normal;
}
table.taskdetail, .taskdetail th, .taskdetail td {
    border: $THINLINE solid black;
}
table.taskdetail th {
    font-weight: normal; font-style: italic;
}
table.taskdetail td {
    font-weight: normal;
}
.taskheader {
    background-color: rgb(200, 200, 200);
}
.trackerheader {
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(218, 112, 240);
}
.tracker_all_consistent {
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(227, 227, 227);
}
.warning {
    background-color: rgb(255, 100, 100);
}

/* The next three: need both L/R to float and clear:both for IE */
.web_logo_header {
    display: block;
    overflow: hidden;
    width: 100%;
    border: none;
    clear: both;
}
/* ... overflow:hidden so the div expands to its floating contents */
.web_logo_header .logo_left {
    width: 45%;
    float: left;
    text-decoration: none;
    border: $ZERO;
}
.web_logo_header .logo_right {
    width: 45%;
    float: right;
    text-decoration: none;
    border: $ZERO;
}

/* For tables that will make it to a PDF, fix Weasyprint column widths.
   But not for all (e.g. webview task list) tables. */
table.clinician, table.extradetail, table.general,
        table.pdf_logo_header, table.summary,
        table.taskconfig, table.taskdetail,
        table.fixed {
    table-layout: fixed;
}

""")

# Image sizing:
# http://stackoverflow.com/questions/787839/resize-image-proportionally-with-css  # noqa

PDF_PAGED_MEDIA_CSS = string.Template("""

/* PDF extras */
#headerContent {
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}
#footerContent {
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}

/* PDF paging via CSS Paged Media */
@page {
    size: A4 $ORIENTATION;
    margin-left: $MAINMARGIN;
    margin-right: $MAINMARGIN;
    margin-top: $MAINMARGIN;
    margin-bottom: $MAINMARGIN;
    @frame header {
        /* -pdf-frame-border: 1; */ /* for debugging */
        -pdf-frame-content: headerContent;
        top: 1cm;
        margin-left: $MAINMARGIN;
        margin-right: $MAINMARGIN;
    }
    @frame footer {
        /* -pdf-frame-border: 1; */ /* for debugging */
        -pdf-frame-content: footerContent;
        bottom: 0.5cm; /* distance up from page's bottom margin? */
        height: 1cm; /* height of the footer */
        margin-left: $MAINMARGIN;
        margin-right: $MAINMARGIN;
    }
}
""")
# WEASYPRINT: NOT WORKING PROPERLY YET: WEASYPRINT DOESN'T YET SUPPORT RUNNING
# ELEMENTS
# http://librelist.com/browser//weasyprint/2013/7/4/header-and-footer-for-each-page/#abe45ec357d593df44ffca48253817ef  # noqa
# http://weasyprint.org/docs/changelog/

COMMON_HEAD = string.Template("""
<!DOCTYPE html> <!-- HTML 5 -->
<html>
    <head>
        <title>CamCOPS</title>
        <meta charset="utf-8">
        <link rel="icon" type="image/png" href="$CAMCOPS_FAVICON_FILE">
        <script>
            /* set "html.svg" if our browser supports SVG */
            if (document.implementation.hasFeature(
                    "http://www.w3.org/TR/SVG11/feature#Image", "1.1")) {
                document.documentElement.className = "svg";
            }
        </script>
        <style type="text/css">
            $CSS
        </style>
    </head>
    <body>
""")

# Re PDFs:
# - The way in which xhtml2pdf copes with column widths
#   is somewhat restricted: CSS only
# - "height" not working for td
# TABLE STYLING HELP:
# http://www.somacon.com/p141.php
# http://www.w3.org/Style/Tables/examples.html


WEB_HEAD = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, WEB_SIZES)),
)
PDF_HEAD_PORTRAIT = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=(
        CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES)) +
        PDF_PAGED_MEDIA_CSS.substitute(
            merge_dicts(COMMON_DEFINITIONS, PDF_SIZES,
                        {"ORIENTATION": "portrait"}))
    ),
)
PDF_HEAD_LANDSCAPE = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=(
        CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES)) +
        PDF_PAGED_MEDIA_CSS.substitute(
            merge_dicts(COMMON_DEFINITIONS, PDF_SIZES,
                        {"ORIENTATION": "landscape"}))
    ),
)
PDF_HEAD_NO_PAGED_MEDIA = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES))
)

COMMON_END = "</body></html>"
WEBEND = COMMON_END
PDFEND = COMMON_END

WKHTMLTOPDF_CSS = string.Template("""
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: $MAINFONTSIZE;  /* absolute */
        line-height: $SMALLLINEHEIGHT;
        padding: 0;
        margin: 0;  /* use header-spacing / footer-spacing instead */
    }
    div {
        font-size: $SMALLFONTSIZE;  /* relative */
    }
""").substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES))
# http://stackoverflow.com/questions/11447672/fix-wkhtmltopdf-headers-clipping-content  # noqa

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
# Table names used by modules that would otherwise have an interdependency
# =============================================================================

HL7MESSAGE_TABLENAME = "_hl7_message_log"

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
SIGNATURE_BLOCK = """
    <div>
        <table class="noborder">
            <tr class="signature_label">
                <td class="signature_label" width="33%">
                    Signature of author/validator
                </td>
                <td class="signature_label" width="33%">
                    Print name
                </td>
                <td class="signature_label" width="33%">
                    Date and time
                </td>
            </tr>
            <tr class="signature">
                <td class="signature">&nbsp;</td>
                <td class="signature">&nbsp;</td>
                <td class="signature">&nbsp;</td>
            </tr>
        </table>
    </div>
"""
# ... can't get "height" to work in table; only seems to like line-height; for
# which, you need some text, hence the &nbsp;
# http://stackoverflow.com/questions/6398172/setting-table-row-height-in-css
TASK_LIST_HEADER = """
    <table>
        <tr>
            <th>Surname, forename (sex, DOB, age)</th>
            <th>Identifiers</th>
            <th>Task type</th>
            <th>Adding user</th>
            <th>Created</th>
            <th>View detail</th>
            <th>Print/save detail</th>
        </tr>
"""
TASK_LIST_FOOTER = """
    </table>
    <div class="footnotes">
        Colour in the Patient column means
            that an ID policy is not yet satisfied.
        Colour in the Task Type column means
            the record is not current.
        Colour in the Created column means
            the task is ‘live’ on the tablet, not finalized
            (so patient and task details may change).
        Colour in the View/Print columns means
            the task is incomplete.
    </div>
"""
#        Colour in the Identifiers column means
#            a conflict between the server’s and the tablet’s ID descriptions.
TSV_PATIENT_FIELD_PREFIX = "_patient_"
CRIS_PATIENT_COMMENT_PREFIX = "(PATIENT) "
CRIS_SUMMARY_COMMENT_PREFIX = "(SUMMARY) "
CRIS_TABLENAME_PREFIX = "camcops_"

QUESTION = "Question"
