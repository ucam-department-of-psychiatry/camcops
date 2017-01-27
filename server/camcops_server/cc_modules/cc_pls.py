#!/usr/bin/env python
# cc_pls.py

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

# There are CONDITIONAL AND IN-FUNCTION IMPORTS HERE; see below. This is to
# minimize the number of modules loaded when this is used in the context of the
# client-side database script, rather than the webview.

import codecs
import configparser
import datetime
from html import escape
import operator
import os
import urllib.error
import urllib.parse
import urllib.request
import logging
from typing import Dict, Optional

import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_pdf as rnc_pdf

from .cc_baseconstants import (
    CAMCOPS_SERVER_DIRECTORY,
    INTROSPECTABLE_EXTENSIONS,
)
from .cc_configfile import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_loglevel,
    get_config_parameter_multiline
)
from .cc_constants import (
    CAMCOPS_LOGO_FILE_WEBREF,
    CONFIG_FILE_MAIN_SECTION,
    CONFIG_FILE_RECIPIENTLIST_SECTION,
    DATEFORMAT,
    DEFAULT_CAMCOPS_LOGO_FILE,
    DEFAULT_DATABASE_TITLE,
    DEFAULT_DB_PORT,
    DEFAULT_DB_SERVER,
    # DEFAULT_EXTRA_STRING_SPEC,
    DEFAULT_LOCAL_INSTITUTION_URL,
    DEFAULT_LOCAL_LOGO_FILE,
    DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES,
    DEFAULT_LOCKOUT_THRESHOLD,
    DEFAULT_MYSQL,
    DEFAULT_MYSQLDUMP,
    DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS,
    DEFAULT_PLOT_FONTSIZE,
    DEFAULT_STRING_FILE,
    DEFAULT_TIMEOUT_MINUTES,
    INTROSPECTION_BASE_DIRECTORY,
    LOCAL_LOGO_FILE_WEBREF,
    NUMBER_OF_IDNUMS,
    PDF_ENGINE,
    PDF_LOGO_HEIGHT,
    URL_RELATIVE_WEBVIEW,
    WEB_HEAD,
)
from . import cc_dt
from . import cc_filename
from .cc_logger import dblog, log
from . import cc_namedtuples
from . import cc_policy
from . import cc_recipdef


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

    def __init__(self) -> None:
        """Initialize with blank values."""
        self.ALLOW_INSECURE_COOKIES = False
        self.ALLOW_MOBILEWEB = False
        self.CAMCOPS_CONFIG_FILE = ""
        self.CAMCOPS_LOGO_FILE_ABSOLUTE = None
        self.CTV_FILENAME_SPEC = ""
        self.DATABASE_TITLE = ""
        self.DBCLIENT_LOGLEVEL = logging.INFO
        self.DBENGINE_LOGLEVEL = logging.INFO
        self.DB_NAME = ""
        self.db = None
        self.DB_PORT = DEFAULT_DB_PORT
        self.DB_SERVER = DEFAULT_DB_SERVER
        self.DB_USER = ""
        self.DISABLE_PASSWORD_AUTOCOMPLETE = False
        self.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE = None
        self.extraStringDicts = None  # dictionary of dictionaries
        self.EXTRA_STRING_FILES = None
        self.HL7_LOCKFILE = None
        self.HL7_RECIPIENT_DEFS = []
        self.IDDESC = [None] * NUMBER_OF_IDNUMS
        self.ID_POLICY_FINALIZE_STRING = ""
        self.ID_POLICY_UPLOAD_STRING = ""
        self.IDSHORTDESC = [None] * NUMBER_OF_IDNUMS
        self.INTROSPECTION = False
        self.INTROSPECTION_FILES = []
        self.LOCAL_INSTITUTION_URL = DEFAULT_LOCAL_INSTITUTION_URL
        self.LOCAL_LOGO_FILE_ABSOLUTE = ""
        self.LOCKOUT_DURATION_INCREMENT_MINUTES = (
            DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES
        )
        self.LOCKOUT_THRESHOLD = DEFAULT_LOCKOUT_THRESHOLD
        self.MAIN_STRING_FILE = DEFAULT_STRING_FILE
        self.MYSQL = DEFAULT_MYSQL
        self.MYSQLDUMP = DEFAULT_MYSQLDUMP
        self.NOW_LOCAL_TZ_ISO8601 = ""
        self.NOW_LOCAL_TZ = None
        self.NOW_UTC_NO_TZ = None
        self.NOW_UTC_WITH_TZ = None
        self.PASSWORD_CHANGE_FREQUENCY_DAYS = None
        self.PATIENT_SPEC = ""
        self.PATIENT_SPEC_IF_ANONYMOUS = ""
        self.PDF_LOGO_LINE = None
        self.PERSISTENT_CONSTANTS_INITIALIZED = False
        # currently not configurable, but easy to add in the future:
        self.PLOT_FONTSIZE = DEFAULT_PLOT_FONTSIZE
        self.remote_addr = None
        self.remote_port = None
        self.SCRIPT_NAME = ""
        self.SCRIPT_PUBLIC_URL_ESCAPED = ""
        self.SEND_ANALYTICS = True
        self.SERVER_NAME = ""
        self.session = None
        self.SESSION_TIMEOUT = datetime.timedelta(
            minutes=DEFAULT_TIMEOUT_MINUTES)
        self.stringDict = None
        self.SUMMARY_TABLES_LOCKFILE = None
        self.TASK_FILENAME_SPEC = ""
        self.TODAY = None
        self.TRACKER_FILENAME_SPEC = ""
        self.useSVG = False
        self.VALID_TABLE_NAMES = []
        self.WEB_LOGO = None
        self.WEBSTART = None
        self.WEBVIEW_LOGLEVEL = logging.INFO
        self.WKHTMLTOPDF_FILENAME = None

    def get_id_desc(self, n: int) -> Optional[str]:
        """Get server's ID description.

        Args:
            n: from 1 to NUMBER_OF_IDNUMS
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return self.IDDESC[n - 1]

    def get_id_shortdesc(self, n: int) -> Optional[str]:
        """Get server's short ID description.

        Args:
            n: from 1 to NUMBER_OF_IDNUMS
        """
        if n < 1 or n > NUMBER_OF_IDNUMS:
            return None
        return self.IDSHORTDESC[n - 1]

    def switch_output_to_png(self) -> None:
        """Switch server to producing figures in PNG."""
        self.useSVG = False

    def switch_output_to_svg(self) -> None:
        """Switch server to producing figures in SVG."""
        self.useSVG = True

    def set_always(self, environ: Dict) -> None:
        """Set the things we set every time the script is invoked (time!)."""

        # ---------------------------------------------------------------------
        # Date/time
        # ---------------------------------------------------------------------
        self.NOW_LOCAL_TZ = cc_dt.get_now_localtz()
        # ... we want nearly all our times offset-aware
        # ... http://stackoverflow.com/questions/4530069
        self.NOW_UTC_WITH_TZ = cc_dt.convert_datetime_to_utc(self.NOW_LOCAL_TZ)
        self.NOW_UTC_NO_TZ = cc_dt.convert_datetime_to_utc_notz(
            self.NOW_LOCAL_TZ)
        self.NOW_LOCAL_TZ_ISO8601 = cc_dt.format_datetime(self.NOW_LOCAL_TZ,
                                                          DATEFORMAT.ISO8601)
        self.TODAY = datetime.date.today()  # fetches the local date

        # ---------------------------------------------------------------------
        # Read from the WSGI environment
        # ---------------------------------------------------------------------
        self.remote_addr = environ.get("REMOTE_ADDR")
        self.remote_port = environ.get("REMOTE_PORT")

        # http://www.zytrax.com/tech/web/env_var.htm
        # Apache standard CGI variables:
        # self.SCRIPT_NAME = environ.get("SCRIPT_NAME", "")
        self.SCRIPT_NAME = URL_RELATIVE_WEBVIEW
        self.SERVER_NAME = environ.get("SERVER_NAME")

        # Reconstruct URL:
        # http://www.python.org/dev/peps/pep-0333/#url-reconstruction
        protocol = environ.get("wsgi.url_scheme", "")
        if environ.get("HTTP_HOST"):
            host = environ.get("HTTP_HOST")
        else:
            host = environ.get("SERVER_NAME", "")
        port = ""
        server_port = environ.get("SERVER_PORT")
        if (server_port and
                ":" not in host and
                not(protocol == "https" and server_port == "443") and
                not(protocol == "http" and server_port == "80")):
            port = ":" + server_port
        script = urllib.parse.quote(environ.get("SCRIPT_NAME", ""))
        path = urllib.parse.quote(environ.get("PATH_INFO", ""))

        # But not the query string:
        # if environ.get("QUERY_STRING"):
        #    query += "?" + environ.get("QUERY_STRING")
        # else:
        #    query = ""

        url = "{protocol}://{host}{port}{script}{path}".format(
            protocol=protocol,
            host=host,
            port=port,
            script=script,
            path=path,
        )

        self.SCRIPT_PUBLIC_URL_ESCAPED = escape(url)

    def set(self, environ: Dict) -> None:
        """Set all variables from environment and thus config file."""

        self.set_always(environ)

        if self.PERSISTENT_CONSTANTS_INITIALIZED:
            return

        # ---------------------------------------------------------------------
        # Open config file
        # ---------------------------------------------------------------------
        self.CAMCOPS_CONFIG_FILE = environ.get("CAMCOPS_CONFIG_FILE")
        if not self.CAMCOPS_CONFIG_FILE:
            # fallback to OS environment
            self.CAMCOPS_CONFIG_FILE = os.environ.get("CAMCOPS_CONFIG_FILE")
        if not self.CAMCOPS_CONFIG_FILE:
            raise AssertionError("CAMCOPS_CONFIG_FILE not specified")
        log.info("Reading from {}".format(self.CAMCOPS_CONFIG_FILE))
        config = configparser.ConfigParser()
        config.read_file(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))

        # ---------------------------------------------------------------------
        # Read from the config file: 1. Most stuff, in alphabetical order
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION

        self.ALLOW_INSECURE_COOKIES = get_config_parameter_boolean(
            config, section, "ALLOW_INSECURE_COOKIES", False)
        self.ALLOW_MOBILEWEB = get_config_parameter_boolean(
            config, section, "ALLOW_MOBILEWEB", False)

        self.CAMCOPS_LOGO_FILE_ABSOLUTE = get_config_parameter(
            config, section, "CAMCOPS_LOGO_FILE_ABSOLUTE", str,
            DEFAULT_CAMCOPS_LOGO_FILE)

        self.CTV_FILENAME_SPEC = get_config_parameter(
            config, section, "CTV_FILENAME_SPEC", str, None)

        self.DATABASE_TITLE = get_config_parameter(
            config, section, "DATABASE_TITLE", str, DEFAULT_DATABASE_TITLE)
        self.DB_NAME = config.get(section, "DB_NAME")
        # ... no default: will fail if not provided
        self.DB_USER = config.get(section, "DB_USER")
        # ... no default: will fail if not provided
        # DB_PASSWORD: handled later, for security reasons (see below)
        self.DB_SERVER = get_config_parameter(
            config, section, "DB_SERVER", str, DEFAULT_DB_SERVER)
        self.DB_PORT = get_config_parameter(
            config, section, "DB_PORT", int, DEFAULT_DB_PORT)

        self.DBCLIENT_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "DBCLIENT_LOGLEVEL", logging.INFO)
        dblog.setLevel(self.DBCLIENT_LOGLEVEL)

        self.DBENGINE_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "DBENGINE_LOGLEVEL", logging.INFO)
        rnc_db.set_loglevel(self.DBENGINE_LOGLEVEL)

        self.DISABLE_PASSWORD_AUTOCOMPLETE = get_config_parameter_boolean(
            config, section, "DISABLE_PASSWORD_AUTOCOMPLETE", True)

        self.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE = get_config_parameter(
            config, section, "EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE", str, None)
        self.EXTRA_STRING_FILES = get_config_parameter_multiline(
            config, section, "EXTRA_STRING_FILES", [])

        self.HL7_LOCKFILE = get_config_parameter(
            config, section, "HL7_LOCKFILE", str, None)

        for n in range(1, NUMBER_OF_IDNUMS + 1):
            i = n - 1
            nstr = str(n)
            self.IDDESC[i] = get_config_parameter(
                config, section, "IDDESC_" + nstr, str, "")
            self.IDSHORTDESC[i] = get_config_parameter(
                config, section, "IDSHORTDESC_" + nstr, str, "")
        self.ID_POLICY_UPLOAD_STRING = get_config_parameter(
            config, section, "UPLOAD_POLICY", str, "")
        self.ID_POLICY_FINALIZE_STRING = get_config_parameter(
            config, section, "FINALIZE_POLICY", str, "")
        self.INTROSPECTION = get_config_parameter_boolean(
            config, section, "INTROSPECTION", True)

        self.LOCAL_INSTITUTION_URL = get_config_parameter(
            config, section, "LOCAL_INSTITUTION_URL",
            str, DEFAULT_LOCAL_INSTITUTION_URL)
        self.LOCAL_LOGO_FILE_ABSOLUTE = get_config_parameter(
            config, section, "LOCAL_LOGO_FILE_ABSOLUTE",
            str, DEFAULT_LOCAL_LOGO_FILE)
        self.LOCKOUT_THRESHOLD = get_config_parameter(
            config, section, "LOCKOUT_THRESHOLD",
            int, DEFAULT_LOCKOUT_THRESHOLD)
        self.LOCKOUT_DURATION_INCREMENT_MINUTES = get_config_parameter(
            config, section, "LOCKOUT_DURATION_INCREMENT_MINUTES",
            int, DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES)

        self.MAIN_STRING_FILE = get_config_parameter(
            config, section, "MAIN_STRING_FILE", str, DEFAULT_STRING_FILE)
        self.MYSQL = get_config_parameter(
            config, section, "MYSQL", str, DEFAULT_MYSQL)
        self.MYSQLDUMP = get_config_parameter(
            config, section, "MYSQLDUMP", str, DEFAULT_MYSQLDUMP)

        self.PASSWORD_CHANGE_FREQUENCY_DAYS = get_config_parameter(
            config, section, "PASSWORD_CHANGE_FREQUENCY_DAYS",
            int, DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS)
        self.PATIENT_SPEC_IF_ANONYMOUS = get_config_parameter(
            config, section, "PATIENT_SPEC_IF_ANONYMOUS", str, "anonymous")
        self.PATIENT_SPEC = get_config_parameter(
            config, section, "PATIENT_SPEC", str, None)

        self.SEND_ANALYTICS = get_config_parameter_boolean(
            config, section, "SEND_ANALYTICS", True)
        session_timeout_minutes = get_config_parameter(
            config, section, "SESSION_TIMEOUT_MINUTES",
            int, DEFAULT_TIMEOUT_MINUTES)
        self.SESSION_TIMEOUT = datetime.timedelta(
            minutes=session_timeout_minutes)
        self.SUMMARY_TABLES_LOCKFILE = get_config_parameter(
            config, section, "SUMMARY_TABLES_LOCKFILE", str, None)

        self.TASK_FILENAME_SPEC = get_config_parameter(
            config, section, "TASK_FILENAME_SPEC", str, None)
        self.TRACKER_FILENAME_SPEC = get_config_parameter(
            config, section, "TRACKER_FILENAME_SPEC", str, None)

        self.WEBVIEW_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "WEBVIEW_LOGLEVEL", logging.INFO)
        log.setLevel(self.WEBVIEW_LOGLEVEL)

        self.WKHTMLTOPDF_FILENAME = get_config_parameter(
            config, section, "WKHTMLTOPDF_FILENAME", str, None)
        rnc_pdf.set_processor(PDF_ENGINE,
                              wkhtmltopdf_filename=self.WKHTMLTOPDF_FILENAME)

        # ---------------------------------------------------------------------
        # Read from the config file: 2. HL7 section
        # ---------------------------------------------------------------------
        # http://stackoverflow.com/questions/335695/lists-in-configparser
        try:
            hl7_items = config.items(CONFIG_FILE_RECIPIENTLIST_SECTION)
            for key, recipientdef_name in hl7_items:
                log.debug("HL7 config: key={}, recipientdef_name="
                          "{}".format(key, recipientdef_name))
                h = cc_recipdef.RecipientDefinition(config, recipientdef_name)
                if h.valid:
                    self.HL7_RECIPIENT_DEFS.append(h)
        except configparser.NoSectionError:
            log.info("No config file section [{}]".format(
                CONFIG_FILE_RECIPIENTLIST_SECTION
            ))

        # ---------------------------------------------------------------------
        # Read from the config file: 3. database password
        # ---------------------------------------------------------------------
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
            # noinspection PyUnusedLocal
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
            # noinspection PyUnusedLocal
            db_password = None
        # ---------------------------------------------------------------------
        # Password is now re-obscured in all situations. Onwards...
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # Read from the database
        # ---------------------------------------------------------------------
        self.VALID_TABLE_NAMES = self.db.get_all_table_names()

        # ---------------------------------------------------------------------
        # Built from the preceding:
        # ---------------------------------------------------------------------

        self.INTROSPECTION_FILES = []
        if self.INTROSPECTION:
            # All introspection starts at INTROSPECTION_BASE_DIRECTORY
            rootdir = INTROSPECTION_BASE_DIRECTORY
            for dir_, subdirs, files in os.walk(rootdir):
                if dir_ == rootdir:
                    pretty_dir = ''
                else:
                    pretty_dir = os.path.relpath(dir_, rootdir)
                for filename in files:
                    basename, ext = os.path.split(filename)
                    if ext not in INTROSPECTABLE_EXTENSIONS:
                        continue
                    fullpath = os.path.join(dir_, filename)
                    prettypath = os.path.join(pretty_dir, filename)
                    self.INTROSPECTION_FILES.append(
                        cc_namedtuples.IntrospectionFileDetails(
                            fullpath=fullpath,
                            prettypath=prettypath,
                            searchterm=filename,
                            ext=ext
                        )
                    )
            self.INTROSPECTION_FILES = sorted(
                self.INTROSPECTION_FILES,
                key=operator.attrgetter("prettypath"))

        # Cache tokenized ID policies
        cc_policy.tokenize_upload_id_policy(self.ID_POLICY_UPLOAD_STRING)
        cc_policy.tokenize_finalize_id_policy(self.ID_POLICY_FINALIZE_STRING)
        # Valid?
        if not cc_policy.upload_id_policy_valid():
            raise RuntimeError("UPLOAD_POLICY invalid in config")
        if not cc_policy.finalize_id_policy_valid():
            raise RuntimeError("FINALIZE_POLICY invalid in config")

        # Note: HTML4 uses <img ...>; XHTML uses <img ... />;
        # HTML5 is happy with <img ... />

        # IE float-right problems: http://stackoverflow.com/questions/1820007
        # Tables are a nightmare in IE (table max-width not working unless you
        # also specify it for image size, etc.)
        self.WEB_LOGO = """
            <div class="web_logo_header">
                <a href="{}"><img class="logo_left" src="{}" alt="" /></a>
                <a href="{}"><img class="logo_right" src="{}" alt="" /></a>
            </div>
        """.format(
            self.SCRIPT_NAME, CAMCOPS_LOGO_FILE_WEBREF,
            self.LOCAL_INSTITUTION_URL, LOCAL_LOGO_FILE_WEBREF
        )

        self.WEBSTART = WEB_HEAD + self.WEB_LOGO

        if PDF_ENGINE in ["weasyprint", "pdfkit"]:
            # weasyprint: div with floating img does not work properly
            self.PDF_LOGO_LINE = """
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
        elif PDF_ENGINE in ["pdfkit"]:
            self.PDF_LOGO_LINE = """
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
            # self.PDF_LOGO_LINE = """
            #     <div class="pdf_logo_header">
            #         <img class="logo_left" src="file://{}" />
            #         <img class="logo_right" src="file://{}" />
            #     </div>
            # """.format(
            #     self.CAMCOPS_LOGO_FILE_ABSOLUTE,
            #     self.LOCAL_LOGO_FILE_ABSOLUTE,
            # )
        elif PDF_ENGINE in ["xhtml2pdf"]:
            # xhtml2pdf
            # hard to get logos positioned any other way than within a table
            self.PDF_LOGO_LINE = """
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
                self.CAMCOPS_LOGO_FILE_ABSOLUTE, PDF_LOGO_HEIGHT,
                self.LOCAL_LOGO_FILE_ABSOLUTE, PDF_LOGO_HEIGHT
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

        # ---------------------------------------------------------------------
        # Now we can keep that state:
        # ---------------------------------------------------------------------
        self.PERSISTENT_CONSTANTS_INITIALIZED = True

    def set_from_environ_and_ping_db(self, environ: Dict) -> None:
        """Set up process-local storage from the incoming environment (which
        may be very fast if already cached) and ensure we have an active
        database connection."""

        # 1. Set up process-local storage
        self.set(environ)
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

    def get_anonymisation_database(self) -> rnc_db.DatabaseSupporter:
        """Open the anonymisation staging database. That is not performance-
        critical and the connection does not need to be cached. Will raise
        an exception upon a connection error."""
        # Follows same security principles as above.
        config = configparser.ConfigParser()
        config.read_file(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))
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
            # noinspection PyUnusedLocal
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
            # noinspection PyUnusedLocal
            password = None
        # ---------------------------------------------------------------------
        # Password is now re-obscured in all situations. Onwards...
        # ---------------------------------------------------------------------
        return db

# =============================================================================
# Process-specific instance
# =============================================================================

pls = LocalStorage()
