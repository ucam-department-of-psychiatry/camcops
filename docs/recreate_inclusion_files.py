#!/usr/bin/env python

"""
docs/recreate_inclusion_files.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

**Rebuild inclusion files for documentation.**

That is, e.g. "command --help > somefile.txt".

"""

import datetime
import logging
from os.path import abspath, dirname, join, pardir, realpath
import subprocess
import sys
from typing import List

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger

log = logging.getLogger(__name__)

THIS_DIR = dirname(realpath(__file__))

DOCS_SOURCE_DIR = join(THIS_DIR, "source")
ADMIN_DIR = join(DOCS_SOURCE_DIR, "administrator")
USER_DIR = join(DOCS_SOURCE_DIR, "user")
DEV_DIR = join(DOCS_SOURCE_DIR, "developer")

CAMCOPS_ROOT_DIR = abspath(join(THIS_DIR, pardir))  # .../camcops
TABLET_BUILD_DIR = join(CAMCOPS_ROOT_DIR, "build-camcops-Linux_x86_64-Debug")
CAMCOPS_CLIENT_EXECUTABLE = join(TABLET_BUILD_DIR, "camcops")
TABLET_ROOT_DIR = join(CAMCOPS_ROOT_DIR, "tablet_qt")
TABLET_TOOLS_DIR = join(TABLET_ROOT_DIR, "tools")
SERVER_ROOT_DIR = join(CAMCOPS_ROOT_DIR, "server")  # .../camcops/server
SERVER_TOOLS_DIR = join(SERVER_ROOT_DIR, "tools")


def run_cmd(cmdargs: List[str],
            output_filename: str,
            timestamp: bool = False,
            comment_prefix: str = "# ",
            encoding: str = sys.getdefaultencoding()) -> None:
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
    """
    log.info(f"Running: {cmdargs}")
    output = subprocess.check_output(cmdargs).decode(encoding)
    log.info(f"... writing to: {output_filename}")
    with open(output_filename, "wt") as f:
        f.write(output)
        if timestamp:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{comment_prefix}Generated at {now}\n")


def main():
    # administrator
    run_cmd(["camcops_backup_mysql_database", "--help"],
            join(ADMIN_DIR, "camcops_backup_mysql_database_help.txt"))
    run_cmd(["camcops_server", "--allhelp"],
            join(ADMIN_DIR, "camcops_server_allhelp.txt"))
    run_cmd(["camcops_server_meta", "--help"],
            join(ADMIN_DIR, "camcops_server_meta_help.txt"))
    log.warning("Skipping camcops_windows_service_help.txt (requires Windows)")
    run_cmd(["camcops_server", "demo_camcops_config"],
            join(ADMIN_DIR, "demo_camcops_config.ini"))
    run_cmd(["camcops_server", "demo_supervisor_config"],
            join(ADMIN_DIR, "demo_supervisor_config.txt"))
    run_cmd(["camcops_server", "demo_apache_config"],
            join(ADMIN_DIR, "demo_apache_config.txt"))
    run_cmd(["camcops_fetch_snomed_codes", "--allhelp"],
            join(ADMIN_DIR, "camcops_fetch_snomed_codes_help.txt"))
    # developer
    run_cmd(["python", join(TABLET_TOOLS_DIR, "build_qt.py"), "--help"],
            join(DEV_DIR, "build_qt_help.txt"))
    run_cmd(["python", join(SERVER_TOOLS_DIR, "build_translations.py"),
             "--help"],
            join(DEV_DIR, "build_translations_help.txt"))
    run_cmd(["python", join(SERVER_TOOLS_DIR, "create_database_migration.py"),
             "--help"],
            join(DEV_DIR, "create_database_migration_help.txt"))
    run_cmd(["python", join(TABLET_TOOLS_DIR, "decrypt_sqlcipher.py"),
             "--help"],
            join(DEV_DIR, "decrypt_sqlcipher_help.txt"))
    run_cmd(["python", join(TABLET_TOOLS_DIR, "encrypt_sqlcipher.py"),
             "--help"],
            join(DEV_DIR, "encrypt_sqlcipher_help.txt"))
    run_cmd(["python", join(SERVER_TOOLS_DIR, "make_xml_skeleton.py"),
             "--help"],
            join(DEV_DIR, "make_xml_skeleton_help.txt"))
    run_cmd(["python", join(TABLET_TOOLS_DIR, "open_sqlcipher.py"),
             "--help"],
            join(DEV_DIR, "open_sqlcipher_help.txt"))
    # user
    run_cmd([CAMCOPS_CLIENT_EXECUTABLE, "--help"],
            join(USER_DIR, "camcops_client_help.txt"))

    log.info("Done.")


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
