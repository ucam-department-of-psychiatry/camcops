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
import urllib.parse

from cardinal_pythonlib.argparse_func import ShowAllSubparserHelpAction  # nopep8
from cardinal_pythonlib.debugging import pdb_run
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
    print_report_on_all_logs,
    set_level_for_logger_and_its_handlers,
)

main_only_quicksetup_rootlogger(
    logging.DEBUG, with_process_id=True, with_thread_id=True
)
log = BraceStyleAdapter(logging.getLogger(__name__))
log.info("CamCOPS starting")

from argparse import ArgumentParser, RawDescriptionHelpFormatter  # nopep8
import codecs  # nopep8
import os  # nopep8
import sys  # nopep8
from typing import Optional, TYPE_CHECKING  # nopep8

import cherrypy  # nopep8
from pyramid.config import Configurator  # nopep8
from pyramid.router import Router  # nopep8
from wsgiref.simple_server import make_server  # nopep8

from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_session  # nopep8
from cardinal_pythonlib.ui import ask_user, ask_user_password  # nopep8

from .cc_modules.cc_alembic import (
    create_database_from_scratch,
    upgrade_database_to_head,
)  # nopep8
from .cc_modules.cc_audit import audit  # nopep8
from .cc_modules.cc_baseconstants import ENVVAR_CONFIG_FILE, STATIC_ROOT_DIR  # nopep8
from .cc_modules.cc_config import (
    get_default_config_from_os_env,  # nopep8
    get_demo_config,
)
from .cc_modules.cc_constants import (
    CAMCOPS_URL,
    DEMO_SUPERVISORD_CONF,
    SEPARATOR_EQUALS,
)  # nopep8
from .cc_modules.cc_blob import ccblob_unit_tests  # nopep8
from .cc_modules.cc_device import ccdevice_unit_tests  # nopep8
from .cc_modules.cc_hl7 import send_all_pending_hl7_messages  # nopep8
from .cc_modules.cc_hl7core import cchl7core_unit_tests  # nopep8
from .cc_modules.cc_patient import ccpatient_unit_tests  # nopep8
from .cc_modules.cc_pyramid import (
    CamcopsAuthenticationPolicy,
    CamcopsAuthorizationPolicy,
    camcops_add_mako_renderer,
    get_session_factory,
    Permission,
    RouteCollection,
)  # nopep8
from .cc_modules.cc_policy import ccpolicy_unit_tests  # nopep8
from .cc_modules.cc_report import ccreport_unit_tests  # nopep8
from .cc_modules.cc_request import CamcopsRequest, command_line_request  # nopep8
from .cc_modules.cc_session import ccsession_unit_tests  # nopep8
from .cc_modules.cc_serversettings import ServerSettings  # nopep8
from .cc_modules.cc_task import (
    cctask_unit_tests,
    cctask_unit_tests_basic,
    Task,
)  # nopep8
from .cc_modules.cc_tracker import cctracker_unit_tests  # imports matplotlib; SLOW  # nopep8
from .cc_modules.cc_user import ccuser_unit_tests  # nopep8
from .cc_modules.cc_user import set_password_directly, User  # nopep8
from .cc_modules.cc_version import CAMCOPS_SERVER_VERSION  # nopep8
from .cc_modules.client_api import database_unit_tests  # nopep8
from .cc_modules.merge_db import merge_camcops_db

log.debug("All imports complete")

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction

# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

# if sys.version_info[0] != 2 or sys.version_info[1] != 7:
#     # ... sys.version_info.major (etc.) require Python 2.7 in any case!
#     raise RuntimeError(
#         "CamCOPS needs Python 2.7, and this Python version is: "
#         + sys.version)

if sys.version_info[0] != 3:
    raise RuntimeError(
        "CamCOPS needs Python 3, and this Python version is: " + sys.version)

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_ADD_ROUTES = False
DEBUG_AUTHORIZATION = False
DEBUG_LOG_CONFIG = False
DEBUG_RUN_WITH_PDB = False

if (DEBUG_ADD_ROUTES or DEBUG_AUTHORIZATION or DEBUG_LOG_CONFIG or
        DEBUG_RUN_WITH_PDB):
    log.warning("Debugging options enabled!")

# =============================================================================
# Other constants
# =============================================================================

DEFAULT_CONFIG_FILENAME = "/etc/camcops/camcops.conf"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_URL_PATH_ROOT = '/'  # TODO: from config file?


# =============================================================================
# WSGI entry point
# =============================================================================

def make_wsgi_app(debug_toolbar: bool = False,
                  serve_static_files: bool = True) -> Router:
    """
    Makes and returns a WSGI application, attaching all our special methods.

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

    # See parameters above.

    # -------------------------------------------------------------------------
    # 1. Base app
    # -------------------------------------------------------------------------
    settings = {  # Settings that can't be set directly?
        'debug_authorization': DEBUG_AUTHORIZATION,
    }
    with Configurator(settings=settings) as config:
        # ---------------------------------------------------------------------
        # Authentication; authorizaion (permissions)
        # ---------------------------------------------------------------------
        authentication_policy = CamcopsAuthenticationPolicy()
        config.set_authentication_policy(authentication_policy)
        # Let's not use ACLAuthorizationPolicy, which checks an access control
        # list for a resource hierarchy of objects, but instead:
        authorization_policy = CamcopsAuthorizationPolicy()
        config.set_authorization_policy(authorization_policy)
        config.set_default_permission(Permission.HAPPY)
        # ... applies to all SUBSEQUENT view configuration registrations

        # ---------------------------------------------------------------------
        # Factories
        # ---------------------------------------------------------------------
        config.set_request_factory(CamcopsRequest)
        # ... for request attributes: config, database, etc.
        config.set_session_factory(get_session_factory())
        # ... for request.session

        camcops_add_mako_renderer(config, extension='.mako')

        # deform_bootstrap.includeme(config)

        # ---------------------------------------------------------------------
        # Routes and accompanying views
        # ---------------------------------------------------------------------

        # Add static views
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#serving-static-assets  # noqa
        if serve_static_files:
            config.add_static_view(name=RouteCollection.STATIC.route,
                                   path=STATIC_ROOT_DIR)

        config.add_static_view('deform_static', 'deform:static/')

        # Add all the routes:
        for pr in RouteCollection.all_routes():
            if DEBUG_ADD_ROUTES:
                log.info("{} -> {}", pr.route, pr.path)
            config.add_route(pr.route, pr.path)
        # See also:
        # https://stackoverflow.com/questions/19184612/how-to-ensure-urls-generated-by-pyramids-route-url-and-route-path-are-valid  # noqa

        # Most views are using @view_config() which calls add_view().
        # Scan for @view_config decorators, to map views to routes:
        # https://docs.pylonsproject.org/projects/venusian/en/latest/api.html
        config.scan("camcops_server.cc_modules")

        # ---------------------------------------------------------------------
        # Add tweens (inner to outer)
        # ---------------------------------------------------------------------
        # We will use implicit positioning:
        # - https://www.slideshare.net/aconrad/alex-conrad-pyramid-tweens-ploneconf-2011  # noqa

        # config.add_tween('camcops_server.camcops.http_session_tween_factory')

        # ---------------------------------------------------------------------
        # Debug toolbar
        # ---------------------------------------------------------------------
        if debug_toolbar:
            log.debug("Enabling Pyramid debug toolbar")
            config.include('pyramid_debugtoolbar')  # BEWARE! SIDE EFFECTS
            # ... Will trigger an import that hooks events into all
            # SQLAlchemy queries. There's a bug somewhere relating to that;
            # see notes below relating to the "mergedb" function.
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


def test_serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
               debug_toolbar: bool = True,
               serve_static_files: bool = True) -> None:
    application = make_wsgi_app(debug_toolbar=debug_toolbar,
                                serve_static_files=serve_static_files)
    server = make_server(host, port, application)
    log.info("Serving on host={}, port={}".format(host, port))
    server.serve_forever()


def start_server(host: str,
                 port: int,
                 unix_domain_socket_filename: str,
                 threads_start: int,
                 threads_max: int,  # -1 for no limit
                 server_name: str,
                 log_screen: bool,
                 ssl_certificate: Optional[str],
                 ssl_private_key: Optional[str],
                 root_path: str,
                 debug_toolbar: bool = False,
                 serve_static_files: bool = True) -> None:
    """
    Start CherryPy server
    """
    application = make_wsgi_app(debug_toolbar=debug_toolbar,
                                serve_static_files=serve_static_files)

    cherrypy.config.update({
        # See http://svn.cherrypy.org/trunk/cherrypy/_cpserver.py
        'server.socket_host': host,
        'server.socket_port': port,
        'server.socket_file': unix_domain_socket_filename,
        'server.thread_pool': threads_start,
        'server.thread_pool_max': threads_max,
        'server.server_name': server_name,
        'server.log_screen': log_screen,
    })
    if ssl_certificate and ssl_private_key:
        cherrypy.config.update({
            'server.ssl_module': 'builtin',
            'server.ssl_certificate': ssl_certificate,
            'server.ssl_private_key': ssl_private_key,
        })

    if unix_domain_socket_filename:
        # If this is specified, it takes priority
        log.info("Starting via UNIX domain socket at: {}",
                 unix_domain_socket_filename)
    else:
        log.info("Starting on host: {}", host)
        log.info("Starting on port: {}", port)
    log.info("CamCOPS will be at: {}", root_path)
    log.info("... webview at: {}",
             urllib.parse.urljoin(root_path, RouteCollection.HOME.path))
    log.info("... tablet client API at: {}",
             urllib.parse.urljoin(root_path, RouteCollection.CLIENT_API.path))
    log.info("Thread pool starting size: {}", threads_start)
    log.info("Thread pool max size: {}", threads_max)
    log.critical("boo! this is critical")

    cherrypy.tree.graft(application, root_path)

    try:
        # log.debug("cherrypy.server.thread_pool: {}",
        #           cherrypy.server.thread_pool)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()


# =============================================================================
# Command-line functions
# =============================================================================

def print_demo_config() -> None:
    demo_config = get_demo_config()
    print(demo_config)


def print_demo_supervisorconf() -> None:
    print(DEMO_SUPERVISORD_CONF)


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


def make_superuser(req: CamcopsRequest) -> None:
    """Make a superuser from the command line."""
    print("MAKE SUPERUSER")
    username = ask_user("New superuser")
    if User.user_exists(req, username):
        print("... user already exists!")
        return
    password1 = ask_user_password("New superuser password")
    password2 = ask_user_password("New superuser password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = User.create_superuser(req, username, password1)
    print("Success: " + str(result))


def reset_password(req: CamcopsRequest) -> None:
    """Reset a password from the command line."""
    print("RESET PASSWORD")
    username = ask_user("Username")
    if not User.user_exists(req, username):
        print("... user doesn't exist!")
        return
    password1 = ask_user_password("New password")
    password2 = ask_user_password("New password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = set_password_directly(req, username, password1)
    print("Success: " + str(result))


def enable_user_cli(req: CamcopsRequest) -> None:
    """Re-enable a locked user account from the command line."""
    print("ENABLE LOCKED USER ACCOUNT")
    username = ask_user("Username")
    if not User.user_exists(req, username):
        print("... user doesn't exist!")
        return
    User.enable_user(username)
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

def camcops_main() -> None:
    """
    Command-line entry point.
    """
    # Fetch command-line options.

    # -------------------------------------------------------------------------
    # Base parser
    # -------------------------------------------------------------------------

    parser = ArgumentParser(
        prog="camcops",  # name the user will use to call it
        description="CamCOPS server version {}, by Rudolf Cardinal.".format(
            CAMCOPS_SERVER_VERSION),
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False)
    parser.add_argument(
        '-h', '--help', action=ShowAllSubparserHelpAction,
        help='show this help message and exit')
    parser.add_argument(
        "-v", "--version", action="version",
        version="CamCOPS {}".format(CAMCOPS_SERVER_VERSION))

    # -------------------------------------------------------------------------
    # argparse code
    # -------------------------------------------------------------------------

    _reqnamed = 'required named arguments'

    def add_sub(sp: "_SubParsersAction", cmd: str,
                config_mandatory: Optional[bool] = False,
                help: str = None,
                give_config_wsgi_help: bool = False) -> ArgumentParser:
        """
        config_mandatory:
            None = don't ask for config
            False = ask for it, but not mandatory
            True = mandatory
        """
        subparser = sp.add_parser(
            cmd, help=help,
            formatter_class=RawDescriptionHelpFormatter
        )  # type: ArgumentParser
        subparser.add_argument(
            '--verbose', action='count', default=0,
            help="Be verbose")
        if give_config_wsgi_help:
            cfg_help = (
                "Configuration file. (When run in WSGI mode, this is read "
                "from the {ev} variable in (1) the WSGI environment, "
                "or (2) the operating system environment.)".format(
                    ev=ENVVAR_CONFIG_FILE))
        else:
            cfg_help = "Configuration file"
        if config_mandatory is None:
            pass
        elif config_mandatory:
            g = subparser.add_argument_group(_reqnamed)
            # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments  # noqa
            g.add_argument("--config", required=True, help=cfg_help)
        else:
            subparser.add_argument("--config", help=cfg_help)
        return subparser

    def add_req_named(sp: ArgumentParser, switch: str, help: str,
                      action: str = None) -> None:
        # noinspection PyProtectedMember
        reqgroup = next((g for g in sp._action_groups
                         if g.title == _reqnamed), None)
        if not reqgroup:
            reqgroup = sp.add_argument_group(_reqnamed)
        reqgroup.add_argument(switch, required=True, action=action, help=help)

    # -------------------------------------------------------------------------
    # Subcommand subparser
    # -------------------------------------------------------------------------

    subparsers = parser.add_subparsers(help='Specify one sub-command')  # type: _SubParsersAction  # noqa

    # You can't use "add_subparsers" more than once.
    # Subparser groups seem not yet to be supported:
    #   https://bugs.python.org/issue9341
    #   https://bugs.python.org/issue14037

    # -------------------------------------------------------------------------
    # Getting started commands
    # -------------------------------------------------------------------------

    democonfig_parser = add_sub(
        subparsers, "democonfig", config_mandatory=None,
        help="Print a demo CamCOPS config file")
    democonfig_parser.set_defaults(func=lambda args: print_demo_config())

    demosupervisorconf_parser = add_sub(
        subparsers, "demosupervisorconf", config_mandatory=None,
        help="Print a demo 'supervisor' config file for CamCOPS")
    demosupervisorconf_parser.set_defaults(
        func=lambda args: print_demo_supervisorconf())

    # -------------------------------------------------------------------------
    # Database commands
    # -------------------------------------------------------------------------

    upgradedb_parser = add_sub(
        subparsers, "upgradedb", config_mandatory=True,
        help="Upgrade database to most recent version (via Alembic)")
    upgradedb_parser.set_defaults(func=None)

    showtitle_parser = add_sub(
        subparsers, "showtitle",
        help="Show database title")
    showtitle_parser.set_defaults(func=None)

    mergedb_parser = add_sub(
        subparsers, "mergedb", config_mandatory=True,
        help="Merge in data from an old or recent CamCOPS database")
    mergedb_parser.add_argument(
        '--report_every', type=int, default=10000,
        help="Report progress every n rows")
    mergedb_parser.add_argument(
        '--echo', action="store_true",
        help="Echo SQL to source database")
    mergedb_parser.add_argument(
        '--dummy_run', action="store_true",
        help="Perform a dummy run only; do not alter destination database")
    mergedb_parser.add_argument(
        '--info_only', action="store_true",
        help="Show table information only; don't do any work")
    mergedb_parser.add_argument(
        '--skip_hl7_logs', action="store_true",
        help="Skip the HL7 message log table")
    mergedb_parser.add_argument(
        '--skip_audit_logs', action="store_true",
        help="Skip the audit log table")
    mergedb_parser.add_argument(
        '--default_group_id', type=int, default=None,
        help="Default group ID (integer) to apply to old records without one. "
             "If none is specified, a new group will be created for such "
             "records.")
    mergedb_parser.add_argument(
        '--default_group_name', type=str, default=None,
        help="If default_group_id is not specified, use this group name. The "
             "group will be looked up if it exists, and created if not.")
    add_req_named(
        mergedb_parser,
        "--src",
        help="Source database (specified as an SQLAlchemy URL). The contents "
             "of this database will be merged into the database specified "
             "in the config file.")
    mergedb_parser.set_defaults(func=lambda args: merge_camcops_db(
        src=args.src,
        echo=args.echo,
        report_every=args.report_every,
        dummy_run=args.dummy_run,
        info_only=args.info_only,
        skip_hl7_logs=args.skip_hl7_logs,
        skip_audit_logs=args.skip_audit_logs,
        default_group_id=args.default_group_id,
        default_group_name=args.default_group_name,
    ))
    # WATCH OUT. There appears to be a bug somewhere in the way that the
    # Pyramid debug toolbar registers itself with SQLAlchemy (see
    # pyramid_debugtoolbar/panels/sqla.py; look for "before_cursor_execute"
    # and "after_cursor_execute". Somehow, some connections (but not all) seem
    # to get this event registered twice. The upshot is that the sequence can
    # lead to an attempt to double-delete the debug toolbar's timer:
    #
    # _before_cursor_execute: <sqlalchemy.engine.base.Connection object at 0x7f5c1fa7c630>, 'SHOW CREATE TABLE `_hl7_run_log`', ()  # noqa
    # _before_cursor_execute: <sqlalchemy.engine.base.Connection object at 0x7f5c1fa7c630>, 'SHOW CREATE TABLE `_hl7_run_log`', ()  # noqa
    #       ^^^ this is the problem: event called twice
    # _after_cursor_execute: <sqlalchemy.engine.base.Connection object at 0x7f5c1fa7c630>, 'SHOW CREATE TABLE `_hl7_run_log`', ()  # noqa
    # _after_cursor_execute: <sqlalchemy.engine.base.Connection object at 0x7f5c1fa7c630>, 'SHOW CREATE TABLE `_hl7_run_log`', ()  # noqa
    #       ^^^ and this is where the problem becomes evident
    # Traceback (most recent call last):
    # ...
    #   File "/home/rudolf/dev/venvs/camcops/lib/python3.5/site-packages/pyramid_debugtoolbar/panels/sqla.py", line 51, in _after_cursor_execute  # noqa
    #     delattr(conn, 'pdtb_start_timer')
    # AttributeError: pdtb_start_timer
    #
    # So the simplest thing is only to register the debug toolbar for stuff
    # that might need it...

    createdb_parser = add_sub(
        subparsers, "createdb", config_mandatory=True,
        help="Create CamCOPS database from scratch (AVOID; use the upgrade "
             "facility instead)")
    add_req_named(
        createdb_parser,
        '--confirm_create_db', action="store_true",
        help="Must specify this too, as a safety measure")

    def _create_db(args):
        cfg = get_default_config_from_os_env()
        create_database_from_scratch(cfg)

    createdb_parser.set_defaults(func=_create_db)

    # db_group.add_argument(
    #     "-s", "--summarytables", action="store_true", default=False,
    #     help="Make summary tables")

    # -------------------------------------------------------------------------
    # User commands
    # -------------------------------------------------------------------------

    superuser_parser = add_sub(
        subparsers, "superuser",
        help="Make superuser")
    superuser_parser.set_defaults(func=None)

    password_parser = add_sub(
        subparsers, "password",
        help="Reset a user's password")
    password_parser.set_defaults(func=None)

    enableuser_parser = add_sub(
        subparsers, "enableuser",
        help="Re-enable a locked user account")
    enableuser_parser.set_defaults(func=None)

    # -------------------------------------------------------------------------
    # Export options
    # -------------------------------------------------------------------------

    descriptions_parser = add_sub(
        subparsers, "descriptions",
        help="Export table descriptions")
    descriptions_parser.set_defaults(func=None)

    hl7_parser = add_sub(
        subparsers, "hl7",
        help="Send pending HL7 messages and outbound files")
    hl7_parser.set_defaults(func=None)

    showhl7queue_parser = add_sub(
        subparsers, "show_hl7_queue",
        help="View outbound HL7/file queue (without sending)")
    showhl7queue_parser.set_defaults(func=None)

    # export_group.add_argument(
    #     "-y", "--anonstaging", action="store_true", default=False,
    #     help="Generate/regenerate anonymisation staging database")

    # -------------------------------------------------------------------------
    # Test options
    # -------------------------------------------------------------------------

    unittest_parser = add_sub(
        subparsers, "unittest", config_mandatory=None,
        help="Test internal code")
    unittest_parser.set_defaults(func=None)

    testserve_parser = add_sub(
        subparsers, "testserve",
        help="Test web server (single-thread, single-process, HTTP-only, "
             "Pyramid; for development use only")
    testserve_parser.add_argument(
        '--host', type=str, default=DEFAULT_HOST,
        help="hostname to listen on")
    testserve_parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help="port to listen on")
    testserve_parser.add_argument(
        '--debug_toolbar', action="store_true",
        help="Enable the Pyramid debug toolbar"
    )
    testserve_parser.set_defaults(func=lambda args: test_serve(
        host=args.host,
        port=args.port,
        debug_toolbar=args.debug_toolbar
    ))

    # *** add unit test

    # -------------------------------------------------------------------------
    # Web server options
    # -------------------------------------------------------------------------

    serve_parser = add_sub(
        subparsers, "serve",
        help="Start web server (via CherryPy)")
    serve_parser.add_argument(
        "--serve", action="store_true",
        help="")
    serve_parser.add_argument(
        '--host', type=str, default=DEFAULT_HOST,
        help="hostname to listen on")
    serve_parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help="port to listen on")
    serve_parser.add_argument(
        '--unix_domain_socket', type=str, default="",
        help="UNIX domain socket to listen on (overrides host/port if "
             "specified)")
    serve_parser.add_argument(
        "--server_name", type=str, default="localhost",
        help="CherryPy's SERVER_NAME environ entry")
    serve_parser.add_argument(
        "--threads_start", type=int, default=10,
        help="Number of threads for server to start with")
    serve_parser.add_argument(
        "--threads_max", type=int, default=-1,
        help="Maximum number of threads for server to use (-1 for no limit)")
    serve_parser.add_argument(
        "--ssl_certificate", type=str,
        help="SSL certificate file "
             "(e.g. /etc/ssl/certs/ssl-cert-snakeoil.pem)")
    serve_parser.add_argument(
        "--ssl_private_key", type=str,
        help="SSL private key file "
             "(e.g. /etc/ssl/private/ssl-cert-snakeoil.key)")
    serve_parser.add_argument(
        "--log_screen", dest="log_screen", action="store_true",
        help="log access requests etc. to terminal (default)")
    serve_parser.add_argument(
        "--no_log_screen", dest="log_screen", action="store_false",
        help="don't log access requests etc. to terminal")
    serve_parser.set_defaults(log_screen=True)
    serve_parser.add_argument(
        "--debug_static", action="store_true",
        help="show debug info for static file requests")
    serve_parser.add_argument(
        "--root_path", type=str, default=DEFAULT_URL_PATH_ROOT,
        help="Root path to serve CRATE at. Default: {}".format(
            DEFAULT_URL_PATH_ROOT))
    serve_parser.add_argument(
        '--debug_toolbar', action="store_true",
        help="Enable the Pyramid debug toolbar"
    )
    serve_parser.set_defaults(func=lambda args: start_server(
        host=args.host,
        port=args.port,
        threads_start=args.threads_start,
        threads_max=args.threads_max,
        unix_domain_socket_filename=args.unix_domain_socket,
        server_name=args.server_name,
        log_screen=args.log_screen,
        ssl_certificate=args.ssl_certificate,
        ssl_private_key=args.ssl_private_key,
        root_path=args.root_path,
        debug_toolbar=args.debug_toolbar
    ))

    # -------------------------------------------------------------------------
    # OK; parse the arguments
    # -------------------------------------------------------------------------

    progargs = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    loglevel = logging.DEBUG if progargs.verbose >= 1 else logging.INFO
    rootlogger = logging.getLogger()
    set_level_for_logger_and_its_handlers(rootlogger, loglevel)

    # Say hello
    log.info("CamCOPS server version {}", CAMCOPS_SERVER_VERSION)
    log.info("By Rudolf Cardinal. See {}", CAMCOPS_URL)
    log.info("Using {} tasks", len(Task.all_subclasses_by_tablename()))
    log.debug("Command-line arguments: {!r}", progargs)

    if DEBUG_LOG_CONFIG:
        print_report_on_all_logs()

    # Finalize the config filename
    if hasattr(progargs, 'config') and progargs.config:
        # We want the the config filename in the environment from now on:
        os.environ[ENVVAR_CONFIG_FILE] = progargs.config
    cfg_name = os.environ.get(ENVVAR_CONFIG_FILE, None)
    log.info("Using configuration file: {!r}", cfg_name)

    progargs.func(progargs)
    sys.exit(0)

    raise NotImplementedError("Bugs below here!")

    # -------------------------------------------------------------------------
    # Subsequent actions require a command-line request.
    # -------------------------------------------------------------------------
    # Request objects are ubiquitous, and allow code to refer to the HTTP
    # request, config, HTTP session, database session, and so on. Here we make
    # a special sort of request for use from the command line.
    req = command_line_request()
    # Note also that any database accesses will be auto-committed via the
    # request.

    if progargs.upgradedb:
        upgrade_database_to_head()
        n_actions += 1

    if progargs.showtitle:
        print("Database title: {}".format(req.config.database_title))
        n_actions += 1

    if progargs.summarytables:
        make_summary_tables()
        n_actions += 1

    if progargs.superuser:
        make_superuser(req)
        n_actions += 1

    if progargs.password:
        reset_password(req)
        n_actions += 1

    if progargs.enableuser:
        enable_user_cli(req)
        n_actions += 1

    if progargs.hl7:
        send_all_pending_hl7_messages(req.config)
        n_actions += 1

    if progargs.show_hl7_queue:
        send_all_pending_hl7_messages(req.config, show_queue_only=True)
        n_actions += 1

    if progargs.anonstaging:
        generate_anonymisation_staging_db()
        n_actions += 1

    if progargs.test:
        test(req)
        n_actions += 1

    if progargs.dbunittest:
        database_unit_tests()
        n_actions += 1

    if progargs.testserve:
        test_serve()
        n_actions += 1

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
           dbtitle=req.config.database_title))

        # avoid input():
        # http://www.gossamer-threads.com/lists/python/python/46911
        choice = input("Choose: ")
        try:
            choice = int(choice)
        except ValueError:
            choice = None

        if choice == 1:
            upgrade_database_to_head()
            reset_storedvars()
        elif choice == 2:
            print("Database title: {}".format(req.config.database_title))
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

def main():
    if DEBUG_RUN_WITH_PDB:
        pdb_run(camcops_main)
    else:
        camcops_main()


if __name__ == '__main__':
    main()
