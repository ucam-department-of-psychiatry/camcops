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

from argparse import (
    ArgumentParser,
    ArgumentDefaultsHelpFormatter,
    Namespace,
    RawDescriptionHelpFormatter,
)
import logging
import os
import multiprocessing
import sys
from typing import List, Optional, TYPE_CHECKING

from cardinal_pythonlib.argparse_func import ShowAllSubparserHelpAction
from cardinal_pythonlib.debugging import pdb_run
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
    print_report_on_all_logs,
    set_level_for_logger_and_its_handlers,
)
from cardinal_pythonlib.process import launch_external_file
from cardinal_pythonlib.sqlalchemy.dialect import (
    ALL_SQLA_DIALECTS,
    SqlaDialectName,
)
from cardinal_pythonlib.wsgi.constants import WsgiEnvVar
from cardinal_pythonlib.wsgi.reverse_proxied_mw import ReverseProxiedMiddleware

from camcops_server.cc_modules.cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    DOCUMENTATION_URL,
)
from camcops_server.cc_modules.cc_config import (
    CamcopsConfig,
    get_default_config_from_os_env,
    get_demo_apache_config,
    get_demo_config,
    get_demo_mysql_create_db,
    get_demo_mysql_dump_script,
    get_demo_supervisor_config,
)
from camcops_server.cc_modules.cc_constants import (
    CAMCOPS_URL,
    DEFAULT_FLOWER_ADDRESS,
    DEFAULT_FLOWER_PORT,
    DEFAULT_HOST,
    DEFAULT_MAX_THREADS,
    DEFAULT_PORT,
    URL_PATH_ROOT,
)
from camcops_server.cc_modules.cc_exception import raise_runtime_error
from camcops_server.cc_modules.cc_snomed import send_athena_icd_snomed_to_xml
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from argparse import _SubParsersAction
    from pyramid.router import Router

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

if sys.version_info[0] < 3:
    raise_runtime_error(
        "CamCOPS needs Python 3+, and this Python version is: " + sys.version)

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_LOG_CONFIG = False
DEBUG_RUN_WITH_PDB = False


# =============================================================================
# Simple command-line functions
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


# =============================================================================
# Stub command-line functions requiring more substantial imports
# =============================================================================

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

def _upgrade_database_to_head(show_sql_only: bool) -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_alembic import upgrade_database_to_head  # delayed import  # noqa
    upgrade_database_to_head(show_sql_only=show_sql_only)


def _upgrade_database_to_revision(revision: str,
                                  show_sql_only: bool = False) -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_alembic import upgrade_database_to_revision  # delayed import  # noqa
    upgrade_database_to_revision(revision=revision,
                                 show_sql_only=show_sql_only)


def _downgrade_database_to_revision(
        revision: str,
        show_sql_only: bool = False,
        confirm_downgrade_db: bool = False) -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_alembic import downgrade_database_to_revision  # delayed import  # noqa
    downgrade_database_to_revision(
        revision=revision,
        show_sql_only=show_sql_only,
        confirm_downgrade_db=confirm_downgrade_db)


def _create_database_from_scratch(cfg: "CamcopsConfig") -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_alembic import create_database_from_scratch  # delayed import  # noqa
    create_database_from_scratch(cfg=cfg)


def _print_database_title() -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.print_database_title()


def _merge_camcops_db(src: str,
                      echo: bool,
                      report_every: int,
                      dummy_run: bool,
                      info_only: bool,
                      skip_export_logs: bool,
                      skip_audit_logs: bool,
                      default_group_id: Optional[int],
                      default_group_name: Optional[str]) -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.merge_db import merge_camcops_db  # delayed import  # noqa
    merge_camcops_db(src=src,
                     echo=echo,
                     report_every=report_every,
                     dummy_run=dummy_run,
                     info_only=info_only,
                     skip_export_logs=skip_export_logs,
                     skip_audit_logs=skip_audit_logs,
                     default_group_id=default_group_id,
                     default_group_name=default_group_name)


def _get_all_ddl(dialect_name: str = SqlaDialectName.MYSQL) -> str:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_sqlalchemy import get_all_ddl  # delayed import  # noqa
    return get_all_ddl(dialect_name=dialect_name)


def _reindex(cfg: CamcopsConfig) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.reindex(cfg=cfg)


# -----------------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------------

def _make_superuser(username: str = None) -> bool:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.make_superuser(username=username)


def _reset_password(username: str = None) -> bool:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.reset_password(username=username)


def _enable_user_cli(username: str = None) -> bool:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.enable_user_cli(username=username)


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------

def _cmd_export(recipient_names: List[str] = None,
                all_recipients: bool = False,
                via_index: bool = True) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.cmd_export(recipient_names=recipient_names,
                           all_recipients=all_recipients,
                           via_index=via_index)


def _cmd_show_export_queue(recipient_names: List[str] = None,
                           all_recipients: bool = False,
                           via_index: bool = True,
                           pretty: bool = False) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.cmd_show_export_queue(recipient_names=recipient_names,
                               all_recipients=all_recipients,
                               via_index=via_index,
                               pretty=pretty)


# -----------------------------------------------------------------------------
# Web server
# -----------------------------------------------------------------------------

def _make_wsgi_app_from_argparse_args(args: Namespace) -> "Router":
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.make_wsgi_app_from_argparse_args(args=args)


def _test_serve_pyramid(application: "Router",
                        host: str = DEFAULT_HOST,
                        port: int = DEFAULT_PORT) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.test_serve_pyramid(application=application,
                            host=host,
                            port=port)


def _serve_cherrypy(application: "Router",
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
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.serve_cherrypy(
        application=application,
        host=host,
        port=port,
        unix_domain_socket_filename=unix_domain_socket_filename,
        threads_start=threads_start,
        threads_max=threads_max,
        server_name=server_name,
        log_screen=log_screen,
        ssl_certificate=ssl_certificate,
        ssl_private_key=ssl_private_key,
        root_path=root_path)


def _serve_gunicorn(application: "Router",
                    host: str,
                    port: int,
                    unix_domain_socket_filename: str,
                    num_workers: int,
                    ssl_certificate: Optional[str],
                    ssl_private_key: Optional[str],
                    reload: bool = False,
                    timeout_s: int = 30,
                    debug_show_gunicorn_options: bool = False) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.serve_gunicorn(
        application=application,
        host=host,
        port=port,
        unix_domain_socket_filename=unix_domain_socket_filename,
        num_workers=num_workers,
        ssl_certificate=ssl_certificate,
        ssl_private_key=ssl_private_key,
        reload=reload,
        timeout_s=timeout_s,
        debug_show_gunicorn_options=debug_show_gunicorn_options)


# -----------------------------------------------------------------------------
# Celery etc.
# -----------------------------------------------------------------------------

def _launch_celery_workers(verbose: bool = False) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.launch_celery_workers(verbose=verbose)


def _launch_celery_beat(verbose: bool = False) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.launch_celery_beat(verbose=verbose)


def _launch_celery_flower(address: str = DEFAULT_FLOWER_ADDRESS,
                          port: int = DEFAULT_FLOWER_PORT) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.launch_celery_flower(address=address,
                              port=port)


# -----------------------------------------------------------------------------
# Testing and development
# -----------------------------------------------------------------------------

def _self_test(show_only: bool = False) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.self_test(show_only=show_only)


def _dev_cli() -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.dev_cli()


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

    # -------------------------------------------------------------------------
    # Common arguments
    # -------------------------------------------------------------------------

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
    # "Getting started" commands
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
        func=lambda args: _upgrade_database_to_head(
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
        func=lambda args: _upgrade_database_to_revision(
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
    dev_downgrade_parser.add_argument(
        '--confirm_downgrade_db', action="store_true",
        help="Must specify this too, as a safety measure")
    dev_downgrade_parser.add_argument(
        "--show_sql_only", action="store_true",
        help="Show SQL only (to stdout); don't execute it"
    )
    dev_downgrade_parser.set_defaults(
        func=lambda args: _downgrade_database_to_revision(
            revision=args.destination_db_revision,
            show_sql_only=args.show_sql_only,
            confirm_downgrade_db=args.confirm_downgrade_db,
        )
    )

    # Show database title
    showdbtitle_parser = add_sub(
        subparsers, "show_db_title",
        help="Show database title")
    showdbtitle_parser.set_defaults(
        func=lambda args: _print_database_title())

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
    mergedb_parser.set_defaults(func=lambda args: _merge_camcops_db(
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
        func=lambda args: _create_database_from_scratch(
            cfg=get_default_config_from_os_env()
        )
    )

    # Print database schema
    ddl_parser = add_sub(
        subparsers, "ddl",
        help="Print database schema (data definition language; DDL)")
    ddl_parser.add_argument(
        '--dialect', type=str, default=SqlaDialectName.MYSQL,
        help="SQL dialect (options: {})".format(", ".join(ALL_SQLA_DIALECTS)))
    ddl_parser.set_defaults(
        func=lambda args: print(_get_all_ddl(dialect_name=args.dialect)))

    # Rebuild server indexes
    reindex_parser = add_sub(
        subparsers, "reindex",
        help="Recreate task index"
    )
    reindex_parser.set_defaults(
        func=lambda args: _reindex(
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
    superuser_parser.set_defaults(func=lambda args: _make_superuser(
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
    password_parser.set_defaults(func=lambda args: _reset_password(
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
    enableuser_parser.set_defaults(func=lambda args: _enable_user_cli(
        username=args.username
    ))

    # -------------------------------------------------------------------------
    # Export options
    # -------------------------------------------------------------------------

    def _add_export_options(sp: ArgumentParser) -> None:
        sp.add_argument(
            '--recipients', type=str, nargs="*",
            help="Export recipients (as named in config file)")
        sp.add_argument(
            '--all_recipients', action="store_true",
            help="Use all recipients")
        sp.add_argument(
            '--disable_task_index', action="store_true",
            help="Disable use of the task index (for debugging only)")

    # Send incremental export messages
    export_parser = add_sub(
        subparsers, "export",
        help="Trigger pending exports")
    _add_export_options(export_parser)
    export_parser.set_defaults(
        func=lambda args: _cmd_export(
            recipient_names=args.recipients,
            all_recipients=args.all_recipients,
            via_index=not args.disable_task_index,
        ))

    # Show incremental export queue
    show_export_queue_parser = add_sub(
        subparsers, "show_export_queue",
        help="View outbound export queue (without sending)")
    _add_export_options(show_export_queue_parser)
    show_export_queue_parser.add_argument(
        '--pretty', action="store_true",
        help="Pretty (but slower) formatting for tasks")
    show_export_queue_parser.set_defaults(
        func=lambda args: _cmd_show_export_queue(
            recipient_names=args.recipients,
            all_recipients=args.all_recipients,
            via_index=not args.disable_task_index,
            pretty=args.pretty,
        ))

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
    serve_cp_parser.set_defaults(func=lambda args: _serve_cherrypy(
        application=_make_wsgi_app_from_argparse_args(args),
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
    serve_gu_parser.set_defaults(func=lambda args: _serve_gunicorn(
        application=_make_wsgi_app_from_argparse_args(args),
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
    serve_pyr_parser.set_defaults(func=lambda args: _test_serve_pyramid(
        application=_make_wsgi_app_from_argparse_args(args),
        host=args.host,
        port=args.port
    ))

    # -------------------------------------------------------------------------
    # Preprocessing options
    # -------------------------------------------------------------------------

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
    # Celery options
    # -------------------------------------------------------------------------

    # Launch Celery workers
    celery_worker_parser = add_sub(
        subparsers, "launch_workers",
        help="Launch Celery workers, for background processing"
    )
    celery_worker_parser.set_defaults(func=lambda args: _launch_celery_workers(
        verbose=args.verbose,
    ))

    # Launch Celery Bear
    celery_beat_parser = add_sub(
        subparsers, "launch_scheduler",
        help="Launch Celery Beat scheduler, to schedule background jobs"
    )
    celery_beat_parser.set_defaults(func=lambda args: _launch_celery_beat(
        verbose=args.verbose,
    ))

    # Launch Celery Flower monitor
    celery_flower_parser = add_sub(
        subparsers, "launch_monitor",
        help="Launch Celery Flower monitor, to monitor background jobs"
    )
    celery_flower_parser.add_argument(
        "--address", type=str, default=DEFAULT_FLOWER_ADDRESS,
        help="Address to use for Flower"
    )
    celery_flower_parser.add_argument(
        "--port", type=int, default=DEFAULT_FLOWER_PORT,
        help="Port to use for Flower"
    )
    celery_flower_parser.set_defaults(func=lambda args: _launch_celery_flower(
        address=args.address,
        port=args.port,
    ))

    # -------------------------------------------------------------------------
    # Test options
    # -------------------------------------------------------------------------

    # Show available self-tests
    showtests_parser = add_sub(
        subparsers, "show_tests", config_mandatory=None,
        help="Show available self-tests")
    showtests_parser.set_defaults(func=lambda args: _self_test(show_only=True))

    # Self-test
    selftest_parser = add_sub(
        subparsers, "self_test", config_mandatory=None,
        help="Test internal code")
    selftest_parser.set_defaults(func=lambda args: _self_test())

    # Launch a Python command line
    dev_cli_parser = add_sub(
        subparsers, "dev_cli",
        help="Developer command-line interface, with config loaded as "
             "'config'."
    )
    dev_cli_parser.set_defaults(func=lambda args: _dev_cli())

    # -------------------------------------------------------------------------
    # OK; parser built; now parse the arguments
    # -------------------------------------------------------------------------
    progargs = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    loglevel = logging.DEBUG if progargs.verbose else logging.INFO
    main_only_quicksetup_rootlogger(
        level=loglevel, with_process_id=True, with_thread_id=True)
    rootlogger = logging.getLogger()
    set_level_for_logger_and_its_handlers(rootlogger, loglevel)

    # Say hello
    log.info(
        """
# =============================================================================
# CamCOPS server version {version}
# Created by Rudolf Cardinal. See {url}
# Python interpreter: {interpreter!r}
# =============================================================================
""",
        version=CAMCOPS_SERVER_VERSION,
        url=CAMCOPS_URL,
        interpreter=sys.executable,
    )
    log.debug(
        """
# -----------------------------------------------------------------------------
# This program: {thisprog!r}
# Command-line arguments: {progargs!r}
# -----------------------------------------------------------------------------
""",
        thisprog=__file__,
        progargs=progargs,
    )
    if DEBUG_LOG_CONFIG or DEBUG_RUN_WITH_PDB:
        log.warning("Debugging options enabled!")
    if DEBUG_LOG_CONFIG:
        print_report_on_all_logs()

    # Finalize the config filename; ensure it's in the environment variable
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
