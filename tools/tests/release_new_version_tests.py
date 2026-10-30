"""
tools/tests/release_new_version_tests.py

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

import csv
from datetime import date
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from semantic_version import Version


from release_new_version import VersionReleaser


class VersionReleaserTests(TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.project_filename = join(
            self.temporary_directory.name, "camcops.pro"
        )
        self.play_store_release_history_filename = join(
            self.temporary_directory.name, "play_store_release_history.csv"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_versions_updated_in_android_releases_table(self) -> None:
        with open(self.project_filename, "w") as f:
            f.write("""
    ANDROID_MIN_SDK_VERSION = "23"
    ANDROID_TARGET_SDK_VERSION = "36"
            """)

        with open(self.play_store_release_history_filename, "w") as f:
            fieldnames = [
                "Google Play Store release name",
                "AndroidManifest.xml version code",
                "AndroidManifest.xml name",
                "To Play Store on",
                "Minimum Android API",
                "Target Android API",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "Google Play Store release name": "2.4.24",
                    "AndroidManifest.xml version code": "55 (32-bit ARM); 56 (64-bit ARM)",  # noqa: E501
                    "AndroidManifest.xml name": "2.4.24",
                    "To Play Store on": "2026-01-23",
                    "Minimum Android API": 23,
                    "Target Android API": 35,
                }
            )

        releaser = VersionReleaser(
            new_client_version=Version("2.4.25"),
            new_server_version=Version("2.4.25"),
            release_date=date(2026, 10, 29),
            update_versions=True,
            skip_git_checks=True,
            project_filename=self.project_filename,
            play_store_release_history_filename=self.play_store_release_history_filename,  # noqa: E501
        )

        releaser.check_android_releases_table()

        with open(self.play_store_release_history_filename, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        last_row = rows[-1]

        self.assertEqual(
            last_row,
            {
                "Google Play Store release name": "2.4.25",
                "AndroidManifest.xml version code": "57 (32-bit ARM); 58 (64-bit ARM)",  # noqa: E501
                "AndroidManifest.xml name": "2.4.25",
                "To Play Store on": "2026-10-29",
                "Minimum Android API": "23",
                "Target Android API": "36",
            },
        )
