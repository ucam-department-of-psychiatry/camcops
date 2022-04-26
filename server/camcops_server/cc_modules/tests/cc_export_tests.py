#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_export_tests.py

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

from os.path import join
from pathlib import Path
import tempfile
import unittest

from camcops_server.cc_modules.cc_export import UserDownloadFile


# =============================================================================
# Unit tests
# =============================================================================


class ExportTests(unittest.TestCase):
    """
    Test aspects of the export infrastructure.
    """

    def test_directory_safety(self) -> None:
        """
        Here we ensure that passing a dodgy path to
        :class:`camcops_server.cc_modules.cc_export.UserDownloadFile` fails.
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            topdir = Path(tmpdirname)
            safe_dirname = "safe_dir"
            safe_dir = topdir / safe_dirname
            safe_dir.mkdir()
            danger_dirname = "danger_dir"
            danger_dir = topdir / danger_dirname
            danger_dir.mkdir()
            safe_filename = "safe_file.txt"
            safe_file = safe_dir / safe_filename
            safe_file.touch()
            danger_filename = "danger_file.txt"
            danger_file = danger_dir / danger_filename
            danger_file.touch()

            # log.debug(f"Top directory for test: {tmpdirname}")

            ok = UserDownloadFile(safe_filename, str(safe_dir))
            self.assertEqual(ok.exists, True)

            danger_path = join("..", danger_dir, danger_filename)
            bad = UserDownloadFile(danger_path, str(safe_dir))
            self.assertEqual(bad.exists, False)
