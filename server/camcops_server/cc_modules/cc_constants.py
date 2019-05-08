#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_constants.py

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

**Various constants.**

"""

# Helpful UTF-8 characters: ‘’ “” – — × • ≤ ≥ ≠ ± →

import os

from camcops_server.cc_modules.cc_baseconstants import STATIC_ROOT_DIR

# =============================================================================
# Number of ID numbers. Don't alter this lightly; influences database fields.
# =============================================================================

NUMBER_OF_IDNUMS_DEFUNCT = 8  # DEFUNCT BUT DO NOT REMOVE OR ALTER. EIGHT.
# ... In older versions: determined number of ID number fields.
# (Now this is arbitrary.) Still used to support old clients.

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_DB_PORT = 3306
DEFAULT_DB_SERVER = "localhost"
DEFAULT_LOCAL_INSTITUTION_URL = "http://www.camcops.org/"
DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES = 10
DEFAULT_LOCKOUT_THRESHOLD = 10
DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS = 0  # zero for never

DEFAULT_TIMEOUT_MINUTES = 30
DEFAULT_PLOT_FONTSIZE = 8

MINIMUM_PASSWORD_LENGTH = 8

# =============================================================================
# Launching
# =============================================================================

DEFAULT_CHERRYPY_SERVER_NAME = "localhost"
DEFAULT_FLOWER_ADDRESS = "127.0.0.1"
DEFAULT_FLOWER_PORT = 5555  # http://docs.celeryproject.org/en/latest/userguide/monitoring.html  # noqa
DEFAULT_GUNICORN_TIMEOUT_S = 30
DEFAULT_HOST = "127.0.0.1"
DEFAULT_START_THREADS = 10
DEFAULT_MAX_THREADS = 100
# ... beware the default MySQL connection limit of 151;
#     https://dev.mysql.com/doc/refman/5.7/en/too-many-connections.html
DEFAULT_PORT = 8000
URL_PATH_ROOT = '/'

# =============================================================================
# More filenames
# =============================================================================

DEFAULT_CAMCOPS_LOGO_FILE = os.path.join(STATIC_ROOT_DIR, "logo_camcops.png")
DEFAULT_LOCAL_LOGO_FILE = os.path.join(STATIC_ROOT_DIR, "logo_local.png")

# =============================================================================
# Webview constants
# =============================================================================

DEFAULT_ROWS_PER_PAGE = 25
DEVICE_NAME_FOR_SERVER = "server"  # Do not alter.
USER_NAME_FOR_SYSTEM = "system"  # Do not alter.


# =============================================================================
# Date formats
# =============================================================================

class DateFormat(object):
    """
    Assorted date/time formats.
    """
    SHORT_DATE = "%d %b %Y"  # e.g. 24 Jul 2013
    LONG_DATE = "%d %B %Y"  # e.g. 24 July 2013
    LONG_DATE_WITH_DAY = "%a %d %B %Y"  # e.g. Wed 24 July 2013
    LONG_DATETIME = "%d %B %Y, %H:%M %z"  # ... e.g. 24 July 2013, 20:04 +0100
    LONG_DATETIME_WITH_DAY = "%a %d %B %Y, %H:%M %z"  # ... e.g. Wed 24 July 2013, 20:04 +0100  # noqa
    LONG_DATETIME_WITH_DAY_NO_TZ = "%a %d %B %Y, %H:%M"  # ... e.g. Wed 24 July 2013, 20:04  # noqa
    SHORT_DATETIME_WITH_DAY_NO_TZ = "%a %d %b %Y, %H:%M"  # ... e.g. Wed 24 Jul 2013, 20:04  # noqa
    LONG_DATETIME_SECONDS = "%d %B %Y, %H:%M:%S %z"
    SHORT_DATETIME = "%d %b %Y, %H:%M %z"
    SHORT_DATETIME_NO_TZ = "%d %b %Y, %H:%M"
    SHORT_DATETIME_SECONDS = "%d %b %Y, %H:%M:%S %z"
    HOURS_MINUTES = "%H:%M"
    ISO8601 = "%Y-%m-%dT%H:%M:%S%z"  # e.g. 2013-07-24T20:04:07+0100
    ISO8601_HUMANIZED_TO_MINUTES = "%Y-%m-%d %H:%M"  # e.g. 2013-07-24 20:04
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
    """
    Collections of permitted values.
    """
    BIT = [0, 1]


NO_CHAR = 'N'
YES_CHAR = 'Y'

# Database values:
SEX_FEMALE = "F"
SEX_MALE = "M"
SEX_OTHER_UNSPECIFIED = "X"
POSSIBLE_SEX_VALUES = [SEX_FEMALE, SEX_MALE, SEX_OTHER_UNSPECIFIED]


# =============================================================================
# Field names/specifications
# =============================================================================

# defunct # PKNAME = "_pk"
TABLET_ID_FIELD = "id"
MOVE_OFF_TABLET_FIELD = "_move_off_tablet"
CLIENT_DATE_FIELD = "when_last_modified"

# Used for old client support, and TSV field names etc.:
FP_ID_NUM = "idnum"
FP_ID_DESC = "iddesc"
FP_ID_SHORT_DESC = "idshortdesc"

CRIS_CLUSTER_KEY_FIELDSPEC = dict(
    name="_task_main_pk", cctype="INT_UNSIGNED",
    comment="(CRIS) Server primary key for task and linked records"
)


# =============================================================================
# Other special values
# =============================================================================

# CAMCOPS_URL = "http://www.camcops.org/"
CAMCOPS_URL = "https://camcops.readthedocs.io/"
ERA_NOW = "NOW"  # defines the current era in database records

# =============================================================================
# PDF engine: now always "pdfkit".
# =============================================================================

# PDF_ENGINE = "xhtml2pdf"  # working
PDF_ENGINE = "pdfkit"  # working
# PDF_ENGINE = "weasyprint"  # working but table <tr> element bugs
# ... value must be one of: xhtml2pdf, weasyprint, pdfkit

# =============================================================================
# Simple constants for HTML/plots/display
# =============================================================================

WHOLE_PANEL = 111  # as in: ax = fig.add_subplot(111)

DEFAULT_PLOT_DPI = 300

# Debugging option
USE_SVG_IN_HTML = True  # set to False for PNG debugging

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
    "quiet": "",  # Suppress "Loading pages (1/6)" etc.
}


class CssClass(object):
    """
    CSS names.

    Values should match e.g. ``camcops_server/templates/css/css_base.mako``.
    """
    BAD_ID_POLICY_MILD = "badidpolicy_mild"
    BAD_ID_POLICY_SEVERE = "badidpolicy_severe"
    BANNER = "banner"
    BANNER_REFERRAL_GENERAL_ADULT = "banner_referral_general_adult"
    BANNER_REFERRAL_OLD_AGE = "banner_referral_old_age"
    BANNER_REFERRAL_SUBSTANCE_MISUSE = "banner_referral_substance_misuse"
    CENTREGAP_TD = "centregap_td"
    CLINICIAN = "clinician"
    COPYRIGHT = "copyright"
    CTV_DATELIMIT_START = "ctv_datelimit_start"
    CTV_DATELIMIT_END = "ctv_datelimit_end"
    CTV_TASKHEADING = "ctv_taskheading"
    CTV_FIELDHEADING = "ctv_fieldheading"
    CTV_FIELDSUBHEADING = "ctv_fieldsubheading"
    CTV_FIELDDESCRIPTION = "ctv_fielddescription"
    CTV_FIELDCONTENT = "ctv_fieldcontent"
    CTV_WARNINGS = "ctv_warnings"
    ERROR = "error"
    EXPLANATION = "explanation"
    EXTRADETAIL = "extradetail"
    EXTRADETAIL2 = "extradetail2"
    FILTER = "filter"
    FILTERS = "filters"
    FIGURE = "figure"
    FOOTNOTES = "footnotes"
    FORMTITLE = "formtitle"
    GENERAL = "general"
    GREEN = "green"
    HANGINGINDENT = "hangingindent"
    HEADING = "heading"
    HIGHLIGHT = "highlight"
    IMAGE_TD = "image_td"
    IMPORTANT = "important"
    INCOMPLETE = "incomplete"
    INDENT = "indent"
    INDENTED = "indented"
    LIVE_ON_TABLET = "live_on_tablet"
    LOGO_LEFT = "logo_left"
    LOGO_RIGHT = "logo_right"
    NAVIGATION = "navigation"
    NOBORDER = "noborder"
    NOBORDERPHOTO = "noborderphoto"
    OFFICE = "office"
    PATIENT = "patient"
    PHOTO = "photo"
    PDF_LOGO_HEADER = "pdf_logo_header"
    QA_TABLE_HEADING = "qa_tableheading"
    RESPONDENT = "respondent"
    SIGNATURE = "signature"
    SIGNATURE_LABEL = "signature_label"
    SMALLPRINT = "smallprint"
    SPECIALNOTE = "specialnote"
    SUBHEADING = "subheading"
    SUBSUBHEADING = "subsubheading"
    SUMMARY = "summary"
    SUPERUSER = "superuser"
    TASKCONFIG = "taskconfig"
    TASKDETAIL = "taskdetail"
    TASKHEADER = "taskheader"
    TRACKERHEADER = "trackerheader"
    TRACKER_ALL_CONSISTENT = "tracker_all_consistent"
    WARNING = "warning"
    WEB_LOGO_HEADER = "web_logo_header"


# =============================================================================
# Task constants
# =============================================================================

ANON_PATIENT = "XXXX"
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


# =============================================================================
# Config constants
# =============================================================================

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
    TRANSMISSION_METHOD = "TRANSMISSION_METHOD"
    XML_FIELD_COMMENTS = "XML_FIELD_COMMENTS"
