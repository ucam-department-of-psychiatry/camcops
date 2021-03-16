#!/usr/bin/env python

r"""
tools/release_new_version.py

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

"""

from datetime import datetime
import logging
import os
import re
from subprocess import run
import sys
from typing import List, Optional, Tuple

from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_CHANGEDATE,
    CAMCOPS_SERVER_VERSION_STRING,
)
from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from semantic_version import Version

EXIT_FAILURE = 1

ROOT_TOOLS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.join(ROOT_TOOLS_DIR, "..")
DOCS_SOURCE_DIR = os.path.join(PROJECT_ROOT, "docs", "source")
CPP_SOURCE_DIR = os.path.join(PROJECT_ROOT, "tablet_qt")
CHANGELOG = os.path.join(DOCS_SOURCE_DIR, "changelog.rst")
CLIENT_VERSION_FILE = os.path.join(CPP_SOURCE_DIR,
                                   "version",
                                   "camcopsversion.cpp")
INNOSETUP_FILE = os.path.join(CPP_SOURCE_DIR,
                              "camcops_windows_innosetup.iss")

log = logging.getLogger(__name__)


# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
def in_virtualenv() -> bool:
    return (
        hasattr(sys, "real_prefix") or
        (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )


def run_with_check(args: List[str]) -> None:
    run(args, check=True)


def get_progress_version() -> Optional[Version]:
    progress_version = None

    regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*(IN PROGRESS).*\*\*$"
    with open(CHANGELOG, "r") as f:
        for line in f.readlines():
            m = re.match(regex, line)
            if m is not None:
                progress_version = Version(
                    major=int(m.group(1)),
                    minor=int(m.group(2)),
                    patch=int(m.group(3))
                )

    return progress_version


def get_released_versions() -> List[Tuple[datetime, Version]]:
    regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*released\s+(\d+)\s+([a-zA-Z]+)\s+(\d+).*\*\*$"  # noqa: E501

    releases = []

    with open(CHANGELOG, "r") as f:
        for line in f.readlines():
            m = re.match(regex, line)
            if m is not None:
                released_version = Version(
                    major=int(m.group(1)),
                    minor=int(m.group(2)),
                    patch=int(m.group(3))
                )

                try:
                    date_string = f"{m.group(4)} {m.group(5)} {m.group(6)}"
                    release_date = datetime.strptime(date_string, "%d %b %Y")
                except ValueError:
                    raise ValueError(f"Couldn't parse date when processing this line:\n{line}")

                releases.append((released_version, release_date))

    return releases


def get_client_version() -> Optional[Version]:
    regex = r"^const Version CAMCOPS_CLIENT_VERSION\((\d+),\s+(\d+),\s+(\d+)\);$"
    with open(CLIENT_VERSION_FILE, "r") as f:
        for line in f.readlines():
            m = re.match(regex, line)
            if m is not None:
                return Version(
                    major=int(m.group(1)),
                    minor=int(m.group(2)),
                    patch=int(m.group(3))
                )


def get_client_date() -> Optional[datetime]:
    regex = r"^const QDate CAMCOPS_CLIENT_CHANGEDATE\((\d+),\s+(\d+),\s+(\d+)\);$"
    with open(CLIENT_VERSION_FILE, "r") as f:
        for line in f.readlines():
            m = re.match(regex, line)
            if m is not None:
                return datetime(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3))
                )


def get_innosetup_version() -> Optional[Version]:
    regex = r"^#define CamcopsClientVersion \"(\d+)\.(\d+)\.(\d+)\""
    with open(INNOSETUP_FILE, "r") as f:
        for line in f.readlines():
            m = re.match(regex, line)
            if m is not None:
                return Version(
                    major=int(m.group(1)),
                    minor=int(m.group(2)),
                    patch=int(m.group(3))
                )


def main() -> None:
    if not in_virtualenv():
        log.error("release_new_version.py must be run inside virtualenv")
        sys.exit(EXIT_FAILURE)

    # This is a work in progress
    # What do we want this script to do?

    # Check and/or bump all the version numbers
    # Check and/or update the changelog
    # Check and tag the Git repository
    # Build the Ubuntu server packages (deb/rpm)
    # Build the pypi server package
    # Distribute the server packages to GitHub and PyPI

    # Build the client (depending on the platform)
    # Distribute to Play Store / Apple Store / GitHub

    # Ideally we want to do all the checks before tagging and building
    # so we don't get the version numbers spiralling out of control
    # this may be impossible for errors when deploying to Apple Store etc

    releases = get_released_versions()
    latest_version, latest_date = releases[-1]
    progress_version = get_progress_version()

    if progress_version is None:
        print(("No version is marked as IN PROGRESS in the changelog. "
               "Normally that would be the next unreleased version"))

    current_server_version = Version(CAMCOPS_SERVER_VERSION_STRING)
    current_server_date = datetime.strptime(CAMCOPS_SERVER_CHANGEDATE, "%Y-%m-%d")
    current_client_version = get_client_version()
    current_client_date = get_client_date()

    current_windows_version = get_innosetup_version()

    if current_server_version == progress_version:
        print(f"The current server version ({current_server_version}) matches "
              f"the current IN PROGRESS "
              f"version in the changelog. You probably want to bump the server "
              f"version, or mark the version in the changelog as released")

    if current_client_version == progress_version:
        print(f"The current client version ({current_client_version}) matches "
              f"the current IN PROGRESS version in the changelog. You probably "
              f"want to bump the server "
              f"version, or mark the version in the changelog as released")

    if current_client_version != current_windows_version:
        print(f"The current client version ({current_client_version}) does not "
              f"match the Windows InnoSetup version "
              f"({current_windows_version})")


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
