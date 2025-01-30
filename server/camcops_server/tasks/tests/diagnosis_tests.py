"""
camcops_server/tasks/tests/diagnosis_tests.py

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

from camcops_server.cc_modules.cc_testfactories import UserFactory
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.diagnosis import DiagnosisICD10FinderReport


class DiagnosisICD10FinderReportTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.report = DiagnosisICD10FinderReport()
        self.req._debugging_user = UserFactory()

    def test_no_records_creates_empty_report(self) -> None:
        pages = self.report.get_spreadsheet_pages(self.req)

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].headings, [])
        self.assertEqual(pages[0].rows, [])
