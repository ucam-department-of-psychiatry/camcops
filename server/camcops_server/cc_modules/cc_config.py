#!/usr/bin/env python
# camcops_server/cc_modules/cc_config.py

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

# There are CONDITIONAL AND IN-FUNCTION IMPORTS HERE; see below. This is to
# minimize the number of modules loaded when this is used in the context of the
# client-side database script, rather than the webview.

import codecs
import configparser
import contextlib
import datetime
import operator
import os
import logging
from typing import Dict, Generator, List

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_loglevel,
    get_config_parameter_multiline
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.randomness import create_base64encoded_randomness
from cardinal_pythonlib.sqlalchemy.alembic_func import (
    get_current_and_head_revision,
)
from cardinal_pythonlib.sqlalchemy.engine_func import (
    is_sqlserver,
    is_sqlserver_2008_or_later,
)
from cardinal_pythonlib.sqlalchemy.logs import pre_disable_sqlalchemy_extra_echo_log  # noqa
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from cardinal_pythonlib.sqlalchemy.session import (
    get_safe_url_from_engine,
    make_mysql_url,
)
from pendulum import DateTime as Pendulum
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession

from .cc_baseconstants import (
    ALEMBIC_BASE_DIR,
    ALEMBIC_CONFIG_FILENAME,
    ALEMBIC_VERSION_TABLE,
    CAMCOPS_EXECUTABLE,
    CAMCOPS_SERVER_DIRECTORY,
    DEFAULT_EXTRA_STRINGS_DIR,
    ENVVAR_CONFIG_FILE,
    INTROSPECTABLE_EXTENSIONS,
    LINUX_DEFAULT_LOCK_DIR,
    LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
    STATIC_ROOT_DIR,
)
from .cc_cache import cache_region_static, fkg
from .cc_constants import (
    CONFIG_FILE_MAIN_SECTION,
    CONFIG_FILE_RECIPIENTLIST_SECTION,
    DEFAULT_CAMCOPS_LOGO_FILE,
    DEFAULT_LOCAL_INSTITUTION_URL,
    DEFAULT_LOCAL_LOGO_FILE,
    DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES,
    DEFAULT_LOCKOUT_THRESHOLD,
    DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS,
    DEFAULT_PLOT_FONTSIZE,
    DEFAULT_TIMEOUT_MINUTES,
    INTROSPECTION_BASE_DIRECTORY,
)
from .cc_filename import FilenameSpecElement, PatientSpecElementForFilename
from .cc_pyramid import MASTER_ROUTE_CLIENT_API
from .cc_simpleobjects import IntrospectionFileDetails
from .cc_recipdef import ConfigParamRecipient, RecipientDefinition
from .cc_version_string import CAMCOPS_SERVER_VERSION_STRING

log = BraceStyleAdapter(logging.getLogger(__name__))

pre_disable_sqlalchemy_extra_echo_log()


# =============================================================================
# Demo config
# =============================================================================

DEFAULT_DB_NAME = 'camcops'
DEFAULT_DB_USER = 'YYY_USERNAME_REPLACE_ME'
DEFAULT_DB_PASSWORD = 'ZZZ_PASSWORD_REPLACE_ME'
DEFAULT_DB_READONLY_USER = 'QQQ_USERNAME_REPLACE_ME'
DEFAULT_DB_READONLY_PASSWORD = 'PPP_PASSWORD_REPLACE_ME'
DUMMY_INSTITUTION_URL = 'http://www.mydomain/'


class ConfigParamMain(object):
    ALLOW_INSECURE_COOKIES = "ALLOW_INSECURE_COOKIES"
    CAMCOPS_LOGO_FILE_ABSOLUTE = "CAMCOPS_LOGO_FILE_ABSOLUTE"
    CLIENT_API_LOGLEVEL = "CLIENT_API_LOGLEVEL"
    CTV_FILENAME_SPEC = "CTV_FILENAME_SPEC"
    DB_URL = "DB_URL"
    DB_ECHO = "DB_ECHO"
    DISABLE_PASSWORD_AUTOCOMPLETE = "DISABLE_PASSWORD_AUTOCOMPLETE"
    EXTRA_STRING_FILES = "EXTRA_STRING_FILES"
    HL7_LOCKFILE = "HL7_LOCKFILE"
    INTROSPECTION = "INTROSPECTION"
    LOCAL_INSTITUTION_URL = "LOCAL_INSTITUTION_URL"
    LOCAL_LOGO_FILE_ABSOLUTE = "LOCAL_LOGO_FILE_ABSOLUTE"
    LOCKOUT_DURATION_INCREMENT_MINUTES = "LOCKOUT_DURATION_INCREMENT_MINUTES"
    LOCKOUT_THRESHOLD = "LOCKOUT_THRESHOLD"
    PASSWORD_CHANGE_FREQUENCY_DAYS = "PASSWORD_CHANGE_FREQUENCY_DAYS"
    PATIENT_SPEC = "PATIENT_SPEC"
    PATIENT_SPEC_IF_ANONYMOUS = "PATIENT_SPEC_IF_ANONYMOUS"
    SESSION_COOKIE_SECRET = "SESSION_COOKIE_SECRET"
    SESSION_TIMEOUT_MINUTES = "SESSION_TIMEOUT_MINUTES"
    SUMMARY_TABLES_LOCKFILE = "SUMMARY_TABLES_LOCKFILE"
    TASK_FILENAME_SPEC = "TASK_FILENAME_SPEC"
    TRACKER_FILENAME_SPEC = "TRACKER_FILENAME_SPEC"
    WEBVIEW_LOGLEVEL = "WEBVIEW_LOGLEVEL"
    WKHTMLTOPDF_FILENAME = "WKHTMLTOPDF_FILENAME"


def get_demo_config(extra_strings_dir: str = None,
                    lock_dir: str = None,
                    hl7_lockfile_stem: str = None,
                    static_dir: str = None,
                    summary_table_lock_file_stem: str = None,
                    db_url: str = None,
                    db_echo: bool = False) -> str:
    extra_strings_dir = extra_strings_dir or DEFAULT_EXTRA_STRINGS_DIR
    extra_strings_spec = os.path.join(extra_strings_dir, '*')
    lock_dir = lock_dir or LINUX_DEFAULT_LOCK_DIR
    hl7_lockfile_stem = hl7_lockfile_stem or os.path.join(
        lock_dir, 'camcops.hl7')
    static_dir = static_dir or STATIC_ROOT_DIR
    summary_table_lock_file_stem = (
        summary_table_lock_file_stem or os.path.join(
            lock_dir, 'camcops.summarytables'
        )
    )
    # ...
    # http://www.debian.org/doc/debian-policy/ch-opersys.html#s-writing-init
    # https://people.canonical.com/~cjwatson/ubuntu-policy/policy.html/ch-opersys.html  # noqa
    session_cookie_secret = create_base64encoded_randomness(num_bytes=64)

    if not db_url:
        db_url = make_mysql_url(username=DEFAULT_DB_USER,
                                password=DEFAULT_DB_PASSWORD,
                                dbname=DEFAULT_DB_NAME)
    return """
# Demonstration CamCOPS configuration file.
# Created by CamCOPS version {version} at {now}.

# =============================================================================
# Format of the CamCOPS configuration file
# =============================================================================
# COMMENTS. Hashes (#) and semicolons (;) mark out comments.
# SECTIONS. Sections are indicated with: [section]
# NAME/VALUE (KEY/VALUE) PAIRS.
# - The parser used is ConfigParser (Python).
# - It allows "name=value" or "name:value".
# - BOOLEAN OPTIONS. For Boolean options, TRUE values are any of: 1, yes, true,
#   on (case-insensitive). FALSE values are any of: 0, no, false, off.
# - UTF-8 encoding. Use this. For ConfigParser, the file is explicitly opened
#   in UTF-8 mode.
# - Avoid indentation.

# =============================================================================
# Main section: [{CONFIG_FILE_MAIN_SECTION}]
# =============================================================================

[{CONFIG_FILE_MAIN_SECTION}]

# -----------------------------------------------------------------------------
# Database connection/tools
# -----------------------------------------------------------------------------

# {cp.DB_URL}: SQLAlchemy connection URL.
# See http://docs.sqlalchemy.org/en/latest/core/engines.html
# Examples:
# - MySQL under Linux via mysqlclient
#   $$ pip install mysqlclient
#   DB_URL = mysql+mysqldb://<username>:<password>@<host>:<port>/<database>?charset=utf8
#
#   (The default MySQL port is 3306, and 'localhost' is often the right host.)
#
# - SQL Server under Windows via ODBC and username/password authentication
#   C:\> pip install pyodbc
#   DB_URL = mssql+pyodbc://<username>:<password>@<odbc_dsn_name>
#
# - ... or via Windows authentication: 
#   DB_URL = mssql+pyodbc://@<odbc_dsn_name>

{cp.DB_URL} = {db_url}

# {cp.DB_ECHO}: echo all SQL?

{cp.DB_ECHO} = {db_echo}

# -----------------------------------------------------------------------------
# URLs and paths
# -----------------------------------------------------------------------------
#
# A quick note on absolute and relative URLs, and how CamCOPS is mounted.
#
# Suppose your CamCOPS site is visible at
#       https://www.somewhere.ac.uk/camcops_smith_lab/webview
#       ^      ^^                 ^^                ^^      ^
#       +------++-----------------++----------------++------+
#       |       |                  |                 |
#       1       2                  3                 4
#
# Part 1 is the protocol, and part 2 the machine name.
# Part 3 is the mount point. The main server (e.g. Apache) knows where the
# CamCOPS script is mounted (in this case /camcops_smith_lab). It does NOT
# tell the script via the script's WSGI environment. Therefore, if the script
# sends HTML including links, the script can operate only in relative mode.
# For it to operate in absolute mode, it would need to know (3).
# Part 4 is visible to the CamCOPS script.
#
# If CamCOPS emitted URLs starting with '/', it would need to be told at least
# part (3). To use absolute URLs, it would need to know all of (1), (2), (3).
# We will follow others (e.g. http://stackoverflow.com/questions/2005079) and
# use only relative URLs.

# {cp.LOCAL_INSTITUTION_URL}: Clicking on your institution's logo in the CamCOPS
# menu will take you to this URL.
# Edit the next line to point to your institution:

{cp.LOCAL_INSTITUTION_URL} = {DUMMY_INSTITUTION_URL}

# {cp.LOCAL_LOGO_FILE_ABSOLUTE}: Specify the full path to your institution's logo
# file, e.g. /var/www/logo_local_myinstitution.png . It's used for PDF
# generation; HTML views use the fixed string "static/logo_local.png", aliased
# to your file via the Apache configuration file).
# Edit the next line to point to your local institution's logo file:

{cp.LOCAL_LOGO_FILE_ABSOLUTE} = {static_dir}/logo_local.png

# {cp.CAMCOPS_LOGO_FILE_ABSOLUTE}: similarly, but for the CamCOPS logo.
# It's fine not to specify this.

# {cp.CAMCOPS_LOGO_FILE_ABSOLUTE} = {static_dir}/logo_camcops.png

# {cp.EXTRA_STRING_FILES}: multiline list of filenames (with absolute paths), read
# by the server, and used as EXTRA STRING FILES. Should at the MINIMUM point
# to the string file camcops.xml
# May use "glob" pattern-matching (see
# https://docs.python.org/3.5/library/glob.html).

{cp.EXTRA_STRING_FILES} = {extra_strings_spec}

# {cp.INTROSPECTION}: permits the offering of CamCOPS source code files to the user,
# allowing inspection of tasks' internal calculating algorithms. Default is
# true.

{cp.INTROSPECTION} = true

# {cp.HL7_LOCKFILE}: filename stem used for process locking for HL7 message
# transmission. Default is {hl7_lockfile_stem}
# The actual lockfile will, in this case, be called
#     {hl7_lockfile_stem}.lock
# and other process-specific files will be created in the same directory (so
# the CamCOPS script must have permission from the operating system to do so).
# The installation script will create the directory {lock_dir}

{cp.HL7_LOCKFILE} = {hl7_lockfile_stem}

# {cp.SUMMARY_TABLES_LOCKFILE}: file stem used for process locking for summary table
# generation. Default is {summary_table_lock_file_stem}.
# The lockfile will, in this case, be called
#     {summary_table_lock_file_stem}.lock
# and other process-specific files will be created in the same directory (so
# the CamCOPS script must have permission from the operating system to do so).
# The installation script will create the directory {lock_dir}

{cp.SUMMARY_TABLES_LOCKFILE} = {summary_table_lock_file_stem}

# {cp.WKHTMLTOPDF_FILENAME}: for the pdfkit PDF engine, specify a filename for
# wkhtmltopdf that incorporates any need for an X Server (not the default
# /usr/bin/wkhtmltopdf). See http://stackoverflow.com/questions/9604625/ .
# A suitable one is bundled with CamCOPS, so you shouldn't have to alter this
# default. Default is None, which usually ends up calling /usr/bin/wkhtmltopdf

{cp.WKHTMLTOPDF_FILENAME} =

# -----------------------------------------------------------------------------
# Login and session configuration
# -----------------------------------------------------------------------------

# {cp.SESSION_COOKIE_SECRET}: Secret used for HTTP cookie signing via Pyramid.
# Put something random in here and keep it secret.
# (When you make a CamCOPS demo config, the value shown is fresh and random.)

{cp.SESSION_COOKIE_SECRET} = camcops_autogenerated_secret_{session_cookie_secret}

# {cp.SESSION_TIMEOUT_MINUTES}: Time after which a session will expire (default 30).

{cp.SESSION_TIMEOUT_MINUTES} = 30

# {cp.PASSWORD_CHANGE_FREQUENCY_DAYS}: Force password changes (at webview login)
# with this frequency (0 for never). Note that password expiry will not prevent
# uploads from tablets, but when the user next logs on, a password change will
# be forced before they can do anything else.

{cp.PASSWORD_CHANGE_FREQUENCY_DAYS} = 0

# {cp.LOCKOUT_THRESHOLD}: Lock user accounts after every n login failures (default
# 10).

{cp.LOCKOUT_THRESHOLD} = 10

# {cp.LOCKOUT_DURATION_INCREMENT_MINUTES}: Account lockout time increment (default
# 10).
# Suppose {cp.LOCKOUT_THRESHOLD} = 10 and {cp.LOCKOUT_DURATION_INCREMENT_MINUTES} = 20.
# After the first 10 failures, the account will be locked for 20 minutes.
# After the next 10 failures, the account will be locked for 40 minutes.
# After the next 10 failures, the account will be locked for 60 minutes, and so
# on. Time and administrators can unlock accounts.

{cp.LOCKOUT_DURATION_INCREMENT_MINUTES} = 10

# {cp.DISABLE_PASSWORD_AUTOCOMPLETE}: if true, asks browsers not to autocomplete the
# password field on the main login page. The correct setting for maximum
# security is debated (don't cache passwords, versus allow a password manager
# so that users can use better/unique passwords). Default: true.
# Note that some browsers (e.g. Chrome v34 and up) may ignore this.

{cp.DISABLE_PASSWORD_AUTOCOMPLETE} = true

# -----------------------------------------------------------------------------
# Suggested filenames for saving PDFs from the web view
# -----------------------------------------------------------------------------
# Try with Chrome, Firefox. Internet Explorer may be less obliging.

# {cp.PATIENT_SPEC_IF_ANONYMOUS}: for anonymous tasks, this fixed string is 
# used as the patient descriptor (see also {cp.PATIENT_SPEC} below).
# Typically "anonymous".

{cp.PATIENT_SPEC_IF_ANONYMOUS} = anonymous

# {cp.PATIENT_SPEC}: string, into which substitutions will be made, that defines the
# {{{fse.PATIENT}}} element available for substitution into the *_FILENAME_SPEC
# variables (see below). Possible substitutions:
#
#   {{{pse.SURNAME}}}      : patient's surname in upper case
#   {{{pse.FORENAME}}}     : patient's forename in upper case
#   {{{pse.DOB}}}          : patient's date of birth (format "%Y-%m-%d", e.g.
#                    2013-07-24)
#   {{{pse.SEX}}}          : patient's sex (M, F, X)
#
#   {{{pse.IDSHORTDESC_PREFIX}1}} : short description of the relevant ID number, if that ID
#   {{{pse.IDSHORTDESC_PREFIX}2}}   number is not blank; otherwise blank
#   ...
#
#   {{{pse.IDNUM_PREFIX}1}}       : ID numbers
#   {{{pse.IDNUM_PREFIX}2}}
#   ...
#
#   {{{pse.ALLIDNUMS}}}    : all available ID numbers in "shortdesc-value" pairs joined
#                    by "_". For example, if ID numbers 1, 4, and 5 are
#                    non-blank, this would have the format
#                    {pse.IDSHORTDESC_PREFIX}1-{pse.IDNUM_PREFIX}1_{pse.IDSHORTDESC_PREFIX}4-{pse.IDNUM_PREFIX}4_{pse.IDSHORTDESC_PREFIX}5-{pse.IDNUM_PREFIX}5

{cp.PATIENT_SPEC} = {{{pse.SURNAME}}}_{{{pse.FORENAME}}}_{{{pse.ALLIDNUMS}}}

# {cp.TASK_FILENAME_SPEC}:
# {cp.TRACKER_FILENAME_SPEC}:
# {cp.CTV_FILENAME_SPEC}:
# Strings used for suggested filenames to save from the webview, for tasks,
# trackers, and clinical text views. Substitutions will be made to determine
# the filename to be used for each file. Possible substitutions:
#
#   {{{fse.PATIENT}}}   : Patient string. If the task is anonymous, this is
#                 {cp.PATIENT_SPEC_IF_ANONYMOUS}; otherwise, it is defined by
#                 {cp.PATIENT_SPEC} above.
#   {{{fse.CREATED}}}   : Date/time of task creation.  Dates/times are of the format
#                 "%Y-%m-%dT%H%M", e.g. 2013-07-24T2004. They are expressed in
#                 the timezone of creation (but without the timezone
#                 information for filename brevity).
#   {{{fse.NOW}}}       : Time of access/download (i.e. time now), in local timezone.
#   {{{fse.TASKTYPE}}}  : Base table name of the task (e.g. "phq9"). May contain an
#                 underscore. Blank for to trackers/CTVs.
#   {{{fse.SERVERPK}}}  : Server's primary key. (In combination with tasktype, this
#                 uniquely identifies not just a task but a version of that
#                 task.) Blank for trackers/CTVs.
#   {{{fse.FILETYPE}}}  : e.g. "pdf", "html", "xml" (lower case)
#   {{{fse.ANONYMOUS}}} : evaluates to {cp.PATIENT_SPEC_IF_ANONYMOUS} if anonymous,
#                 otherwise ""
#   ... plus all those substitutions applicable to {cp.PATIENT_SPEC}
#
# After these substitutions have been made, the entire filename is then
# processed to ensure that only characters generally acceptable to filenames
# are used (see convert_string_for_filename() in the CamCOPS source code).
# Specifically:
#
#   - Unicode converted to 7-bit ASCII (will mangle, e.g. removing accents)
#   - spaces converted to underscores
#   - characters are removed unless they are one of the following: all
#     alphanumeric characters (0-9, A-Z, a-z); '-'; '_'; '.'; and the
#     operating-system-specific directory separator (Python's os.sep, a forward
#     slash '/' on UNIX or a backslash '\' under Windows).

{cp.TASK_FILENAME_SPEC} = CamCOPS_{{patient}}_{{created}}_{{tasktype}}-{{serverpk}}.{{filetype}}
{cp.TRACKER_FILENAME_SPEC} = CamCOPS_{{patient}}_{{now}}_tracker.{{filetype}}
{cp.CTV_FILENAME_SPEC} = CamCOPS_{{patient}}_{{now}}_clinicaltextview.{{filetype}}

# -----------------------------------------------------------------------------
# Debugging options
# -----------------------------------------------------------------------------
# Possible log levels are (case-insensitive): "debug", "info", "warn"
# (equivalent: "warning"), "error", and "critical" (equivalent: "fatal").

# {cp.WEBVIEW_LOGLEVEL}: Set the level of detail provided from the webview to the
# Apache server log. (Loglevel option; see above.)

{cp.WEBVIEW_LOGLEVEL} = info

# {cp.CLIENT_API_LOGLEVEL}: Set the log level for the tablet client database access
# script. (Loglevel option; see above.)

{cp.CLIENT_API_LOGLEVEL} = info

# {cp.ALLOW_INSECURE_COOKIES}: DANGEROUS option that removes the requirement that
# cookies be HTTPS (SSL) only.

{cp.ALLOW_INSECURE_COOKIES} = false

# =============================================================================
# List of HL7/file recipients, and then details for each one
# =============================================================================
# This section defines a list of recipients to which Health Level Seven (HL7)
# messages or raw files will be sent. Typically, you will send them by calling
# "camcops -7 CONFIGFILE" regularly from the system's /etc/crontab or other
# scheduling system. For example, a conventional /etc/crontab file has these
# fields:
#
#   minutes, hours, day_of_month, month, day_of_week, user, command
#
# so you could add a line like this to /etc/crontab:
#
#   * * * * *  root  camcops -7 /etc/camcops/MYCONFIG.conf
#
# ... and CamCOPS would run its exports once per minute. See "man 5 crontab"
# or http://en.wikipedia.org/wiki/Cron for more options.
#
# In this section, keys are ignored; values are section headings (one per
# recipient).

[{CONFIG_FILE_RECIPIENTLIST_SECTION}]

# Examples (commented out):

# recipient=recipient_A
# recipient=recipient_B

# =============================================================================
# Individual HL7/file recipient configurations
# =============================================================================
# Dates are YYYY-MM-DD, e.g. 2013-12-31, or blank

# Example (disabled because it's not in the list above)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# First example
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[recipient_A]

# {cpr.TYPE}: one of the following methods.
#   hl7
#       Sends HL7 messages across a TCP/IP network.
#   file
#       Writes files to a local filesystem.

{cpr.TYPE} = hl7

# -----------------------------------------------------------------------------
# Options applicable to HL7 messages and file transfers
# -----------------------------------------------------------------------------

# {cpr.GROUP_ID}: CamCOPS group to export from.
# HL7 messages are sent from one group at a time. Which group will this
# recipient definition use? (Note that you can just duplicate a recipient
# definition to export a second or subsequent group.)
# This is an integer.

{cpr.GROUP_ID} = 1

# {cpr.PRIMARY_IDNUM}: which ID number (1-8) should be considered the "internal"
# (primary) ID number? Must be specified for HL7 messages. May be blank for
# file transmission.

{cpr.PRIMARY_IDNUM} = 1

# {cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY}: defines behaviour relating to the
# primary ID number (as defined by PRIMARY_IDNUM).
# - If true, no message sending will be attempted unless the {cpr.PRIMARY_IDNUM} is a
#   mandatory part of the finalizing policy (and if {cpr.FINALIZED_ONLY} is false,
#   also of the upload policy).
# - If false, messages will be sent, but ONLY FROM TASKS FOR WHICH THE
#   {cpr.PRIMARY_IDNUM} IS PRESENT; others will be ignored.
# - For file sending only, this will be ignored if {cpr.PRIMARY_IDNUM} is blank.
# - For file sending only, this setting does not apply to anonymous tasks,
#   whose behaviour is controlled by {cpr.INCLUDE_ANONYMOUS} (see below).

{cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY} = true

# {cpr.START_DATE}: earliest date for which tasks will be sent. Assessed against the
# task's "when_created" field, converted to Universal Coordinated Time (UTC) --
# that is, this date is in UTC (beware if you are in a very different time
# zone). Blank to apply no start date restriction.

{cpr.START_DATE} =

# {cpr.END_DATE}: latest date for which tasks will be sent. In UTC. Assessed against
# the task's "when_created" field (converted to UTC). Blank to apply no end
# date restriction.

{cpr.END_DATE} =

# {cpr.FINALIZED_ONLY}: if true, only send tasks that are finalized (moved off their
# originating tablet and not susceptible to later modification). If false, also
# send tasks that are uploaded but not yet finalized (they will then be sent
# again if they are modified later).

{cpr.FINALIZED_ONLY} = true

# {cpr.TASK_FORMAT}: one of: pdf, html, xml

{cpr.TASK_FORMAT} = pdf

# {cpr.XML_FIELD_COMMENTS}: if {cpr.TASK_FORMAT} is xml, then {cpr.XML_FIELD_COMMENTS} determines
# whether field comments are included. These describe the meaning of each field
# so add to space requirements but provide more information for human readers.
# (Default true.)

{cpr.XML_FIELD_COMMENTS} = true

# -----------------------------------------------------------------------------
# Options applicable to HL7 only ({cpr.TYPE} = hl7)
# -----------------------------------------------------------------------------

# {cpr.HOST}: HL7 hostname or IP address

{cpr.HOST} = myhl7server.mydomain

# {cpr.PORT}: HL7 port (default 2575)

{cpr.PORT} = 2575

# {cpr.PING_FIRST}: if true, requires a successful ping to the server prior to
# sending HL7 messages. (Note: this is a TCP/IP ping, and tests that the
# machine is up, not that it is running an HL7 server.) Default: true.

{cpr.PING_FIRST} = true

# {cpr.NETWORK_TIMEOUT_MS}: network time (in milliseconds). Default: 10000.

{cpr.NETWORK_TIMEOUT_MS} = 10000

# {cpr.KEEP_MESSAGE}: keep a copy of the entire message in the databaase. Default is
# false. WARNING: may consume significant space in the database.

{cpr.KEEP_MESSAGE} = false

# {cpr.KEEP_REPLY}: keep a copy of the reply (e.g. acknowledgement) message received
# from the server. Default is false. WARNING: may consume significant space.

{cpr.KEEP_REPLY} = false

# {cpr.DIVERT_TO_FILE}: Override HOST/PORT options and send HL7 messages to this
# (single) file instead. Each messages is appended to the file. Default is
# blank (meaning network transmission will be used). This is a debugging
# option, allowing you to redirect HL7 messages to a file and inspect them.

{cpr.DIVERT_TO_FILE} =

# {cpr.TREAT_DIVERTED_AS_SENT}: Any messages that are diverted to a file (using
# {cpr.DIVERT_TO_FILE}) are treated as having been sent (thus allowing the file to
# mimic an HL7-receiving server that's accepting messages happily). If set to
# false (the default), a diversion will allow you to preview messages for
# debugging purposes without "swallowing" them. BEWARE, though: if you have
# an automatically scheduled job (for example, to send messages every minute)
# and you divert with this flag set to false, you will end up with a great many
# message attempts!

{cpr.TREAT_DIVERTED_AS_SENT} = false

# -----------------------------------------------------------------------------
# Options applicable to file transfers only (TYPE = file)
# -----------------------------------------------------------------------------

# {cpr.INCLUDE_ANONYMOUS}: include anonymous tasks.
# - Note that anonymous tasks cannot be sent via HL7; the HL7 specification is
#   heavily tied to identification.
# - Note also that this setting operates independently of the
#   {cpr.REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY} setting.

{cpr.INCLUDE_ANONYMOUS} = true

# {cpr.PATIENT_SPEC_IF_ANONYMOUS}: for anonymous tasks, this string is used as the
# patient descriptor (see also {cpr.PATIENT_SPEC}, {cpr.FILENAME_SPEC} below). Typically
# "anonymous".

{cpr.PATIENT_SPEC_IF_ANONYMOUS} = anonymous

# {cpr.PATIENT_SPEC}: string, into which substitutions will be made, that defines the
# {{patient}} element available for substitution into the {cpr.FILENAME_SPEC} (see
# below). Possible substitutions: as for {cpr.PATIENT_SPEC} in the main
# "[{CONFIG_FILE_MAIN_SECTION}]" section of the configuration file (see above).

{cpr.PATIENT_SPEC} = {{surname}}_{{forename}}_{{idshortdesc1}}{{idnum1}}

# {cpr.FILENAME_SPEC}: string into which substitutions will be made to determine the
# filename to be used for each file. Possible substitutions: as for
# {cp.PATIENT_SPEC} in the main "[{CONFIG_FILE_MAIN_SECTION}]" section of the configuration
# file (see above).

{cpr.FILENAME_SPEC} = /my_nfs_mount/mypath/CamCOPS_{{patient}}_{{created}}_{{tasktype}}-{{serverpk}}.{{filetype}}

# {cpr.MAKE_DIRECTORY}: make the directory if it doesn't already exist. Default is
# false.

{cpr.MAKE_DIRECTORY} = true

# {cpr.OVERWRITE_FILES}: whether or not to attempt overwriting existing files of the
# same name (default false). There is a DANGER of inadvertent data loss if you
# set this to true. (Needing to overwrite a file suggests that your filenames
# are not task-unique; try ensuring that both the {{tasktype}} and {{serverpk}}
# attributes are used in the filename.)

{cpr.OVERWRITE_FILES} = false

# {cpr.RIO_METADATA}: whether or not to export a metadata file for Servelec's RiO
# (default false).
# Details of this file format are in cc_task.py / Task.get_rio_metadata().
# The metadata filename is that of its associated file, but with the extension
# replaced by ".metadata" (e.g. X.pdf is accompanied by X.metadata).
# If {cpr.RIO_METADATA} is true, the following options also apply:
#   {cpr.RIO_IDNUM}: which of the ID numbers (as above) is the RiO ID?
#   {cpr.RIO_UPLOADING_USER}: username for the uploading user (maximum of 10
#       characters)
#   {cpr.RIO_DOCUMENT_TYPE}: document type as defined in the receiving RiO system.
#       This is a code that maps to a human-readable document type; for
#       example, the code "APT" might map to "Appointment Letter". Typically we
#       might want a code that maps to "Clinical Correspondence", but the code
#       will be defined within the local RiO system configuration.

{cpr.RIO_METADATA} = false
{cpr.RIO_IDNUM} = 2
{cpr.RIO_UPLOADING_USER} = CamCOPS
{cpr.RIO_DOCUMENT_TYPE} = CC

# {cpr.SCRIPT_AFTER_FILE_EXPORT}: filename of a shell script or other executable to
# run after file export is complete. You might use this script, for example, to
# move the files to a different location (such as across a network). If the
# parameter is blank, no script will be run. If no files are exported, the
# script will not be run.
# - Parameters passed to the script: a list of all the filenames exported.
#   (This includes any RiO metadata filenames.)
# - WARNING: the script will execute with the same permissions as the instance
#   of CamCOPS that's doing the export (so, for example, if you run CamCOPS
#   from your /etc/crontab as root, then this script will be run as root; that
#   can pose a risk!).
# - The script executes while the export lock is still held by CamCOPS (i.e.
#   further HL7/file transfers won't be started until the script(s) is/are
#   complete).
# - If the script fails, an error message is recorded, but the file transfer is
#   still considered to have been made (CamCOPS has done all it can and the
#   responsibility now lies elsewhere).
# - Example test script: suppose this is /usr/local/bin/print_arguments:
#       #!/bin/bash
#       for f in $$@
#       do
#           echo "CamCOPS has just exported this file: $$f"
#       done
#   ... then you could set:
#       {cpr.SCRIPT_AFTER_FILE_EXPORT} = /usr/local/bin/print_arguments

{cpr.SCRIPT_AFTER_FILE_EXPORT} =

    """.format(  # noqa
        cp=ConfigParamMain,
        cpr=ConfigParamRecipient,
        CONFIG_FILE_MAIN_SECTION=CONFIG_FILE_MAIN_SECTION,
        CONFIG_FILE_RECIPIENTLIST_SECTION=CONFIG_FILE_RECIPIENTLIST_SECTION,
        db_echo=db_echo,
        db_url=db_url,
        DEFAULT_DB_NAME=DEFAULT_DB_NAME,
        DEFAULT_DB_PASSWORD=DEFAULT_DB_PASSWORD,
        DEFAULT_DB_USER=DEFAULT_DB_USER,
        extra_strings_spec=extra_strings_spec,
        hl7_lockfile_stem=hl7_lockfile_stem,
        lock_dir=lock_dir,
        static_dir=static_dir,
        summary_table_lock_file_stem=summary_table_lock_file_stem,
        DUMMY_INSTITUTION_URL=DUMMY_INSTITUTION_URL,
        fse=FilenameSpecElement,
        now=str(Pendulum.now()),
        pse=PatientSpecElementForFilename,
        session_cookie_secret=session_cookie_secret,
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


# =============================================================================
# Demo configuration files, other than the CamCOPS config file itself
# =============================================================================

DEFAULT_INTERNAL_PORT = 8000
DEFAULT_SOCKET_FILENAME = "/tmp/.camcops.sock"


def get_demo_supervisor_config(
        specimen_internal_port: int = DEFAULT_INTERNAL_PORT,
        specimen_socket_file: str = DEFAULT_SOCKET_FILENAME) -> str:
    return """
# =============================================================================
# Demonstration 'supervisor' config file for CamCOPS.
# Created by CamCOPS version {version} at {now}.
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
# - Indented lines are treated as continuation (even in commands; no need for
#   end-of-line backslashes or similar).
# - The downside of that is that indented comment blocks can join onto your
#   commands! Beware that.
# - You can't put quotes around the directory variable
#   http://stackoverflow.com/questions/10653590
# - Python programs that are installed within a Python virtual environment 
#   automatically use the virtualenv's copy of Python via their shebang; you do
#   not need to specify that by hand, nor the PYTHONPATH.
# - The "environment" setting sets the OS environment. The "--env" parameter
#   to gunicorn, if you use it, sets the WSGI environment.

[program:camcops]

command = {CAMCOPS_EXECUTABLE}
    serve_gunicorn
    --config /etc/camcops/camcops.conf
    --unix_domain_socket {specimen_socket_file}
    --trusted_proxy_headers 
        HTTP_X_FORWARDED_HOST 
        HTTP_X_FORWARDED_SERVER 
        HTTP_X_FORWARDED_PORT 
        HTTP_X_FORWARDED_PROTO 
        HTTP_X_SCRIPT_NAME

# To run via a TCP socket, use e.g.:
#   --host 127.0.0.1 --port {specimen_internal_port}
# To run via a UNIX domain socket, use e.g.
#   --unix_domain_socket {specimen_socket_file} 

directory = {CAMCOPS_SERVER_DIRECTORY}

environment = MPLCONFIGDIR="{LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR}"

# MPLCONFIGDIR specifies a cache directory for matplotlib, which greatly
# speeds up its subsequent loading. 

user = www-data

# ... Ubuntu: typically www-data
# ... CentOS: typically apache

stdout_logfile = /var/log/supervisor/camcops_out.log
stderr_logfile = /var/log/supervisor/camcops_err.log

autostart = true
autorestart = true
startsecs = 30
stopwaitsecs = 60

    """.format(
        CAMCOPS_EXECUTABLE=CAMCOPS_EXECUTABLE,
        CAMCOPS_SERVER_DIRECTORY=CAMCOPS_SERVER_DIRECTORY,
        LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR=LINUX_DEFAULT_MATPLOTLIB_CACHE_DIR,
        now=str(Pendulum.now()),
        specimen_internal_port=specimen_internal_port,
        specimen_socket_file=specimen_socket_file,
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


def get_demo_apache_config(
        urlbase: str = "/camcops",
        specimen_internal_port: int = DEFAULT_INTERNAL_PORT,
        specimen_socket_file: str = DEFAULT_SOCKET_FILENAME) -> str:
    return """
    # Demonstration Apache config file section for CamCOPS.
    # Created by CamCOPS version {version} at {now}.
    #
    # Under Ubuntu, the Apache config will be somewhere in /etc/apache2/
    # Under CentOS, the Apache config will be somewhere in /etc/httpd/
    #
    # This section should go within the <VirtualHost> directive for the secure
    # (SSL, HTTPS) part of the web site. 

<VirtualHost *:443>
    # ...

    # =========================================================================
    # CamCOPS
    # =========================================================================
    # Apache operates on the principle that the first match wins. So, if we
    # want to serve CamCOPS but then override some of its URLs to serve static
    # files faster, we define the static stuff first.

        # ---------------------------------------------------------------------
        # 1. Serve static files
        # ---------------------------------------------------------------------
        # a) offer them at the appropriate URL
        # b) provide permission
        # c) disable ProxyPass for static files

        # Change this: aim the alias at your own institutional logo.
        
    Alias {urlbase}/static/logo_local.png {STATIC_ROOT_DIR}/logo_local.png
    
        # We move from more specific to less specific aliases; the first match
        # takes precedence. (Apache will warn about conflicting aliases if
        # specified in a wrong, less-to-more-specific, order.)

    Alias {urlbase}/static/ {STATIC_ROOT_DIR}/

    <Directory {STATIC_ROOT_DIR}>
        Require all granted
        
        # ... for old Apache version (e.g. 2.2), use instead:
        # Order allow,deny
        # Allow from all
    </Directory>
    
        # Don't ProxyPass the static files; we'll serve them via Apache.
        
    ProxyPassMatch ^{urlbase}/static/ !

        # ---------------------------------------------------------------------
        # 2. Proxy requests to the CamCOPS web server and back; allow access
        # ---------------------------------------------------------------------
        # ... either via an internal TCP/IP port (e.g. 1024 or higher, and NOT
        #     accessible to users);
        # ... or, better, via a Unix socket, e.g. /tmp/.camcops.sock
        #
        # NOTES
        # - When you ProxyPass {urlbase}, you should browse to
        #       https://YOURSITE{urlbase}
        #   and point your tablet devices to
        #       https://YOURSITE{urlbase}{MASTER_ROUTE_CLIENT_API}
        # - Don't specify trailing slashes for the ProxyPass and 
        #   ProxyPassReverse directives.
        #   If you do, http://host/camcops will fail though
        #              http://host/camcops/ will succeed.
        # - Ensure that you put the CORRECT PROTOCOL (http, https) in the rules
        #   below.
        # - For ProxyPass options, see https://httpd.apache.org/docs/2.2/mod/mod_proxy.html#proxypass
        #   ... including "retry=0" to stop Apache disabling the connection for
        #       a while on failure.
        # - Using a socket
        #   - this requires Apache 2.4.9, and passes after the '|' character a
        #     URL that determines the Host: value of the request; see
        #     https://httpd.apache.org/docs/trunk/mod/mod_proxy.html#proxypass
        # - CamCOPS MUST BE TOLD about its location and protocol, because that
        #   information is critical for synthesizing URLs, but is stripped out
        #   by the reverse proxy system. There are two ways:
        #   (i)  specifying headers or WSGI environment variables, such as
        #        the HTTP(S) headers X-Forwarded-Proto and X-Script-Name below
        #        (CamCOPS is aware of these);
        #   (ii) specifying options to "camcops serve", including
        #           --script_name
        #           --scheme
        #        and optionally
        #           --server
        #
        # So:
        #
        # ~~~~~~~~~~~~~~~~~
        # (a) Reverse proxy
        # ~~~~~~~~~~~~~~~~~
        #
        # PORT METHOD
        # Note the use of "http" (reflecting the backend), not https (like the
        # front end).
        
    ProxyPass {urlbase} http://127.0.0.1:{specimen_internal_port} retry=0
    ProxyPassReverse {urlbase} http://127.0.0.1:{specimen_internal_port} retry=0

        # UNIX SOCKET METHOD (Apache 2.4.9 and higher)
        #
        # The general syntax is:
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|PROTOCOL://HOST/EXTRA_URL_FOR_BACKEND retry=0
        # Note that:
        #   - the protocol should be http, not https (Apache deals with the
        #     HTTPS part and passes HTTP on)
        #   - the EXTRA_URL_FOR_BACKEND needs to be (a) unique for each
        #     instance or Apache will use a single worker for multiple
        #     instances, and (b) blank for the backend's benefit. Since those
        #     two conflict when there's >1 instance, there's a problem.
        #   - Normally, HOST is given as localhost. It may be that this problem
        #     is solved by using a dummy unique value for HOST:
        #     https://bz.apache.org/bugzilla/show_bug.cgi?id=54101#c1
        #
        # If your Apache version is too old, you will get the error
        #   "AH00526: Syntax error on line 56 of /etc/apache2/sites-enabled/SOMETHING:
        #    ProxyPass URL must be absolute!"
        # On Ubuntu, if your Apache is too old, you could use
        #   sudo add-apt-repository ppa:ondrej/apache2
        # ... details at https://launchpad.net/~ondrej/+archive/ubuntu/apache2
        #
        # If you get this error:
        #   AH01146: Ignoring parameter 'retry=0' for worker 'unix:/tmp/.camcops_gunicorn.sock|https://localhost' because of worker sharing
        #   https://wiki.apache.org/httpd/ListOfErrors
        # ... then your URLs are overlapping and should be redone or sorted:
        #   http://httpd.apache.org/docs/2.4/mod/mod_proxy.html#workers
        # The part that must be unique for each instance, with no part a
        # leading substring of any other, is THIS_BIT in:
        #   ProxyPass /URL_USER_SEES unix:SOCKETFILE|https://localhost/THIS_BIT retry=0
        #
        # If you get an error like this:
        #   AH01144: No protocol handler was valid for the URL /SOMEWHERE. If you are using a DSO version of mod_proxy, make sure the proxy submodules are included in the configuration using LoadModule.
        # Then do this:
        #   sudo a2enmod proxy proxy_http
        #   sudo apache2ctl restart
        #
        # If you get an error like this:
        #   ... [proxy_http:error] [pid 32747] (103)Software caused connection abort: [client 109.151.49.173:56898] AH01102: error reading status line from remote server httpd-UDS:0
        #       [proxy:error] [pid 32747] [client 109.151.49.173:56898] AH00898: Error reading from remote server returned by /camcops_bruhl/webview
        # then check you are specifying http://, not https://, in the ProxyPass
        #
        # Other information sources:
        #   https://emptyhammock.com/projects/info/pyweb/webconfig.html

    # ProxyPass /camcops unix:{specimen_socket_file}|https://dummy1/ retry=0
    # ProxyPassReverse /camcops unix:{specimen_socket_file}|https://dummy1/ retry=0

        # ~~~~~~~~~~~~~~~~~~~~~~~~~
        # (b) Allow proxy over SSL.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~
        # Without this, you will get errors like:
        #   ... SSL Proxy requested for wombat:443 but not enabled [Hint: SSLProxyEngine]
        #   ... failed to enable ssl support for 0.0.0.0:0 (httpd-UDS)
        
    SSLProxyEngine on

    <Location /camcops>

            # ~~~~~~~~~~~~~~~~    
            # (c) Allow access
            # ~~~~~~~~~~~~~~~~
            
        Require all granted

        # ... for old Apache version (e.g. 2.2), use instead:
        # Order allow,deny
        # Allow from all

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # (d) Tell the proxied application that we are using HTTPS, and
            #     where the application is installed
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #     ... https://stackoverflow.com/questions/16042647
            #
            # EITHER enable mod_headers (e.g. "sudo a2enmod headers") and set:
            
        RequestHeader set X-Forwarded-Proto https
        RequestHeader set X-Script-Name {urlbase}
        
            # and call CamCOPS like:
            #
            # camcops serve_gunicorn \\
            #       --config SOMECONFIG \\
            #       --trusted_proxy_headers \\
            #           HTTP_X_FORWARDED_HOST \\
            #           HTTP_X_FORWARDED_SERVER \\
            #           HTTP_X_FORWARDED_PORT \\
            #           HTTP_X_FORWARDED_PROTO \\
            #           HTTP_X_SCRIPT_NAME
            #
            # (X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Server are
            # supplied by Apache automatically)
            #
            # ... OR specify those options by hand in the CamCOPS command.
            
    </Location>

        # ---------------------------------------------------------------------
        # 3. For additional instances
        # ---------------------------------------------------------------------
        # (a) duplicate section 1 above, editing the base URL and CamCOPS
        #     connection (socket/port);
        # (b) you will also need to create an additional CamCOPS instance,
        #     as above;
        # (c) add additional static aliases (in section 2 above).
        #
        # HOWEVER, consider adding more CamCOPS groups, rather than creating
        # additional instances; the former are *much* easier to administer!


    #==========================================================================
    # SSL security (for HTTPS)
    #==========================================================================

        # You will also need to install your SSL certificate; see the 
        # instructions that came with it. You get a certificate by creating a 
        # certificate signing request (CSR). You enter some details about your 
        # site, and a software tool makes (1) a private key, which you keep 
        # utterly private, and (2) a CSR, which you send to a Certificate 
        # Authority (CA) for signing. They send back a signed certificate, and 
        # a chain of certificates leading from yours to a trusted root CA.
        #
        # You can create your own (a 'snake-oil' certificate), but your tablets
        # and browsers will not trust it, so this is a bad idea.
        #
        # Once you have your certificate: edit and uncomment these lines:

    # SSLEngine on

    # SSLCertificateKeyFile /etc/ssl/private/my.private.key

        # ... a private file that you made before creating the certificate
        # request, and NEVER GAVE TO ANYBODY, and NEVER WILL (or your
        # security is broken and you need a new certificate).

    # SSLCertificateFile /etc/ssl/certs/my.public.cert

        # ... signed and supplied to you by the certificate authority (CA),
        # from the public certificate you sent to them.

    # SSLCertificateChainFile /etc/ssl/certs/my-institution.ca-bundle

        # ... made from additional certificates in a chain, supplied to you by
        # the CA. For example, mine is univcam.ca-bundle, made with the
        # command:
        #
        # cat TERENASSLCA.crt UTNAddTrustServer_CA.crt AddTrustExternalCARoot.crt > univcam.ca-bundle

</VirtualHost>

    """.format(  # noqa
        MASTER_ROUTE_CLIENT_API=MASTER_ROUTE_CLIENT_API,
        now=str(Pendulum.now()),
        specimen_internal_port=specimen_internal_port,
        specimen_socket_file=specimen_socket_file,
        STATIC_ROOT_DIR=STATIC_ROOT_DIR,
        urlbase=urlbase,
        version=CAMCOPS_SERVER_VERSION_STRING,
    )


def get_demo_mysql_create_db() -> str:
    return """
# First, from the Linux command line, log in to MySQL as root:

mysql --host=127.0.0.1 --port=3306 --user=root --password
# ... or the usual short form: mysql -u root -p

# Create the database:

CREATE DATABASE {DEFAULT_DB_NAME};

# Ideally, create another user that only has access to the CamCOPS database.
# You should do this, so that you don’t use the root account unnecessarily.

GRANT ALL PRIVILEGES ON {DEFAULT_DB_NAME}.* TO '{DEFAULT_DB_USER}'@'localhost' IDENTIFIED BY '{DEFAULT_DB_PASSWORD}';

# For future use: if you plan to explore your database directly for analysis,
# you may want to create a read-only user. Though it may not be ideal (check:
# are you happy the user can see the audit trail?), you can create a user with
# read-only access to the entire database like this:

GRANT SELECT {DEFAULT_DB_NAME}.* TO '{DEFAULT_DB_READONLY_USER}'@'localhost' IDENTIFIED BY '{DEFAULT_DB_READONLY_PASSWORD}';

# All done. Quit MySQL:

exit
    """.format(  # noqa
        DEFAULT_DB_NAME=DEFAULT_DB_NAME,
        DEFAULT_DB_USER=DEFAULT_DB_USER,
        DEFAULT_DB_PASSWORD=DEFAULT_DB_PASSWORD,
        DEFAULT_DB_READONLY_USER=DEFAULT_DB_READONLY_USER,
        DEFAULT_DB_READONLY_PASSWORD=DEFAULT_DB_READONLY_PASSWORD,
    )


def get_demo_mysql_dump_script() -> str:
    return """#!/bin/bash

# Minimal simple script to dump all current MySQL databases.
# This file must be READABLE ONLY BY ROOT (or equivalent, backup)!
# The password is in cleartext.
# Once you have copied this file and edited it, perform:
#     sudo chown root:root <filename>
#     sudo chmod 700 <filename>
# Then you can add it to your /etc/crontab for regular execution.

BACKUPDIR='/var/backups/mysql'
BACKUPFILE='all_my_mysql_databases.sql'
USERNAME='root'  # MySQL username
PASSWORD='PPPPPP_REPLACE_ME'  # MySQL password

# Make directory unless it exists already:

mkdir -p $BACKUPDIR

# Dump the database:

mysqldump -u $USERNAME -p$PASSWORD --all-databases --force > $BACKUPDIR/$BACKUPFILE

# Make sure the backups (which may contain sensitive information) are only
# readable by the 'backup' user group:

cd $BACKUPDIR
chown -R backup:backup *
chmod -R o-rwx *
chmod -R ug+rw *

    """  # noqa


# =============================================================================
# Configuration class. (It gets cached on a per-process basis.)
# =============================================================================

class CamcopsConfig(object):
    """
    Class representing the config.
    """

    def __init__(self, config_filename: str) -> None:
        """Initialize from config file."""
        cp = ConfigParamMain

        # ---------------------------------------------------------------------
        # Open config file
        # ---------------------------------------------------------------------
        self.camcops_config_file = config_filename
        if not self.camcops_config_file:
            raise AssertionError("{} not specified".format(ENVVAR_CONFIG_FILE))
        log.info("Reading from {}", self.camcops_config_file)
        config = configparser.ConfigParser()
        with codecs.open(self.camcops_config_file, "r", "utf8") as file:
            config.read_file(file)

        # ---------------------------------------------------------------------
        # Read from the config file: 1. Most stuff, in alphabetical order
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION

        self.allow_insecure_cookies = get_config_parameter_boolean(
            config, section, cp.ALLOW_INSECURE_COOKIES, False)

        self.camcops_logo_file_absolute = get_config_parameter(
            config, section, cp.CAMCOPS_LOGO_FILE_ABSOLUTE, str,
            DEFAULT_CAMCOPS_LOGO_FILE)

        self.ctv_filename_spec = get_config_parameter(
            config, section, cp.CTV_FILENAME_SPEC, str, None)

        self.db_url = config.get(section, cp.DB_URL)
        # ... no default: will fail if not provided
        self.db_echo = get_config_parameter_boolean(
            config, section, cp.DB_ECHO, False)
        self.client_api_loglevel = get_config_parameter_loglevel(
            config, section, cp.CLIENT_API_LOGLEVEL, logging.INFO)
        logging.getLogger("camcops_server.cc_modules.client_api")\
            .setLevel(self.client_api_loglevel)
        # ... MUTABLE GLOBAL STATE (if relatively unimportant); *** fix

        self.disable_password_autocomplete = get_config_parameter_boolean(
            config, section, cp.DISABLE_PASSWORD_AUTOCOMPLETE, True)

        self.extra_string_files = get_config_parameter_multiline(
            config, section, cp.EXTRA_STRING_FILES, [])

        self.hl7_lockfile = get_config_parameter(
            config, section, cp.HL7_LOCKFILE, str, None)

        self.introspection = get_config_parameter_boolean(
            config, section, cp.INTROSPECTION, True)

        self.local_institution_url = get_config_parameter(
            config, section, cp.LOCAL_INSTITUTION_URL,
            str, DEFAULT_LOCAL_INSTITUTION_URL)
        self.local_logo_file_absolute = get_config_parameter(
            config, section, cp.LOCAL_LOGO_FILE_ABSOLUTE,
            str, DEFAULT_LOCAL_LOGO_FILE)
        self.lockout_threshold = get_config_parameter(
            config, section, cp.LOCKOUT_THRESHOLD,
            int, DEFAULT_LOCKOUT_THRESHOLD)
        self.lockout_duration_increment_minutes = get_config_parameter(
            config, section, cp.LOCKOUT_DURATION_INCREMENT_MINUTES,
            int, DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES)

        self.password_change_frequency_days = get_config_parameter(
            config, section, cp.PASSWORD_CHANGE_FREQUENCY_DAYS,
            int, DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS)
        self.patient_spec_if_anonymous = get_config_parameter(
            config, section, cp.PATIENT_SPEC_IF_ANONYMOUS, str, "anonymous")
        self.patient_spec = get_config_parameter(
            config, section, cp.PATIENT_SPEC, str, None)
        # currently not configurable, but easy to add in the future:
        self.plot_fontsize = DEFAULT_PLOT_FONTSIZE

        # self.send_analytics = get_config_parameter_boolean(
        #     config, section, "SEND_ANALYTICS", True)
        session_timeout_minutes = get_config_parameter(
            config, section, cp.SESSION_TIMEOUT_MINUTES,
            int, DEFAULT_TIMEOUT_MINUTES)
        self.session_cookie_secret = get_config_parameter(
            config, section, cp.SESSION_COOKIE_SECRET, str, None)
        self.session_timeout = datetime.timedelta(
            minutes=session_timeout_minutes)
        self.summary_tables_lockfile = get_config_parameter(
            config, section, cp.SUMMARY_TABLES_LOCKFILE, str, None)

        self.task_filename_spec = get_config_parameter(
            config, section, cp.TASK_FILENAME_SPEC, str, None)
        self.tracker_filename_spec = get_config_parameter(
            config, section, cp.TRACKER_FILENAME_SPEC, str, None)

        self.webview_loglevel = get_config_parameter_loglevel(
            config, section, cp.WEBVIEW_LOGLEVEL, logging.INFO)
        logging.getLogger().setLevel(self.webview_loglevel)  # root logger
        # ... MUTABLE GLOBAL STATE (if relatively unimportant) *** fix
        self.wkhtmltopdf_filename = get_config_parameter(
            config, section, cp.WKHTMLTOPDF_FILENAME, str, None)

        # ---------------------------------------------------------------------
        # Read from the config file: 2. HL7 section
        # ---------------------------------------------------------------------
        # http://stackoverflow.com/questions/335695/lists-in-configparser
        self.hl7_recipient_defs = []  # type: List[RecipientDefinition]
        try:
            hl7_items = config.items(CONFIG_FILE_RECIPIENTLIST_SECTION)
            for key, recipientdef_name in hl7_items:
                log.debug("HL7 config: key={}, recipientdef_name={}",
                          key, recipientdef_name)
                h = RecipientDefinition(config=config,
                                        section=recipientdef_name)
                self.hl7_recipient_defs.append(h)
        except configparser.NoSectionError:
            log.info("No config file section [{}]",
                     CONFIG_FILE_RECIPIENTLIST_SECTION)

        # ---------------------------------------------------------------------
        # Built from the preceding:
        # ---------------------------------------------------------------------

        self.introspection_files = []  # type: List[IntrospectionFileDetails]
        if self.introspection:
            # All introspection starts at INTROSPECTION_BASE_DIRECTORY
            rootdir = INTROSPECTION_BASE_DIRECTORY
            for dir_, subdirs, files in os.walk(rootdir):
                if dir_ == rootdir:
                    pretty_dir = ''
                else:
                    pretty_dir = os.path.relpath(dir_, rootdir)
                for filename in files:
                    basename, ext = os.path.splitext(filename)
                    if ext not in INTROSPECTABLE_EXTENSIONS:
                        continue
                    fullpath = os.path.join(dir_, filename)
                    prettypath = os.path.join(pretty_dir, filename)
                    self.introspection_files.append(
                        IntrospectionFileDetails(
                            fullpath=fullpath,
                            prettypath=prettypath,
                            ext=ext
                        )
                    )
            self.introspection_files = sorted(
                self.introspection_files,
                key=operator.attrgetter("prettypath"))

        # ---------------------------------------------------------------------
        # More validity checks
        # ---------------------------------------------------------------------
        if not self.patient_spec_if_anonymous:
            raise RuntimeError(
                "Blank PATIENT_SPEC_IF_ANONYMOUS in [server] "
                "section of config file")

        if not self.patient_spec:
            raise RuntimeError(
                "Missing/blank PATIENT_SPEC in [server] section"
                " of config file")

        if not self.session_cookie_secret:
            raise RuntimeError(
                "Invalid or missing SESSION_COOKIE_SECRET "
                "setting in [server] section of config file")

        if not self.task_filename_spec:
            raise RuntimeError("Missing/blank TASK_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.tracker_filename_spec:
            raise RuntimeError("Missing/blank TRACKER_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.ctv_filename_spec:
            raise RuntimeError("Missing/blank CTV_FILENAME_SPEC in "
                               "[server] section of config file")

        # ---------------------------------------------------------------------
        # Other attributes
        # ---------------------------------------------------------------------
        self._sqla_engine = None

    def get_sqla_engine(self) -> Engine:
        """
        I was previously misinterpreting the appropriate scope of an Engine.
        I thought: create one per request.
        But the Engine represents the connection *pool*.
        So if you create them all the time, you get e.g. a
        'Too many connections' error.

        "The appropriate scope is once per [database] URL per application,
        at the module level."

        https://groups.google.com/forum/#!topic/sqlalchemy/ZtCo2DsHhS4
        https://stackoverflow.com/questions/8645250/how-to-close-sqlalchemy-connection-in-mysql

        Now, our CamcopsConfig instance is cached, so there should be one of
        them overall. See get_config() below.

        Therefore, making the engine a member of this class should do the
        trick, whilst avoiding global variables.
        """
        if self._sqla_engine is None:
            self._sqla_engine = create_engine(
                self.db_url,
                echo=self.db_echo,
                pool_pre_ping=True,
                # pool_size=0,  # no limit (for parallel testing, which failed)
            )
            log.debug("Created SQLAlchemy engine for URL {}".format(
                get_safe_url_from_engine(self._sqla_engine)))
        return self._sqla_engine

    @property
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def get_all_table_names(self) -> List[str]:
        engine = self.get_sqla_engine()
        return get_table_names(engine=engine)

    @contextlib.contextmanager
    def get_dbsession_context(self) -> Generator[SqlASession, None, None]:
        engine = self.get_sqla_engine()
        maker = sessionmaker(bind=engine)
        dbsession = maker()  # type: SqlASession
        # noinspection PyBroadException
        try:
            yield dbsession
            dbsession.commit()
        except Exception:
            dbsession.rollback()
        finally:
            dbsession.close()

    def _assert_valid_database_engine(self) -> None:
        """
        Excluding invalid backend database types.

        Specifically, SQL Server versions before 2008 don't support timezones
        and we need that.
        """
        engine = self.get_sqla_engine()
        if not is_sqlserver(engine):
            return
        assert is_sqlserver_2008_or_later(engine), (
            "If you use Microsoft SQL Server as the back-end database for a "
            "CamCOPS server, it must be at least SQL Server 2008. Older "
            "versions do not have time zone awareness."
        )

    def _assert_database_is_at_head(self) -> None:
        current, head = get_current_and_head_revision(
            database_url=self.db_url,
            alembic_config_filename=ALEMBIC_CONFIG_FILENAME,
            alembic_base_dir=ALEMBIC_BASE_DIR,
            version_table=ALEMBIC_VERSION_TABLE,
        )
        if current == head:
            log.debug("Database is at correct (head) revision of {}", current)
        else:
            msg = (
                "Database structure is at version {} but should be at "
                "version {}. CamCOPS will not start. Please use the "
                "'upgrade_db' command to fix this.".format(current, head))
            log.critical(msg)
            raise RuntimeError(msg)

    def assert_database_ok(self) -> None:
        self._assert_valid_database_engine()
        self._assert_database_is_at_head()


# =============================================================================
# Get config filename from an appropriate environment (WSGI or OS)
# =============================================================================

def get_config_filename_from_os_env() -> str:
    # We do NOT trust the WSGI environment for this.
    config_filename = os.environ.get(ENVVAR_CONFIG_FILE)
    if not config_filename:
        raise AssertionError(
            "OS environment did not provide the required "
            "environment variable {}".format(ENVVAR_CONFIG_FILE))
    return config_filename


# =============================================================================
# Cached instances
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def get_config(config_filename: str) -> CamcopsConfig:
    return CamcopsConfig(config_filename)


# =============================================================================
# Get default config
# =============================================================================

def get_default_config_from_os_env() -> CamcopsConfig:
    return get_config(get_config_filename_from_os_env())


# =============================================================================
# NOTES
# =============================================================================

TO_BE_IMPLEMENTED_AS_COMMAND_LINE_SWITCH = """

# -----------------------------------------------------------------------------
# Export to a staging database for CRIS, CRATE, or similar anonymisation
# software (anonymisation staging database; ANONSTAG)
# -----------------------------------------------------------------------------

{cp.ANONSTAG_DB_URL} = {anonstag_db_url}
{cp.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE} = /tmp/camcops_cris_dd_draft.tsv

*** Note that we must check that the anonymisation staging database doesn't
    have the same URL as the main one (or "isn't the same one" in a more
    robust fashion)! Because this is so critical, probably best to:
    - require a completely different database name
    - ensure no table names overlap (e.g. add a prefix)

"""
