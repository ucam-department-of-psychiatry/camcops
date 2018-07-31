#!/usr/bin/env python
# camcops_server/cc_modules/cc_constants.py

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

# Helpful UTF-8 characters: ‘’ “” – — × • ≤ ≥ ≠ ± →

import os

from .cc_baseconstants import (
    CAMCOPS_SERVER_DIRECTORY,
    STATIC_ROOT_DIR,
)

# =============================================================================
# Number of ID numbers. Don't alter this lightly; influences database fields.
# =============================================================================

NUMBER_OF_IDNUMS_DEFUNCT = 8  # DEFUNCT BUT DO NOT REMOVE OR ALTER. EIGHT.
# ... In older versions: determined number of ID number fields.
# (Now this is arbitrary.) Still used to support old clients.

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE_MAIN_SECTION = "server"
CONFIG_FILE_RECIPIENTLIST_SECTION = "recipients"

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
# More filenames
# =============================================================================

DEFAULT_CAMCOPS_LOGO_FILE = os.path.join(STATIC_ROOT_DIR, "logo_camcops.png")
DEFAULT_LOCAL_LOGO_FILE = os.path.join(STATIC_ROOT_DIR, "logo_local.png")

# =============================================================================
# Introspection
# =============================================================================

INTROSPECTION_BASE_DIRECTORY = CAMCOPS_SERVER_DIRECTORY

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
    """
    Collections of permitted values.
    """
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

CAMCOPS_URL = "http://www.camcops.org/"
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
}


class CssClass(object):
    """
    Values should match e.g. css_base.mako
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
# Table names used by modules that would otherwise have an interdependency, or
# are defined elsewhere
# =============================================================================

HL7MESSAGE_TABLENAME = "_hl7_message_log"

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
