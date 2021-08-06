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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

"""

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import re
from subprocess import CalledProcessError, PIPE, run
import sys
from typing import Iterable, List, Optional, Tuple

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
SERVER_SOURCE_DIR = os.path.join(PROJECT_ROOT, "server")
SERVER_TOOLS_DIR = os.path.join(SERVER_SOURCE_DIR, "tools")
SERVER_DIST_DIR = os.path.join(SERVER_SOURCE_DIR, "dist")
SERVER_PACKAGE_DIR = os.path.join(SERVER_SOURCE_DIR, "packagebuild")
MAKE_LINUX_PACKAGES = os.path.join(SERVER_TOOLS_DIR, "MAKE_LINUX_PACKAGES.py")
CHANGELOG = os.path.join(DOCS_SOURCE_DIR, "changelog.rst")
SERVER_VERSION_FILE = os.path.join(
    SERVER_SOURCE_DIR, "camcops_server", "cc_modules", "cc_version_string.py"
)
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


class MissingVersionException(Exception):
    pass


class MissingDateException(Exception):
    pass


class VersionReleaser:
    #                         (               1                       )( 2 )( 3  )( 4 )(  5 )( 6 )( 7  )   # noqa: E501
    client_version_search = r"(^const Version CAMCOPS_CLIENT_VERSION\()(\d+)(,\s+)(\d+)(,\s+)(\d+)(\);$)"  # noqa: E501
    client_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    #                      (               1                        )( 2 )( 3  )( 4 )(  5 )( 6 )( 7  )   # noqa: E501
    client_date_search = r"(^const QDate CAMCOPS_CLIENT_CHANGEDATE\()(\d+)(,\s+)(\d+)(,\s+)(\d+)(\);$)"  # noqa: E501
    client_date_replace = r"\g<1>{year}\g<3>{month}\g<5>{day}\g<7>"

    #                          (              1                )( 2 )( 3)( 4 )( 5)( 6 )(7)  # noqa: E501
    windows_version_search = r'(^#define CamcopsClientVersion ")(\d+)(\.)(\d+)(\.)(\d+)(")'  # noqa: E501
    windows_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    #                          (          1          )( 2 )( 3)( 4 )( 5)( 6 )(7)  # noqa: E501
    android_version_search = r'(android:versionName=")(\d+)(\.)(\d+)(\.)(\d+)(")'  # noqa: E501
    android_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    #                            (                      1                         )( 3 )( 3)( 4 )( 5)( 6 )(    7    )  # noqa: E501
    ios_short_version_search = r"(<key>CFBundleShortVersionString</key>\s+<string>)(\d+)(\.)(\d+)(\.)(\d+)(</string>)"  # noqa: E501
    ios_short_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>"

    #                      (                  1                  )( 2 )( 3)( 4 )( 5)( 6 )( 7)( 8 )(    9    )  # noqa: E501
    ios_version_search = r"(<key>CFBundleVersion</key>\s+<string>)(\d+)(\.)(\d+)(\.)(\d+)(\.)(\d+)(</string>)"  # noqa: E501
    ios_version_replace = r"\g<1>{major}\g<3>{minor}\g<5>{patch}\g<7>{extra}\g<9>"  # noqa: E501

    def __init__(
        self,
        new_client_version: Version,
        new_server_version: Version,
        release_date: datetime.date,
        update_versions: bool,
    ) -> None:
        self.new_client_version = new_client_version
        self.new_server_version = new_server_version
        self.release_date = release_date
        self.update_versions = update_versions
        self.errors = []

    def run_with_check(self, args: List[str]) -> None:
        """
        Run a command with arguments. Raise :exc:`CalledProcessError` if the
        exit code was not zero.
        """
        run(args, check=True)

    def get_progress_version(self) -> Optional[Version]:
        """
        Return the version number in the changelog marked "IN PROGRESS", or
        ``None``.
        """
        progress_version = None

        regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*(IN PROGRESS).*\*\*$"
        with open(CHANGELOG, "r") as f:
            for line in f.readlines():
                m = re.match(regex, line)
                if m is not None:
                    progress_version = Version(
                        major=int(m.group(1)),
                        minor=int(m.group(2)),
                        patch=int(m.group(3)),
                    )

        return progress_version

    def get_released_versions(self) -> List[Tuple[Version, datetime]]:
        """
        Returns a list of ``(version, date_released)`` tuples from the changelog.
        """
        regex = r"^\*\*.*(\d+)\.(\d+)\.(\d+).*released\s+(\d+)\s+([a-zA-Z]+)\s+(\d+).*\*\*$"  # noqa: E501

        releases = []

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

                    releases.append((released_version, release_date))

        return releases

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

        raise MissingDateException(
            "Could not find date in camcopsversion.cpp"
        )

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

        raise MissingVersionException(
            "Could not find version in Info.plist"
        )

    def check_server_version(self) -> None:
        if self.new_server_version == self.progress_version:
            self.errors.append(
                f"The desired server version ({self.new_server_version}) "
                "matches the current IN PROGRESS version in the changelog. You "
                "probably want to mark the version in the changelog as released"
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
            "({self.new_server_version})"
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
                f"The desired client version ({self.new_client_version}) matches "
                "the current IN PROGRESS version in the changelog. You probably "
                "want to mark the version in the changelog as released"
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

        if Version(major=current_ios_version[0],
                   minor=current_ios_version[1],
                   patch=current_ios_version[2]) == self.new_client_version:
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
            self.errors.append("There are unpushed changes")

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

    def perform_checks(self) -> None:
        releases = self.get_released_versions()
        latest_version, latest_date = releases[-1]
        self.progress_version = self.get_progress_version()

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

        self.check_uncommitted_changes()
        self.check_unpushed_changes()
        self.check_release_tag()
        self.check_unpushed_tags()

    def release(self) -> None:
        if self.should_release_server:
            self.remove_old_packages()
            self.run_with_check([MAKE_LINUX_PACKAGES])

            self.remove_old_pypi_builds()
            os.chdir(SERVER_SOURCE_DIR)
            self.run_with_check(["python", "setup.py", "sdist", "bdist_wheel"])
            pypi_packages = [str(f) for f in self.get_pypi_builds()]
            self.run_with_check(["twine", "upload"] + pypi_packages)

            print("Now upload the .rpm and .deb files to GitHub")

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

        todo:: should this find all ``.rpm``, too? The RPM package builder converts
        ``server_`` to ``server-``, not found by this expression.
        """
        for f in Path(SERVER_PACKAGE_DIR).glob("camcops-server_*"):
            f.unlink()

    def get_pypi_builds(self) -> Iterable[Path]:
        """
        Iterates through old PyPI upload files (e.g. ``camcops_server-*.tar.gz``).
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

    / Check and update all the version numbers (TODO: Android releases doc)
    / Check the changelog
    / Check the Git repository
    / Build the Ubuntu server packages (deb/rpm)
    / Build the pypi server package
    / Distribute the server packages to PyPI
    - Distribute the server packages to GitHub (or use GitHub actions)

    - Build the client (depending on the platform)
    - Distribute to Play Store / Apple Store / GitHub

    Ideally we want to do all the checks before tagging and building so we
    don't get the version numbers spiralling out of control this may be
    impossible for errors when deploying to Apple Store etc.

    """
    if not in_virtualenv():
        log.error("release_new_version.py must be run inside virtualenv")
        sys.exit(EXIT_FAILURE)

    parser = argparse.ArgumentParser(
        description="Release CamCOPS to various places",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        sys.exit(EXIT_FAILURE)

    # OK to proceed to the next step
    releaser.release()


if __name__ == "__main__":
    main_only_quicksetup_rootlogger()
    main()
