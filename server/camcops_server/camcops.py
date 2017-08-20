#!/usr/bin/env python
# camcops_server/camcops.py

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

# SET UP LOGGING BEFORE WE IMPORT CAMCOPS MODULES, allowing them to log during
# imports (see e.g. cc_plot).
# Currently sets up colour logging even if under WSGI environment. This is fine
# for gunicorn from the command line; I'm less clear about whether the disk
# logs look polluted by ANSI codes; needs checking.
import logging
from cardinal_pythonlib.logs import (
    main_only_quicksetup_rootlogger,
    BraceStyleAdapter,
)
main_only_quicksetup_rootlogger(logging.DEBUG)
log = BraceStyleAdapter(logging.getLogger(__name__))
log.info("CamCOPS starting")

import argparse  # nopep8
import codecs  # nopep8
import getpass  # nopep8
import os  # nopep8
import sys  # nopep8

from pyramid.config import Configurator  # nopep8
from pyramid.interfaces import ISession  # nopep8
from pyramid.router import Router  # nopep8
from pyramid.session import SignedCookieSessionFactory  # nopep8
from wsgiref.simple_server import make_server  # nopep8

from cardinal_pythonlib.convert import convert_to_bool  # nopep8
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_session  # nop3p8

from .cc_modules.cc_analytics import ccanalytics_unit_tests  # nopep8
from .cc_modules.cc_audit import audit  # nopep8
from .cc_modules.cc_constants import (
    CAMCOPS_URL,
    ENVVAR_CONFIG_FILE,
    SEPARATOR_EQUALS,
)  # nopep8
from .cc_modules.cc_blob import Blob, ccblob_unit_tests  # nopep8
from .cc_modules.cc_device import ccdevice_unit_tests, Device  # nopep8
from .cc_modules.cc_dump import ccdump_unit_tests  # nopep8
from .cc_modules.cc_hl7 import send_all_pending_hl7_messages  # nopep8
from .cc_modules.cc_hl7core import cchl7core_unit_tests  # nopep8
from .cc_modules.cc_patient import ccpatient_unit_tests  # nopep8
from .cc_modules.cc_pyramid import COOKIE_NAME, RouteCollection  # nopep8
from .cc_modules.cc_policy import ccpolicy_unit_tests  # nopep8
from .cc_modules.cc_report import ccreport_unit_tests  # nopep8
from .cc_modules.cc_request import CamcopsRequest, command_line_request  # nopep8
from .cc_modules.cc_session import ccsession_unit_tests, CamcopsSession  # nopep8
from .cc_modules.cc_storedvar import (
    ServerStoredVar,
    ServerStoredVarNames,
    StoredVarTypes,
)  # nopep8
from .cc_modules.cc_task import (
    cctask_unit_tests,
    cctask_unit_tests_basic,
)  # nopep8
from .cc_modules.cc_tracker import cctracker_unit_tests  # imports matplotlib; SLOW  # nopep8
from .cc_modules.cc_user import ccuser_unit_tests  # nopep8
from .cc_modules.cc_user import set_password_directly  # nopep8
from .cc_modules.cc_version import CAMCOPS_SERVER_VERSION, make_version  # nopep8
from .database import database_unit_tests  # nopep8
from .webview import (
    get_tsv_header_from_dict,
    get_tsv_line_from_dict,
    make_summary_tables,
    webview_unit_tests,
    write_descriptions_comments,
)  # nopep8

log.debug("All imports complete")


# =============================================================================
# Debugging options
# =============================================================================

# Note that: (*) os.environ is available at load time but is separate from the
# WSGI environment; (*) the WSGI environment is sent with each request; (*) we
# need the following information at load time.

# For debugging, set the next variable to True, and it will provide much
# better HTML debugging output.
# Use caution enabling this on a production system.
# However, system passwords should be concealed regardless (see cc_shared.py).
CAMCOPS_DEBUG_TO_HTTP_CLIENT = convert_to_bool(
    os.environ.get("CAMCOPS_DEBUG_TO_HTTP_CLIENT", False))

# Report profiling information to the HTTPD log? (Adds overhead; do not enable
# for production systems.)
CAMCOPS_PROFILE = convert_to_bool(os.environ.get("CAMCOPS_PROFILE", False))

CAMCOPS_SERVE_STATIC_FILES = convert_to_bool(
    os.environ.get("CAMCOPS_SERVE_STATIC_FILES", True))

# The other debugging control is in cc_shared: see the log.setLevel() calls,
# controlled primarily by the configuration file's DEBUG_OUTPUT option.

# =============================================================================
# Other constants
# =============================================================================

DEFAULT_CONFIG_FILENAME = "/etc/camcops/camcops.conf"


# =============================================================================
# WSGI entry point
# =============================================================================
# The WSGI framework looks for: def application(environ, start_response)
# ... must be called "application"
# ... at least for some servers!

DEFUNCT = '''

# Disable client-side caching for anything non-static
webview_application = DisableClientSideCachingMiddleware(webview_application)
database_application = DisableClientSideCachingMiddleware(database_application)

# Don't apply ZIP compression here as middleware: it needs to be done
# selectively by content type, and is best applied automatically by Apache
# (which is easy).
if CAMCOPS_DEBUG_TO_HTTP_CLIENT:
    webview_application = ErrorReportingMiddleware(webview_application)
if CAMCOPS_PROFILE:
    webview_application = ProfilerMiddleware(webview_application)
    database_application = ProfilerMiddleware(database_application)


def application(environ: Dict[str, str],
                start_response: Callable[[str, HEADERS_TYPE], None]) \
        -> Iterable[bytes]:
    """
    Master WSGI entry point.

    Provides a wrapper around the main WSGI application in order to trap
    database errors, so that a commit or rollback is guaranteed, and so a crash
    cannot leave the database in a locked state and thereby mess up other
    processes.
    """

    if environ["wsgi.multithread"]:
        log.critical("Error: started in multithreaded mode")
        raise RuntimeError("Cannot be run in multithreaded mode")

    # Set global variables, connect/reconnect to database, etc.
    pls.set_from_environ_and_ping_db(environ)

    log.debug("WSGI environment: {0!r}", environ)

    path = environ['PATH_INFO']
    # log.debug("PATH_INFO: {}", path)

    # Trap any errors from here.
    # http://doughellmann.com/2009/06/19/python-exception-handling-techniques.html  # noqa

    # noinspection PyBroadException
    try:
        if path == URL_ROOT_WEBVIEW:
            return webview_application(environ, start_response)
            # ... it will commit (the earlier the better for speed)
        elif path == URL_ROOT_DATABASE:
            return database_application(environ, start_response)
            # ... it will commit (the earlier the better for speed)
        else:
            # No URL matches
            msg = ("URL not found (message from camcops.py). "
                   "URL path was: {}.".format(path))
            output = msg.encode('utf-8')
            start_response('404 Not Found', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(output))),
            ])
            return [output]
    except:
        try:
            raise  # re-raise the original error
        finally:
            # noinspection PyBroadException
            try:
                pls.db.rollback()
            except:
                pass  # ignore errors in rollback


if CAMCOPS_SERVE_STATIC_FILES:
    application = SharedDataMiddleware(application, {
        URL_ROOT_STATIC: STATIC_ROOT_DIR
    })
'''


# -----------------------------------------------------------------------------
# CamcopsSession and Pyramid HTTP session handling
# -----------------------------------------------------------------------------

def get_session_factory() -> SignedCookieSessionFactory:
    """
    We have to give a Pyramid request a way of making an HTTP session.
    We must return a session factory.
    - An example is an instance of SignedCookieSessionFactory().
    - A session factory has the signature [1]:
            sessionfactory(req: CamcopsRequest) -> session_object
      ... where session "is a namespace" [2]
      ... but more concretely implementis the pyramid.interfaces.ISession 
          interface
      [1] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session-factory
      [2] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session
    - We want to be able to make the session by reading the CamcopsConfig from
      the request.
    """  # noqa
    def factory(req: CamcopsRequest) -> ISession:
        """
        How does the session write the cookies to the response?

            SignedCookieSessionFactory
                BaseCookieSessionFactory  # pyramid/session.py
                    CookieSession
                        def changed():
                            if not self._dirty:
                                self._dirty = True
                                def set_cookie_callback(request, response):
                                    self._set_cookie(response)
                                    # ...
                                self.request.add_response_callback(set_cookie_callback)  # noqa

                        def _set_cookie(self, response):
                            # ...
                            response.set_cookie(...)

        """
        cfg = req.config
        secure_cookies = not cfg.ALLOW_INSECURE_COOKIES
        pyramid_factory = SignedCookieSessionFactory(
            secret=cfg.session_cookie_secret,
            hashalg='sha512',  # the default
            salt='camcops_pyramid_session.',
            cookie_name=COOKIE_NAME,
            max_age=None,  # browser scope; session cookie
            path='/',  # the default
            domain=None,  # the default
            secure=secure_cookies,
            httponly=secure_cookies,
            timeout=None,  # we handle timeouts at the database level instead
            reissue_time=0,  # default; reissue cookie at every request
            set_on_exception=True,  # (default) cookie even if exception raised
            serializer=None,  # (default) use pyramid.session.PickleSerializer
            # As max_age and expires are left at their default of None, these
            # are session cookies.
        )
        return pyramid_factory(req)

    return factory


# -----------------------------------------------------------------------------
# Make the WSGI app, attaching in our special methods
# -----------------------------------------------------------------------------

def make_wsgi_app() -> Router:
    """
    Makes and returns a WSGI application.

    QUESTION: how do we access the WSGI environment (passed to the WSGI app)
    from within a Pyramid request?
    ANSWER:
        Configurator.make_wsgi_app() calls Router.__init__()
        and returns: app = Router(...)
        The WSGI framework uses: response = app(environ, start_response)
        which therefore calls: Router.__call__(environ, start_response)
        which does:
              response = self.execution_policy(environ, self)
              return response(environ, start_response)
        So something LIKE this will be called:
              Router.default_execution_policy(environ, router)
                  with router.request_context(environ) as request:
                      # ...
        So the environ is handled by Router.request_context(environ)
        which will call BaseRequest.__init__()
        which does:
              d = self.__dict__
              d['environ'] = environ
        so we should be able to use
              request.environ  # type: Dict[str, str]
    """
    log.debug("Creating WSGI app")

    # -------------------------------------------------------------------------
    # 0. Settings that transcend the config file
    # -------------------------------------------------------------------------
    # Most things should be in the config file. This enables us to run multiple
    # configs (e.g. multiple CamCOPS databases) through the same process.
    # However, some things we need to know right now, to make the WSGI app.
    # Here, OS environment variables and command-line switches are appropriate.

    use_debug_toolbar = True  # *** make env var or CLI or both

    # -------------------------------------------------------------------------
    # 1. Base app
    # -------------------------------------------------------------------------
    with Configurator() as config:
        # ---------------------------------------------------------------------
        # Session attributes: config, database, other
        # ---------------------------------------------------------------------
        config.set_request_factory(CamcopsRequest)

        # SUMMARY OF IMPORTANT REQUEST PROPERTIES, AND STANDARD NAMES:
        #
        # Built in to Pyramid:
        #       pyramid_session = request.session  # type: ISession
        #       ...
        # Added here:  -- see CamcopsRequest

        # ---------------------------------------------------------------------
        # Routes and accompanying views
        # ---------------------------------------------------------------------
        # Most views are using @view_config() which calls add_view().
        for pr in RouteCollection.all_routes():
            config.add_route(pr.route, pr.path)
        # *** # config.scan()

        # See also:
        # https://stackoverflow.com/questions/19184612/how-to-ensure-urls-generated-by-pyramids-route-url-and-route-path-are-valid  # noqa

        # ---------------------------------------------------------------------
        # Add tweens (inner to outer)
        # ---------------------------------------------------------------------
        # We will use implicit positioning:
        # - https://www.slideshare.net/aconrad/alex-conrad-pyramid-tweens-ploneconf-2011  # noqa

        # config.add_tween('camcops_server.camcops.http_session_tween_factory')
        config.set_session_factory(get_session_factory())

        # ---------------------------------------------------------------------
        # Debug toolbar
        # ---------------------------------------------------------------------
        if use_debug_toolbar:
            config.include('pyramid_debugtoolbar')
            config.add_route(RouteCollection.DEBUG_TOOLBAR.route,
                             RouteCollection.DEBUG_TOOLBAR.path)

        # ---------------------------------------------------------------------
        # Make app
        # ---------------------------------------------------------------------
        app = config.make_wsgi_app()

    # -------------------------------------------------------------------------
    # 2. Middleware above the Pyramid level
    # -------------------------------------------------------------------------
    # ...

    # -------------------------------------------------------------------------
    # 3. Done
    # -------------------------------------------------------------------------
    log.debug("WSGI app created")
    return app


application = make_wsgi_app()


def test_serve(host: str = '0.0.0.0', port: int = 8000) -> None:
    server = make_server(host, port, application)
    log.info("Serving on host={}, port={}".format(host, port))
    server.serve_forever()


# =============================================================================
# User command-line interaction
# =============================================================================

def ask_user(prompt: str, default: str = None) -> str:
    """Prompts the user, with a default. Returns a string."""
    if default is None:
        prompt += ": "
    else:
        prompt += " [" + default + "]: "
    result = input(prompt)
    return result if len(result) > 0 else default


def ask_user_password(prompt: str) -> str:
    """Read a password from the console."""
    return getpass.getpass(prompt + ": ")


# =============================================================================
# Command-line debugging
# =============================================================================

# a = cc_task.TaskFactory("ace3", 6)
# a = cc_task.TaskFactory("ace3", 10)
# a.dump()
# a.write_pdf_to_disk("ace3test.pdf")

# p = cc_task.TaskFactory("phq9", 86)
# p = cc_task.TaskFactory("phq9", 1)
# p = cc_task.TaskFactory("phq9", 15)
# p.dump()
# p.write_pdf_to_disk("phq9test.pdf")

# b = Blob(3)

# create_demo_user()


# =============================================================================
# Command-line functions
# =============================================================================

def export_descriptions_comments() -> None:
    """Export an HTML version of database fields/comments to a file of the
    user's choice."""
    filename = ask_user("Output HTML file",
                        "camcops_table_descriptions.html")
    include_views = bool(ask_user(
        "Include views (leave blank for no, anything else for yes)? "
    ))
    with open(filename, 'wb') as file:
        write_descriptions_comments(file, include_views)
    print("Done.")


def reset_storedvars() -> None:
    """Copy key descriptions (database title, ID descriptions, policies) from
    the config file to the database.

    These are stored so researchers can access them from the database.
    However, they're not used directly by the server (or the database.pl upload
    script).
    """
    print("Setting database title/ID descriptions from configuration file")
    dbt = ServerStoredVar(ServerStoredVarNames.DATABASE_TITLE,
                          StoredVarTypes.TYPE_TEXT)
    dbt.set_value(pls.DATABASE_TITLE)
    pls.db.db_exec_literal(
        "DELETE FROM {ssvtable} WHERE name LIKE 'idDescription%'".format(
            ssvtable=ServerStoredVar.TABLENAME,
        ))
    pls.db.db_exec_literal(
        "DELETE FROM {ssvtable} WHERE name LIKE 'idShortDescription%'".format(
            ssvtable=ServerStoredVar.TABLENAME,
        ))
    for n in pls.get_which_idnums():
        nstr = str(n)
        sv_id = ServerStoredVar("idDescription" + nstr, "text")
        sv_id.set_value(pls.get_id_desc(n))
        sv_sd = ServerStoredVar("idShortDescription" + nstr, "text")
        sv_sd.set_value(pls.get_id_shortdesc(n))
    sv_id_policy_upload = ServerStoredVar("idPolicyUpload", "text")
    sv_id_policy_upload.set_value(pls.ID_POLICY_UPLOAD_STRING)
    sv_id_policy_finalize = ServerStoredVar("idPolicyFinalize", "text")
    sv_id_policy_finalize.set_value(pls.ID_POLICY_FINALIZE_STRING)
    audit("Reset stored variables", from_console=True)


def generate_anonymisation_staging_db() -> None:
    db = pls.get_anonymisation_database()  # may raise
    ddfilename = pls.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE
    classes = get_all_task_classes()
    with codecs.open(ddfilename, mode="w", encoding="utf8") as f:
        written_header = False
        for cls in classes:
            if cls.is_anonymous:
                continue
            # Drop, make and populate tables
            cls.make_cris_tables(db)
            # Add info to data dictionary
            rows = cls.get_cris_dd_rows()
            if not rows:
                continue
            if not written_header:
                f.write(get_tsv_header_from_dict(rows[0]) + "\n")
                written_header = True
            for r in rows:
                f.write(get_tsv_line_from_dict(r) + "\n")
    db.commit()
    print("Draft data dictionary written to {}".format(ddfilename))


def make_superuser() -> None:
    """Make a superuser from the command line."""
    print("MAKE SUPERUSER")
    username = ask_user("New superuser")
    if user_exists(username):
        print("... user already exists!")
        return
    password1 = ask_user_password("New superuser password")
    password2 = ask_user_password("New superuser password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = create_superuser(username, password1)
    print("Success: " + str(result))


def reset_password() -> None:
    """Reset a password from the command line."""
    print("RESET PASSWORD")
    username = ask_user("Username")
    if not user_exists(username):
        print("... user doesn't exist!")
        return
    password1 = ask_user_password("New password")
    password2 = ask_user_password("New password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    req = command_line_request()
    result = set_password_directly(req, username, password1)
    print("Success: " + str(result))


def enable_user_cli() -> None:
    """Re-enable a locked user account from the command line."""
    print("ENABLE LOCKED USER ACCOUNT")
    username = ask_user("Username")
    if not user_exists(username):
        print("... user doesn't exist!")
        return
    enable_user(username)
    print("Enabled.")


# -----------------------------------------------------------------------------
# Test rig
# -----------------------------------------------------------------------------

def test() -> None:
    """Run all unit tests."""
    # We do some rollbacks so as not to break performance of ongoing tasks.

    req = command_line_request()

    print("-- Ensuring all tasks have basic info")
    cctask_unit_tests_basic()
    pls.db.rollback()

    print("-- Testing camcopswebview")
    webview_unit_tests()
    pls.db.rollback()

    print("-- Testing cc_analytics")
    ccanalytics_unit_tests(req)
    pls.db.rollback()

    print("-- Testing cc_blob")
    ccblob_unit_tests(req)
    pls.db.rollback()

    # cc_constants: no functions

    print("-- Testing cc_device")
    ccdevice_unit_tests(req.dbsession)
    pls.db.rollback()

    print("-- Testing cc_dump")
    ccdump_unit_tests()
    pls.db.rollback()

    print("-- Testing cc_hl7core")
    cchl7core_unit_tests(req.dbsession)
    pls.db.rollback()

    # cc_namedtuples: simple, and doesn't need cc_shared

    print("-- Testing cc_patient")
    ccpatient_unit_tests(req)
    pls.db.rollback()

    print("-- Testing cc_policy")
    ccpolicy_unit_tests()
    pls.db.rollback()

    print("-- Testing cc_report")
    ccreport_unit_tests(req)
    pls.db.rollback()

    print("-- Testing cc_session")
    ccsession_unit_tests(req)
    pls.db.rollback()

    # at present only tested implicitly: cc_shared

    print("-- Testing cc_tracker")
    cctracker_unit_tests(req)
    pls.db.rollback()

    print("-- Testing cc_user")
    ccuser_unit_tests(req)
    pls.db.rollback()

    # cc_version: no functions

    # Done last (slowest)
    print("-- Testing cc_task")
    cctask_unit_tests()
    pls.db.rollback()


# =============================================================================
# Command-line processor
# =============================================================================

def cli_main() -> None:
    """
    Command-line entry point.
    """
    # Fetch command-line options.
    parser = argparse.ArgumentParser(
        prog="camcops",  # name the user will use to call it
        description=("CamCOPS command-line tool. "
                     "Run with no arguments for an interactive menu.")
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version="CamCOPS {}".format(CAMCOPS_SERVER_VERSION))
    parser.add_argument(
        "-m", "--maketables",
        action="store_true", default=False,
        help="Make/remake tables and views")
    parser.add_argument(
        "--dropsuperfluous", action="store_true",
        help="Additional option to --maketables to drop superfluous columns; "
        "requires both confirmatory flags as well")
    parser.add_argument(
        "--confirm_drop_superfluous_1", action="store_true",
        help="Confirmatory flag 1/2 for --dropsuperfluous")
    parser.add_argument(
        "--confirm_drop_superfluous_2", action="store_true",
        help="Confirmatory flag 2/2 for --dropsuperfluous")
    parser.add_argument(
        "-r", "--resetstoredvars", action="store_true", default=False,
        help="Redefine database title/patient ID number meanings/ID policy")
    parser.add_argument(
        "-t", "--title", action="store_true", default=False, dest="showtitle",
        help="Show database title")
    parser.add_argument(
        "-s", "--summarytables", action="store_true", default=False,
        help="Make summary tables")
    parser.add_argument(
        "-u", "--superuser", action="store_true", default=False,
        help="Make superuser")
    parser.add_argument(
        "-p", "--password", action="store_true", default=False,
        help="Reset a user's password")
    parser.add_argument(
        "-e", "--enableuser", action="store_true", default=False,
        help="Re-enable a locked user account")
    parser.add_argument(
        "-d", "--descriptions", action="store_true", default=False,
        help="Export table descriptions")
    parser.add_argument(
        "-7", "--hl7", action="store_true", default=False,
        help="Send pending HL7 messages and outbound files")
    parser.add_argument(
        "-q", "--queue", action="store_true", default=False,
        dest="show_hl7_queue",
        help="View outbound HL7/file queue (without sending)")
    parser.add_argument(
        "-y", "--anonstaging", action="store_true", default=False,
        help="Generate/regenerate anonymisation staging database")
    parser.add_argument(
        "-x", "--test", action="store_true", default=False,
        help="Test internal code")
    parser.add_argument(
        "--dbunittest", action="store_true", default=False,
        help="Unit tests for database code")
    parser.add_argument('--verbose', action='count', default=0,
                        help="Verbose startup")
    parser.add_argument(
        "configfilename", nargs="?", default=None,
        help=(
            "Configuration file. (When run in WSGI mode, this is read from "
            "the {ev} variable in (1) the WSGI environment, "
            "or (2) the operating system environment.)".format(
                ev=ENVVAR_CONFIG_FILE
            )
        ))
    args = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    loglevel = logging.DEBUG if args.verbose >= 1 else logging.INFO
    logging.getLogger().setLevel(loglevel)  # set level for root logger

    # Say hello
    log.info("CamCOPS version {}".format(CAMCOPS_SERVER_VERSION))
    log.info("By Rudolf Cardinal. See " + CAMCOPS_URL)

    # If we don't know the config filename yet, ask the user
    if not args.configfilename:
        args.configfilename = ask_user(
            "Configuration file",
            os.environ.get(ENVVAR_CONFIG_FILE, DEFAULT_CONFIG_FILENAME))
    # For command-line use, we want the the config filename in the environment:
    os.environ[ENVVAR_CONFIG_FILE] = args.configfilename
    log.info("Using configuration file: {}".format(args.configfilename))

    # Request objects are ubiquitous, and allow code to refer to the HTTP
    # request, config, HTTP session, database session, and so on. Here we make
    # a special sort of request for use from the command line.
    req = command_line_request()
    # Note also that any database accesses will be auto-committed via the
    # request.

    # In order:
    n_actions = 0

    if args.maketables:
        drop_superfluous_columns = False
        if (args.dropsuperfluous and args.confirm_drop_superfluous_1 and
                args.confirm_drop_superfluous_2):
            drop_superfluous_columns = True
        make_tables(drop_superfluous_columns)
        n_actions += 1

    if args.resetstoredvars:
        reset_storedvars()
        n_actions += 1

    if args.showtitle:
        print("Database title: {}".format(req.config.DATABASE_TITLE))
        n_actions += 1

    if args.summarytables:
        make_summary_tables()
        n_actions += 1

    if args.superuser:
        make_superuser()
        n_actions += 1

    if args.password:
        reset_password()
        n_actions += 1

    if args.descriptions:
        export_descriptions_comments()
        n_actions += 1

    if args.enableuser:
        enable_user_cli()
        n_actions += 1

    if args.hl7:
        send_all_pending_hl7_messages(req.config)
        n_actions += 1

    if args.show_hl7_queue:
        send_all_pending_hl7_messages(req.config, show_queue_only=True)
        n_actions += 1

    if args.anonstaging:
        generate_anonymisation_staging_db()
        n_actions += 1

    if args.test:
        test()
        n_actions += 1

    if args.dbunittest:
        database_unit_tests()
        n_actions += 1

    if n_actions > 0:
        sys.exit(0)
        # ... otherwise proceed to the menu

    # Menu
    while True:
        print("""
{sep}
CamCOPS version {version} (command line).
Using database: {dburl} ({dbtitle}).

1) Make/remake tables and views
   ... MUST be the first action on a new database
   ... will not destroy existing data
   ... also performs item 3 below
2) Show database title
3) Copy database title/patient ID number meanings/ID policy into database
4) Make summary tables
5) Make superuser
6) Reset a user's password
7) Enable a locked user account
8) Export table descriptions with field comments
9) Test internal code (should always succeed)
10) Send all pending HL7 messages
11) Show HL7 queue without sending
12) Regenerate anonymisation staging database
13) Drop all views and summary tables
14) Run test web server directly
15) Exit
""".format(sep=SEPARATOR_EQUALS,
           version=CAMCOPS_SERVER_VERSION,
           dburl=get_safe_url_from_session(req.dbsession),
           dbtitle=req.config.DATABASE_TITLE))

        # avoid input():
        # http://www.gossamer-threads.com/lists/python/python/46911
        choice = input("Choose: ")
        try:
            choice = int(choice)
        except ValueError:
            choice = None

        if choice == 1:
            make_tables(drop_superfluous_columns=False)
            reset_storedvars()
        elif choice == 2:
            print("Database title: {}".format(req.config.DATABASE_TITLE))
        elif choice == 3:
            reset_storedvars()
        elif choice == 4:
            make_summary_tables(from_console=True)
        elif choice == 5:
            make_superuser()
        elif choice == 6:
            reset_password()
        elif choice == 7:
            enable_user_cli()
        elif choice == 8:
            export_descriptions_comments()
        elif choice == 9:
            test()
        elif choice == 10:
            send_all_pending_hl7_messages(req.config)
        elif choice == 11:
            send_all_pending_hl7_messages(req.config, show_queue_only=True)
        elif choice == 12:
            generate_anonymisation_staging_db()
        elif choice == 13:
            drop_all_views_and_summary_tables()
        elif choice == 14:
            test_serve()
        elif choice == 15:
            sys.exit(0)

        # Must commit, or we may lock the database while watching the menu
        req.dbsession.commit()  # command-line interactive menu route commit


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == '__main__':
    cli_main()
