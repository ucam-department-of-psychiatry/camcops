#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

# There are CONDITIONAL AND IN-FUNCTION IMPORTS HERE; see below. This is to
# minimize the number of modules loaded when this is used in the context of the
# client-side database script, rather than the webview.

import codecs
import ConfigParser
import datetime
import logging

import pythonlib.rnc_db as rnc_db
import pythonlib.rnc_pdf as rnc_pdf

from cc_configfile import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_loglevel,
    get_config_parameter_multiline
)
from cc_constants import (
    CONFIG_FILE_MAIN_SECTION,
    DATEFORMAT,
    DEFAULT_DB_PORT,
    DEFAULT_DB_SERVER,
    NUMBER_OF_IDNUMS
)
import cc_dt
import cc_logger
import cc_version


# =============================================================================
# Constants
# =============================================================================

DEFAULT_DATABASE_TITLE = u"CamCOPS database"
DEFAULT_LOCAL_INSTITUTION_URL = "http://www.camcops.org/"
DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES = 10
DEFAULT_LOCKOUT_THRESHOLD = 10
DEFAULT_MYSQLDUMP = "/usr/bin/mysqldump"
DEFAULT_MYSQL = "/usr/bin/mysql"
DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS = 0  # zero for never
DEFAULT_RESOURCES_DIRECTORY = "/usr/share/camcops/server"
DEFAULT_TIMEOUT_MINUTES = 30
DEFAULT_PLOT_FONTSIZE = 8

# Defaults depending on those above
DEFAULT_INTROSPECTION_DIRECTORY = DEFAULT_RESOURCES_DIRECTORY

CAMCOPS_STRINGS_FILE = "strings.xml"
CAMCOPS_LOGO_FILE_WEBREF = "logo_camcops.png"
CAMCOPS_LOGO_FILE_PDFREF = "logo_camcops.svg"
LOCAL_LOGO_FILE_WEBREF = "logo_local.png"
LOCAL_LOGO_FILE_PDFREF = "logo_local.svg"

CONFIG_FILE_RECIPIENTLIST_SECTION = "recipients"

INTROSPECTABLE_EXTENSIONS = [".js", ".jsx", ".html", ".py", ".pl", ".xml"]
INTROSPECTABLE_DIRECTORIES = [
    "server",
    "server/cc_modules",
    "server/pythonlib",
    "server/tasks",
    "tablet",
    "tablet/common",
    "tablet/html",
    "tablet/lib",
    "tablet/menu",
    "tablet/menulib",
    "tablet/questionnaire",
    "tablet/questionnairelib",
    "tablet/screen",
    "tablet/table",
    "tablet/task",
    "tablet/task_html",
]


# =============================================================================
# Process-local storage class
# =============================================================================
# I think:
# Code that sits here is run once per *process*.
# The application object is called at least once per *thread*.
# ... but also more than once per thread.
# I've not grasped the method of creating proper thread-local storage
# and having it persist across multiple WSGI calls.
# So let's use process-local storage.

# class LocalStorage(threading.local):
class LocalStorage(object):
    """Process-local storage class. One instance per process. Persists across
    sessions thanks to mod_wsgi."""

    def __init__(self):
        """Initialize with blank values."""
        self.PERSISTENT_CONSTANTS_INITIALIZED = False

        self.NOW_LOCAL_TZ = None
        self.NOW_UTC_WITH_TZ = None
        self.NOW_UTC_NO_TZ = None
        self.NOW_LOCAL_TZ_ISO8601 = ""
        self.TODAY = None

        self.SCRIPT_NAME = ""
        self.SERVER_NAME = ""
        self.CAMCOPS_CONFIG_FILE = ""
        self.SCRIPT_PUBLIC_URL_ESCAPED = ""

        self.DB_NAME = ""
        self.DB_USER = ""
        self.DB_SERVER = DEFAULT_DB_SERVER
        self.DB_PORT = DEFAULT_DB_PORT
        self.MYSQL = DEFAULT_MYSQL
        self.MYSQLDUMP = DEFAULT_MYSQLDUMP

        self.DATABASE_TITLE = ""
        self.IDDESC = [None] * NUMBER_OF_IDNUMS
        self.IDSHORTDESC = [None] * NUMBER_OF_IDNUMS
        self.ID_POLICY_UPLOAD_STRING = ""
        self.ID_POLICY_FINALIZE_STRING = ""

        self.LOCAL_INSTITUTION_URL = DEFAULT_LOCAL_INSTITUTION_URL
        self.RESOURCES_DIRECTORY = DEFAULT_RESOURCES_DIRECTORY
        self.LOCAL_LOGO_FILE_ABSOLUTE = ""
        self.INTROSPECTION_DIRECTORY = DEFAULT_INTROSPECTION_DIRECTORY
        self.INTROSPECTION = False
        self.HL7_LOCKFILE = None
        self.SUMMARY_TABLES_LOCKFILE = None
        self.WKHTMLTOPDF_FILENAME = None
        self.EXTRA_STRING_FILES = None

        self.SESSION_TIMEOUT = datetime.timedelta(
            minutes=DEFAULT_TIMEOUT_MINUTES)
        self.PASSWORD_CHANGE_FREQUENCY_DAYS = None
        self.LOCKOUT_THRESHOLD = DEFAULT_LOCKOUT_THRESHOLD
        self.LOCKOUT_DURATION_INCREMENT_MINUTES = (
            DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES
        )
        self.DISABLE_PASSWORD_AUTOCOMPLETE = False

        self.PATIENT_SPEC_IF_ANONYMOUS = ""
        self.PATIENT_SPEC = ""
        self.TASK_FILENAME_SPEC = ""
        self.TRACKER_FILENAME_SPEC = ""
        self.CTV_FILENAME_SPEC = ""

        self.WEBVIEW_LOGLEVEL = logging.INFO
        self.DBENGINE_LOGLEVEL = logging.INFO
        self.DBCLIENT_LOGLEVEL = logging.INFO

        self.SEND_ANALYTICS = True

        self.HL7_RECIPIENT_DEFS = []

        self.INTROSPECTION_FILES = []

        self.CAMCOPS_STRINGS_FILE_ABSOLUTE = None
        self.CAMCOPS_LOGO_FILE_ABSOLUTE = None

        self.WEB_LOGO = None
        self.WEBSTART = None
        self.PDF_LOGO_LINE = None

        self.ALLOW_MOBILEWEB = False

        self.db = None

        self.stringDict = None
        self.extraStringDicts = None  # dictionary of dictionaries
        self.useSVG = False
        self.session = None
        # currently not configurable, but easy to add in the future:
        self.PLOT_FONTSIZE = DEFAULT_PLOT_FONTSIZE

        self.remote_addr = None
        self.remote_port = None

    def get_id_desc(self, n):
        """Get server's ID description.

        Args:
            n: from 1 to NUMBER_OF_IDNUMS
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return self.IDDESC[n - 1]

    def get_id_shortdesc(self, n):
        """Get server's short ID description.

        Args:
            n: from 1 to NUMBER_OF_IDNUMS
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return self.IDSHORTDESC[n - 1]

    def switch_output_to_png(self):
        """Switch server to producing figures in PNG."""
        self.useSVG = False

    def switch_output_to_svg(self):
        """Switch server to producing figures in SVG."""
        self.useSVG = True

    def set_always(self):
        """Set the things we set every time the script is invoked (time!)."""
        self.NOW_LOCAL_TZ = cc_dt.get_now_localtz()
        # ... we want nearly all our times offset-aware
        # ... http://stackoverflow.com/questions/4530069
        self.NOW_UTC_WITH_TZ = cc_dt.convert_datetime_to_utc(self.NOW_LOCAL_TZ)
        self.NOW_UTC_NO_TZ = cc_dt.convert_datetime_to_utc_notz(
            self.NOW_LOCAL_TZ)
        self.NOW_LOCAL_TZ_ISO8601 = cc_dt.format_datetime(self.NOW_LOCAL_TZ,
                                                          DATEFORMAT.ISO8601)
        self.TODAY = datetime.date.today()  # fetches the local date

    def set_common(self, environ, config, as_client_db):
        # logger = cc_logger.dblogger if as_client_db else cc_logger.logger
        # ---------------------------------------------------------------------
        # Read from the config file:
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION

        SESSION_TIMEOUT_MINUTES = get_config_parameter(
            config, section, "SESSION_TIMEOUT_MINUTES",
            int, DEFAULT_TIMEOUT_MINUTES)
        self.SESSION_TIMEOUT = datetime.timedelta(
            minutes=SESSION_TIMEOUT_MINUTES)

        self.EXTRA_STRING_FILES = get_config_parameter_multiline(
            config, section, "EXTRA_STRING_FILES", [])

        self.DB_NAME = config.get(section, "DB_NAME")
        # ... no default: will fail if not provided
        self.DB_USER = config.get(section, "DB_USER")
        # ... no default: will fail if not provided
        # DB_PASSWORD: handled later, for security reasons (see below)
        self.DB_SERVER = get_config_parameter(
            config, section, "DB_SERVER", str, DEFAULT_DB_SERVER)
        self.DB_PORT = get_config_parameter(
            config, section, "DB_PORT", int, DEFAULT_DB_PORT)

        self.DATABASE_TITLE = get_config_parameter(
            config, section, "DATABASE_TITLE", unicode, DEFAULT_DATABASE_TITLE)
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            i = n - 1
            nstr = str(n)
            self.IDDESC[i] = get_config_parameter(
                config, section, "IDDESC_" + nstr, unicode, u"")
            self.IDSHORTDESC[i] = get_config_parameter(
                config, section, "IDSHORTDESC_" + nstr, unicode, u"")
        self.ID_POLICY_UPLOAD_STRING = get_config_parameter(
            config, section, "UPLOAD_POLICY", str, "")
        self.ID_POLICY_FINALIZE_STRING = get_config_parameter(
            config, section, "FINALIZE_POLICY", str, "")

        self.DBENGINE_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "DBENGINE_LOGLEVEL", logging.INFO)
        rnc_db.set_loglevel(self.DBENGINE_LOGLEVEL)

        self.WKHTMLTOPDF_FILENAME = get_config_parameter(
            config, section, "WKHTMLTOPDF_FILENAME", str, None)
        rnc_pdf.set_processor(cc_version.PDF_ENGINE,
                              wkhtmltopdf_filename=self.WKHTMLTOPDF_FILENAME)

        # ---------------------------------------------------------------------
        # SECURITY: in this section (reading the database password from the
        # config file and connecting to the database), consider the possibility
        # of a password leaking via a debugging exception handler. This
        # includes the possibility that the database code will raise an
        # exception that reveals the password, so we must replace all
        # exceptions with our own, bland one. In addition, we must obscure the
        # variable that actually contains the password, in all circumstances.
        # ---------------------------------------------------------------------
        try:
            db_password = config.get(section, "DB_PASSWORD")
        except:  # deliberately conceal details for security
            db_password = None
            raise RuntimeError("Problem reading DB_PASSWORD from config")

        if db_password is None:
            raise RuntimeError("No database password specified")
            # OK from a security perspective: if there's no password, there's
            # no password to leak via a debugging exception handler

        # Now connect to the database:
        try:
            self.db = rnc_db.DatabaseSupporter()
            # To generate a password-leak situation, e.g. mis-spell "password"
            # in the call below. If the exception is not caught,
            # wsgi_errorreporter.py will announce the password.
            # So we catch it!
            self.db.connect_to_database_mysql(
                server=self.DB_SERVER,
                port=self.DB_PORT,
                database=self.DB_NAME,
                user=self.DB_USER,
                password=db_password,
                autocommit=False  # NB therefore need to commit
                # ... done in camcops.py at the end of a session
            )
        except:  # deliberately conceal details for security
            raise rnc_db.NoDatabaseError(
                "Problem opening or reading from database; details concealed "
                "for security reasons")
        finally:
            # Executed whether an exception is raised or not.
            db_password = None
        # ---------------------------------------------------------------------
        # Password is now re-obscured in all situations. Onwards...
        # ---------------------------------------------------------------------

    def set_webview(self, environ, config):
        # ---------------------------------------------------------------------
        # Delayed imports
        # ---------------------------------------------------------------------
        import cgi
        import operator
        import os
        import urllib

        import cc_filename
        import cc_html  # caution, circular import
        import cc_policy
        import cc_namedtuples
        import cc_recipdef
        import cc_version

        logger = cc_logger.logger

        # ---------------------------------------------------------------------
        # Read from the environment
        # ---------------------------------------------------------------------
        # http://www.zytrax.com/tech/web/env_var.htm
        # Apache standard CGI variables:
        self.SCRIPT_NAME = environ.get("SCRIPT_NAME", "")
        self.SERVER_NAME = environ.get("SERVER_NAME")

        # Reconstruct URL:
        # http://www.python.org/dev/peps/pep-0333/#url-reconstruction
        url = environ.get("wsgi.url_scheme", "") + "://"
        if environ.get("HTTP_HOST"):
            url += environ.get("HTTP_HOST")
        else:
            url += environ.get("SERVER_NAME", "")
        if environ.get("wsgi.url_scheme") == "https":
            if environ.get("SERVER_PORT") != "443":
                url += ':' + environ.get("SERVER_PORT", "")
        else:
            if environ.get("SERVER_PORT") != "80":
                url += ':' + environ.get("SERVER_PORT", "")
        url += urllib.quote(environ.get("SCRIPT_NAME", ""))
        url += urllib.quote(environ.get("PATH_INFO", ""))
        # But not the query string:
        # if environ.get("QUERY_STRING"):
        #    url += "?" + environ.get("QUERY_STRING")

        self.SCRIPT_PUBLIC_URL_ESCAPED = cgi.escape(url)

        # ---------------------------------------------------------------------
        # Read from the config file:
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION
        self.MYSQL = get_config_parameter(
            config, section, "MYSQL", str, DEFAULT_MYSQL)
        self.MYSQLDUMP = get_config_parameter(
            config, section, "MYSQLDUMP", str, DEFAULT_MYSQLDUMP)

        self.LOCAL_INSTITUTION_URL = get_config_parameter(
            config, section, "LOCAL_INSTITUTION_URL",
            str, DEFAULT_LOCAL_INSTITUTION_URL)
        # note order dependency: RESOURCES_DIRECTORY, LOCAL_LOGO_FILE_ABSOLUTE
        self.RESOURCES_DIRECTORY = get_config_parameter(
            config, section, "RESOURCES_DIRECTORY",
            str, DEFAULT_RESOURCES_DIRECTORY)
        self.LOCAL_LOGO_FILE_ABSOLUTE = get_config_parameter(
            config, section, "LOCAL_LOGO_FILE_ABSOLUTE",
            str, os.path.join(self.RESOURCES_DIRECTORY,
                              LOCAL_LOGO_FILE_PDFREF))
        self.INTROSPECTION_DIRECTORY = get_config_parameter(
            config, section, "INTROSPECTION_DIRECTORY",
            str, DEFAULT_INTROSPECTION_DIRECTORY)
        self.INTROSPECTION = get_config_parameter_boolean(
            config, section, "INTROSPECTION", True)
        self.HL7_LOCKFILE = get_config_parameter(
            config, section, "HL7_LOCKFILE", str, None)
        self.SUMMARY_TABLES_LOCKFILE = get_config_parameter(
            config, section, "SUMMARY_TABLES_LOCKFILE", str, None)

        self.PASSWORD_CHANGE_FREQUENCY_DAYS = get_config_parameter(
            config, section, "PASSWORD_CHANGE_FREQUENCY_DAYS",
            int, DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS)
        self.LOCKOUT_THRESHOLD = get_config_parameter(
            config, section, "LOCKOUT_THRESHOLD",
            int, DEFAULT_LOCKOUT_THRESHOLD)
        self.LOCKOUT_DURATION_INCREMENT_MINUTES = get_config_parameter(
            config, section, "LOCKOUT_DURATION_INCREMENT_MINUTES",
            int, DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES)
        self.DISABLE_PASSWORD_AUTOCOMPLETE = get_config_parameter_boolean(
            config, section, "DISABLE_PASSWORD_AUTOCOMPLETE", True)

        self.PATIENT_SPEC_IF_ANONYMOUS = get_config_parameter(
            config, section, "PATIENT_SPEC_IF_ANONYMOUS", str, "anonymous")
        self.PATIENT_SPEC = get_config_parameter(
            config, section, "PATIENT_SPEC", str, None)
        self.TASK_FILENAME_SPEC = get_config_parameter(
            config, section, "TASK_FILENAME_SPEC", str, None)
        self.TRACKER_FILENAME_SPEC = get_config_parameter(
            config, section, "TRACKER_FILENAME_SPEC", str, None)
        self.CTV_FILENAME_SPEC = get_config_parameter(
            config, section, "CTV_FILENAME_SPEC", str, None)

        self.WEBVIEW_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "WEBVIEW_LOGLEVEL", logging.INFO)
        logger.setLevel(self.WEBVIEW_LOGLEVEL)

        self.SEND_ANALYTICS = get_config_parameter_boolean(
            config, section, "SEND_ANALYTICS", True)

        self.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE = get_config_parameter(
            config, section, "EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE", str, None)

        # http://stackoverflow.com/questions/335695/lists-in-configparser
        try:
            hl7_items = config.items(CONFIG_FILE_RECIPIENTLIST_SECTION)
            for key, recipientdef_name in hl7_items:
                logger.debug(u"HL7 config: key={}, recipientdef_name="
                             "{}".format(key, recipientdef_name))
                h = cc_recipdef.RecipientDefinition(config, recipientdef_name)
                if h.valid:
                    self.HL7_RECIPIENT_DEFS.append(h)
        except ConfigParser.NoSectionError:
            logger.info("No config file section [{}]".format(
                CONFIG_FILE_RECIPIENTLIST_SECTION
            ))

        # ---------------------------------------------------------------------
        # Built from the preceding:
        # ---------------------------------------------------------------------

        self.INTROSPECTION_FILES = []
        if self.INTROSPECTION:
            rootdir = self.INTROSPECTION_DIRECTORY
            for d in INTROSPECTABLE_DIRECTORIES:
                searchdir = os.sep.join([rootdir, d]) if d else rootdir
                for fname in os.listdir(searchdir):
                    junk, ext = os.path.splitext(fname)
                    if ext not in INTROSPECTABLE_EXTENSIONS:
                        continue
                    fullpath = os.sep.join([searchdir, fname])
                    prettypath = os.sep.join([d, fname]) if d else fname
                    self.INTROSPECTION_FILES.append(
                        cc_namedtuples.IntrospectionFileDetails(
                            fullpath=fullpath,
                            prettypath=prettypath,
                            searchterm=fname,
                            ext=ext
                        )
                    )
            self.INTROSPECTION_FILES = sorted(self.INTROSPECTION_FILES,
                                              key=operator.attrgetter(
                                                  "prettypath"))

        # Cache tokenized ID policies
        cc_policy.tokenize_upload_id_policy(self.ID_POLICY_UPLOAD_STRING)
        cc_policy.tokenize_finalize_id_policy(self.ID_POLICY_FINALIZE_STRING)
        # Valid?
        if not cc_policy.upload_id_policy_valid():
            raise RuntimeError("UPLOAD_POLICY invalid in config")
        if not cc_policy.finalize_id_policy_valid():
            raise RuntimeError("FINALIZE_POLICY invalid in config")

        if self.RESOURCES_DIRECTORY is not None:
            self.CAMCOPS_STRINGS_FILE_ABSOLUTE = os.path.join(
                self.RESOURCES_DIRECTORY, CAMCOPS_STRINGS_FILE)
            self.CAMCOPS_LOGO_FILE_ABSOLUTE = os.path.join(
                self.RESOURCES_DIRECTORY, CAMCOPS_LOGO_FILE_PDFREF)

        # Note: HTML4 uses <img ...>; XHTML uses <img ... />;
        # HTML5 is happy with <img ... />

        # IE float-right problems: http://stackoverflow.com/questions/1820007
        # Tables are a nightmare in IE (table max-width not working unless you
        # also specify it for image size, etc.)
        self.WEB_LOGO = u"""
            <div class="web_logo_header">
                <a href="{}"><img class="logo_left" src="{}" alt="" /></a>
                <a href="{}"><img class="logo_right" src="{}" alt="" /></a>
            </div>
        """.format(
            self.SCRIPT_NAME, CAMCOPS_LOGO_FILE_WEBREF,
            self.LOCAL_INSTITUTION_URL, LOCAL_LOGO_FILE_WEBREF
        )

        self.WEBSTART = cc_html.WEB_HEAD + self.WEB_LOGO

        if cc_version.PDF_ENGINE in ["weasyprint", "pdfkit"]:
            # weasyprint: div with floating img does not work properly
            self.PDF_LOGO_LINE = u"""
                <div class="pdf_logo_header">
                    <table>
                        <tr>
                            <td class="image_td">
                                <img class="logo_left" src="file://{}" />
                            </td>
                            <td class="centregap_td"></td>
                            <td class="image_td">
                                <img class="logo_right" src="file://{}" />
                            </td>
                        </tr>
                    </table>
                </div>
            """.format(
                self.CAMCOPS_LOGO_FILE_ABSOLUTE,
                self.LOCAL_LOGO_FILE_ABSOLUTE,
            )
        elif cc_version.PDF_ENGINE in ["pdfkit"]:
            self.PDF_LOGO_LINE = u"""
                <div class="pdf_logo_header">
                    <table>
                        <tr>
                            <td class="image_td">
                                <img class="logo_left" src="file://{}" />
                            </td>
                            <td class="centregap_td"></td>
                            <td class="image_td">
                                <img class="logo_right" src="file://{}" />
                            </td>
                        </tr>
                    </table>
                </div>
            """.format(
                self.CAMCOPS_LOGO_FILE_ABSOLUTE,
                self.LOCAL_LOGO_FILE_ABSOLUTE,
            )
            #self.PDF_LOGO_LINE = u"""
            #    <div class="pdf_logo_header">
            #        <img class="logo_left" src="file://{}" />
            #        <img class="logo_right" src="file://{}" />
            #    </div>
            #""".format(
            #    self.CAMCOPS_LOGO_FILE_ABSOLUTE,
            #    self.LOCAL_LOGO_FILE_ABSOLUTE,
            #)
        elif cc_version.PDF_ENGINE in ["xhtml2pdf"]:
            # xhtml2pdf
            # hard to get logos positioned any other way than within a table
            self.PDF_LOGO_LINE = u"""
                <div class="header">
                    <table class="noborder">
                        <tr class="noborder">
                            <td class="noborderphoto" width="45%">
                                <img src="file://{}" height="{}"
                                        align="left" />
                            </td>
                            <td class="noborderphoto" width="10%"></td>
                            <td class="noborderphoto" width="45%">
                                <img src="file://{}" height="{}"
                                        align="right" />
                            </td>
                        </tr>
                    </table>
                </div>
            """.format(
                self.CAMCOPS_LOGO_FILE_ABSOLUTE, cc_html.PDF_LOGO_HEIGHT,
                self.LOCAL_LOGO_FILE_ABSOLUTE, cc_html.PDF_LOGO_HEIGHT
            )
        else:
            raise AssertionError("Invalid PDF engine")

        if not self.PATIENT_SPEC_IF_ANONYMOUS:
            raise RuntimeError("Blank PATIENT_SPEC_IF_ANONYMOUS in [server] "
                               "section of config file")

        if not self.PATIENT_SPEC:
            raise RuntimeError("Missing/blank PATIENT_SPEC in [server] section"
                               " of config file")
        if not cc_filename.patient_spec_for_filename_is_valid(
                self.PATIENT_SPEC):
            raise RuntimeError("Invalid PATIENT_SPEC in [server] section of "
                               "config file")

        if not self.TASK_FILENAME_SPEC:
            raise RuntimeError("Missing/blank TASK_FILENAME_SPEC in "
                               "[server] section of config file")
        if not cc_filename.filename_spec_is_valid(self.TASK_FILENAME_SPEC):
            raise RuntimeError("Invalid TASK_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.TRACKER_FILENAME_SPEC:
            raise RuntimeError("Missing/blank TRACKER_FILENAME_SPEC in "
                               "[server] section of config file")
        if not cc_filename.filename_spec_is_valid(self.TRACKER_FILENAME_SPEC):
            raise RuntimeError("Invalid TRACKER_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.CTV_FILENAME_SPEC:
            raise RuntimeError("Missing/blank CTV_FILENAME_SPEC in "
                               "[server] section of config file")
        if not cc_filename.filename_spec_is_valid(self.CTV_FILENAME_SPEC):
            raise RuntimeError("Invalid CTV_FILENAME_SPEC in "
                               "[server] section of config file")

    def set_dbclient(self, environ, config):
        logger = cc_logger.dblogger

        # ---------------------------------------------------------------------
        # Read from the environment
        # ---------------------------------------------------------------------
        self.remote_addr = environ.get("REMOTE_ADDR")
        self.remote_port = environ.get("REMOTE_PORT")

        # ---------------------------------------------------------------------
        # Read from the config file:
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION
        self.ALLOW_MOBILEWEB = get_config_parameter_boolean(
            config, section, "ALLOW_MOBILEWEB", False)
        self.DBCLIENT_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "DBCLIENT_LOGLEVEL", logging.INFO)
        logger.setLevel(self.DBCLIENT_LOGLEVEL)

        # ---------------------------------------------------------------------
        # Read from the database
        # ---------------------------------------------------------------------
        self.VALID_TABLE_NAMES = self.db.get_all_table_names()

    def set(self, environ, as_client_db=False):
        """Set all variables from environment and thus config file."""

        self.set_always()

        if self.PERSISTENT_CONSTANTS_INITIALIZED:
            return

        logger = cc_logger.dblogger if as_client_db else cc_logger.logger
        logger.debug("Setting persistent constants")

        self.CAMCOPS_CONFIG_FILE = environ.get("CAMCOPS_CONFIG_FILE")
        config = ConfigParser.ConfigParser()
        config.readfp(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))

        self.set_common(environ, config, as_client_db)
        if as_client_db:
            self.set_dbclient(environ, config)
        else:
            self.set_webview(environ, config)

        # Now we can keep that state:
        self.PERSISTENT_CONSTANTS_INITIALIZED = True

    def set_from_environ_and_ping_db(self, environ, as_client_db=False):
        """Set up process-local storage from the incoming environment (which
        may be very fast if already cached) and ensure we have an active
        database connection."""

        # 1. Set up process-local storage
        self.set(environ, as_client_db)
        # ... will do almost nothing if its
        #     PERSISTENT_CONSTANTS_INITIALIZED flag is set
        # ... so we also have to:

        # 2. Ping MySQL connection, to reconnect if it's timed out.
        # This should fix:
        #   Problem: "MySQL server has gone away"
        #   mysqld --verbose --help | grep wait-timeout
        #   ... 28,800 seconds = 480 minutes = 8 hours
        #   http://stackoverflow.com/questions/2582506
        self.db.ping()

    def get_anonymisation_database(self):
        """Open the anonymisation staging database. That is not performance-
        critical and the connection does not need to be cached. Will raise
        an exception upon a connection error."""
        # Follows same security principles as above.
        config = ConfigParser.ConfigParser()
        config.readfp(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))
        section = CONFIG_FILE_MAIN_SECTION

        server = get_config_parameter(
            config, section, "ANONSTAG_DB_SERVER", str, DEFAULT_DB_SERVER)
        port = get_config_parameter(
            config, section, "ANONSTAG_DB_PORT", int, DEFAULT_DB_PORT)
        database = get_config_parameter(
            config, section, "ANONSTAG_DB_NAME", str, None)
        if database is None:
            raise RuntimeError("ANONSTAG_DB_NAME not specified in config")
        user = get_config_parameter(
            config, section, "ANONSTAG_DB_USER", str, None)
        if user is None:
            raise RuntimeError("ANONSTAG_DB_USER not specified in config")
        # It is a potential disaster if the anonymisation database is the same
        # database as the main database - risk of destroying original data.
        # We mitigate this risk in two ways.
        # (1) We check here. Since different server/port combinations could
        #     resolve to the same host, we take the extremely conservative
        #     approach of requiring a different database name.
        if database == self.DB_NAME:
            raise RuntimeError("ANONSTAG_DB_NAME must be different from "
                               "DB_NAME")
        # (2) We prefix all tablenames in the CRIS staging database;
        #     see cc_task.
        try:
            password = get_config_parameter(
                config, section, "ANONSTAG_DB_PASSWORD", str, None)
        except:  # deliberately conceal details for security
            password = None
            raise RuntimeError("Problem reading ANONSTAG_DB_PASSWORD from "
                               "config")
        if password is None:
            raise RuntimeError("ANONSTAG_DB_PASSWORD not specified in config")
        try:
            db = rnc_db.DatabaseSupporter()
            db.connect_to_database_mysql(
                server=server,
                port=port,
                database=database,
                user=user,
                password=password,
                autocommit=False  # NB therefore need to commit
                # ... done in camcops.py at the end of a session
            )
        except:  # deliberately conceal details for security
            raise rnc_db.NoDatabaseError(
                "Problem opening or reading from database; details concealed "
                "for security reasons")
        finally:
            # Executed whether an exception is raised or not.
            password = None
        # ---------------------------------------------------------------------
        # Password is now re-obscured in all situations. Onwards...
        # ---------------------------------------------------------------------
        return db

# =============================================================================
# Process-specific instance
# =============================================================================

pls = LocalStorage()
