#!/usr/bin/env python

"""
camcops_server/camcops_server.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    RawDescriptionHelpFormatter,
)
import logging
import os
import pprint
import sys
from typing import Dict, List, Optional, Type, TYPE_CHECKING

from cardinal_pythonlib.argparse_func import (
    ShowAllSubparserHelpAction,
    MapType,
    nonnegative_int,
)
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
from cardinal_pythonlib.wsgi.reverse_proxied_mw import ReverseProxiedConfig

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
)
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

if sys.version_info < (3, 6):
    raise AssertionError("Need Python 3.6 or higher; this is " + sys.version)

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
    if not show_sql_only:
        log.warning("You should run the 'reindex' command.")


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
                      # skip_export_logs: bool,
                      # skip_audit_logs: bool,
                      default_group_id: Optional[int],
                      default_group_name: Optional[str],
                      groupnum_map: Dict[int, int],
                      whichidnum_map: Dict[int, int]) -> None:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.merge_db import merge_camcops_db  # delayed import  # noqa
    merge_camcops_db(src=src,
                     echo=echo,
                     report_every=report_every,
                     dummy_run=dummy_run,
                     info_only=info_only,
                     # skip_export_logs=skip_export_logs,
                     # skip_audit_logs=skip_audit_logs,
                     default_group_id=default_group_id,
                     default_group_name=default_group_name,
                     groupnum_map=groupnum_map,
                     whichidnum_map=whichidnum_map)


def _get_all_ddl(dialect_name: str = SqlaDialectName.MYSQL) -> str:
    # noinspection PyUnresolvedReferences
    import camcops_server.camcops_server_core  # delayed import; import side effects  # noqa
    from camcops_server.cc_modules.cc_sqlalchemy import get_all_ddl  # delayed import  # noqa
    return get_all_ddl(dialect_name=dialect_name)


def _reindex(cfg: CamcopsConfig) -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    core.reindex(cfg=cfg)


def _check_index(cfg: CamcopsConfig,
                 show_all_bad: bool = False) -> bool:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    return core.check_index(cfg=cfg, show_all_bad=show_all_bad)


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

def make_wsgi_app_from_config() -> "Router":
    """
    Reads the config file and creates a WSGI application.
    """
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    cfg = get_default_config_from_os_env()
    reverse_proxied_config = ReverseProxiedConfig(
        trusted_proxy_headers=cfg.trusted_proxy_headers,
        http_host=cfg.proxy_http_host,
        remote_addr=cfg.proxy_remote_addr,
        script_name=(
            cfg.proxy_script_name or
            os.environ.get(WsgiEnvVar.SCRIPT_NAME, "")
        ),
        server_port=cfg.proxy_server_port,
        server_name=cfg.proxy_server_name,
        url_scheme=cfg.proxy_url_scheme,
        rewrite_path_info=cfg.proxy_rewrite_path_info,
    )
    return core.make_wsgi_app(
        debug_toolbar=cfg.debug_toolbar,
        reverse_proxied_config=reverse_proxied_config,
        debug_reverse_proxy=cfg.debug_reverse_proxy,
        show_requests=cfg.show_requests,
        show_request_immediately=cfg.show_request_immediately,
        show_response=cfg.show_response,
        show_timing=cfg.show_timing,
    )


def _test_serve_pyramid() -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    application = make_wsgi_app_from_config()
    cfg = get_default_config_from_os_env()
    core.test_serve_pyramid(application=application,
                            host=cfg.host,
                            port=cfg.port)


def _serve_cherrypy() -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    application = make_wsgi_app_from_config()
    cfg = get_default_config_from_os_env()
    core.serve_cherrypy(
        application=application,
        host=cfg.host,
        port=cfg.port,
        unix_domain_socket_filename=cfg.unix_domain_socket,
        threads_start=cfg.cherrypy_threads_start,
        threads_max=cfg.cherrypy_threads_max,
        server_name=cfg.cherrypy_server_name,
        log_screen=cfg.cherrypy_root_path,
        ssl_certificate=cfg.ssl_certificate,
        ssl_private_key=cfg.ssl_private_key,
        root_path=cfg.cherrypy_root_path)


def _serve_gunicorn() -> None:
    import camcops_server.camcops_server_core as core  # delayed import; import side effects  # noqa
    application = make_wsgi_app_from_config()
    cfg = get_default_config_from_os_env()
    core.serve_gunicorn(
        application=application,
        host=cfg.host,
        port=cfg.port,
        unix_domain_socket_filename=cfg.unix_domain_socket,
        num_workers=cfg.gunicorn_num_workers,
        ssl_certificate=cfg.ssl_certificate,
        ssl_private_key=cfg.ssl_private_key,
        reload=cfg.gunicorn_debug_reload,
        timeout_s=cfg.gunicorn_timeout_s,
        debug_show_gunicorn_options=cfg.debug_show_gunicorn_options)


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
        cfg_help = (
            f"Configuration file (if not specified, the environment"
            f" variable {ENVVAR_CONFIG_FILE} is checked)"
        )
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
                  action: str = None, type: Type = None) -> None:
    """
    Adds a required but named argument. This is a bit unconventional; for
    example, making the ``--config`` option mandatory even though ``--`` is
    usually a prefix for optional arguments.

    Args:
        sp: the :class:`ArgumentParser` to add to
        switch: passed to :func:`add_argument`
        help: passed to :func:`add_argument`
        action: passed to :func:`add_argument`
        type: passed to :func:`add_argument`
    """
    # noinspection PyProtectedMember
    reqgroup = next((g for g in sp._action_groups
                     if g.title == _REQNAMED), None)
    if not reqgroup:
        reqgroup = sp.add_argument_group(_REQNAMED)
    kwargs = dict(required=True, help=help)
    if action:
        assert type is None, "Don't specify action and type"
        kwargs["action"] = action
    elif type:
        kwargs["type"] = type
    reqgroup.add_argument(switch, **kwargs)


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
            f"CamCOPS server, created by Rudolf Cardinal; version "
            f"{CAMCOPS_SERVER_VERSION}.\n"
            f"Use 'camcops_server <COMMAND> --help' for more detail on each "
            f"command."
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
        version=f"CamCOPS {CAMCOPS_SERVER_VERSION}")
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
    dev_upgrade_db_parser = add_sub(
        subparsers, "dev_upgrade_db", config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Upgrade a database to "
             "a specific revision."
    )
    dev_upgrade_db_parser.add_argument(
        "--destination_db_revision", type=str, required=True,
        help="The target database revision"
    )
    dev_upgrade_db_parser.add_argument(
        "--show_sql_only", action="store_true",
        help="Show SQL only (to stdout); don't execute it"
    )
    dev_upgrade_db_parser.set_defaults(
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
    # noinspection PyTypeChecker
    int_int_mapper = MapType(from_type=nonnegative_int,
                             to_type=nonnegative_int)
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
    # mergedb_parser.add_argument(
    #     '--skip_export_logs', action="store_true",
    #     help="Skip the export log tables")
    # mergedb_parser.add_argument(
    #     '--skip_audit_logs', action="store_true",
    #     help="Skip the audit log table")
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
    # noinspection PyTypeChecker
    add_req_named(
        mergedb_parser,
        "--whichidnum_map",
        type=int_int_mapper,
        help="Map to convert ID number types, in the format "
             "'from_a:to_a,from_b:to_b,...', where all values are integers.")
    # noinspection PyTypeChecker
    add_req_named(
        mergedb_parser,
        "--groupnum_map",
        type=int_int_mapper,
        help="Map to convert group numbers, in the format "
             "'from_a:to_a,from_b:to_b,...', where all values are integers.")
    mergedb_parser.set_defaults(func=lambda args: _merge_camcops_db(
        src=args.src,
        echo=args.echo,
        report_every=args.report_every,
        dummy_run=args.dummy_run,
        info_only=args.info_only,
        # skip_export_logs=args.skip_export_logs,
        # skip_audit_logs=args.skip_audit_logs,
        default_group_id=args.default_group_id,
        default_group_name=args.default_group_name,
        whichidnum_map=args.whichidnum_map,
        groupnum_map=args.groupnum_map,
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
        help=f"SQL dialect (options: {', '.join(ALL_SQLA_DIALECTS)})")
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

    check_index_parser = add_sub(
        subparsers, "check_index",
        help="Check index validity (exit code 0 for OK, 1 for bad)"
    )
    check_index_parser.add_argument(
        "--show_all_bad", action="store_true",
        help="Show all bad index entries (rather than stopping at the first)"
    )
    check_index_parser.set_defaults(
        func=lambda args: _check_index(
            cfg=get_default_config_from_os_env(),
            show_all_bad=args.show_all_bad
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
        help="Start web server via CherryPy")
    serve_cp_parser.set_defaults(func=lambda args: _serve_cherrypy())

    # Serve via Gunicorn
    serve_gu_parser = add_sub(
        subparsers, "serve_gunicorn",
        help="Start web server via Gunicorn (not available under Windows)")
    serve_gu_parser.set_defaults(func=lambda args: _serve_gunicorn())

    # Serve via the Pyramid test server
    serve_pyr_parser = add_sub(
        subparsers, "serve_pyramid",
        help="Start test web server via Pyramid (single-thread, "
             "single-process, HTTP-only; for development use only)")
    serve_pyr_parser.set_defaults(func=lambda args: _test_serve_pyramid())

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
# =============================================================================
""",
        version=CAMCOPS_SERVER_VERSION,
        url=CAMCOPS_URL,
    )
    log.debug(
        """
# -----------------------------------------------------------------------------
# Python interpreter: {interpreter!r}
# This program: {thisprog!r}
# Command-line arguments:
{progargs}
# -----------------------------------------------------------------------------
""",
        interpreter=sys.executable,
        thisprog=__file__,
        progargs=pprint.pformat(vars(progargs)),
    )
    if DEBUG_LOG_CONFIG or DEBUG_RUN_WITH_PDB:
        log.warning("Debugging options enabled!")
    if DEBUG_LOG_CONFIG:
        print_report_on_all_logs()

    if progargs.command not in ["self_test"]:
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
