#!/usr/bin/env python

"""
docs/recreate_inclusion_files.py

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

**Rebuild inclusion files for documentation.**

That is, e.g. "command --help > somefile.txt".

"""

import argparse
import datetime
import logging
import os
from os import DirEntry, environ, scandir
from os.path import abspath, dirname, exists, join, pardir, realpath
import re
import subprocess
import sys
from typing import Dict, Generator, List, Optional

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter

from camcops_server.cc_modules.cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    ENVVAR_GENERATING_CAMCOPS_DOCS,
    ENVVARS_PROHIBITED_DURING_DOC_BUILD,
)

log = logging.getLogger(__name__)

EXIT_FAILURE = 1

THIS_DIR = dirname(realpath(__file__))

DOCS_SOURCE_DIR = join(THIS_DIR, "source")
ADMIN_DIR = join(DOCS_SOURCE_DIR, "administrator")
USER_CLIENT_DIR = join(DOCS_SOURCE_DIR, "user_client")
DEV_DIR = join(DOCS_SOURCE_DIR, "developer")

CAMCOPS_ROOT_DIR = abspath(join(THIS_DIR, pardir))  # .../camcops
TABLET_ROOT_DIR = join(CAMCOPS_ROOT_DIR, "tablet_qt")
TABLET_TOOLS_DIR = join(TABLET_ROOT_DIR, "tools")
SERVER_ROOT_DIR = join(CAMCOPS_ROOT_DIR, "server")  # .../camcops/server
SERVER_TOOLS_DIR = join(SERVER_ROOT_DIR, "tools")


def build_directories() -> Generator[DirEntry, None, None]:
    with scandir(CAMCOPS_ROOT_DIR) as it:
        for entry in it:
            if entry.name.startswith("build-") and entry.is_dir():
                yield entry


def find_camcops_client_executable() -> Optional[str]:
    for entry in build_directories():
        camcops_executable = join(entry.path, "camcops")

        if exists(camcops_executable):
            return camcops_executable

    return None


def run_cmd(
    cmdargs: List[str],
    output_filename: str,
    timestamp: bool = False,
    comment_prefix: str = "# ",
    encoding: str = sys.getdefaultencoding(),
    replacement_dict: Optional[Dict[str, str]] = None,
) -> None:
    """
    Args:
        cmdargs:
            Command to run
        output_filename:
            File to write command's output to
        timestamp:
            Add timestamp? Perhaps helpful, but means that all files will
            appear to change whenever this script is run, because their
            timestamp will change.
        comment_prefix:
            Comment prefix for this type of output file
        encoding:
            Encoding to use
        replacement_dict:
            Optional dictionary of regexes to find and replace in the output
    """
    log.info(f"Running: {cmdargs}")

    if replacement_dict is None:
        replacement_dict = {}
    modified_env = environ.copy()
    modified_env[ENVVAR_GENERATING_CAMCOPS_DOCS] = "True"
    modified_env.pop("CAMCOPS_QT6_BASE_DIR", None)
    modified_env[ENVVAR_CONFIG_FILE] = "/path/to/camcops/config_file.ini"
    modified_env["POEDIT"] = "/path/to/poedit"
    modified_env["LCONVERT"] = "/path/to/lconvert"
    modified_env["LRELEASE"] = "/path/to/lrelease"
    modified_env["LUPDATE"] = "/path/to/lupdate"

    output = subprocess.check_output(cmdargs, env=modified_env).decode(
        encoding
    )

    for search, replace in replacement_dict.items():
        output = re.sub(search, replace, output, count=1, flags=re.MULTILINE)

    log.info(f"... writing to: {output_filename}")
    with open(output_filename, "wt") as f:
        f.write(output)
        if timestamp:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{comment_prefix}Generated at {now}\n")


def main() -> None:
    # -------------------------------------------------------------------------
    # Argument parser
    # -------------------------------------------------------------------------
    if sys.version_info < (3, 10):
        log.error("You must run this script with Python 3.10 or later")
        sys.exit(EXIT_FAILURE)

    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "--skip_client_help",
        action="store_true",
        help="Don't try to build the client help file",
        default=False,
    )
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Checks
    # -------------------------------------------------------------------------
    # After offering help to the command-line user, check the environment is
    # correct. That is, ensure none of the specified environment variables are
    # present (usually because they will mess up the default help!). But more
    # helpfully, clear the variables and proceed, rather than complaining
    # annoyingly.
    for k in ENVVARS_PROHIBITED_DURING_DOC_BUILD:
        os.environ.pop(k, None)  # remove key if present

    # Do this first to exit early if not built
    if not args.skip_client_help:
        # user
        camcops_client_executable = find_camcops_client_executable()
        if camcops_client_executable is None:
            log.error("Cannot find a camcops executable. Have you built it?")
            sys.exit(EXIT_FAILURE)
        run_cmd(
            [camcops_client_executable, "--help"],
            join(USER_CLIENT_DIR, "_camcops_client_help.txt"),
            replacement_dict={
                camcops_client_executable: "/path/to/camcops/client/executable"
            },
        )

    # -------------------------------------------------------------------------
    # Build the various inclusion files
    # -------------------------------------------------------------------------

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # administrator
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    run_cmd(
        ["camcops_backup_mysql_database", "--help"],
        join(ADMIN_DIR, "_camcops_backup_mysql_database_help.txt"),
    )
    run_cmd(
        ["camcops_server", "--allhelp"],
        join(ADMIN_DIR, "_camcops_server_allhelp.txt"),
    )
    run_cmd(
        ["camcops_server_meta", "--help"],
        join(ADMIN_DIR, "_camcops_server_meta_help.txt"),
    )
    log.warning("Skipping camcops_windows_service_help.txt (requires Windows)")

    secret_regex = (
        r"^(SESSION_COOKIE_SECRET = camcops_autogenerated_secret_)[\w-]+=="
    )
    secret_replacement = (
        r"\g<1>YhXZQ4zVMYobWawci-zbv6nn6B6iMrZcUkGjpko4pEx"
        r"jwNgOpgjGh0TVzUEMt1u3DlzRGI6RJVxd8ohvKGleag=="
    )

    run_cmd(
        ["camcops_server", "demo_camcops_config"],
        join(ADMIN_DIR, "_demo_camcops_config.ini"),
        replacement_dict={secret_regex: secret_replacement},
    )
    run_cmd(
        ["camcops_server", "demo_supervisor_config"],
        join(ADMIN_DIR, "_demo_supervisor_config.ini"),
    )
    run_cmd(
        ["camcops_server", "demo_apache_config"],
        join(ADMIN_DIR, "_demo_apache_config.conf"),
    )
    run_cmd(
        ["camcops_fetch_snomed_codes", "--allhelp"],
        join(ADMIN_DIR, "_camcops_fetch_snomed_codes_help.txt"),
    )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # developer
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    run_cmd(
        ["python", join(TABLET_TOOLS_DIR, "build_qt.py"), "--help"],
        join(DEV_DIR, "_build_qt_help.txt"),
    )
    run_cmd(
        [
            "python",
            join(SERVER_TOOLS_DIR, "build_server_translations.py"),
            "--help",
        ],
        join(DEV_DIR, "_build_server_translations_help.txt"),
    )
    run_cmd(
        [
            "python",
            join(SERVER_TOOLS_DIR, "create_database_migration.py"),
            "--help",
        ],
        join(DEV_DIR, "_create_database_migration_help.txt"),
    )
    run_cmd(
        [
            "python",
            join(TABLET_TOOLS_DIR, "build_client_translations.py"),
            "--help",
        ],
        join(DEV_DIR, "_build_client_translations_help.txt"),
    )
    run_cmd(
        ["python", join(TABLET_TOOLS_DIR, "decrypt_sqlcipher.py"), "--help"],
        join(DEV_DIR, "_decrypt_sqlcipher_help.txt"),
    )
    run_cmd(
        ["python", join(TABLET_TOOLS_DIR, "encrypt_sqlcipher.py"), "--help"],
        join(DEV_DIR, "_encrypt_sqlcipher_help.txt"),
    )
    run_cmd(
        ["python", join(SERVER_TOOLS_DIR, "make_xml_skeleton.py"), "--help"],
        join(DEV_DIR, "_make_xml_skeleton_help.txt"),
    )
    run_cmd(
        ["python", join(TABLET_TOOLS_DIR, "open_sqlcipher.py"), "--help"],
        join(DEV_DIR, "_open_sqlcipher_help.txt"),
    )

    log.info("Done.")


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
