#!/usr/bin/env python

"""
camcops_server/camcops_server.py

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

**Command-line entry point for the CamCOPS server.**

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
from typing import Any, Dict, List, Optional, TYPE_CHECKING  # nopep8
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
    downgrade_database_to_revision,
    upgrade_database_to_head,
    upgrade_database_to_revision,
)  # nopep8
from camcops_server.cc_modules.cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    DOCUMENTATION_URL,
)  # nopep8
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.client_api  # import side effects (register unit test)  # nopep8
from camcops_server.cc_modules.cc_config import (
    CamcopsConfig,
    get_config_filename_from_os_env,
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
from camcops_server.cc_modules.cc_exception import raise_runtime_error  # nopep8
from camcops_server.cc_modules.cc_export import (
    print_export_queue,
    export,
)  # nopep8
from camcops_server.cc_modules.cc_pyramid import RouteCollection  # nopep8
from camcops_server.cc_modules.cc_request import (
    CamcopsRequest,
    command_line_request_context,
    get_command_line_request,
    pyramid_configurator_context,
)  # nopep8
from camcops_server.cc_modules.cc_snomed import send_athena_icd_snomed_to_xml  # nopep8
from camcops_server.cc_modules.cc_sqlalchemy import get_all_ddl  # nopep8
from camcops_server.cc_modules.cc_string import all_extra_strings_as_dicts  # nopep8
from camcops_server.cc_modules.cc_task import Task  # nopep8
from camcops_server.cc_modules.cc_taskindex import reindex_everything  # nopep8
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

log.info("Imports complete")

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction

# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

if sys.version_info[0] != 3:
    raise_runtime_error(
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
# Helper functions for web server launcher
# =============================================================================

def ensure_database_is_ok() -> None:
    """
    Opens a link to the database and checks it's of the correct version
    (or otherwise raises an assertion error).
    """
    config = get_default_config_from_os_env()
    config.assert_database_ok()


def join_url_fragments(*fragments: str) -> str:
    """
    Combines fragments to make a URL.

    (``urllib.parse.urljoin`` doesn't do what we want.)
    """
    newfrags = [f[1:] if f.startswith("/") else f for f in fragments]
    return "/".join(newfrags)


def precache() -> None:
    """
    Populates the major caches.
    """
    log.info("Prepopulating caches")
    config_filename = get_config_filename_from_os_env()
    config = get_default_config_from_os_env()
    _ = all_extra_strings_as_dicts(config_filename)
    _ = config.get_task_snomed_concepts()
    _ = config.get_icd9cm_snomed_concepts()
    _ = config.get_icd10_snomed_concepts()


# =============================================================================
# WSGI entry point
# =============================================================================

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
    """
    Reads the command-line (argparse) arguments, and creates a WSGI
    application.

    Must match :func:`add_wsgi_options`, which sets up argparse
    parsers.
    """
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


# =============================================================================
# Web server launchers
# =============================================================================

def test_serve_pyramid(application: Router,
                       host: str = DEFAULT_HOST,
                       port: int = DEFAULT_PORT) -> None:
    """
    Launches an extremely simple Pyramid web server (via
    ``wsgiref.make_server``).
    """
    ensure_database_is_ok()
    precache()
    server = make_server(host, port, application)
    log.info("Serving on host={}, port={}", host, port)
    server.serve_forever()


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
    Start CherryPy server.

    - Multithreading.
    - Any platform.
    """
    ensure_database_is_ok()
    precache()

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

      - https://eli.thegreenplace.net/2012/01/16/python-parallelizing-cpu-bound-tasks-with-multiprocessing/
      - http://www.dabeaz.com/python/UnderstandingGIL.pdf

    - UNIX only.

    - The Pyramid debug toolbar detects a multiprocessing web server and says
      "shan't, because I use global state".
    """  # noqa
    if BaseApplication is None:
        raise_runtime_error("Gunicorn does not run under Windows. "
                            "(It relies on the UNIX fork() facility.)")

    ensure_database_is_ok()
    precache()

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

        def load_config(self) -> None:
            # The Gunicorn example looks somewhat convoluted! Let's be simpler:
            for key, value in self.options.items():
                key_lower = key.lower()
                if key_lower in self.cfg.settings and value is not None:
                    self.cfg.set(key_lower, value)

        def load(self) -> Router:
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
# Helper functions for command-line functions
# =============================================================================

def get_username_from_cli(req: CamcopsRequest,
                          prompt: str,
                          starting_username: str = "",
                          must_exist: bool = False,
                          must_not_exist: bool = False) -> str:
    """
    Asks the user (via stdout/stdin) for a username.

    Args:
        req: CamcopsRequest object
        prompt: textual prompt
        starting_username: try this username and ask only if it fails tests
        must_exist: the username must exist
        must_not_exist: the username must not exist

    Returns:
        the username

    """
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
            log.error("... username {!r} is reserved", USER_NAME_FOR_SYSTEM)
            continue
        return username


def get_new_password_from_cli(username: str) -> str:
    """
    Asks the user (via stdout/stdin) for a new password for the specified
    username. Returns the password.
    """
    while True:
        password1 = ask_user_password("New password for user "
                                      "{}".format(username))
        if not password1 or len(password1) < MINIMUM_PASSWORD_LENGTH:
            log.error("... passwords can't be blank or shorter than {} "
                      "characters", MINIMUM_PASSWORD_LENGTH)
            continue
        password2 = ask_user_password("New password for user {} "
                                      "(again)".format(username))
        if password1 != password2:
            log.error("... passwords don't match; try again")
            continue
        return password1


# =============================================================================
# Command-line functions
# =============================================================================

def launch_manual() -> None:
    """
    Use the operating system "launch something" tool to show the CamCOPS
    documentation.
    """
    launch_external_file(DOCUMENTATION_URL)


def print_demo_camcops_config() -> None:
    """
    Prints a demonstration config file to stdout.
    """
    print(get_demo_config())


def print_demo_supervisor_config() -> None:
    """
    Prints a demonstration ``supervisord`` config file to stdout.
    """
    print(get_demo_supervisor_config())


def print_demo_apache_config() -> None:
    """
    Prints a demonstration Apache HTTPD config file segment (for CamCOPS)
    to stdout.
    """
    print(get_demo_apache_config())


def print_demo_mysql_create_db() -> None:
    """
    Prints a demonstration MySQL database creation script to stdout.
    """
    print(get_demo_mysql_create_db())


def print_demo_mysql_dump_script() -> None:
    """
    Prints a demonstration MySQL database dump script to stdout.
    """
    print(get_demo_mysql_dump_script())


def print_database_title() -> None:
    """
    Prints the database title (for the current config) to stdout.
    """
    with command_line_request_context() as req:
        print(req.database_title)


_ = '''
def generate_anonymisation_staging_db() -> None:
    """
    Generates an anonymisation staging database -- that is, a database with
    patient IDs in every row of every table, suitable for feeding into an
    anonymisation system like CRATE
    (https://dx.doi.org/10.1186%2Fs12911-017-0437-1).

    **BROKEN; NEEDS TO BE REPLACED.**
    """
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
    log.info("Draft data dictionary written to {}", ddfilename)
'''


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
            log.info("Giving superuser status to {!r}", username)
            existing_user.superuser = True
            success = True
        else:
            log.info("Creating superuser {!r}", username)
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
        log.info("Resetting password for user {!r}", username)
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
                log.critical("No such user: {!r}", username)
                return False
        SecurityLoginFailure.enable_user(req, username)
        log.info("Enabled.")
        return True


def cmd_show_export_queue(recipient_names: List[str] = None,
                          via_index: bool = True) -> None:
    """
    Shows tasks that would be exported.

    Args:
        recipient_names: list of export recipient names (as per the config
            file); blank for "all"
        via_index: use the task index (faster)?
    """
    with command_line_request_context() as req:
        print_export_queue(req, recipient_names, via_index=via_index)


def cmd_export(recipient_names: List[str] = None,
               via_index: bool = True) -> None:
    """
    Send all outbound incremental export messages (e.g. HL7).

    Args:
        recipient_names: list of export recipient names (as per the config
            file); blank for "all"
        via_index: use the task index (faster)?
    """
    with command_line_request_context() as req:
        export(req, recipient_names, via_index=via_index)


def reindex(cfg: CamcopsConfig) -> None:
    """
    Drops and regenerates the server task index.

    Args:
        cfg: a :class:`camcops_server.cc_modules.cc_config.CamcopsConfig`
    """
    ensure_database_is_ok()
    with cfg.get_dbsession_context() as dbsession:
        reindex_everything(dbsession)


# =============================================================================
# Test rig
# =============================================================================

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

        # noinspection PyProtectedMember,PyUnresolvedReferences
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


def dev_cli() -> None:
    """
    Fire up a developer debug command-line.
    """
    config = get_default_config_from_os_env()
    # noinspection PyUnusedLocal
    engine = config.get_sqla_engine()
    # noinspection PyUnusedLocal
    req = get_command_line_request()
    # noinspection PyUnusedLocal
    dbsession = req.dbsession
    log.error("""Entering developer command-line.
    - Config is available in 'config'.
    - Database engine is available in 'engine'.
    - Dummy request is available in 'req'.
    - Database session is available in 'dbsession'.
    """)
    import pdb
    pdb.set_trace()


# =============================================================================
# Command-line processor
# =============================================================================

_REQNAMED = 'required named arguments'


# noinspection PyShadowingBuiltins
def add_sub(sp: "_SubParsersAction",
            cmd: str,
            config_mandatory: Optional[bool] = False,
            description: str = None,
            help: str = None) -> ArgumentParser:
    """
    Adds (and returns) a subparser to an ArgumentParser.

    Args:
        sp: the ``_SubParsersAction`` object from a call to
            :func:`argparse.ArgumentParser.add_subparsers`.
        cmd: the command for the subparser (e.g. ``docs`` to make the command
            ``camcops docs``).
        config_mandatory:
            Does this subcommand require a CamCOPS config file? ``None`` =
            don't ask for config. ``False`` = ask for it, but not mandatory as
            a command-line argument. ``True`` = mandatory as a command-line
            argument.
        description: Used for the description in the detailed help, e.g.
            "camcops docs --help". Defaults to the value of the ``help``
            argument.
        help: Used for this subparser's contribution to the main help summary,
            i.e. ``camcops --help``.

    Returns:
        the subparser

    """
    if description is None:
        description = help
    subparser = sp.add_parser(
        cmd,
        help=help,
        description=description,
        formatter_class=ArgumentDefaultsHelpFormatter
    )  # type: ArgumentParser
    # This needs to be in the top-level parser and the sub-parsers (it does not
    # appear in the subparsers just because it's in the top-level parser, which
    # sounds like an argparse bug given its help, but there you go).
    subparser.add_argument(
        '-v', '--verbose', action='store_true',
        help="Be verbose")
    if config_mandatory:  # True
        cfg_help = "Configuration file"
    else:  # None, False
        cfg_help = ("Configuration file (if not specified, the environment"
                    " variable {} is checked)".format(ENVVAR_CONFIG_FILE))
    if config_mandatory is None:  # None
        pass
    elif config_mandatory:  # True
        g = subparser.add_argument_group(_REQNAMED)
        # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments  # noqa
        g.add_argument("--config", required=True, help=cfg_help)
    else:  # False
        subparser.add_argument("--config", help=cfg_help)
    return subparser


# noinspection PyShadowingBuiltins
def add_req_named(sp: ArgumentParser, switch: str, help: str,
                  action: str = None) -> None:
    """
    Adds a required but named argument. This is a bit unconventional; for
    example, making the ``--config`` option mandatory even though ``--`` is
    usually a prefix for optional arguments.

    Args:
        sp: the :class:`ArgumentParser` to add to
        switch: passed to :func:`add_argument`
        help: passed to :func:`add_argument`
        action: passed to :func:`add_argument`
    """
    # noinspection PyProtectedMember
    reqgroup = next((g for g in sp._action_groups
                     if g.title == _REQNAMED), None)
    if not reqgroup:
        reqgroup = sp.add_argument_group(_REQNAMED)
    reqgroup.add_argument(switch, required=True, action=action, help=help)


def add_wsgi_options(sp: ArgumentParser) -> None:
    """
    Adds to the specified :class:`ArgumentParser` all the options that we
    always want for any WSGI server.
    """
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
    Primary command-line entry point. Parse command-line arguments and act.

    Note that we can't easily use delayed imports to speed up the help output,
    because the help system has function calls embedded into it.
    """
    # Fetch command-line options.

    # -------------------------------------------------------------------------
    # Base parser
    # -------------------------------------------------------------------------

    parser = ArgumentParser(
        description=(
            "CamCOPS server, created by Rudolf Cardinal; version {}.\n"
            "Use 'camcops_server <COMMAND> --help' for more detail on each "
            "command.".format(CAMCOPS_SERVER_VERSION)
        ),
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
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help="Be verbose")

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

    # Launch documentation
    docs_parser = add_sub(
        subparsers, "docs", config_mandatory=None,
        help="Launch the main documentation (CamCOPS manual)"
    )
    docs_parser.set_defaults(
        func=lambda args: launch_manual())

    # Print demo CamCOPS config
    democonfig_parser = add_sub(
        subparsers, "demo_camcops_config", config_mandatory=None,
        help="Print a demo CamCOPS config file")
    democonfig_parser.set_defaults(
        func=lambda args: print_demo_camcops_config())

    # Print demo supervisor config
    demosupervisorconf_parser = add_sub(
        subparsers, "demo_supervisor_config", config_mandatory=None,
        help="Print a demo 'supervisor' config file for CamCOPS")
    demosupervisorconf_parser.set_defaults(
        func=lambda args: print_demo_supervisor_config())

    # Print demo Apache config section
    demoapacheconf_parser = add_sub(
        subparsers, "demo_apache_config", config_mandatory=None,
        help="Print a demo Apache config file section for CamCOPS")
    demoapacheconf_parser.set_defaults(
        func=lambda args: print_demo_apache_config())

    # Print demo MySQL database creation commands
    demo_mysql_create_db_parser = add_sub(
        subparsers, "demo_mysql_create_db", config_mandatory=None,
        help="Print demo instructions to create a MySQL database for CamCOPS")
    demo_mysql_create_db_parser.set_defaults(
        func=lambda args: print_demo_mysql_create_db())

    # Print demo Bash MySQL dump script
    demo_mysql_dump_script_parser = add_sub(
        subparsers, "demo_mysql_dump_script", config_mandatory=None,
        help="Print demo instructions to dump all current MySQL databases")
    demo_mysql_dump_script_parser.set_defaults(
        func=lambda args: print_demo_mysql_dump_script())

    # -------------------------------------------------------------------------
    # Database commands
    # -------------------------------------------------------------------------

    # Upgrade database
    upgradedb_parser = add_sub(
        subparsers, "upgrade_db", config_mandatory=True,
        help="Upgrade database to most recent version (via Alembic)")
    upgradedb_parser.add_argument(
        "--show_sql_only", action="store_true",
        help="Show SQL only (to stdout); don't execute it"
    )
    upgradedb_parser.set_defaults(
        func=lambda args: upgrade_database_to_head(
            show_sql_only=args.show_sql_only
        )
    )

    # Developer: upgrade database to a specific revision
    dev_upgrade_to_parser = add_sub(
        subparsers, "dev_upgrade_to", config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Upgrade a database to "
             "a specific revision."
    )
    dev_upgrade_to_parser.add_argument(
        "--destination_db_revision", type=str, required=True,
        help="The target database revision"
    )
    dev_upgrade_to_parser.add_argument(
        "--show_sql_only", action="store_true",
        help="Show SQL only (to stdout); don't execute it"
    )
    dev_upgrade_to_parser.set_defaults(
        func=lambda args: upgrade_database_to_revision(
            revision=args.destination_db_revision,
            show_sql_only=args.show_sql_only
        )
    )

    # Developer: downgrade database
    dev_downgrade_parser = add_sub(
        subparsers, "dev_downgrade_db", config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Downgrades a database to "
             "a specific revision. May DESTROY DATA."
    )
    dev_downgrade_parser.add_argument(
        "--destination_db_revision", type=str, required=True,
        help="The target database revision"
    )
    add_req_named(
        dev_downgrade_parser,
        '--confirm_downgrade_db', action="store_true",
        help="Must specify this too, as a safety measure")
    dev_downgrade_parser.add_argument(
        "--show_sql_only", action="store_true",
        help="Show SQL only (to stdout); don't execute it"
    )
    dev_downgrade_parser.set_defaults(
        func=lambda args: downgrade_database_to_revision(
            revision=args.destination_db_revision,
            show_sql_only=args.show_sql_only
        )
    )

    # Show database title
    showdbtitle_parser = add_sub(
        subparsers, "show_db_title",
        help="Show database title")
    showdbtitle_parser.set_defaults(
        func=lambda args: print_database_title())

    # Merge in data fom another database
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
        skip_export_logs=args.skip_hl7_logs,
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

    # Create database
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
        )
    )

    # Rebuild server indexes
    reindex_parser = add_sub(
        subparsers, "reindex",
        help="Recreate task index"
    )
    reindex_parser.set_defaults(
        func=lambda args: reindex(
            cfg=get_default_config_from_os_env()
        )
    )

    # -------------------------------------------------------------------------
    # User commands
    # -------------------------------------------------------------------------

    # Make superuser
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

    # Reset a user's password
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

    # Re-enable a locked account
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

    # Print database schema
    ddl_parser = add_sub(
        subparsers, "ddl",
        help="Print database schema (data definition language; DDL)")
    ddl_parser.add_argument(
        '--dialect', type=str, default=SqlaDialectName.MYSQL,
        help="SQL dialect (options: {})".format(", ".join(ALL_SQLA_DIALECTS)))
    ddl_parser.set_defaults(
        func=lambda args: print(get_all_ddl(dialect_name=args.dialect)))

    def _add_export_options(sp: ArgumentParser) -> None:
        sp.add_argument(
            '--recipients', type=str, nargs="*",
            help="Export recipients (as named in config file); "
                 "ignore to show all")
        sp.add_argument(
            '--disable_task_index', action="store_true",
            help="Disable use of the task index (for debugging only)")

    # Send incremental export messages
    export_parser = add_sub(
        subparsers, "export",
        help="Trigger pending exports")
    _add_export_options(export_parser)
    export_parser.set_defaults(
        func=lambda args: cmd_export(
            args.recipients,
            via_index=not args.disable_task_index,
        ))

    # Show incremental export queue
    show_export_queue_parser = add_sub(
        subparsers, "show_export_queue",
        help="View outbound export queue (without sending)")
    _add_export_options(show_export_queue_parser)
    show_export_queue_parser.set_defaults(
        func=lambda args: cmd_show_export_queue(
            recipient_names=args.recipients,
            via_index=not args.disable_task_index,
        ))

    # -------------------------------------------------------------------------
    # Test options
    # -------------------------------------------------------------------------

    # Show available self-tests
    showtests_parser = add_sub(
        subparsers, "show_tests", config_mandatory=None,
        help="Show available self-tests")
    showtests_parser.set_defaults(func=lambda args: self_test(show_only=True))

    # Self-test
    selftest_parser = add_sub(
        subparsers, "self_test", config_mandatory=None,
        help="Test internal code")
    selftest_parser.set_defaults(func=lambda args: self_test())

    # Serve via the Pyramid test server
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

    # Launch a Python command line
    dev_cli_parser = add_sub(
        subparsers, "dev_cli",
        help="Developer command-line interface, with config loaded as "
             "'config'."
    )
    dev_cli_parser.set_defaults(func=lambda args: dev_cli())

    # -------------------------------------------------------------------------
    # Web server options
    # -------------------------------------------------------------------------

    # Serve via CherryPy
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

    # Serve via Gunicorn
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

    # Preprocessing options

    athena_icd_snomed_to_xml_parser = add_sub(
        subparsers, "convert_athena_icd_snomed_to_xml",
        help="Fetch SNOMED-CT codes for ICD-9-CM and ICD-10 from the Athena "
             "OHDSI data set (http://athena.ohdsi.org/) and write them to "
             "the CamCOPS XML format"
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--athena_concept_tsv_filename", type=str, required=True,
        help="Path to CONCEPT.csv file from Athena download"
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--athena_concept_relationship_tsv_filename", type=str, required=True,
        help="Path to CONCEPT_RELATIONSHIP.csv file from Athena download"
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--icd9_xml_filename", type=str, required=True,
        help="Filename of ICD-9-CM/SNOMED-CT XML file to write"
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--icd10_xml_filename", type=str, required=True,
        help="Filename of ICD-10/SNOMED-CT XML file to write"
    )
    athena_icd_snomed_to_xml_parser.set_defaults(
        func=lambda args: send_athena_icd_snomed_to_xml(
            athena_concept_tsv_filename=args.athena_concept_tsv_filename,
            athena_concept_relationship_tsv_filename=args.athena_concept_relationship_tsv_filename,  # noqa
            icd9_xml_filename=args.icd9_xml_filename,
            icd10_xml_filename=args.icd10_xml_filename,
        )
    )

    # -------------------------------------------------------------------------
    # OK; parser built; now parse the arguments
    # -------------------------------------------------------------------------
    progargs = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    loglevel = logging.DEBUG if progargs.verbose else logging.INFO
    rootlogger = logging.getLogger()
    set_level_for_logger_and_its_handlers(rootlogger, loglevel)

    # Say hello
    log.info("CamCOPS server version {}", CAMCOPS_SERVER_VERSION)
    log.info("Created by Rudolf Cardinal. See {}", CAMCOPS_URL)
    log.debug("Python interpreter: {!r}", sys.executable)
    log.debug("This program: {!r}", __file__)
    log.debug("Command-line arguments: {!r}", progargs)
    log.info("Using {} tasks", len(Task.all_subclasses_by_tablename()))
    if DEBUG_LOG_CONFIG:
        print_report_on_all_logs()

    # Finalize the config filename
    if hasattr(progargs, 'config') and progargs.config:
        # We want the the config filename in the environment from now on:
        os.environ[ENVVAR_CONFIG_FILE] = progargs.config
    cfg_name = os.environ.get(ENVVAR_CONFIG_FILE, None)
    log.info("Using configuration file: {!r}", cfg_name)

    # Call the subparser function for the chosen command
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
    """
    Command-line entry point. Calls :func:`camcops_main`.
    """
    if DEBUG_RUN_WITH_PDB:
        pdb_run(camcops_main)
    else:
        camcops_main()


if __name__ == '__main__':
    main()
