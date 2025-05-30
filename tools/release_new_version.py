#!/usr/bin/env python

r"""
tools/release_new_version.py

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

"""

import argparse
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
import re
from subprocess import CalledProcessError, PIPE, run
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import ArgumentDefaultsRichHelpFormatter
from semantic_version import Version

from camcops_server.cc_modules.cc_version_string import (
    CAMCOPS_SERVER_CHANGEDATE,
    CAMCOPS_SERVER_VERSION_STRING,
)

EXIT_FAILURE = 1

ROOT_TOOLS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.join(ROOT_TOOLS_DIR, "..")

# Docs paths
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
REBUILD_DOCS = os.path.join(DOCS_DIR, "rebuild_docs.py")
DOCS_SOURCE_DIR = os.path.join(DOCS_DIR, "source")
CHANGELOG = os.path.join(DOCS_SOURCE_DIR, "changelog.rst")
APACHE_CONFIG_FILE = os.path.join(
    DOCS_SOURCE_DIR, "administrator", "_demo_apache_config.conf"
)
PLAY_STORE_RELEASE_HISTORY_FILE = os.path.join(
    DOCS_SOURCE_DIR, "developer", "play_store_release_history.csv"
)

# Server paths
SERVER_SOURCE_DIR = os.path.join(PROJECT_ROOT, "server")
SERVER_TOOLS_DIR = os.path.join(SERVER_SOURCE_DIR, "tools")
SERVER_DIST_DIR = os.path.join(SERVER_SOURCE_DIR, "dist")
SERVER_PACKAGE_DIR = os.path.join(SERVER_SOURCE_DIR, "packagebuild")
MAKE_LINUX_PACKAGES = os.path.join(SERVER_TOOLS_DIR, "MAKE_LINUX_PACKAGES.py")
SERVER_VERSION_FILE = os.path.join(
    SERVER_SOURCE_DIR, "camcops_server", "cc_modules", "cc_version_string.py"
)

# Client paths
CPP_SOURCE_DIR = os.path.join(PROJECT_ROOT, "tablet_qt")
PROJECT_FILE = os.path.join(CPP_SOURCE_DIR, "camcops.pro")
CLIENT_VERSION_FILE = os.path.join(
    CPP_SOURCE_DIR, "version", "camcopsversion.cpp"
)
ANDROID_MANIFEST_FILE = os.path.join(
    CPP_SOURCE_DIR, "android", "AndroidManifest.xml"
)
INNOSETUP_FILE = os.path.join(CPP_SOURCE_DIR, "camcops_windows_innosetup.iss")
IOS_INFO_PLIST_FILE = os.path.join(CPP_SOURCE_DIR, "ios", "Info.plist")

log = logging.getLogger(__name__)


# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
def in_virtualenv() -> bool:
    """
    Are we running inside a Python virtual environment?
    """
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def valid_date(date_string: str) -> datetime.date:
    """
    Converts a string like "2020-12-31" to a date, or raises.
    """
    # https://stackoverflow.com/questions/25470844/specify-date-format-for-python-argparse-input-arguments  # noqa: E501
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        message = f"Not a valid date: '{date_string}'"
        raise argparse.ArgumentTypeError(message)


class MissingCodeException(Exception):
    pass


class MissingVersionException(Exception):
    pass


class MissingDateException(Exception):
    pass


class VersionReleaser:
    client_version_search = (
        # (               1                       )( 2 )( 3  )( 4 )(  5 )( 6 )( 7  )   # noqa: E501
        r"(^const Version CAMCOPS_CLIENT_VERSION\()(\d+)(,\s+)(\d+)(,\s+)(\d+)(\);$)"  # noqa: E501
    )
    client_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    client_date_search = (
        # (               1                        )( 2 )( 3  )( 4 )(  5 )( 6 )( 7  )   # noqa: E501
        r"(^const QDate CAMCOPS_CLIENT_CHANGEDATE\()(\d+)(,\s+)(\d+)(,\s+)(\d+)(\);$)"  # noqa: E501
    )
    client_date_replace = r"\g<1>{year}\g<3>{month}\g<5>{day}\g<7>"

    windows_version_search = (
        # (              1                )( 2 )( 3)( 4 )( 5)( 6 )(7)
        r'(^#define CamcopsClientVersion ")(\d+)(\.)(\d+)(\.)(\d+)(")'
    )
    windows_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    android_version_search = (
        # (          1          )( 2 )( 3)( 4 )( 5)( 6 )(7)
        r'(android:versionName=")(\d+)(\.)(\d+)(\.)(\d+)(")'
    )
    android_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    android_version_codes_table_search = (
        # ( 1 ) (      2       ); ( 3 ) (      4      ))
        r"(\d+) (\(32-bit ARM\)); (\d+) (\(64-bit ARM\))"
    )

    android_32_bit_version_code_search = (
        r'(CAMCOPS_32_BIT_VERSION_CODE) = "(\d+)"'
    )
    android_32_bit_version_code_replace = r'\g<1> = "{code_32_bit}"'

    android_64_bit_version_code_search = (
        r'(CAMCOPS_64_BIT_VERSION_CODE) = "(\d+)"'
    )
    android_64_bit_version_code_replace = r'\g<1> = "{code_64_bit}"'

    ios_short_version_search = (
        # (                      1                         )( 3 )( 3)( 4 )( 5)( 6 )(    7    )  # noqa: E501
        r"(<key>CFBundleShortVersionString</key>\s+<string>)(\d+)(\.)(\d+)(\.)(\d+)(</string>)"  # noqa: E501
    )
    ios_short_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    ios_version_search = (
        # (                  1                  )( 2 )( 3)( 4 )( 5)( 6 )( 7)( 8 )(    9    )  # noqa: E501
        r"(<key>CFBundleVersion</key>\s+<string>)(\d+)(\.)(\d+)(\.)(\d+)(\.)(\d+)(</string>)"  # noqa: E501
    )
    ios_version_replace = (
        r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>{extra}\g<9>"
    )

    apache_config_version_search = (
        # (               1              )( 2 )( 3)( 4 )( 5)( 6 )( 7)
        r"(^# Created by CamCOPS version )(\d+)(\.)(\d+)(\.)(\d+)(\.)"
    )

    def __init__(
        self,
        new_client_version: Version,
        new_server_version: Version,
        release_date: datetime.date,
        update_versions: bool,
    ) -> None:
        self.new_client_version = new_client_version
        self.new_server_version = new_server_version
        self._progress_version = None
        self.release_date = release_date
        self._released_versions = None
        self.update_versions = update_versions
        self.errors = []

    def run_with_check(self, args: List[str]) -> None:
        """
        Run a command with arguments. Raise :exc:`CalledProcessError` if the
        exit code was not zero.
        """
        run(args, check=True)

    @property
    def progress_version(self) -> Optional[Version]:
        """
        Return the version number in the changelog marked "IN PROGRESS", or
        ``None``.
        """
        if self._progress_version is None:
            regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*(IN PROGRESS).*\*\*$"
            with open(CHANGELOG, "r") as f:
                for line in f.readlines():
                    m = re.match(regex, line)
                    if m is not None:
                        self._progress_version = Version(
                            major=int(m.group(1)),
                            minor=int(m.group(2)),
                            patch=int(m.group(3)),
                        )

        return self._progress_version

    @property
    def released_versions(self) -> List[Tuple[Version, datetime]]:
        """
        Returns a list of ``(version, date_released)`` tuples from the
        changelog.
        """
        if self._released_versions is None:
            self._released_versions = self._get_released_versions()

        return self._released_versions

    def _get_released_versions(self) -> List[Tuple[Version, datetime]]:
        regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*released\s+(\d+)\s+([a-zA-Z]+)\s+(\d+).*\*\*$"  # noqa: E501

        released_versions = []

        with open(CHANGELOG, "r") as f:
            for line in f.readlines():
                m = re.match(regex, line)
                if m is not None:
                    released_version = Version(
                        major=int(m.group(1)),
                        minor=int(m.group(2)),
                        patch=int(m.group(3)),
                    )

                    try:
                        date_string = f"{m.group(4)} {m.group(5)} {m.group(6)}"
                        release_date = datetime.strptime(
                            date_string, "%d %b %Y"
                        ).date()
                    except ValueError:
                        raise ValueError(
                            f"Couldn't parse date when processing "
                            f"this line:\n{line}"
                        )

                    released_versions.append((released_version, release_date))

        return released_versions

    def get_client_version(self) -> Version:
        """
        Return the current client version, from ``camcopsversion.cpp``, or
        raise.
        """
        with open(CLIENT_VERSION_FILE, "r") as f:
            for line in f.readlines():
                m = re.match(self.client_version_search, line)
                if m is not None:
                    return Version(
                        major=int(m.group(2)),
                        minor=int(m.group(4)),
                        patch=int(m.group(6)),
                    )

        raise MissingVersionException(
            "Could not find version in camcopsversion.cpp"
        )

    def get_client_date(self) -> datetime:
        """
        Return the client changedate, from ``camcopsversion.cpp``, or raise.
        """
        with open(CLIENT_VERSION_FILE, "r") as f:
            for line in f.readlines():
                m = re.match(self.client_date_search, line)
                if m is not None:
                    return datetime(
                        int(m.group(2)), int(m.group(4)), int(m.group(6))
                    ).date()

        raise MissingDateException("Could not find date in camcopsversion.cpp")

    def get_innosetup_version(self) -> Version:
        """
        Return the version number in the Inno Setup config file,
        ``camcops_windows_innosetup.iss`` or raise.
        """
        with open(INNOSETUP_FILE, "r") as f:
            for line in f.readlines():
                m = re.match(self.windows_version_search, line)
                if m is not None:
                    return Version(
                        major=int(m.group(2)),
                        minor=int(m.group(4)),
                        patch=int(m.group(6)),
                    )

        raise MissingVersionException(
            "Could not find version in camcops_windows_innosetup.iss"
        )

    def get_android_version(self) -> Version:
        """
        Returns the version number in the Android manifest,
        ``AndroidManifest.xml``, or raises.
        """
        with open(ANDROID_MANIFEST_FILE, "r") as f:
            m = re.search(self.android_version_search, f.read())
            if m is not None:
                return Version(
                    major=int(m.group(2)),
                    minor=int(m.group(4)),
                    patch=int(m.group(6)),
                )

        raise MissingVersionException(
            "Could not find version in AndroidManifest.xml"
        )

    def get_ios_short_version(self) -> Version:
        """
        Returns the short version number in the iOS ``Info.plist`` file, or
        raises.
        """
        with open(IOS_INFO_PLIST_FILE, "r") as f:
            m = re.search(self.ios_short_version_search, f.read())
            if m is not None:
                return Version(
                    major=int(m.group(2)),
                    minor=int(m.group(4)),
                    patch=int(m.group(6)),
                )

        raise MissingVersionException(
            "Could not find short version in Info.plist"
        )

    def get_ios_version(self) -> Tuple[int, int, int, int]:
        """
        Returns the version number in the iOS ``Info.plist`` file, or
        raises.

        Semantic_version doesn't like three dots
        so we return the version as a tuple of integers
        """
        with open(IOS_INFO_PLIST_FILE, "r") as f:
            m = re.search(self.ios_version_search, f.read())
            if m is not None:
                return (
                    int(m.group(2)),
                    int(m.group(4)),
                    int(m.group(6)),
                    int(m.group(8)),
                )

        raise MissingVersionException("Could not find version in Info.plist")

    def check_quick_link_years(self) -> None:
        ref_regex = r"- :ref:`(\d{4}) <changelog_(\d{4})>`$"
        refs = []

        with open(CHANGELOG, "r") as f:
            for line in f.readlines():
                m = re.match(ref_regex, line)
                if m is not None:
                    refs.append((m.group(1), m.group(2)))

        release_year = str(self.release_date.year)
        if (release_year, release_year) not in refs:
            self.errors.append(f"No :ref: for {release_year} in changelog")

        target_regex = r"\.\. _changelog_(\d{4})\:$"
        year_regex = r"(\d{4})$"

        targets = []
        headings = []

        with open(CHANGELOG, "r") as f:
            year_heading = None
            for line in f.readlines():
                m = re.match(target_regex, line)
                if m is not None:
                    target_year = m.group(1)
                    if (target_year, target_year) not in refs:
                        self.errors.append(
                            f"No :ref: for year {target_year} in changelog"
                        )
                    targets.append((target_year, target_year))

                if year_heading is not None and line == "~~~~\n":
                    if (year_heading, year_heading) not in refs:
                        self.errors.append(
                            f"No :ref:  for year {year_heading} in "
                            "changelog"
                        )
                    if year_heading != target_year:
                        self.errors.append(
                            f"{year_heading} appeared after {target_year} in "
                            "changelog"
                        )
                    headings.append((year_heading, year_heading))

                m = re.match(year_regex, line)
                if m is not None:
                    year_heading = m.group(1)
                else:
                    year_heading = None

            if targets != refs or headings != refs:
                self.errors.append(":ref: years:")
                self.errors.append([r[0] for r in refs])
                self.errors.append("target years:")
                self.errors.append([t[0] for t in targets])

                self.errors.append("year headings:")
                self.errors.append([h[0] for h in headings])
                self.errors.append(
                    "Mismatch between :ref: years, target years "
                    "and year headings"
                )

    def check_quick_link_versions(self) -> None:
        ref_regex = r"- :ref:`v(\d+\.\d+\.\d+) <changelog_v(\d+\.\d+\.\d+)>`$"
        refs = []

        with open(CHANGELOG, "r") as f:
            for line in f.readlines():
                m = re.match(ref_regex, line)
                if m is not None:
                    refs.append((Version(m.group(1)), Version(m.group(2))))

        if (self.release_version, self.release_version) not in refs:
            self.errors.append(
                f"No :ref: for {self.release_version} in changelog"
            )

        target_regex = r"\.\. _changelog_v(\d+\.\d+\.\d+)\:$"

        targets = []

        with open(CHANGELOG, "r") as f:
            for line in f.readlines():
                m = re.match(target_regex, line)
                if m is not None:
                    target_version = Version(m.group(1))
                    if (target_version, target_version) not in refs:
                        self.errors.append(
                            f"No :ref: for version {target_version} "
                            "in changelog"
                        )
                    targets.append((target_version, target_version))

        versions = []
        for version, date in self.released_versions:
            versions.append((version, version))

        if targets != refs or versions != refs:
            self.errors.append(":ref: versions:")
            self.errors.append([r[0] for r in refs])
            self.errors.append("target versions:")
            self.errors.append([t[0] for t in targets])
            self.errors.append("released versions:")
            self.errors.append([v[0] for v in versions])

            self.errors.append(
                "Mismatch between :ref: versions, target versions "
                "and version headings"
            )

    def check_server_version(self) -> None:
        if self.new_server_version == self.progress_version:
            self.errors.append(
                f"The desired server version ({self.new_server_version}) "
                "matches the current IN PROGRESS version in the changelog. "
                "You probably want to mark the version in the changelog as "
                "released"
            )

        current_server_version = Version(CAMCOPS_SERVER_VERSION_STRING)
        if current_server_version == self.new_server_version:
            return

        if self.update_versions:
            return self.update_file(
                SERVER_VERSION_FILE,
                r'^CAMCOPS_SERVER_VERSION_STRING = "(\d+)\.(\d+)\.(\d+)"',
                f'CAMCOPS_SERVER_VERSION_STRING = "{self.new_server_version}"',
            )

        self.errors.append(
            f"The current server version ({current_server_version}) "
            "does not match the desired server version "
            f"({self.new_server_version})"
        )

    def check_server_date(self) -> None:
        current_server_date = datetime.strptime(
            CAMCOPS_SERVER_CHANGEDATE, "%Y-%m-%d"
        ).date()
        if current_server_date == self.release_date:
            return

        if self.update_versions:
            new_date = self.release_date.strftime("%Y-%m-%d")

            return self.update_file(
                SERVER_VERSION_FILE,
                r'^CAMCOPS_SERVER_CHANGEDATE = "(\d{4})-(\d{2})-(\d{2})"',
                f'CAMCOPS_SERVER_CHANGEDATE = "{new_date}"',
            )

        self.errors.append(
            "The release date in cc_version_string.py "
            f"({current_server_date}) does not match the desired "
            f"release date ({self.release_date})"
        )

    def check_client_version(self) -> None:
        if self.new_client_version == self.progress_version:
            self.errors.append(
                f"The desired client version ({self.new_client_version}) "
                "matches the current IN PROGRESS version in the changelog. "
                "You probably want to mark the version in the changelog as "
                "released"
            )

        current_client_version = self.get_client_version()
        if current_client_version == self.new_client_version:
            return

        if self.update_versions:
            return self.update_file(
                CLIENT_VERSION_FILE,
                self.client_version_search,
                self.client_version_replace.format(
                    major=self.new_client_version.major,
                    minor=self.new_client_version.minor,
                    patch=self.new_client_version.patch,
                ),
            )

        self.errors.append(
            f"The current client version ({current_client_version}) "
            "does not match the desired client version "
            f"({self.new_client_version})"
        )

    def check_client_date(self) -> None:
        current_client_date = self.get_client_date()
        if current_client_date == self.release_date:
            return

        if self.update_versions:
            return self.update_file(
                CLIENT_VERSION_FILE,
                self.client_date_search,
                self.client_date_replace.format(
                    year=self.release_date.year,
                    month=self.release_date.month,
                    day=self.release_date.day,
                ),
            )

        self.errors.append(
            "The release date in camcopsversion.cpp "
            f"({current_client_date}) does not match the desired "
            f"release date ({self.release_date})"
        )

    def check_windows_version(self) -> None:
        current_windows_version = self.get_innosetup_version()
        if current_windows_version == self.new_client_version:
            return

        if self.update_versions:
            return self.update_file(
                INNOSETUP_FILE,
                self.windows_version_search,
                self.windows_version_replace.format(
                    major=self.new_client_version.major,
                    minor=self.new_client_version.minor,
                    patch=self.new_client_version.patch,
                ),
            )

        self.errors.append(
            f"The Windows InnoSetup version ({current_windows_version}) "
            f"does not match the desired client version "
            f"({self.new_client_version})"
        )

    def check_android_version(self) -> None:
        current_android_version = self.get_android_version()
        if current_android_version == self.new_client_version:
            return

        if self.update_versions:
            return self.update_file(
                ANDROID_MANIFEST_FILE,
                self.android_version_search,
                self.android_version_replace.format(
                    major=self.new_client_version.major,
                    minor=self.new_client_version.minor,
                    patch=self.new_client_version.patch,
                ),
            )

        self.errors.append(
            f"The Android version ({current_android_version}) "
            f"does not match the desired client version "
            f"({self.new_client_version})"
        )

    def check_ios_short_version(self) -> None:
        current_ios_short_version = self.get_ios_short_version()

        if current_ios_short_version == self.new_client_version:
            return

        if self.update_versions:
            return self.update_file(
                IOS_INFO_PLIST_FILE,
                self.ios_short_version_search,
                self.ios_short_version_replace.format(
                    major=self.new_client_version.major,
                    minor=self.new_client_version.minor,
                    patch=self.new_client_version.patch,
                ),
            )

        self.errors.append(
            f"The iOS short version ({current_ios_short_version}) "
            f"does not match the desired client version "
            f"({self.new_client_version})"
        )

    def check_ios_version(self) -> None:
        current_ios_version = self.get_ios_version()

        if (
            Version(
                major=current_ios_version[0],
                minor=current_ios_version[1],
                patch=current_ios_version[2],
            )
            == self.new_client_version
        ):
            return

        if self.update_versions:
            return self.update_file(
                IOS_INFO_PLIST_FILE,
                self.ios_version_search,
                self.ios_version_replace.format(
                    major=self.new_client_version.major,
                    minor=self.new_client_version.minor,
                    patch=self.new_client_version.patch,
                    extra=1,
                ),
            )

        self.errors.append(
            f"The iOS version ({current_ios_version}) "
            f"does not match the desired client version "
            f"({self.new_client_version})"
        )

    def check_android_releases_table(self) -> None:
        releases = self.get_android_releases()

        if not self.should_release_client:
            # Not updating the client but there should be a N/A entry for the
            # server version in the CSV table of releases included in the
            # developer documentation.
            if releases[-1]["version"] == self.new_server_version:
                return

            if self.update_versions:
                return self.append_to_releases_table(self.new_server_version)

            return self.errors.append(
                f"No 'N/A' entry for {self.new_server_version} in the Android "
                "releases table (included in the developer documentation)"
            )

        if releases[-1]["version"] == self.new_client_version:
            return

        next_32_bit_version_code = releases[-1]["code_32_bit"] + 2
        next_64_bit_version_code = releases[-1]["code_64_bit"] + 2

        if self.update_versions:
            version_code_string = (
                f"{next_32_bit_version_code} (32-bit ARM); "
                f"{next_64_bit_version_code} (64-bit ARM)"
            )

            return self.append_to_releases_table(
                self.new_client_version,
                version_code_string=version_code_string,
                version_name=self.new_client_version,
                release_date_string=self.release_date.strftime("%Y-%m-%d"),
                minimum_android_api=23,
                target_android_api=34,  # As of 2024-08-31
            )

        self.errors.append(
            f"No entry for {self.new_client_version} in the Android "
            "releases table (included in the developer documentation)"
        )

    def append_to_releases_table(
        self,
        release_name: Version,
        version_code_string: str = "N/A, server only",
        version_name: Union[Version, str] = "N/A",
        release_date_string: str = "N/A",
        minimum_android_api: Union[int, str] = "N/A",
        target_android_api: Union[int, str] = "N/A",
    ) -> None:
        with open(PLAY_STORE_RELEASE_HISTORY_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    release_name,
                    version_code_string,
                    version_name,
                    release_date_string,
                    minimum_android_api,
                    target_android_api,
                ]
            )

    def check_android_32_bit_version_code(self) -> None:
        if not self.should_release_client:
            return

        releases = self.get_android_releases()
        latest_32_bit_version_code = releases[-1]["code_32_bit"]

        if releases[-1]["version"] == self.new_client_version:
            next_32_bit_version_code = latest_32_bit_version_code
        else:
            next_32_bit_version_code = latest_32_bit_version_code + 2

        current_32_bit_version_code = self.get_android_32_bit_version_code()

        if current_32_bit_version_code == next_32_bit_version_code:
            return

        if self.update_versions:
            return self.update_file(
                PROJECT_FILE,
                self.android_32_bit_version_code_search,
                self.android_32_bit_version_code_replace.format(
                    code_32_bit=next_32_bit_version_code,
                ),
            )

        return self.errors.append(
            f"The 32-bit version code ({current_32_bit_version_code}) in "
            f"camcops.pro should be {next_32_bit_version_code}"
        )

    def get_android_32_bit_version_code(self) -> int:
        with open(PROJECT_FILE, "r") as f:
            m = re.search(self.android_32_bit_version_code_search, f.read())
            if m is not None:
                return int(m.group(2))

        raise MissingCodeException(
            "Could not 32-bit version code in camcops.pro"
        )

    def check_android_64_bit_version_code(self) -> None:
        if not self.should_release_client:
            return

        releases = self.get_android_releases()
        latest_64_bit_version_code = releases[-1]["code_64_bit"]

        if releases[-1]["version"] == self.new_client_version:
            next_64_bit_version_code = latest_64_bit_version_code
        else:
            next_64_bit_version_code = latest_64_bit_version_code + 2

        current_64_bit_version_code = self.get_android_64_bit_version_code()

        if current_64_bit_version_code == next_64_bit_version_code:
            return

        if self.update_versions:
            return self.update_file(
                PROJECT_FILE,
                self.android_64_bit_version_code_search,
                self.android_64_bit_version_code_replace.format(
                    code_64_bit=next_64_bit_version_code,
                ),
            )

        return self.errors.append(
            f"The 64-bit version code ({current_64_bit_version_code}) in "
            f"camcops.pro should be {next_64_bit_version_code}"
        )

    def get_android_64_bit_version_code(self) -> int:
        with open(PROJECT_FILE, "r") as f:
            m = re.search(self.android_64_bit_version_code_search, f.read())
            if m is not None:
                return int(m.group(2))

        raise MissingCodeException(
            "Could not 64-bit version code in camcops.pro"
        )

    def get_android_releases(self) -> List[Dict[str, Any]]:
        releases = []

        code_32_bit = 0
        code_64_bit = 0

        with open(PLAY_STORE_RELEASE_HISTORY_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    version = Version(row["AndroidManifest.xml name"])
                except ValueError:
                    try:
                        version = Version(
                            row["Google Play Store release name"]
                        )
                    except ValueError:
                        version = ""

                m = re.match(
                    self.android_version_codes_table_search,
                    row["AndroidManifest.xml version code"],
                )
                if m is not None:
                    code_32_bit = int(m.group(1))
                    code_64_bit = int(m.group(3))

                releases.append(
                    dict(
                        version=version,
                        code_32_bit=code_32_bit,
                        code_64_bit=code_64_bit,
                    )
                )
            return releases

    def update_file(self, filename: str, search: str, replace: str) -> None:
        print(f"Updating {filename}...")
        with open(filename, "r") as f:
            content = f.read()
            new_content = re.sub(
                search, replace, content, count=1, flags=re.MULTILINE
            )

        with open(filename, "w") as f:
            f.write(new_content)

    def check_uncommitted_changes(self) -> None:
        # https://stackoverflow.com/questions/3878624/how-do-i-programmatically-determine-if-there-are-uncommitted-changes  # noqa: E501
        os.chdir(PROJECT_ROOT)
        run(["git", "update-index", "--refresh"])
        try:
            self.run_with_check(["git", "diff-index", "--quiet", "HEAD", "--"])
        except CalledProcessError:
            self.errors.append("There are uncommitted changes")

    def check_unpushed_changes(self) -> None:
        git_log = run(
            ["git", "log", "origin/master..HEAD"], stdout=PIPE
        ).stdout.decode("utf-8")
        if len(git_log) > 0:
            self.errors.append("There are unpushed or unmerged changes")

    def check_release_tag(self) -> None:
        release_tag = self.get_release_tag()

        tags = run(["git", "tag"], stdout=PIPE).stdout.decode("utf-8").split()

        if release_tag not in tags:
            self.errors.append(f"Could not find a git tag '{release_tag}'")

    def check_unpushed_tags(self) -> None:
        output = run(
            ["git", "push", "--tags", "--dry-run"], stderr=PIPE
        ).stderr.decode("utf-8")
        if "Everything up-to-date" not in output:
            self.errors.append("There are unpushed tags")

    def check_package_installed(self, package: str) -> None:
        try:
            self.run_with_check(["pip", "show", "--quiet", package])
        except CalledProcessError:
            self.errors.append(
                (
                    f"'{package}' is not installed. "
                    f"To release to PyPI: pip install {package}"
                )
            )

    def perform_checks(self) -> None:
        latest_version, latest_date = self.released_versions[-1]
        if self.progress_version is None:
            print(
                (
                    "No version is marked as IN PROGRESS in the changelog. "
                    "Normally that would be the next unreleased version"
                )
            )

        if latest_version != self.release_version:
            self.errors.append(
                f"The latest version in the changelog ({latest_version}) "
                f"does not match '{self.release_version}'"
            )

        if latest_date != self.release_date:
            self.errors.append(
                "The date of the latest version in the changelog "
                f"({latest_date}) does not match '{self.release_date}'"
            )

        self.check_quick_link_years()
        self.check_quick_link_versions()

        self.check_server_version()
        if self.should_release_server:
            self.check_server_date()

        self.check_client_version()
        if self.should_release_client:
            self.check_client_date()

        self.check_windows_version()
        self.check_android_version()
        self.check_ios_short_version()
        self.check_ios_version()

        self.check_android_releases_table()
        self.check_android_32_bit_version_code()
        self.check_android_64_bit_version_code()

        if len(self.errors) == 0:
            self.check_docs()

        self.check_uncommitted_changes()
        self.check_unpushed_changes()
        self.check_release_tag()
        self.check_unpushed_tags()
        self.check_package_installed("wheel")
        self.check_package_installed("twine")

    def check_docs(self) -> None:
        # The GitHub docs workflow will do a more thorough check. This
        # will hopefully be enough.
        if self.get_apache_config_file_version() != self.new_server_version:
            self.rebuild_docs()

    def get_apache_config_file_version(self) -> Version:
        with open(APACHE_CONFIG_FILE, "r") as f:
            for line in f.readlines():
                m = re.match(self.apache_config_version_search, line)
                if m is not None:
                    return Version(
                        major=int(m.group(2)),
                        minor=int(m.group(4)),
                        patch=int(m.group(6)),
                    )

    def rebuild_docs(self) -> None:
        self.run_with_check([REBUILD_DOCS, "--warnings_as_errors"])

    def release(self) -> None:
        if self.should_release_server:
            self.remove_old_packages()
            self.run_with_check([MAKE_LINUX_PACKAGES])

            self.remove_old_pypi_builds()
            os.chdir(SERVER_SOURCE_DIR)

            # "bdist_wheel" removed from below to allow GitHub dependencies
            # Currenly fhirclient is on a fork
            self.run_with_check(["python", "setup.py", "sdist"])
            pypi_packages = [str(f) for f in self.get_pypi_builds()]
            print(
                "Uploading to PyPI. You will need an API token from "
                "https://pypi.org/manage/account/. If prompted for username "
                "and password, enter '__token__' as the username and the API "
                "token (long string beginning with pypi-) as the password. "
                "Alternatively you can store these details in ~/.pypirc. See "
                "https://packaging.python.org/en/latest/specifications/pypirc/"
                "..."
            )
            self.run_with_check(["twine", "upload"] + pypi_packages)

            print(
                "A new release will be created on GitHub with the "
                ".rpm and .deb files attached. They are also in "
                f"{SERVER_PACKAGE_DIR}"
            )

        if self.should_release_client:
            print("Now build the various client apps and upload.")

    @property
    def should_release_client(self) -> bool:
        return self.new_client_version >= self.new_server_version

    @property
    def should_release_server(self) -> bool:
        return self.new_server_version >= self.new_client_version

    @property
    def release_version(self) -> Version:
        if self.should_release_server:
            return self.new_server_version

        return self.new_client_version

    def get_release_tag(self) -> str:
        """
        Generates a release tag, either for a client release (if client version
        ahead of server), a server release (if server ahead of client), or a
        combined release (if both versions identical).
        """
        if self.new_client_version == self.new_server_version:
            return f"v{self.new_client_version}"

        if self.new_client_version > self.new_server_version:
            return f"v{self.new_client_version}-client"

        return f"v{self.new_server_version}-server"

    def remove_old_packages(self) -> None:
        """
        Deletes old server package build files (e.g. ``.deb``).
        """
        for f in Path(SERVER_PACKAGE_DIR).glob("camcops-server*"):
            f.unlink()

    def get_pypi_builds(self) -> Iterable[Path]:
        """
        Iterates through old PyPI upload files (e.g.
        ``camcops_server-*.tar.gz``).
        """
        return Path(SERVER_DIST_DIR).glob("camcops_server-*")

    def remove_old_pypi_builds(self) -> None:
        """
        Deletes old PyPI upload files (e.g. ``camcops_server-*.tar.gz``).
        """
        for f in self.get_pypi_builds():
            f.unlink()


def main() -> None:
    """
    Do useful things to build and release the server and client.

    This is a work in progress
    What do we want this script to do?

    / Check and update all the version numbers
    / Check the changelog
    / Check the Git repository
    / Build the Ubuntu server packages (deb/rpm)
    / Build the PyPI server package
    / Distribute the server packages to PyPI
    / Use GitHub release action to create the server packages on GitHub

    - Build the client (depending on the platform)
    - Distribute to Play Store / Apple Store / GitHub

    Ideally we want to do all the checks before tagging and building so we
    don't get the version numbers spiralling out of control. This may be
    impossible for errors when deploying to Apple Store etc.

    """
    if not in_virtualenv():
        log.error("release_new_version.py must be run inside virtualenv")
        sys.exit(EXIT_FAILURE)

    if sys.version_info < (3, 10):
        log.error("You must run this script with Python 3.10 or later")
        sys.exit(EXIT_FAILURE)

    parser = argparse.ArgumentParser(
        description="Release CamCOPS to various places",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_argument(
        "--client-version",
        type=str,
        required=True,
        help="New client version number (x.y.z)",
    )
    parser.add_argument(
        "--server-version",
        type=str,
        required=True,
        help="New server version number (x.y.z)",
    )
    parser.add_argument(
        "--release-date",
        type=valid_date,
        default=datetime.now().date(),
        help="Release date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--update-versions",
        action="store_true",
        default=False,
        help="Update any incorrect version numbers",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        default=False,
        help="If all checks pass, build and release",
    )
    args = parser.parse_args()

    releaser = VersionReleaser(
        new_client_version=Version(args.client_version),
        new_server_version=Version(args.server_version),
        release_date=args.release_date,
        update_versions=args.update_versions,
    )
    releaser.perform_checks()

    if len(releaser.errors) > 0:
        for error in releaser.errors:
            print(error)
        if not args.update_versions:
            # TODO: Don't display this message if the versions are already
            # updated
            print(
                "Run the script with --update-versions to automatically "
                "update version numbers"
            )
        sys.exit(EXIT_FAILURE)

    if args.release:
        # OK to proceed to the next step
        releaser.release()
        return

    print("All checks passed. You can run the script again with --release")


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
