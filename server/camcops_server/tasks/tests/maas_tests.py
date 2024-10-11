"""
camcops_server/tasks/tests/maas_tests.py

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

import pendulum

from camcops_server.cc_modules.cc_testfactories import (
    PatientFactory,
    UserFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.maas import Maas, MaasReport
from camcops_server.tasks.tests.factories import MaasFactory


class MaasReportTests(DemoRequestTestCase):
    PROGRESS_COL = 4

    def setUp(self) -> None:
        super().setUp()

        self.report = self.create_report()
        self.req._debugging_user = UserFactory(superuser=True)

        patient = PatientFactory()

        # Default to answering 1 to everything
        response_dict = {q: 1 for q in Maas.TASK_FIELDS}

        # Same patient completing the task at different intervals
        response_dict["q1"] = 2
        response_dict["q2"] = 2
        MaasFactory(
            patient=patient,
            when_created=pendulum.parse("2019-03-01"),
            **response_dict,
        )  # total 17 * 1 + 2 + 2 = 21

        response_dict["q1"] = 5
        response_dict["q2"] = 5
        MaasFactory(
            patient=patient,
            when_created=pendulum.parse("2019-06-01"),
            **response_dict,
        )  # total 17 * 1 + 5 + 5 = 27

    def create_report(self) -> MaasReport:
        return MaasReport(via_index=False)

    def test_average_progress_is_positive(self) -> None:
        pages = self.report.get_spreadsheet_pages(req=self.req)

        # Numbers as above
        expected_progress = 27 - 21
        actual_progress = pages[0].plainrows[0][self.PROGRESS_COL]

        self.assertEqual(actual_progress, expected_progress)
