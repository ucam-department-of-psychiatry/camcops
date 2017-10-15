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

from .cc_baseconstants import CAMCOPS_EXECUTABLE, CAMCOPS_SERVER_DIRECTORY

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
DEFAULT_LOCAL_INSTITUTION_URL = "http://www.camcops.org/"
DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES = 10
DEFAULT_LOCKOUT_THRESHOLD = 10
DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS = 0  # zero for never

# SERVER_BASE_DIRECTORY = os.path.join(PROJECT_BASE_DIRECTORY, "server")
# DEFAULT_STRING_FILE = os.path.join(
#     TABLET_SOURCE_COPY_DIR, "tablet_titanium", "i18n", "en", "strings.xml")
# DEFAULT_EXTRA_STRING_SPEC = os.path.join(
#     PROJECT_BASE_DIRECTORY, "server", "extra_strings", "*")
DEFAULT_TIMEOUT_MINUTES = 30
DEFAULT_PLOT_FONTSIZE = 8

MINIMUM_PASSWORD_LENGTH = 8

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
FP_ID_NUM_DEFUNCT = "idnum"
FP_ID_DESC_DEFUNCT = "iddesc"
FP_ID_SHORT_DESC_DEFUNCT = "idshortdesc"

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

# =============================================================================
# Demo configuration files, other than the CamCOPS config file itself
# =============================================================================

DEMO_SUPERVISORD_CONF = """
# =============================================================================
# Demo supervisor config file for CamCOPS
# =============================================================================
# - Supervisor is a system for controlling background processes running on
#   UNIX-like operating systems. See:
#       http://supervisord.org
# - On Ubuntu systems, you would typically install supervisor with
#       sudo apt install supervisor
#   and then save this file as
#       /etc/supervisor/conf.d/camcops.conf
#
# - IF YOU EDIT THIS FILE, run:
#       sudo service supervisor restart
# - TO MONITOR SUPERVISOR, run:
#       sudo supervisorctl status
#   ... or just "sudo supervisorctl" for an interactive prompt.
#
# - TO ADD MORE CAMCOPS INSTANCES, first consider whether you wouldn't be 
#   better off just adding groups. If you decide you want a completely new
#   instance, make a copy of the [program:camcops] section, renaming the copy, 
#   and change the following:
#   - the --config switch;
#   - the port or socket;
#   - the log files.
#   Then make the main web server point to the copy as well.
#
# NOTES ON THE SUPERVISOR CONFIG FILE AND ENVIRONMENT:
# - You can't put quotes around the directory variable
#   http://stackoverflow.com/questions/10653590
# - Python programs that are installed within a Python virtual environment 
#   automatically use the virtualenv's copy of Python via their shebang; you do
#   not need to specify that by hand, nor the PYTHONPATH.
# - The "environment" setting sets the OS environment. The "--env" parameter
#   to gunicorn, if you use it, sets the WSGI environment.

[program:camcops]

command = {CAMCOPS_EXECUTABLE}
    serve
    --config /etc/camcops/camcops.conf
    --unix_domain_socket /tmp/.camcops.sock
    --threads_start 10 --thread_max 1000

    # To run via a TCP socket, use e.g.:
    #   --host 127.0.0.1 --port 8000
    # To run via a UNIX domain socket, use e.g.
    #   --unix_domain_socket /tmp/.camcops.sock 

directory = {CAMCOPS_SERVER_DIRECTORY}

environment = MPLCONFIGDIR="/var/cache/camcops/matplotlib"

    # MPLCONFIGDIR specifies a cache directory for matplotlib, which greatly
    # speeds up its subsequent loading. 

user = www-data
    # ... Ubuntu: typically www-data
    # ... CentOS: typically apache

stdout_logfile = /var/log/supervisor/camcops_out.log
stderr_logfile = /var/log/supervisor/camcops_err.log

autostart = true
autorestart = true
startsecs = 10
stopwaitsecs = 60

""".format(
    CAMCOPS_EXECUTABLE=CAMCOPS_EXECUTABLE,
    CAMCOPS_SERVER_DIRECTORY=CAMCOPS_SERVER_DIRECTORY,
)
