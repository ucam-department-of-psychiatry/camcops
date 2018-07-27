#!/usr/bin/env python
# camcops_server/camcops.py

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

# SET UP LOGGING BEFORE WE IMPORT CAMCOPS MODULES, allowing them to log during
# imports (see e.g. cc_plot).
# Currently sets up colour logging even if under WSGI environment. This is fine
# for gunicorn from the command line; I'm less clear about whether the disk
# logs look polluted by ANSI codes; needs checking.
import logging
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
    print_report_on_all_logs,
    set_level_for_logger_and_its_handlers,
)
main_only_quicksetup_rootlogger(
    logging.INFO, with_process_id=True, with_thread_id=True
)
log = BraceStyleAdapter(logging.getLogger(__name__))
log.info("CamCOPS starting")

# Main imports

from argparse import (
    ArgumentParser,
    ArgumentDefaultsHelpFormatter,
    Namespace,
    RawDescriptionHelpFormatter,
)  # nopep8
import codecs  # nopep8
import os  # nopep8
import multiprocessing  # nopep8
# from pprint import pformat  # nopep8
import sys  # nopep8
import tempfile  # nopep8
from typing import Any, Dict, Optional, TYPE_CHECKING  # nopep8
import unittest  # nopep8

import cherrypy  # nopep8
try:
    from gunicorn.app.base import BaseApplication
except ImportError:
    BaseApplication = None  # e.g. on Windows: "ImportError: no module named 'fcntl'".  # noqa
from pyramid.router import Router  # nopep8
from wsgiref.simple_server import make_server  # nopep8

from cardinal_pythonlib.argparse_func import ShowAllSubparserHelpAction  # nopep8
from cardinal_pythonlib.classes import gen_all_subclasses  # nopep8
from cardinal_pythonlib.debugging import pdb_run  # nopep8
from cardinal_pythonlib.process import launch_external_file  # nopep8
from cardinal_pythonlib.ui import ask_user, ask_user_password  # nopep8
from cardinal_pythonlib.sqlalchemy.dialect import (
    ALL_SQLA_DIALECTS,
    SqlaDialectName,
)  # nopep8
from cardinal_pythonlib.wsgi.constants import WsgiEnvVar  # nopep8
from cardinal_pythonlib.wsgi.reverse_proxied_mw import (
    ReverseProxiedConfig,
    ReverseProxiedMiddleware,
)  # nopep8

# Import this one early:
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa

from camcops_server.cc_modules.cc_alembic import (
    create_database_from_scratch,
    upgrade_database_to_head,
)  # nopep8
from camcops_server.cc_modules.cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    DOCUMENTATION_INDEX_FILENAME,
)  # nopep8
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.client_api  # import side effects (register unit test)  # nopep8
from camcops_server.cc_modules.cc_config import (
    get_default_config_from_os_env,  # nopep8
    get_demo_apache_config,
    get_demo_config,
    get_demo_mysql_create_db,
    get_demo_mysql_dump_script,
    get_demo_supervisor_config,
)
from camcops_server.cc_modules.cc_constants import (
    CAMCOPS_URL,
    MINIMUM_PASSWORD_LENGTH,
    USER_NAME_FOR_SYSTEM,
)  # nopep8
from camcops_server.cc_modules.cc_hl7 import send_all_pending_hl7_messages  # nopep8
from camcops_server.cc_modules.cc_pyramid import RouteCollection  # nopep8
from camcops_server.cc_modules.cc_request import (
    CamcopsRequest,
    command_line_request_context,
    pyramid_configurator_context,
)  # nopep8
from camcops_server.cc_modules.cc_sqlalchemy import get_all_ddl  # nopep8
from camcops_server.cc_modules.cc_task import Task  # nopep8
from camcops_server.cc_modules.cc_unittest import (
    DemoDatabaseTestCase,
    DemoRequestTestCase,
    ExtendedTestCase,
)  # nopep8
from camcops_server.cc_modules.cc_user import (
    SecurityLoginFailure,
    set_password_directly,
    User,
)  # nopep8
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION  # nopep8
from camcops_server.cc_modules.merge_db import merge_camcops_db  # nopep8

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

DEBUG_LOG_CONFIG = False
DEBUG_RUN_WITH_PDB = False

if DEBUG_LOG_CONFIG or DEBUG_RUN_WITH_PDB:
    log.warning("Debugging options enabled!")

# =============================================================================
# Other constants
# =============================================================================

DEFAULT_CONFIG_FILENAME = "/etc/camcops/camcops.conf"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_MAX_THREADS = 100
# ... beware the default MySQL connection limit of 151;
#     https://dev.mysql.com/doc/refman/5.7/en/too-many-connections.html
DEFAULT_PORT = 8000
URL_PATH_ROOT = '/'


# =============================================================================
# WSGI entry point
# =============================================================================

def ensure_database_is_ok() -> None:
    config = get_default_config_from_os_env()
    config.assert_database_ok()


def make_wsgi_app(debug_toolbar: bool = False,
                  reverse_proxied_config: ReverseProxiedConfig = None,
                  debug_reverse_proxy: bool = False) -> Router:
    """
    Makes and returns a WSGI application, attaching all our special methods.

    QUESTION: how do we access the WSGI environment (passed to the WSGI app)
    from within a Pyramid request?
    ANSWER:

    .. code-block:: none

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

    # Make app
    with pyramid_configurator_context(debug_toolbar=debug_toolbar) as config:
        app = config.make_wsgi_app()

    # Middleware above the Pyramid level
    if reverse_proxied_config and reverse_proxied_config.necessary():
        app = ReverseProxiedMiddleware(app=app,
                                       config=reverse_proxied_config,
                                       debug=debug_reverse_proxy)

    log.debug("WSGI app created")
    return app


def make_wsgi_app_from_argparse_args(args: Namespace) -> Router:
    # ... matches add_wsgi_options()
    reverse_proxied_config = ReverseProxiedConfig(
        trusted_proxy_headers=args.trusted_proxy_headers,
        http_host=args.proxy_http_host,
        remote_addr=args.proxy_remote_addr,
        script_name=(
            args.proxy_script_name or
            os.environ.get(WsgiEnvVar.SCRIPT_NAME, "")
        ),
        server_port=args.proxy_server_port,
        server_name=args.proxy_server_name,
        url_scheme=args.proxy_url_scheme,
        rewrite_path_info=args.proxy_rewrite_path_info,
    )
    return make_wsgi_app(debug_toolbar=args.debug_toolbar,
                         reverse_proxied_config=reverse_proxied_config,
                         debug_reverse_proxy=args.debug_reverse_proxy)


def test_serve_pyramid(application: Router,
                       host: str = DEFAULT_HOST,
                       port: int = DEFAULT_PORT) -> None:
    ensure_database_is_ok()
    server = make_server(host, port, application)
    log.info("Serving on host={}, port={}".format(host, port))
    server.serve_forever()


def join_url_fragments(*fragments: str) -> str:
    # urllib.parse.urljoin doesn't do what we want
    newfrags = [f[1:] if f.startswith("/") else f for f in fragments]
    return "/".join(newfrags)


def serve_cherrypy(application: Router,
                   host: str,
                   port: int,
                   unix_domain_socket_filename: str,
                   threads_start: int,
                   threads_max: int,  # -1 for no limit
                   server_name: str,
                   log_screen: bool,
                   ssl_certificate: Optional[str],
                   ssl_private_key: Optional[str],
                   root_path: str) -> None:
    """
    Start CherryPy server
    - Multithreading.
    - Any platform.
    """
    ensure_database_is_ok()

    # Report on options
    if unix_domain_socket_filename:
        # If this is specified, it takes priority
        log.info("Starting CherryPy server via UNIX domain socket at: {}",
                 unix_domain_socket_filename)
    else:
        log.info("Starting CherryPy server on host {}, port {}", host, port)
    log.info("Within this web server instance, CamCOPS will be at: {}",
             root_path)
    log.info(
        "... webview at: {}",
        # urllib.parse.urljoin is useless for this
        join_url_fragments(root_path, RouteCollection.HOME.path))
    log.info(
        "... tablet client API at: {}",
        join_url_fragments(root_path, RouteCollection.CLIENT_API.path))
    log.info("Thread pool starting size: {}", threads_start)
    log.info("Thread pool max size: {}", threads_max)

    # Set up CherryPy
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

    # Mount WSGI application
    cherrypy.tree.graft(application, root_path)

    # Start server
    try:
        # log.debug("cherrypy.server.thread_pool: {}",
        #           cherrypy.server.thread_pool)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()


def serve_gunicorn(application: Router,
                   host: str,
                   port: int,
                   unix_domain_socket_filename: str,
                   num_workers: int,
                   ssl_certificate: Optional[str],
                   ssl_private_key: Optional[str],
                   reload: bool = False,
                   timeout_s: int = 30,
                   debug_show_gunicorn_options: bool = False) -> None:
    """
    Start Gunicorn server

    - Multiprocessing; this is a Good Thing particularly in Python; see e.g.
      https://eli.thegreenplace.net/2012/01/16/python-parallelizing-cpu-bound-tasks-with-multiprocessing/  # noqa
      http://www.dabeaz.com/python/UnderstandingGIL.pdf

    - UNIX only.

    - The Pyramid debug toolbar detects a multiprocessing web server and says
      "shan't, because I use global state".
    """
    if BaseApplication is None:
        raise RuntimeError("Gunicorn does not run under Windows. "
                           "(It relies on the UNIX fork() facility.)")

    ensure_database_is_ok()

    # Report on options, and calculate Gunicorn versions
    if unix_domain_socket_filename:
        # If this is specified, it takes priority
        log.info("Starting Gunicorn server via UNIX domain socket at: {}",
                 unix_domain_socket_filename)
        bind = "unix:" + unix_domain_socket_filename
    else:
        log.info("Starting Gunicorn server on host {}, port {}", host, port)
        bind = "{}:{}".format(host, port)
    log.info("... using {} workers", num_workers)

    # We encapsulate this class definition in the function, since it inherits
    # from a class whose import will crash under Windows.

    # http://docs.gunicorn.org/en/stable/custom.html

    class StandaloneApplication(BaseApplication):
        def __init__(self,
                     app_: Router,
                     options: Dict[str, Any] = None,
                     debug_show_known_settings: bool = False) -> None:
            self.options = options or {}  # type: Dict[str, Any]
            self.application = app_
            super().__init__()
            if debug_show_known_settings:
                # log.info("Gunicorn settings:\n{}", pformat(self.cfg.settings))
                # ... which basically tells us to look in gunicorn/config.py
                # at every class that inherits from Setting.
                # Each has helpful documentation, as follows:
                possible_keys = sorted(self.cfg.settings.keys())
                for k in possible_keys:
                    v = self.cfg.settings[k]
                    log.info("{}:\n{}", k, v.desc)

        def load_config(self):
            # The Gunicorn example looks somewhat convoluted! Let's be simpler:
            for key, value in self.options.items():
                key_lower = key.lower()
                if key_lower in self.cfg.settings and value is not None:
                    self.cfg.set(key_lower, value)

        def load(self):
            return self.application

    opts = {
        'bind': bind,
        'certfile': ssl_certificate,
        'keyfile': ssl_private_key,
        'reload': reload,
        'timeout': timeout_s,
        'workers': num_workers,
    }
    app = StandaloneApplication(
        application, opts,
        debug_show_known_settings=debug_show_gunicorn_options)
    app.run()


# =============================================================================
# Command-line functions
# =============================================================================

def launch_manual() -> None:
    launch_external_file(DOCUMENTATION_INDEX_FILENAME)


def print_demo_camcops_config() -> None:
    print(get_demo_config())


def print_demo_supervisor_config() -> None:
    print(get_demo_supervisor_config())


def print_demo_apache_config() -> None:
    print(get_demo_apache_config())


def print_demo_mysql_create_db() -> None:
    print(get_demo_mysql_create_db())


def print_demo_mysql_dump_script() -> None:
    print(get_demo_mysql_dump_script())


def print_database_title() -> None:
    with command_line_request_context() as req:
        print(req.database_title)


def generate_anonymisation_staging_db() -> None:
    # generate_anonymisation_staging_db: *** BROKEN; REPLACE
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
    log.info("Draft data dictionary written to {}".format(ddfilename))


def get_username_from_cli(req: CamcopsRequest,
                          prompt: str,
                          starting_username: str = "",
                          must_exist: bool = False,
                          must_not_exist: bool = False) -> str:
    assert not (must_exist and must_not_exist)
    first = True
    while True:
        if first:
            username = starting_username
            first = False
        else:
            username = ""
        username = username or ask_user(prompt)
        exists = User.user_exists(req, username)
        if must_not_exist and exists:
            log.error("... user already exists!")
            continue
        if must_exist and not exists:
            log.error("... no such user!")
            continue
        if username == USER_NAME_FOR_SYSTEM:
            log.error("... username {!r} is reserved".format(
                USER_NAME_FOR_SYSTEM))
            continue
        return username


def get_new_password_from_cli(username: str) -> str:
    while True:
        password1 = ask_user_password("New password for user "
                                      "{}".format(username))
        if not password1 or len(password1) < MINIMUM_PASSWORD_LENGTH:
            log.error("... passwords can't be blank or shorter than {} "
                      "characters".format(MINIMUM_PASSWORD_LENGTH))
            continue
        password2 = ask_user_password("New password for user {} "
                                      "(again)".format(username))
        if password1 != password2:
            log.error("... passwords don't match; try again")
            continue
        return password1


def make_superuser(username: str = None) -> bool:
    """
    Make a superuser from the command line.
    """
    with command_line_request_context() as req:
        username = get_username_from_cli(
            req=req,
            prompt="Username for new superuser (or to gain superuser status)",
            starting_username=username,
        )
        existing_user = User.get_user_by_name(req.dbsession, username)
        if existing_user:
            log.info("Giving superuser status to {!r}".format(username))
            existing_user.superuser = True
            success = True
        else:
            log.info("Creating superuser {!r}".format(username))
            password = get_new_password_from_cli(username=username)
            success = User.create_superuser(req, username, password)
        if success:
            log.info("Success")
            return True
        else:
            log.critical("Failed to create superuser")
            return False


def reset_password(username: str = None) -> bool:
    """
    Reset a password from the command line.
    """
    with command_line_request_context() as req:
        username = get_username_from_cli(
            req=req,
            prompt="Username to reset password for",
            starting_username=username,
            must_exist=True,
        )
        log.info("Resetting password for user {!r}".format(username))
        password = get_new_password_from_cli(username)
        success = set_password_directly(req, username, password)
        if success:
            log.info("Success")
        else:
            log.critical("Failure")
        return success


def enable_user_cli(username: str = None) -> bool:
    """
    Re-enable a locked user account from the command line.
    """
    with command_line_request_context() as req:
        if username is None:
            username = get_username_from_cli(
                req=req,
                prompt="Username to unlock",
                must_exist=True,
            )
        else:
            if not User.user_exists(req, username):
                log.critical("No such user: {!r}".format(username))
                return False
        SecurityLoginFailure.enable_user(req, username)
        log.info("Enabled.")
        return True


def send_hl7(show_queue_only: bool) -> None:
    with command_line_request_context() as req:
        send_all_pending_hl7_messages(req.config,
                                      show_queue_only=show_queue_only)


# -----------------------------------------------------------------------------
# Test rig
# -----------------------------------------------------------------------------

def self_test(show_only: bool = False) -> None:
    """
    Run all unit tests.
    """

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpconfigfilename = os.path.join(tmpdirname, "dummy_config.conf")
        configtext = get_demo_config()
        with open(tmpconfigfilename, "w") as file:
            file.write(configtext)
        # First, for safety:
        os.environ[ENVVAR_CONFIG_FILE] = tmpconfigfilename
        # ... we're going to be using a test (SQLite) database, but we want to
        # be very sure that nothing writes to a real database! Also, we will
        # want to read from this dummy config at some point.

        # If you use this:
        #       loader = TestLoader()
        #       suite = loader.discover(CAMCOPS_SERVER_DIRECTORY)
        # ... then it fails because submodules contain relative imports (e.g.
        # "from ..cc_modules.something import x" and this gives "ValueError:
        # attemped relative import beyond top-level package". As the unittest
        # docs say, "In order to be compatible with test discovery, all of the
        # test files must be modules or packages... importable from the
        # top-level directory of the project".
        #
        # However, having imported everything, all our tests should be
        # subclasses of TestCase... but so are some other things.
        #
        # So we have a choice:
        # 1. manual test specification (yuk)
        # 2. hack around TestCase.__subclasses__ to exclude "built-in" ones
        # 3. abandon relative imports
        #   ... not a bad general idea (they often seem to cause problems!)
        #   ... however, the discovery process (a) fails with importing
        #       "alembic.versions", but more problematically, imports tasks
        #       twice, which gives errors like
        #       "sqlalchemy.exc.InvalidRequestError: Table 'ace3' is already
        #       defined for this MetaData instance."
        # So, hack it is.

        # noinspection PyProtectedMember
        skip_testclass_subclasses = [
            # The ugly hack: what you see from
            # unittest.TestCase.__subclasses__() from a clean import:
            unittest.case.FunctionTestCase,  # built in
            unittest.case._SubTest,  # built in
            unittest.loader._FailedTest,  # built in
            # plus our extras:
            DemoDatabaseTestCase,  # our base class
            DemoRequestTestCase,  # also a base class
            ExtendedTestCase,  # also a base class
        ]
        suite = unittest.TestSuite()
        for cls in gen_all_subclasses(unittest.TestCase):
            # log.critical("Considering: {}", cls)
            if cls in skip_testclass_subclasses:
                continue
            if not cls.__module__.startswith("camcops_server"):
                # don't, for example, run cardinal_pythonlib self-tests
                continue
            log.info("Discovered test: {}", cls)
            suite.addTest(unittest.makeSuite(cls))
        if show_only:
            return
        runner = unittest.TextTestRunner()
        runner.run(suite)


# =============================================================================
# Command-line processor
# =============================================================================

_REQNAMED = 'required named arguments'


# noinspection PyShadowingBuiltins
def add_sub(sp: "_SubParsersAction", cmd: str,
            config_mandatory: Optional[bool] = False,
            description: str = None,
            help: str = None) -> ArgumentParser:
    """
    help:
        Used for the main help summary, i.e. "camcops --help".
    description:
        Used for the description in the detailed help, e.g.
        "camcops docs --help". Defaults to "help".
    config_mandatory:
        None = don't ask for config
        False = ask for it, but not mandatory
        True = mandatory
    """
    if description is None:
        description = help
    subparser = sp.add_parser(
        cmd,
        help=help,
        description=description,
        formatter_class=ArgumentDefaultsHelpFormatter
    )  # type: ArgumentParser
    subparser.add_argument(
        '-v', '--verbose', action='store_true',
        help="Be verbose")
    if config_mandatory:
        cfg_help = "Configuration file"
    else:
        cfg_help = ("Configuration file (if not specified, the environment"
                    " variable {} is checked)".format(ENVVAR_CONFIG_FILE))
    if config_mandatory is None:
        pass
    elif config_mandatory:
        g = subparser.add_argument_group(_REQNAMED)
        # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments  # noqa
        g.add_argument("--config", required=True, help=cfg_help)
    else:
        subparser.add_argument("--config", help=cfg_help)
    return subparser


# noinspection PyShadowingBuiltins
def add_req_named(sp: ArgumentParser, switch: str, help: str,
                  action: str = None) -> None:
    # noinspection PyProtectedMember
    reqgroup = next((g for g in sp._action_groups
                     if g.title == _REQNAMED), None)
    if not reqgroup:
        reqgroup = sp.add_argument_group(_REQNAMED)
    reqgroup.add_argument(switch, required=True, action=action, help=help)


def add_wsgi_options(sp: ArgumentParser) -> None:
    sp.add_argument(
        "--trusted_proxy_headers", type=str, nargs="*",
        help=(
            "Trust these WSGI environment variables for when the server "
            "is behind a reverse proxy (e.g. an Apache front-end web "
            "server). Options: {!r}".format(
                ReverseProxiedMiddleware.ALL_CANDIDATES)
        )
    )
    sp.add_argument(
        '--proxy_http_host', type=str, default=None,
        help=(
            "Option to set the WSGI HTTP host directly. "
            "This affects the WSGI variable {w}. If not specified, "
            "trusted variables within {v!r} will be used.".format(
                w=WsgiEnvVar.HTTP_HOST,
                v=ReverseProxiedMiddleware.CANDIDATES_HTTP_HOST,
            )
        )
    )
    sp.add_argument(
        '--proxy_remote_addr', type=str, default=None,
        help=(
            "Option to set the WSGI remote address directly. "
            "This affects the WSGI variable {w}. If not specified, "
            "trusted variables within {v!r} will be used.".format(
                w=WsgiEnvVar.REMOTE_ADDR,
                v=ReverseProxiedMiddleware.CANDIDATES_REMOTE_ADDR,
            )
        )
    )
    sp.add_argument(
        "--proxy_script_name", type=str, default=None,
        help=(
            "Path at which this script is mounted. Set this if you are "
            "hosting this CamCOPS instance at a non-root path, unless you "
            "set trusted WSGI headers instead. For example, "
            "if you are running an Apache server and want this instance "
            "of CamCOPS to appear at /somewhere/camcops, then (a) "
            "configure your Apache instance to proxy requests to "
            "/somewhere/camcops/... to this server (e.g. via an internal "
            "TCP/IP port or UNIX socket) and specify this option. If this "
            "option is not set, then the OS environment variable {sn} "
            "will be checked as well, and if that is not set, trusted "
            "variables within {v!r} will be used. This option affects the "
            "WSGI variables {sn} and {pi}.".format(
                sn=WsgiEnvVar.SCRIPT_NAME,
                pi=WsgiEnvVar.PATH_INFO,
                v=ReverseProxiedMiddleware.CANDIDATES_SCRIPT_NAME,
            )
        )
    )
    sp.add_argument(
        '--proxy_server_port', type=int, default=None,
        help=(
            "Option to set the WSGI server port directly. "
            "This affects the WSGI variable {w}. If not specified, "
            "trusted variables within {v!r} will be used.".format(
                w=WsgiEnvVar.SERVER_PORT,
                v=ReverseProxiedMiddleware.CANDIDATES_SERVER_PORT,
            )
        )
    )
    sp.add_argument(
        '--proxy_server_name', type=str, default=None,
        help=(
            "Option to set the WSGI server name directly. "
            "This affects the WSGI variable {w}. If not specified, "
            "trusted variables within {v!r} will be used.".format(
                w=WsgiEnvVar.SERVER_NAME,
                v=ReverseProxiedMiddleware.CANDIDATES_SERVER_NAME,
            )
        )
    )
    sp.add_argument(
        '--proxy_url_scheme', type=str, default=None,
        help=(
            "Option to set the WSGI scheme (e.g. http, https) directly. "
            "This affects the WSGI variable {w}. If not specified, "
            "trusted variables within {v!r} will be used.".format(
                w=WsgiEnvVar.WSGI_URL_SCHEME,
                v=ReverseProxiedMiddleware.CANDIDATES_URL_SCHEME,
            )
        )
    )
    sp.add_argument(
        '--proxy_rewrite_path_info', action="store_true",
        help=(
            "If SCRIPT_NAME is rewritten, this option causes PATH_INFO to "
            "be rewritten, if it starts with SCRIPT_NAME, to strip off "
            "SCRIPT_NAME. Appropriate for some front-end web browsers "
            "with limited reverse proxying support (but do not use for "
            "Apache with ProxyPass, because that rewrites incoming URLs "
            "properly)."
        )
    )
    sp.add_argument(
        '--debug_reverse_proxy', action="store_true",
        help="For --behind_reverse_proxy: show debugging information as "
             "WSGI variables are rewritten."
    )
    sp.add_argument(
        '--debug_toolbar', action="store_true",
        help="Enable the Pyramid debug toolbar"
    )


def camcops_main() -> None:
    """
    Command-line entry point.

    Note that we can't easily use delayed imports to speed up the help output,
    because the help system has function calls embedded into it.
    """
    # Fetch command-line options.

    # -------------------------------------------------------------------------
    # Base parser
    # -------------------------------------------------------------------------

    parser = ArgumentParser(
        prog="camcops",  # name the user will use to call it
        description="""CamCOPS server version {}, by Rudolf Cardinal.
Use 'camcops <COMMAND> --help' for more detail on each command.""".format(
            CAMCOPS_SERVER_VERSION),
        formatter_class=RawDescriptionHelpFormatter,
        # add_help=False  # only do this if manually overriding the method
    )
    parser.add_argument(
        '--allhelp',
        action=ShowAllSubparserHelpAction,
        help='show help for all commands and exit')
    parser.add_argument(
        "--version", action="version",
        version="CamCOPS {}".format(CAMCOPS_SERVER_VERSION))

    # -------------------------------------------------------------------------
    # Subcommand subparser
    # -------------------------------------------------------------------------

    subparsers = parser.add_subparsers(
        title="commands",
        description="Valid CamCOPS commands are as follows.",
        help='Specify one command.',
        dest='command',  # sorts out the help for the command being mandatory
        # https://stackoverflow.com/questions/23349349/argparse-with-required-subparser  # noqa
    )  # type: _SubParsersAction  # noqa
    subparsers.required = True  # requires a command
    # You can't use "add_subparsers" more than once.
    # Subparser groups seem not yet to be supported:
    #   https://bugs.python.org/issue9341
    #   https://bugs.python.org/issue14037

    # -------------------------------------------------------------------------
    # Getting started commands
    # -------------------------------------------------------------------------

    docs_parser = add_sub(
        subparsers, "docs", config_mandatory=None,
        help="Launch the main documentation (CamCOPS manual)"
    )
    docs_parser.set_defaults(
        func=lambda args: launch_manual())

    democonfig_parser = add_sub(
        subparsers, "demo_camcops_config", config_mandatory=None,
        help="Print a demo CamCOPS config file")
    democonfig_parser.set_defaults(
        func=lambda args: print_demo_camcops_config())

    demosupervisorconf_parser = add_sub(
        subparsers, "demo_supervisor_config", config_mandatory=None,
        help="Print a demo 'supervisor' config file for CamCOPS")
    demosupervisorconf_parser.set_defaults(
        func=lambda args: print_demo_supervisor_config())

    demoapacheconf_parser = add_sub(
        subparsers, "demo_apache_config", config_mandatory=None,
        help="Print a demo Apache config file section for CamCOPS")
    demoapacheconf_parser.set_defaults(
        func=lambda args: print_demo_apache_config())

    demo_mysql_create_db_parser = add_sub(
        subparsers, "demo_mysql_create_db", config_mandatory=None,
        help="Print demo instructions to create a MySQL database for CamCOPS")
    demo_mysql_create_db_parser.set_defaults(
        func=lambda args: print_demo_mysql_create_db())

    demo_mysql_dump_script_parser = add_sub(
        subparsers, "demo_mysql_dump_script", config_mandatory=None,
        help="Print demo instructions to dump all current MySQL databases")
    demo_mysql_dump_script_parser.set_defaults(
        func=lambda args: print_demo_mysql_dump_script())

    # -------------------------------------------------------------------------
    # Database commands
    # -------------------------------------------------------------------------

    upgradedb_parser = add_sub(
        subparsers, "upgrade_db", config_mandatory=True,
        help="Upgrade database to most recent version (via Alembic)")
    upgradedb_parser.set_defaults(
        func=lambda args: upgrade_database_to_head(show_sql_only=False))

    show_upgrade_sql_parser = add_sub(
        subparsers, "show_upgrade_sql", config_mandatory=True,
        help="Show SQL for upgrading database (to stdout)")
    show_upgrade_sql_parser.set_defaults(
        func=lambda args: upgrade_database_to_head(show_sql_only=True))

    showdbtitle_parser = add_sub(
        subparsers, "show_db_title",
        help="Show database title")
    showdbtitle_parser.set_defaults(
        func=lambda args: print_database_title())

    mergedb_parser = add_sub(
        subparsers, "merge_db", config_mandatory=True,
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
        subparsers, "create_db", config_mandatory=True,
        help="Create CamCOPS database from scratch (AVOID; use the upgrade "
             "facility instead)")
    add_req_named(
        createdb_parser,
        '--confirm_create_db', action="store_true",
        help="Must specify this too, as a safety measure")
    createdb_parser.set_defaults(
        func=lambda args: create_database_from_scratch(
            cfg=get_default_config_from_os_env()
        ))

    # db_group.add_argument(
    #     "-s", "--summarytables", action="store_true", default=False,
    #     help="Make summary tables")

    # -------------------------------------------------------------------------
    # User commands
    # -------------------------------------------------------------------------

    superuser_parser = add_sub(
        subparsers, "make_superuser",
        help="Make superuser, or give superuser status to an existing user")
    superuser_parser.add_argument(
        '--username',
        help="Username of superuser to create/promote (if omitted, you will "
             "be asked to type it in)")
    superuser_parser.set_defaults(func=lambda args: make_superuser(
        username=args.username
    ))

    password_parser = add_sub(
        subparsers, "reset_password",
        help="Reset a user's password")
    password_parser.add_argument(
        '--username',
        help="Username to change password for (if omitted, you will be asked "
             "to type it in)")
    password_parser.set_defaults(func=lambda args: reset_password(
        username=args.username
    ))

    enableuser_parser = add_sub(
        subparsers, "enable_user",
        help="Re-enable a locked user account")
    enableuser_parser.add_argument(
        '--username',
        help="Username to enable (if omitted, you will be asked "
             "to type it in)")
    enableuser_parser.set_defaults(func=lambda args: enable_user_cli(
        username=args.username
    ))

    # -------------------------------------------------------------------------
    # Export options
    # -------------------------------------------------------------------------

    ddl_parser = add_sub(
        subparsers, "ddl",
        help="Print database schema (data definition language; DDL)")
    ddl_parser.add_argument(
        '--dialect', type=str, default=SqlaDialectName.MYSQL,
        help="SQL dialect (options: {})".format(", ".join(ALL_SQLA_DIALECTS)))
    ddl_parser.set_defaults(
        func=lambda args: print(get_all_ddl(dialect_name=args.dialect)))

    hl7_parser = add_sub(
        subparsers, "hl7",
        help="Send pending HL7 messages and outbound files")
    hl7_parser.set_defaults(
        func=lambda args: send_hl7(show_queue_only=False))

    showhl7queue_parser = add_sub(
        subparsers, "show_hl7_queue",
        help="View outbound HL7/file queue (without sending)")
    showhl7queue_parser.set_defaults(
        func=lambda args: send_hl7(show_queue_only=True))

    # *** ANONYMOUS STAGING DATABASE DISABLED TEMPORARILY
    # anonstaging_parser = add_sub(
    #     subparsers, "anonstaging",
    #     help="Generate/regenerate anonymisation staging database")
    # anonstaging_parser.set_defaults(
    #     func=lambda args: generate_anonymisation_staging_db())

    # -------------------------------------------------------------------------
    # Test options
    # -------------------------------------------------------------------------

    showtests_parser = add_sub(
        subparsers, "show_tests", config_mandatory=None,
        help="Show available self-tests")
    showtests_parser.set_defaults(func=lambda args: self_test(show_only=True))

    selftest_parser = add_sub(
        subparsers, "self_test", config_mandatory=None,
        help="Test internal code")
    selftest_parser.set_defaults(func=lambda args: self_test())

    serve_pyr_parser = add_sub(
        subparsers, "serve_pyramid",
        help="Test web server (single-thread, single-process, HTTP-only, "
             "Pyramid; for development use only")
    serve_pyr_parser.add_argument(
        '--host', type=str, default=DEFAULT_HOST,
        help="Hostname to listen on")
    serve_pyr_parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help="Port to listen on")
    add_wsgi_options(serve_pyr_parser)
    serve_pyr_parser.set_defaults(func=lambda args: test_serve_pyramid(
        application=make_wsgi_app_from_argparse_args(args),
        host=args.host,
        port=args.port
    ))

    # -------------------------------------------------------------------------
    # Web server options
    # -------------------------------------------------------------------------

    serve_cp_parser = add_sub(
        subparsers, "serve_cherrypy",
        help="Start web server (via CherryPy)")
    serve_cp_parser.add_argument(
        "--serve", action="store_true",
        help="")
    serve_cp_parser.add_argument(
        '--host', type=str, default=DEFAULT_HOST,
        help="hostname to listen on")
    serve_cp_parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help="port to listen on")
    serve_cp_parser.add_argument(
        '--unix_domain_socket', type=str, default="",
        help="UNIX domain socket to listen on (overrides host/port if "
             "specified)")
    serve_cp_parser.add_argument(
        "--server_name", type=str, default="localhost",
        help="CherryPy's SERVER_NAME environ entry")
    serve_cp_parser.add_argument(
        "--threads_start", type=int, default=10,
        help="Number of threads for server to start with")
    serve_cp_parser.add_argument(
        "--threads_max", type=int, default=DEFAULT_MAX_THREADS,
        help="Maximum number of threads for server to use (-1 for no limit) "
             "(BEWARE exceeding the permitted number of database connections)")
    serve_cp_parser.add_argument(
        "--ssl_certificate", type=str,
        help="SSL certificate file "
             "(e.g. /etc/ssl/certs/ssl-cert-snakeoil.pem)")
    serve_cp_parser.add_argument(
        "--ssl_private_key", type=str,
        help="SSL private key file "
             "(e.g. /etc/ssl/private/ssl-cert-snakeoil.key)")
    serve_cp_parser.add_argument(
        "--log_screen", dest="log_screen", action="store_true",
        help="Log access requests etc. to terminal (default)")
    serve_cp_parser.add_argument(
        "--no_log_screen", dest="log_screen", action="store_false",
        help="Don't log access requests etc. to terminal")
    serve_cp_parser.set_defaults(log_screen=True)
    serve_cp_parser.add_argument(
        "--root_path", type=str, default=URL_PATH_ROOT,
        help=(
            "Root path to serve CRATE at, WITHIN this CherryPy web server "
            "instance. (There is unlikely to be a reason to use something "
            "other than '/'; do not confuse this with the mount point "
            "within a wider, e.g. Apache, configuration, which is set "
            "instead by the WSGI variable {}; see the "
            "--trusted_proxy_headers and --proxy_script_name "
            "options.)".format(WsgiEnvVar.SCRIPT_NAME)
        )
    )
    add_wsgi_options(serve_cp_parser)
    serve_cp_parser.set_defaults(func=lambda args: serve_cherrypy(
        application=make_wsgi_app_from_argparse_args(args),
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
    ))

    cpu_count = multiprocessing.cpu_count()

    serve_gu_parser = add_sub(
        subparsers, "serve_gunicorn",
        help="Start web server (via Gunicorn) (not available under Windows)")
    serve_gu_parser.add_argument(
        "--serve", action="store_true",
        help="")
    serve_gu_parser.add_argument(
        '--host', type=str, default=DEFAULT_HOST,
        help="hostname to listen on")
    serve_gu_parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help="port to listen on")
    serve_gu_parser.add_argument(
        '--unix_domain_socket', type=str, default="",
        help="UNIX domain socket to listen on (overrides host/port if "
             "specified)")
    serve_gu_parser.add_argument(
        "--num_workers", type=int, default=cpu_count * 2,
        help="Number of worker processes for server to use")
    serve_gu_parser.add_argument(
        "--debug_reload", action="store_true",
        help="Debugging option: reload Gunicorn upon code change")
    serve_gu_parser.add_argument(
        "--ssl_certificate", type=str,
        help="SSL certificate file "
             "(e.g. /etc/ssl/certs/ssl-cert-snakeoil.pem)")
    serve_gu_parser.add_argument(
        "--ssl_private_key", type=str,
        help="SSL private key file "
             "(e.g. /etc/ssl/private/ssl-cert-snakeoil.key)")
    serve_gu_parser.add_argument(
        "--timeout", type=int, default=30,
        help="Gunicorn worker timeout (s)"
    )
    serve_gu_parser.add_argument(
        "--debug_show_gunicorn_options", action="store_true",
        help="Debugging option: show possible Gunicorn settings"
    )
    serve_gu_parser.set_defaults(log_screen=True)
    add_wsgi_options(serve_gu_parser)
    serve_gu_parser.set_defaults(func=lambda args: serve_gunicorn(
        application=make_wsgi_app_from_argparse_args(args),
        host=args.host,
        port=args.port,
        num_workers=args.num_workers,
        unix_domain_socket_filename=args.unix_domain_socket,
        ssl_certificate=args.ssl_certificate,
        ssl_private_key=args.ssl_private_key,
        reload=args.debug_reload,
        timeout_s=args.timeout,
        debug_show_gunicorn_options=args.debug_show_gunicorn_options,
    ))

    # -------------------------------------------------------------------------
    # OK; parse the arguments
    # -------------------------------------------------------------------------

    progargs = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    loglevel = logging.DEBUG if progargs.verbose else logging.INFO
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

    if progargs.func is None:
        raise NotImplementedError("Command-line function not implemented!")
    success = progargs.func(progargs)  # type: Optional[bool]
    if success is None or success is True:
        sys.exit(0)
    else:
        sys.exit(1)


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
