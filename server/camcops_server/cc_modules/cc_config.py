#!/usr/bin/env python
# camcops_server/cc_modules/cc_config.py

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
import contextlib
import datetime
import operator
import os
import logging
from typing import Dict, Generator, List, Optional

from cardinal_pythonlib.configfiles import (
    get_config_parameter,
    get_config_parameter_boolean,
    get_config_parameter_loglevel,
    get_config_parameter_multiline
)
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.pdf as rnc_pdf
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession

from .cc_baseconstants import (
    INTROSPECTABLE_EXTENSIONS,
)
from .cc_cache import cache_region_static, fkg
from .cc_constants import (
    CONFIG_FILE_MAIN_SECTION,
    CONFIG_FILE_RECIPIENTLIST_SECTION,
    DEFAULT_CAMCOPS_LOGO_FILE,
    DEFAULT_DATABASE_TITLE,
    DEFAULT_LOCAL_INSTITUTION_URL,
    DEFAULT_LOCAL_LOGO_FILE,
    DEFAULT_LOCKOUT_DURATION_INCREMENT_MINUTES,
    DEFAULT_LOCKOUT_THRESHOLD,
    DEFAULT_MYSQL,
    DEFAULT_MYSQLDUMP,
    DEFAULT_PASSWORD_CHANGE_FREQUENCY_DAYS,
    DEFAULT_PLOT_FONTSIZE,
    DEFAULT_TIMEOUT_MINUTES,
    ENVVAR_CONFIG_FILE,
    INTROSPECTION_BASE_DIRECTORY,
    PDF_ENGINE,
    PDF_LOGO_HEIGHT,
)
from .cc_filename import (
    filename_spec_is_valid,
    patient_spec_for_filename_is_valid,
)
from .cc_simpleobjects import IntrospectionFileDetails
from .cc_policy import (
    finalize_id_policy_valid,
    tokenize_finalize_id_policy,
    tokenize_upload_id_policy,
    upload_id_policy_valid,
)
from .cc_recipdef import RecipientDefinition

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Configuration class. (It gets cached on a per-process basis.)
# =============================================================================

class CamcopsConfig(object):
    """Process-local storage class. One instance per process. Persists across
    sessions thanks to mod_wsgi."""

    def __init__(self, config_filename: str) -> None:
        """Initialize from config file."""

        # ---------------------------------------------------------------------
        # Open config file
        # ---------------------------------------------------------------------
        self.CAMCOPS_CONFIG_FILE = config_filename
        if not self.CAMCOPS_CONFIG_FILE:
            raise AssertionError("{} not specified".format(ENVVAR_CONFIG_FILE))
        log.info("Reading from {}", self.CAMCOPS_CONFIG_FILE)
        config = configparser.ConfigParser()
        config.read_file(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))

        # ---------------------------------------------------------------------
        # Read from the config file: 1. Most stuff, in alphabetical order
        # ---------------------------------------------------------------------
        section = CONFIG_FILE_MAIN_SECTION

        self.ALLOW_INSECURE_COOKIES = get_config_parameter_boolean(
            config, section, "ALLOW_INSECURE_COOKIES", False)
        # self.ALLOW_MOBILEWEB = get_config_parameter_boolean(
        #     config, section, "ALLOW_MOBILEWEB", False)
        self.ALLOW_MOBILEWEB = False  # disabled permanently

        self.CAMCOPS_LOGO_FILE_ABSOLUTE = get_config_parameter(
            config, section, "CAMCOPS_LOGO_FILE_ABSOLUTE", str,
            DEFAULT_CAMCOPS_LOGO_FILE)

        self.CTV_FILENAME_SPEC = get_config_parameter(
            config, section, "CTV_FILENAME_SPEC", str, None)

        self.DATABASE_TITLE = get_config_parameter(
            config, section, "DATABASE_TITLE", str, DEFAULT_DATABASE_TITLE)
        self.DB_URL = config.get(section, "DB_URL")
        # ... no default: will fail if not provided
        self.DB_ECHO = get_config_parameter_boolean(
            config, section, "DB_ECHO", False)
        self.DBCLIENT_LOGLEVEL = get_config_parameter_loglevel(
            config, section, "DBCLIENT_LOGLEVEL", logging.INFO)
        logging.getLogger("camcops_server.database")\
            .setLevel(self.DBCLIENT_LOGLEVEL)
        # ... MUTABLE GLOBAL STATE (if relatively unimportant)

        self.DISABLE_PASSWORD_AUTOCOMPLETE = get_config_parameter_boolean(
            config, section, "DISABLE_PASSWORD_AUTOCOMPLETE", True)

        self.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE = get_config_parameter(
            config, section, "EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE", str, None)
        self.EXTRA_STRING_FILES = get_config_parameter_multiline(
            config, section, "EXTRA_STRING_FILES", [])

        self.HL7_LOCKFILE = get_config_parameter(
            config, section, "HL7_LOCKFILE", str, None)

        # The ConfigParser forces all its keys to lower care.
        self.IDDESC = {}  # type: Dict[int, str]
        self.IDSHORTDESC = {}  # type: Dict[int, str]
        descprefix = "iddesc_"
        shortdescprefix = "idshortdesc_"
        for key, desc in config.items(section):
            if key.startswith(descprefix):
                nstr = key[len(descprefix):]
                try:
                    which_idnum = int(nstr)
                except (TypeError, ValueError):
                    raise AssertionError(
                        "Bad ID description config key: " + repr(key))
                if which_idnum <= 0:
                    raise AssertionError(
                        "Bad ID number: {} (must be >=1)".format(nstr))
                if not desc:
                    raise AssertionError(
                        "Bad description for ID {}: {}".format(
                            nstr, repr(desc)))
                shortdesc = get_config_parameter(
                    config, section, shortdescprefix + nstr, str, "")
                if not shortdesc:
                    raise AssertionError(
                        "ID number {} has description but no short "
                        "description".format(nstr))
                self.IDDESC[which_idnum] = desc
                self.IDSHORTDESC[which_idnum] = shortdesc

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

        # self.MAIN_STRING_FILE = get_config_parameter(
        #     config, section, "MAIN_STRING_FILE", str, DEFAULT_STRING_FILE)
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
        # currently not configurable, but easy to add in the future:
        self.PLOT_FONTSIZE = DEFAULT_PLOT_FONTSIZE

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
        logging.getLogger().setLevel(self.WEBVIEW_LOGLEVEL)  # root logger
        # ... MUTABLE GLOBAL STATE (if relatively unimportant)  # noqa

        self.WKHTMLTOPDF_FILENAME = get_config_parameter(
            config, section, "WKHTMLTOPDF_FILENAME", str, None)

        # ---------------------------------------------------------------------
        # Read from the config file: 2. HL7 section
        # ---------------------------------------------------------------------
        # http://stackoverflow.com/questions/335695/lists-in-configparser
        self.HL7_RECIPIENT_DEFS = []  # type: List[RecipientDefinition]
        try:
            hl7_items = config.items(CONFIG_FILE_RECIPIENTLIST_SECTION)
            for key, recipientdef_name in hl7_items:
                log.debug("HL7 config: key={}, recipientdef_name={}",
                          key, recipientdef_name)
                h = RecipientDefinition(
                    valid_which_idnums=self.get_which_idnums(),
                    config=config,
                    section=recipientdef_name)
                if h.valid:
                    self.HL7_RECIPIENT_DEFS.append(h)
        except configparser.NoSectionError:
            log.info("No config file section [{}]",
                     CONFIG_FILE_RECIPIENTLIST_SECTION)

        # ---------------------------------------------------------------------
        # Built from the preceding:
        # ---------------------------------------------------------------------

        self.INTROSPECTION_FILES = []  # type: List[IntrospectionFileDetails]
        if self.INTROSPECTION:
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
                    self.INTROSPECTION_FILES.append(
                        IntrospectionFileDetails(
                            fullpath=fullpath,
                            prettypath=prettypath,
                            searchterm=filename,
                            ext=ext
                        )
                    )
            self.INTROSPECTION_FILES = sorted(
                self.INTROSPECTION_FILES,
                key=operator.attrgetter("prettypath"))

        valid_which_idnums = self.get_which_idnums()

        # Cache tokenized ID policies
        tokenize_upload_id_policy(policy=self.ID_POLICY_UPLOAD_STRING,
                                  valid_which_idnums=valid_which_idnums)
        tokenize_finalize_id_policy(policy=self.ID_POLICY_FINALIZE_STRING,
                                    valid_which_idnums=valid_which_idnums)
        # Valid?
        if not upload_id_policy_valid():
            raise RuntimeError(
                "UPLOAD_POLICY invalid in config (policy: {})".format(
                    repr(self.ID_POLICY_UPLOAD_STRING)))
        if not finalize_id_policy_valid():
            raise RuntimeError(
                "FINALIZE_POLICY invalid in config (policy: {})".format(
                    repr(self.ID_POLICY_FINALIZE_STRING)))

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
        if not patient_spec_for_filename_is_valid(
                patient_spec=self.PATIENT_SPEC,
                valid_which_idnums=valid_which_idnums):
            raise RuntimeError("Invalid PATIENT_SPEC in [server] section of "
                               "config file")

        if not self.TASK_FILENAME_SPEC:
            raise RuntimeError("Missing/blank TASK_FILENAME_SPEC in "
                               "[server] section of config file")
        if not filename_spec_is_valid(self.TASK_FILENAME_SPEC,
                                      valid_which_idnums=valid_which_idnums):
            raise RuntimeError("Invalid TASK_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.TRACKER_FILENAME_SPEC:
            raise RuntimeError("Missing/blank TRACKER_FILENAME_SPEC in "
                               "[server] section of config file")
        if not filename_spec_is_valid(self.TRACKER_FILENAME_SPEC,
                                      valid_which_idnums=valid_which_idnums):
            raise RuntimeError("Invalid TRACKER_FILENAME_SPEC in "
                               "[server] section of config file")

        if not self.CTV_FILENAME_SPEC:
            raise RuntimeError("Missing/blank CTV_FILENAME_SPEC in "
                               "[server] section of config file")
        if not filename_spec_is_valid(self.CTV_FILENAME_SPEC,
                                      valid_which_idnums=valid_which_idnums):
            raise RuntimeError("Invalid CTV_FILENAME_SPEC in "
                               "[server] section of config file")

        self.VALID_TABLE_NAMES = self._get_all_table_names()  # reads db

        # *** NEED TO BE CONFIGURABLE:
        self.session_cookie_secret = "hello!"  # *** fix!

        # Moved out from CamcopsConfig:
        # ---------------------------------------------------------------------
        # Date/time
        # ---------------------------------------------------------------------
        # self.TODAY = datetime.date.today()  # fetches the local date
        #       -> as above, e.g. now_arrow
        # self.NOW_LOCAL_TZ = get_now_localtz()
        #       ... we want nearly all our times offset-aware
        #       ... http://stackoverflow.com/questions/4530069
        #       -> Request.now_arrow
        # self.NOW_UTC_WITH_TZ = convert_datetime_to_utc(self.NOW_LOCAL_TZ)
        #       -> Request.now_arrow
        # self.NOW_UTC_NO_TZ = convert_datetime_to_utc_notz(self.NOW_LOCAL_TZ)
        #       -> Request.now_utc_datetime
        # self.NOW_LOCAL_TZ_ISO8601 = format_datetime(self.NOW_LOCAL_TZ,
        #                                             DATEFORMAT.ISO8601)
        #       -> Request.now_arrow, etc.
        # ---------------------------------------------------------------------
        # Read from the WSGI environment
        # ---------------------------------------------------------------------
        # self.remote_addr = environ.get("REMOTE_ADDR")
        #       -> Request.remote_addr (Pyramid)
        # self.remote_port = environ.get("REMOTE_PORT")
        #       -> not in Pyramid Request object? Unimportant
        #          Will be available as request.environ["REMOTE_PORT"]
        # # self.SCRIPT_NAME = environ.get("SCRIPT_NAME", "")
        # self.SCRIPT_NAME = URL_RELATIVE_WEBVIEW
        #       -> Request.script_name (Pyramid)
        #       *** CHECK: script_name is different from URL_RELATIVE_WEBVIEW
        # self.SERVER_NAME = environ.get("SERVER_NAME")
        #       -> Request.server_name (Pyramid)
        # ---------------------------------------------------------------------
        # More complex, WSGI-derived
        # ---------------------------------------------------------------------
        #     # Reconstruct URL:
        #     # http://www.python.org/dev/peps/pep-0333/#url-reconstruction
        #     protocol = environ.get("wsgi.url_scheme", "")
        #     if environ.get("HTTP_HOST"):
        #         host = environ.get("HTTP_HOST")
        #     else:
        #         host = environ.get("SERVER_NAME", "")
        #     port = ""
        #     server_port = environ.get("SERVER_PORT")
        #     if (server_port and
        #             ":" not in host and
        #             not(protocol == "https" and server_port == "443") and
        #             not(protocol == "http" and server_port == "80")):
        #         port = ":" + server_port
        #     script = urllib.parse.quote(environ.get("SCRIPT_NAME", ""))
        #     path = urllib.parse.quote(environ.get("PATH_INFO", ""))
        #
        #     # But not the query string:
        #     # if environ.get("QUERY_STRING"):
        #     #    query += "?" + environ.get("QUERY_STRING")
        #     # else:
        #     #    query = ""
        #
        #     url = "{protocol}://{host}{port}{script}{path}".format(
        #         protocol=protocol,
        #         host=host,
        #         port=port,
        #         script=script,
        #         path=path,
        #     )
        #
        #     self.SCRIPT_PUBLIC_URL_ESCAPED = escape(url)
        #
        #           -> ***
        #
        # ---------------------------------------------------------------------
        # Other
        # ---------------------------------------------------------------------
        # self.session = None  # type: Session  -> Request.camcops_session
        # self.WEBSTART -> Request.webstart_html
        # self.WEB_LOGO -> Request.web_logo_html

    def create_engine(self) -> Engine:
        return create_engine(self.DB_URL, echo=self.DB_ECHO,
                             pool_pre_ping=True)

    def _get_all_table_names(self) -> List[str]:
        engine = self.create_engine()
        return get_table_names(engine=engine)

    def get_which_idnums(self) -> List[int]:
        return list(self.IDDESC.keys())

    def get_id_desc(self, which_idnum: int,
                    default: str = None) -> Optional[str]:
        """Get server's ID description."""
        return self.IDDESC.get(which_idnum, default)

    def get_id_shortdesc(self, which_idnum: int,
                         default: str = None) -> Optional[str]:
        """Get server's short ID description."""
        return self.IDSHORTDESC.get(which_idnum, default)

    @contextlib.contextmanager
    def get_dbsession_context(self) -> Generator[SqlASession, None, None]:
        engine = self.create_engine()
        maker = sessionmaker(bind=engine)
        session = maker()  # type: SqlASession
        # noinspection PyBroadException
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # def get_anonymisation_database(self) -> rnc_db.DatabaseSupporter:
    #     """Open the anonymisation staging database. That is not performance-
    #     critical and the connection does not need to be cached. Will raise
    #     an exception upon a connection error."""
    #     # Follows same security principles as above.
    #     config = configparser.ConfigParser()
    #     config.read_file(codecs.open(self.CAMCOPS_CONFIG_FILE, "r", "utf8"))
    #     section = CONFIG_FILE_MAIN_SECTION
    #
    #     server = get_config_parameter(
    #         config, section, "ANONSTAG_DB_SERVER", str, DEFAULT_DB_SERVER)
    #     port = get_config_parameter(
    #         config, section, "ANONSTAG_DB_PORT", int, DEFAULT_DB_PORT)
    #     database = get_config_parameter(
    #         config, section, "ANONSTAG_DB_NAME", str, None)
    #     if database is None:
    #         raise RuntimeError("ANONSTAG_DB_NAME not specified in config")
    #     user = get_config_parameter(
    #         config, section, "ANONSTAG_DB_USER", str, None)
    #     if user is None:
    #         raise RuntimeError("ANONSTAG_DB_USER not specified in config")
    #     # It is a potential disaster if the anonymisation database is the same
    #     # database as the main database - risk of destroying original data.
    #     # We mitigate this risk in two ways.
    #     # (1) We check here. Since different server/port combinations could
    #     #     resolve to the same host, we take the extremely conservative
    #     #     approach of requiring a different database name.
    #     if database == self.DB_NAME:
    #         raise RuntimeError("ANONSTAG_DB_NAME must be different from "
    #                            "DB_NAME")
    #     # (2) We prefix all tablenames in the CRIS staging database;
    #     #     see cc_task.
    #     try:
    #         password = get_config_parameter(
    #             config, section, "ANONSTAG_DB_PASSWORD", str, None)
    #     except:  # deliberately conceal details for security
    #         # noinspection PyUnusedLocal
    #         password = None
    #         raise RuntimeError("Problem reading ANONSTAG_DB_PASSWORD from "
    #                            "config")
    #     if password is None:
    #         raise RuntimeError("ANONSTAG_DB_PASSWORD not specified in config")
    #     try:
    #         db = rnc_db.DatabaseSupporter()
    #         db.connect_to_database_mysql(
    #             server=server,
    #             port=port,
    #             database=database,
    #             user=user,
    #             password=password,
    #             autocommit=False  # NB therefore need to commit
    #             # ... done in camcops.py at the end of a session
    #         )
    #     except:  # deliberately conceal details for security
    #         raise rnc_db.NoDatabaseError(
    #             "Problem opening or reading from database; details concealed "
    #             "for security reasons")
    #     finally:
    #         # Executed whether an exception is raised or not.
    #         # noinspection PyUnusedLocal
    #         password = None
    #     # -------------------------------------------------------------------
    #     # Password is now re-obscured in all situations. Onwards...
    #     # -------------------------------------------------------------------
    #     return db


# =============================================================================
# Get config filename from an appropriate environment (WSGI or OS)
# =============================================================================

def get_config_filename(environ: Dict[str, str] = None) -> str:
    config_filename = None
    if environ is not None:
        # This may be used for WSGI environments
        config_filename = environ.get(ENVVAR_CONFIG_FILE)
    if config_filename is None:
        # Fall back to OS environment
        config_filename = os.environ.get(ENVVAR_CONFIG_FILE)
    if not config_filename:
        raise AssertionError(
            "Neither WSGI nor OS environment provided the required "
            "environment variable {}".format(ENVVAR_CONFIG_FILE))
    return config_filename


# =============================================================================
# Cached instance
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def get_config(config_filename: str) -> CamcopsConfig:
    return CamcopsConfig(config_filename)
