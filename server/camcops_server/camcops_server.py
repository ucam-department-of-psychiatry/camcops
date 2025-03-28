"""
camcops_server/camcops_server.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Command-line entry point for the CamCOPS server.**

"""

from argparse import ArgumentParser
import linecache
import logging
import os
import pprint
import sys
import tracemalloc
from typing import Dict, List, Optional, Type, TYPE_CHECKING
import warnings

from cardinal_pythonlib.argparse_func import (
    ShowAllSubparserHelpAction,
    MapType,
    nonnegative_int,
)
from cardinal_pythonlib.debugging import pdb_run
from cardinal_pythonlib.docker import running_under_docker
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
from rich_argparse import (
    ArgumentDefaultsRichHelpFormatter,
    RawDescriptionRichHelpFormatter,
)
from sqlalchemy import exc
from camcops_server.cc_modules.cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    EXIT_SUCCESS,
    EXIT_FAILURE,
    DOCUMENTATION_URL,
)
from camcops_server.cc_modules.cc_config import (
    CamcopsConfig,
    get_default_config_from_os_env,
    get_demo_apache_config,
    get_demo_config,
    get_demo_supervisor_config,
)
from camcops_server.cc_modules.cc_constants import (
    CAMCOPS_URL,
    DEFAULT_FLOWER_ADDRESS,
    DEFAULT_FLOWER_PORT,
)
from camcops_server.cc_modules.cc_pythonversion import (
    assert_minimum_python_version,
)
from camcops_server.cc_modules.cc_snomed import send_athena_icd_snomed_to_xml
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION

if TYPE_CHECKING:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    from argparse import _SubParsersAction

warnings.filterwarnings("error", category=exc.MovedIn20Warning)
warnings.filterwarnings("error", category=exc.SADeprecationWarning)

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Check Python version (the shebang is not a guarantee)
# =============================================================================

assert_minimum_python_version()


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_LOG_CONFIG = False
DEBUG_RUN_WITH_PDB = False
DEBUG_MEMORY_ALLOCATION = False

if any([DEBUG_LOG_CONFIG, DEBUG_RUN_WITH_PDB, DEBUG_MEMORY_ALLOCATION]):
    log.warning("Debugging options enabled!")


# =============================================================================
# Simple command-line functions
# =============================================================================


def launch_manual() -> None:
    """
    Use the operating system "launch something" tool to show the CamCOPS
    documentation.
    """
    launch_external_file(DOCUMENTATION_URL)


def print_demo_camcops_config(docker: bool = False) -> None:
    """
    Prints a demonstration config file to stdout.
    """
    print(get_demo_config(for_docker=docker or running_under_docker()))


def print_demo_supervisor_config() -> None:
    """
    Prints a demonstration ``supervisord`` config file to stdout.
    """
    print(get_demo_supervisor_config())


def print_demo_apache_config(rootpath: str) -> None:
    """
    Prints a demonstration Apache HTTPD config file segment (for CamCOPS)
    to stdout.
    """
    print(get_demo_apache_config(rootpath=rootpath))


# =============================================================================
# Stub command-line functions requiring more substantial imports
# =============================================================================

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------


def _upgrade_database_to_head(
    cfg: "CamcopsConfig", show_sql_only: bool, reindex: bool = False
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    from camcops_server.cc_modules.cc_alembic import (
        upgrade_database_to_head,
    )  # delayed import

    upgrade_database_to_head(camcops_cfg=cfg, show_sql_only=show_sql_only)
    if reindex and not show_sql_only:
        core.reindex(cfg)


def _upgrade_database_to_revision(
    cfg: "CamcopsConfig", revision: str, show_sql_only: bool = False
) -> None:
    import camcops_server.camcops_server_core as core  # noqa: F401

    # ... delayed import; import side effects

    from camcops_server.cc_modules.cc_alembic import (
        upgrade_database_to_revision,
    )  # delayed import

    upgrade_database_to_revision(
        camcops_cfg=cfg, revision=revision, show_sql_only=show_sql_only
    )


def _downgrade_database_to_revision(
    cfg: "CamcopsConfig",
    revision: str,
    show_sql_only: bool = False,
    confirm_downgrade_db: bool = False,
) -> None:
    import camcops_server.camcops_server_core as core  # noqa: F401

    # ... delayed import; import side effects

    from camcops_server.cc_modules.cc_alembic import (
        downgrade_database_to_revision,
    )  # delayed import

    downgrade_database_to_revision(
        camcops_cfg=cfg,
        revision=revision,
        show_sql_only=show_sql_only,
        confirm_downgrade_db=confirm_downgrade_db,
    )


def _add_dummy_data(
    cfg: "CamcopsConfig", confirm_add_dummy_data: bool = False
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.add_dummy_data(cfg, confirm_add_dummy_data=confirm_add_dummy_data)


def _create_database_from_scratch(cfg: "CamcopsConfig") -> None:
    import camcops_server.camcops_server_core as core  # noqa: F401

    # ... delayed import; import side effects
    from camcops_server.cc_modules.cc_alembic import (
        create_database_from_scratch,
    )  # delayed import

    create_database_from_scratch(camcops_cfg=cfg)


def _print_database_title() -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.print_database_title()


def _show_database_schema(
    schemastem: str,
    make_image: bool = False,
    java: str = None,
    plantuml: str = None,
    height_width_limit: int = None,
    java_memory_limit_mb: int = None,
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.show_database_schema(
        schemastem=schemastem,
        make_image=make_image,
        java=java,
        plantuml=plantuml,
        height_width_limit=height_width_limit,
        java_memory_limit_mb=java_memory_limit_mb,
    )


def _merge_camcops_db(
    src: str,
    echo: bool,
    report_every: int,
    dummy_run: bool,
    info_only: bool,
    # skip_export_logs: bool,
    # skip_audit_logs: bool,
    default_group_id: Optional[int],
    default_group_name: Optional[str],
    groupnum_map: Dict[int, int],
    whichidnum_map: Dict[int, int],
) -> None:
    import camcops_server.camcops_server_core as core  # noqa: F401

    # ... delayed import; import side effects

    from camcops_server.cc_modules.merge_db import (
        merge_camcops_db,
    )  # delayed import

    merge_camcops_db(
        src=src,
        echo=echo,
        report_every=report_every,
        dummy_run=dummy_run,
        info_only=info_only,
        # skip_export_logs=skip_export_logs,
        # skip_audit_logs=skip_audit_logs,
        default_group_id=default_group_id,
        default_group_name=default_group_name,
        groupnum_map=groupnum_map,
        whichidnum_map=whichidnum_map,
    )


def _get_all_ddl(dialect_name: str = SqlaDialectName.MYSQL) -> str:
    import camcops_server.camcops_server_core as core  # noqa: F401

    # ... delayed import; import side effects

    from camcops_server.cc_modules.cc_sqlalchemy import (
        get_all_ddl,
    )  # delayed import

    return get_all_ddl(dialect_name=dialect_name)


def _reindex(cfg: CamcopsConfig) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.reindex(cfg=cfg)


def _check_index(cfg: CamcopsConfig, show_all_bad: bool = False) -> bool:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    return core.check_index(cfg=cfg, show_all_bad=show_all_bad)


# -----------------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------------


def _make_superuser(username: str = None, password: str = None) -> bool:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    return core.make_superuser(username=username, password=password)


def _reset_password(username: str = None) -> bool:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    return core.reset_password(username=username)


def _enable_user_cli(username: str = None) -> bool:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    return core.enable_user_cli(username=username)


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------


def _cmd_export(
    recipient_names: List[str] = None,
    all_recipients: bool = False,
    via_index: bool = True,
    schedule_via_backend: bool = False,
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    return core.cmd_export(
        recipient_names=recipient_names,
        all_recipients=all_recipients,
        via_index=via_index,
        schedule_via_backend=schedule_via_backend,
    )


def _cmd_show_export_queue(
    recipient_names: List[str] = None,
    all_recipients: bool = False,
    via_index: bool = True,
    pretty: bool = False,
    debug_show_fhir: bool = False,
    debug_fhir_include_docs: bool = False,
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.cmd_show_export_queue(
        recipient_names=recipient_names,
        all_recipients=all_recipients,
        via_index=via_index,
        pretty=pretty,
        debug_show_fhir=debug_show_fhir,
        debug_fhir_include_docs=debug_fhir_include_docs,
    )


def _cmd_crate_dd(filename: str, recipient_name: str) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.make_data_dictionary(
        filename=filename, recipient_name=recipient_name, cris=False
    )


def _cmd_cris_dd(filename: str, recipient_name: str) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.make_data_dictionary(
        filename=filename, recipient_name=recipient_name, cris=True
    )


# -----------------------------------------------------------------------------
# Web server
# -----------------------------------------------------------------------------


def _test_serve_pyramid(cfg: "CamcopsConfig") -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.test_serve_pyramid(cfg)


def _serve_cherrypy(cfg: "CamcopsConfig") -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.serve_cherrypy(cfg)


def _serve_gunicorn(cfg: "CamcopsConfig") -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.serve_gunicorn(cfg)


# -----------------------------------------------------------------------------
# Celery etc.
# -----------------------------------------------------------------------------


def _launch_celery_workers(
    cfg: "CamcopsConfig", verbose: bool = False
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.launch_celery_workers(config=cfg, verbose=verbose)


def _launch_celery_beat(cfg: "CamcopsConfig", verbose: bool = False) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.launch_celery_beat(config=cfg, verbose=verbose)


def _launch_celery_flower(
    address: str = DEFAULT_FLOWER_ADDRESS, port: int = DEFAULT_FLOWER_PORT
) -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.launch_celery_flower(address=address, port=port)


def _housekeeping() -> None:
    from camcops_server.cc_modules.celery import housekeeping  # delayed import

    housekeeping()


def _purge_jobs() -> None:
    from camcops_server.cc_modules.celery import purge_jobs  # delayed import

    purge_jobs()


# -----------------------------------------------------------------------------
# Testing and development
# -----------------------------------------------------------------------------


def _dev_cli(cfg: "CamcopsConfig") -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.dev_cli(config=cfg)


def _list_tasks() -> None:
    import camcops_server.camcops_server_core as core

    # ... delayed import; import side effects

    core.print_tasklist()


# =============================================================================
# Command-line processor
# =============================================================================

_REQNAMED = "required named arguments"


# noinspection PyShadowingBuiltins
def add_sub(
    sp: "_SubParsersAction",
    cmd: str,
    config_mandatory: Optional[bool] = False,
    description: str = None,
    help: str = None,
) -> ArgumentParser:
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
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )  # type: ArgumentParser

    # This needs to be in the top-level parser and the sub-parsers (it does not
    # appear in the subparsers just because it's in the top-level parser, which
    # sounds like an argparse bug given its help, but there you go).
    subparser.add_argument(
        "-v", "--verbose", action="store_true", help="Be verbose"
    )

    # Config file handling
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
def add_req_named(
    sp: ArgumentParser,
    switch: str,
    help: str,
    action: str = None,
    type: Type = None,
) -> None:
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
    reqgroup = next(
        (g for g in sp._action_groups if g.title == _REQNAMED), None
    )
    if not reqgroup:
        reqgroup = sp.add_argument_group(_REQNAMED)
    kwargs = dict(required=True, help=help)
    if action:
        assert type is None, "Don't specify action and type"
        kwargs["action"] = action
    elif type:
        kwargs["type"] = type
    reqgroup.add_argument(switch, **kwargs)  # type: ignore[arg-type]


def camcops_main() -> int:
    """
    Primary command-line entry point. Parse command-line arguments and act.

    Note that we can't easily use delayed imports to speed up the help output,
    because the help system has function calls embedded into it.
    """
    # Fetch command-line options.

    # -------------------------------------------------------------------------
    # Base parser
    # -------------------------------------------------------------------------

    # noinspection PyTypeChecker
    parser = ArgumentParser(
        description=(
            f"CamCOPS server, created by Rudolf Cardinal; version "
            f"{CAMCOPS_SERVER_VERSION}.\n"
            f"Use 'camcops_server <COMMAND> --help' for more detail on each "
            f"command."
        ),
        formatter_class=RawDescriptionRichHelpFormatter,
        # add_help=False  # only do this if manually overriding the method
    )

    # -------------------------------------------------------------------------
    # Common arguments
    # -------------------------------------------------------------------------

    # noinspection PyTypeChecker
    parser.add_argument(
        "--allhelp",
        action=ShowAllSubparserHelpAction,
        help="show help for all commands and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"CamCOPS {CAMCOPS_SERVER_VERSION}",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Be verbose"
    )
    parser.add_argument(
        "--no_log", action="store_true", help="Disable log (stderr) entirely."
    )

    # -------------------------------------------------------------------------
    # Subcommand subparser
    # -------------------------------------------------------------------------

    subparsers = parser.add_subparsers(
        title="commands",
        description="Valid CamCOPS commands are as follows.",
        help="Specify one command.",
        dest="command",  # sorts out the help for the command being mandatory
        # https://stackoverflow.com/questions/23349349/argparse-with-required-subparser  # noqa
    )  # type: _SubParsersAction
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
        subparsers,
        "docs",
        config_mandatory=None,
        help="Launch the main documentation (CamCOPS manual)",
    )
    docs_parser.set_defaults(func=lambda args: launch_manual())

    # Print demo CamCOPS config
    democonfig_parser = add_sub(
        subparsers,
        "demo_camcops_config",
        config_mandatory=None,
        help="Print a demo CamCOPS config file",
    )
    democonfig_parser.add_argument(
        "--docker", action="store_true", help="Use settings for Docker"
    )
    democonfig_parser.set_defaults(
        func=lambda args: print_demo_camcops_config(docker=args.docker)
    )

    # Print demo supervisor config
    demosupervisorconf_parser = add_sub(
        subparsers,
        "demo_supervisor_config",
        config_mandatory=None,
        help="Print a demo 'supervisor' config file for CamCOPS",
    )
    demosupervisorconf_parser.set_defaults(
        func=lambda args: print_demo_supervisor_config()
    )

    # Print demo Apache config section
    demoapacheconf_parser = add_sub(
        subparsers,
        "demo_apache_config",
        config_mandatory=None,
        help="Print a demo Apache config file section for CamCOPS",
    )
    demoapacheconf_parser.set_defaults(
        func=lambda args: print_demo_apache_config(rootpath=args.path)
    )
    demoapacheconf_parser.add_argument(
        "--path",
        default="",
        help=(
            "Path where CamCOPS should appear on the server "
            "e.g. 'camcops' for https://example.com/camcops"
        ),
    )

    # -------------------------------------------------------------------------
    # Database commands
    # -------------------------------------------------------------------------

    # Upgrade database
    upgradedb_parser = add_sub(
        subparsers,
        "upgrade_db",
        config_mandatory=True,
        help="Upgrade database to most recent version (via Alembic)",
    )
    upgradedb_parser.add_argument(
        "--show_sql_only",
        action="store_true",
        help="Show SQL only (to stdout); don't execute it",
    )
    upgradedb_parser.add_argument(
        "--no_reindex",
        action="store_true",
        help="Don't recreate the task index",
    )
    upgradedb_parser.set_defaults(
        func=lambda args: _upgrade_database_to_head(
            cfg=get_default_config_from_os_env(),
            show_sql_only=args.show_sql_only,
            reindex=not args.no_reindex,
        )
    )

    # Developer: upgrade database to a specific revision
    dev_upgrade_db_parser = add_sub(
        subparsers,
        "dev_upgrade_db",
        config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Upgrade a database to "
        "a specific revision.",
    )
    dev_upgrade_db_parser.add_argument(
        "--destination_db_revision",
        type=str,
        required=True,
        help="The target database revision",
    )
    dev_upgrade_db_parser.add_argument(
        "--show_sql_only",
        action="store_true",
        help="Show SQL only (to stdout); don't execute it",
    )
    dev_upgrade_db_parser.set_defaults(
        func=lambda args: _upgrade_database_to_revision(
            cfg=get_default_config_from_os_env(),
            revision=args.destination_db_revision,
            show_sql_only=args.show_sql_only,
        )
    )

    # Developer: downgrade database
    dev_downgrade_parser = add_sub(
        subparsers,
        "dev_downgrade_db",
        config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Downgrades a database to "
        "a specific revision. May DESTROY DATA.",
    )
    dev_downgrade_parser.add_argument(
        "--destination_db_revision",
        type=str,
        required=True,
        help="The target database revision",
    )
    dev_downgrade_parser.add_argument(
        "--confirm_downgrade_db",
        action="store_true",
        help="Must specify this too, as a safety measure",
    )
    dev_downgrade_parser.add_argument(
        "--show_sql_only",
        action="store_true",
        help="Show SQL only (to stdout); don't execute it",
    )
    dev_downgrade_parser.set_defaults(
        func=lambda args: _downgrade_database_to_revision(
            cfg=get_default_config_from_os_env(),
            revision=args.destination_db_revision,
            show_sql_only=args.show_sql_only,
            confirm_downgrade_db=args.confirm_downgrade_db,
        )
    )

    # Developer: create dummy database
    dummy_database_parser = add_sub(
        subparsers,
        "dev_add_dummy_data",
        config_mandatory=True,
        help="(DEVELOPER OPTION ONLY.) Populates the database with "
        "a set of dummy patients and tasks for testing.",
    )

    dummy_database_parser.add_argument(
        "--confirm_add_dummy_data",
        action="store_true",
        help="Must specify this too, as a safety measure",
    )

    dummy_database_parser.set_defaults(
        func=lambda args: _add_dummy_data(
            cfg=get_default_config_from_os_env(),
            confirm_add_dummy_data=args.confirm_add_dummy_data,
        )
    )

    # Show database title
    showdbtitle_parser = add_sub(
        subparsers, "show_db_title", help="Show database title"
    )
    showdbtitle_parser.set_defaults(func=lambda args: _print_database_title())

    # Show database schema
    showdbschema_parser = add_sub(
        subparsers,
        "show_db_schema",
        help="Show the database schema as PlantUML +/- PNG",
    )
    showdbschema_parser.add_argument(
        "--schemastem",
        default="schema",
        help="Stem for output filenames (for schema diagrams); "
        "'.plantuml' and '.png' are appended",
    )
    showdbschema_parser.add_argument(
        "--make_image",
        action="store_true",
        help="Create a PNG image (impractically large!)",
    )
    showdbschema_parser.add_argument(
        "--java", default="java", help="Java executable (for schema diagrams)"
    )
    showdbschema_parser.add_argument(
        "--plantuml",
        default="plantuml.jar",
        help="PlantUML Java .jar file (for schema diagrams)",
    )
    showdbschema_parser.add_argument(
        "--height_width_limit",
        type=int,
        default=20000,
        help="Maximum image height/width in pixels",
    )
    showdbschema_parser.add_argument(
        "--java_memory_limit_mb",
        type=int,
        default=2048,
        help="Java virtual machine memory limit in Mb",
    )
    showdbschema_parser.set_defaults(
        func=lambda args: _show_database_schema(
            schemastem=args.schemastem,
            make_image=args.make_image,
            java=args.java,
            plantuml=args.plantuml,
            height_width_limit=args.height_width_limit,
            java_memory_limit_mb=args.java_memory_limit_mb,
        )
    )

    # Merge in data fom another database
    # noinspection PyTypeChecker
    int_int_mapper = MapType(
        from_type=nonnegative_int, to_type=nonnegative_int  # type: ignore[arg-type]  # noqa: E501
    )
    mergedb_parser = add_sub(
        subparsers,
        "merge_db",
        config_mandatory=True,
        help="Merge in data from an old or recent CamCOPS database",
    )
    mergedb_parser.add_argument(
        "--report_every",
        type=int,
        default=10000,
        help="Report progress every n rows",
    )
    mergedb_parser.add_argument(
        "--echo", action="store_true", help="Echo SQL to source database"
    )
    mergedb_parser.add_argument(
        "--dummy_run",
        action="store_true",
        help="Perform a dummy run only; do not alter destination database",
    )
    mergedb_parser.add_argument(
        "--info_only",
        action="store_true",
        help="Show table information only; don't do any work",
    )
    # mergedb_parser.add_argument(
    #     "--skip_export_logs", action="store_true",
    #     help="Skip the export log tables")
    # mergedb_parser.add_argument(
    #     "--skip_audit_logs", action="store_true",
    #     help="Skip the audit log table")
    mergedb_parser.add_argument(
        "--default_group_id",
        type=int,
        default=None,
        help="Default group ID (integer) to apply to old records without one. "
        "If none is specified, a new group will be created for such "
        "records.",
    )
    mergedb_parser.add_argument(
        "--default_group_name",
        type=str,
        default=None,
        help="If default_group_id is not specified, use this group name. The "
        "group will be looked up if it exists, and created if not.",
    )
    add_req_named(
        mergedb_parser,
        "--src",
        help="Source database (specified as an SQLAlchemy URL). The contents "
        "of this database will be merged into the database specified "
        "in the config file.",
    )
    # noinspection PyTypeChecker
    add_req_named(
        mergedb_parser,
        "--whichidnum_map",
        type=int_int_mapper,  # type: ignore[arg-type]
        help="Map to convert ID number types, in the format "
        "'from_a:to_a,from_b:to_b,...', where all values are integers.",
    )
    # noinspection PyTypeChecker
    add_req_named(
        mergedb_parser,
        "--groupnum_map",
        type=int_int_mapper,  # type: ignore[arg-type]
        help="Map to convert group numbers, in the format "
        "'from_a:to_a,from_b:to_b,...', where all values are integers.",
    )
    mergedb_parser.set_defaults(
        func=lambda args: _merge_camcops_db(
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
        )
    )
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
        subparsers,
        "create_db",
        config_mandatory=True,
        help="Create CamCOPS database from scratch (AVOID; use the upgrade "
        "facility instead)",
    )
    add_req_named(
        createdb_parser,
        "--confirm_create_db",
        action="store_true",
        help="Must specify this too, as a safety measure",
    )
    createdb_parser.set_defaults(
        func=lambda args: _create_database_from_scratch(
            cfg=get_default_config_from_os_env()
        )
    )

    # Print database schema
    ddl_parser = add_sub(
        subparsers,
        "ddl",
        help="Print database schema (data definition language; DDL)",
    )
    ddl_parser.add_argument(
        "--dialect",
        type=str,
        default=SqlaDialectName.MYSQL,
        help=f"SQL dialect (options: {', '.join(sorted(ALL_SQLA_DIALECTS))})",
    )
    ddl_parser.set_defaults(
        func=lambda args: print(_get_all_ddl(dialect_name=args.dialect))
    )

    # Rebuild server indexes
    reindex_parser = add_sub(subparsers, "reindex", help="Recreate task index")
    reindex_parser.set_defaults(
        func=lambda args: _reindex(cfg=get_default_config_from_os_env())
    )

    check_index_parser = add_sub(
        subparsers,
        "check_index",
        help="Check index validity (exit code 0 for OK, 1 for bad)",
    )
    check_index_parser.add_argument(
        "--show_all_bad",
        action="store_true",
        help="Show all bad index entries (rather than stopping at the first)",
    )
    check_index_parser.set_defaults(
        func=lambda args: _check_index(
            cfg=get_default_config_from_os_env(),
            show_all_bad=args.show_all_bad,
        )
    )

    # -------------------------------------------------------------------------
    # User commands
    # -------------------------------------------------------------------------

    # Make superuser
    superuser_parser = add_sub(
        subparsers,
        "make_superuser",
        help="Make superuser, or give superuser status to an existing user",
    )
    superuser_parser.add_argument(
        "--username",
        help="Username of superuser to create/promote (if omitted, you will "
        "be asked to type it in)",
    )
    superuser_parser.add_argument(
        "--password",
        help="Password of superuser to create (if omitted, you will "
        "be asked to type it in)",
    )
    superuser_parser.set_defaults(
        func=lambda args: _make_superuser(
            username=args.username, password=args.password
        )
    )

    # Reset a user's password
    password_parser = add_sub(
        subparsers, "reset_password", help="Reset a user's password"
    )
    password_parser.add_argument(
        "--username",
        help="Username to change password for (if omitted, you will be asked "
        "to type it in)",
    )
    password_parser.set_defaults(
        func=lambda args: _reset_password(username=args.username)
    )

    # Re-enable a locked account
    enableuser_parser = add_sub(
        subparsers, "enable_user", help="Re-enable a locked user account"
    )
    enableuser_parser.add_argument(
        "--username",
        help="Username to enable (if omitted, you will be asked "
        "to type it in)",
    )
    enableuser_parser.set_defaults(
        func=lambda args: _enable_user_cli(username=args.username)
    )

    # -------------------------------------------------------------------------
    # Export options
    # -------------------------------------------------------------------------

    def _add_export_options(sp: ArgumentParser) -> None:
        sp.add_argument(
            "--recipients",
            type=str,
            nargs="*",
            help="Export recipients (as named in config file)",
        )
        sp.add_argument(
            "--all_recipients", action="store_true", help="Use all recipients"
        )
        sp.add_argument(
            "--disable_task_index",
            action="store_true",
            help="Disable use of the task index (for debugging only)",
        )

    # Export data
    export_parser = add_sub(
        subparsers, "export", help="Trigger pending exports"
    )
    _add_export_options(export_parser)
    export_parser.add_argument(
        "--schedule_via_backend",
        action="store_true",
        help="Export tasks as a background job",
    )
    export_parser.set_defaults(
        func=lambda args: _cmd_export(
            recipient_names=args.recipients,
            all_recipients=args.all_recipients,
            via_index=not args.disable_task_index,
            schedule_via_backend=args.schedule_via_backend,
        )
    )

    # Show export queue
    show_export_queue_parser = add_sub(
        subparsers,
        "show_export_queue",
        help="View outbound export queue (without sending)",
    )
    _add_export_options(show_export_queue_parser)
    show_export_queue_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty (but slower) formatting for tasks",
    )
    show_export_queue_parser.add_argument(
        "--debug_show_fhir",
        action="store_true",
        help="Show FHIR output for tasks",
    )
    show_export_queue_parser.add_argument(
        "--debug_fhir_include_docs",
        action="store_true",
        help="(If --debug_show_fhir) Included FHIR documents? Large.",
    )
    show_export_queue_parser.set_defaults(
        func=lambda args: _cmd_show_export_queue(
            recipient_names=args.recipients,
            all_recipients=args.all_recipients,
            via_index=not args.disable_task_index,
            pretty=args.pretty,
            debug_show_fhir=args.debug_show_fhir,
            debug_fhir_include_docs=args.debug_fhir_include_docs,
        )
    )

    # Make CRATE data dictionary
    crate_dd_parser = add_sub(
        subparsers,
        "crate_dd",
        help="Make draft data dictionary for CRATE anonymisation tool",
    )
    crate_dd_parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="Output filename (data dictionary to write)",
    )
    crate_dd_parser.add_argument(
        "--recipient",
        type=str,
        required=True,
        help="Export recipient (as named in config file)",
    )
    crate_dd_parser.set_defaults(
        func=lambda args: _cmd_crate_dd(
            filename=args.filename, recipient_name=args.recipient
        )
    )

    # Make CRIS data dictionary
    cris_dd_parser = add_sub(
        subparsers,
        "cris_dd",
        help="Make draft data dictionary for CRIS anonymisation tool",
    )
    cris_dd_parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="Filename of data dictionary to write",
    )
    cris_dd_parser.add_argument(
        "--recipient",
        type=str,
        required=True,
        help="Export recipient (as named in config file)",
    )
    cris_dd_parser.set_defaults(
        func=lambda args: _cmd_cris_dd(
            filename=args.filename, recipient_name=args.recipient
        )
    )

    # -------------------------------------------------------------------------
    # Web server options
    # -------------------------------------------------------------------------

    # Serve via CherryPy
    serve_cp_parser = add_sub(
        subparsers, "serve_cherrypy", help="Start web server via CherryPy"
    )
    serve_cp_parser.set_defaults(
        func=lambda args: _serve_cherrypy(cfg=get_default_config_from_os_env())
    )

    # Serve via Gunicorn
    serve_gu_parser = add_sub(
        subparsers,
        "serve_gunicorn",
        help="Start web server via Gunicorn (not available under Windows)",
    )
    serve_gu_parser.set_defaults(
        func=lambda args: _serve_gunicorn(cfg=get_default_config_from_os_env())
    )

    # Serve via the Pyramid test server
    serve_pyr_parser = add_sub(
        subparsers,
        "serve_pyramid",
        help="Start test web server via Pyramid (single-thread, "
        "single-process, HTTP-only; for development use only)",
    )
    serve_pyr_parser.set_defaults(
        func=lambda args: _test_serve_pyramid(
            cfg=get_default_config_from_os_env()
        )
    )

    # -------------------------------------------------------------------------
    # Preprocessing options
    # -------------------------------------------------------------------------

    athena_icd_snomed_to_xml_parser = add_sub(
        subparsers,
        "convert_athena_icd_snomed_to_xml",
        help="Fetch SNOMED-CT codes for ICD-9-CM and ICD-10 from the Athena "
        "OHDSI data set (https://athena.ohdsi.org/) and write them to "
        "the CamCOPS XML format",
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--athena_concept_tsv_filename",
        type=str,
        required=True,
        help="Path to CONCEPT.csv file from Athena download",
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--athena_concept_relationship_tsv_filename",
        type=str,
        required=True,
        help="Path to CONCEPT_RELATIONSHIP.csv file from Athena download",
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--icd9_xml_filename",
        type=str,
        required=True,
        help="Filename of ICD-9-CM/SNOMED-CT XML file to write",
    )
    athena_icd_snomed_to_xml_parser.add_argument(
        "--icd10_xml_filename",
        type=str,
        required=True,
        help="Filename of ICD-10/SNOMED-CT XML file to write",
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
        subparsers,
        "launch_workers",
        help="Launch Celery workers, for background processing",
    )
    celery_worker_parser.set_defaults(
        func=lambda args: _launch_celery_workers(
            cfg=get_default_config_from_os_env(), verbose=args.verbose
        )
    )

    # Launch Celery Bear
    celery_beat_parser = add_sub(
        subparsers,
        "launch_scheduler",
        help="Launch Celery Beat scheduler, to schedule background jobs",
    )
    celery_beat_parser.set_defaults(
        func=lambda args: _launch_celery_beat(
            cfg=get_default_config_from_os_env(), verbose=args.verbose
        )
    )

    # Launch Celery Flower monitor
    celery_flower_parser = add_sub(
        subparsers,
        "launch_monitor",
        help="Launch Celery Flower monitor, to monitor background jobs",
    )
    celery_flower_parser.add_argument(
        "--address",
        type=str,
        default=DEFAULT_FLOWER_ADDRESS,
        help="Address to use for Flower",
    )
    celery_flower_parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_FLOWER_PORT,
        help="Port to use for Flower",
    )
    celery_flower_parser.set_defaults(
        func=lambda args: _launch_celery_flower(
            address=args.address, port=args.port
        )
    )

    # Housekeeping task
    housekeeping_parser = add_sub(
        subparsers,
        "housekeeping",
        help="Run housekeeping tasks (remove stale sessions, etc.)",
    )
    housekeeping_parser.set_defaults(func=lambda args: _housekeeping())

    # Purge Celery tasks
    purge_jobs_parser = add_sub(
        subparsers,
        "purge_jobs",
        help="Purge any outstanding background (back-end, worker) jobs",
    )
    purge_jobs_parser.set_defaults(func=lambda args: _purge_jobs())

    # -------------------------------------------------------------------------
    # Test options
    # -------------------------------------------------------------------------

    # Launch a Python command line
    dev_cli_parser = add_sub(
        subparsers,
        "dev_cli",
        help="Developer command-line interface, with config loaded as "
        "'config'.",
    )
    dev_cli_parser.set_defaults(
        func=lambda args: _dev_cli(cfg=get_default_config_from_os_env())
    )

    # Show tasklist
    list_tasks_parser = add_sub(
        subparsers,
        "list_tasks",
        help="List supported tasks.",
    )
    list_tasks_parser.set_defaults(func=lambda args: _list_tasks())

    # -------------------------------------------------------------------------
    # OK; parser built; now parse the arguments
    # -------------------------------------------------------------------------
    progargs = parser.parse_args()

    # Initial log level (overridden later by config file but helpful for start)
    if progargs.no_log:
        loglevel = logging.CRITICAL + 1
    elif progargs.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    main_only_quicksetup_rootlogger(
        level=loglevel, with_process_id=True, with_thread_id=True
    )
    rootlogger = logging.getLogger()
    set_level_for_logger_and_its_handlers(rootlogger, loglevel)

    # Say hello
    log.info(
        f"""
# =============================================================================
# CamCOPS server version {CAMCOPS_SERVER_VERSION}
# Created by Rudolf Cardinal. See {CAMCOPS_URL}
# =============================================================================
"""
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
    if DEBUG_LOG_CONFIG:
        print_report_on_all_logs()

    # Finalize the config filename; ensure it's in the environment variable
    if hasattr(progargs, "config") and progargs.config:
        # We want the the config filename in the environment from now on:
        os.environ[ENVVAR_CONFIG_FILE] = progargs.config
    cfg_name = os.environ.get(ENVVAR_CONFIG_FILE, None)
    log.debug("Using configuration file: {!r}", cfg_name)

    # Call the subparser function for the chosen command
    if progargs.func is None:
        raise NotImplementedError("Command-line function not implemented!")
    success = progargs.func(progargs)  # type: Optional[bool]
    if success is None or success is True:
        return EXIT_SUCCESS
    else:
        return EXIT_FAILURE


# =============================================================================
# Command-line entry point
# =============================================================================


def display_top(
    snapshot: tracemalloc.Snapshot,
    key_type: str = "lineno",
    limit: int = 10,
    short_filename: bool = False,
) -> None:
    """
    Display e.g. lines of code allocating the most memory.

    Args:
        snapshot: a :class:`tracemalloc.Snapshot` object
        key_type: thing to group by
        limit: show the top *n*
        short_filename: make source code filenames shorter?
    """
    # Modified from https://docs.python.org/3/library/tracemalloc.html
    print("Calculating memory allocation...")
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(
                False, "<frozen importlib._bootstrap_external>"
            ),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics(key_type)

    print(f"Top {limit} lines")
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        if short_filename:
            # replace "/path/to/module/file.py" with "module/file.py"
            filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        else:
            filename = frame.filename
        print(
            f"#{index}: {filename}:{frame.lineno}: "
            f"{stat.size / 1024:.1f} KiB"
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f"    {line}")

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print(f"{len(other)} other: {size / 1024:.1f} KiB")
    total = sum(stat.size for stat in top_stats)
    print(f"Total allocated size: {total / 1024:.1f} KiB")


def main() -> None:
    """
    Command-line entry point. Calls :func:`camcops_main`.
    """
    if DEBUG_MEMORY_ALLOCATION:
        tracemalloc.start()
    if DEBUG_RUN_WITH_PDB:
        retval = pdb_run(camcops_main)
    else:
        retval = camcops_main()
    if DEBUG_MEMORY_ALLOCATION:
        # https://docs.python.org/3/library/tracemalloc.html
        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot, key_type="lineno", limit=20)
    sys.exit(retval)


if __name__ == "__main__":
    main()
