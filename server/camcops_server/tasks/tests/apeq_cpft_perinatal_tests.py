"""
camcops_server/tasks/tests/apeq_cpft_perinatal_tests.py

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

from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.apeq_cpft_perinatal import (
    APEQCPFTPerinatalReport,
)
from camcops_server.tasks.tests.factories import APEQCPFTPerinatalFactory

# =============================================================================
# Unit tests
# =============================================================================


class APEQCPFTPerinatalReportTestCase(DemoRequestTestCase):
    COL_Q = 0
    COL_TOTAL = 1
    COL_RESPONSE_START = 2

    COL_FF_WHY = 1

    def setUp(self) -> None:
        super().setUp()

        self.report = APEQCPFTPerinatalReport()

        # Really only needed for tests
        self.report.start_datetime = None
        self.report.end_datetime = None


class APEQCPFTPerinatalReportTests(APEQCPFTPerinatalReportTestCase):
    def setUp(self) -> None:
        """
        Creates 20 tasks.
        Should give us:

        .. code-block:: none

            q1: 0 - 50%,
                1 - 25%
                2 - 25%
            q2: 1 - 100%
            q3: 0 - 5%
                1 - 20%
                2 - 75%
            q4: 0 - 10%
                1 - 40%
                2 - 50%
            q5: 0 - 15%
                1 - 55%
                2 - 30%
            q6: 1 - 50%
                2 - 50%
            ff: 0 - 25%
                1 - 10%
                2 - 15%
                3 - 10%
                4 - 5%
                5 - 35%

        """
        super().setUp()

        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=0, q4=0, q5=2, q6=2, ff_rating=5, ff_why="ff_5_1"
        )
        APEQCPFTPerinatalFactory(
            q1=0,
            q2=1,
            q3=1,
            q4=0,
            q5=2,
            q6=2,
            ff_rating=5,
            ff_why="ff_5_2",
            comments="comments_2",
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=1, q4=1, q5=2, q6=2, ff_rating=5
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=1, q4=1, q5=2, q6=2, ff_rating=5
        )
        APEQCPFTPerinatalFactory(
            q1=0,
            q2=1,
            q3=1,
            q4=1,
            q5=2,
            q6=2,
            ff_rating=5,
            comments="comments_5",
        )

        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=2, q4=1, q5=2, q6=2, ff_rating=5
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=2, q4=1, q5=1, q6=2, ff_rating=5
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=2, q4=1, q5=1, q6=2, ff_rating=4, ff_why="ff_4_1"
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=2, q4=1, q5=1, q6=2, ff_rating=3
        )
        APEQCPFTPerinatalFactory(
            q1=0, q2=1, q3=2, q4=1, q5=1, q6=1, ff_rating=3, ff_why="ff_3_1"
        )

        APEQCPFTPerinatalFactory(
            q1=1, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=2, ff_why="ff_2_1"
        )
        APEQCPFTPerinatalFactory(
            q1=1, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=2
        )
        APEQCPFTPerinatalFactory(
            q1=1, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=2, ff_why="ff_2_2"
        )
        APEQCPFTPerinatalFactory(
            q1=1, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=1, ff_why="ff_1_1"
        )
        APEQCPFTPerinatalFactory(
            q1=1, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=1, ff_why="ff_1_2"
        )

        APEQCPFTPerinatalFactory(
            q1=2, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=0
        )
        APEQCPFTPerinatalFactory(
            q1=2, q2=1, q3=2, q4=2, q5=1, q6=1, ff_rating=0
        )
        APEQCPFTPerinatalFactory(
            q1=2, q2=1, q3=2, q4=2, q5=0, q6=None, ff_rating=0
        )
        APEQCPFTPerinatalFactory(
            q1=2, q2=1, q3=2, q4=2, q5=0, q6=None, ff_rating=0
        )
        APEQCPFTPerinatalFactory(
            q1=2,
            q2=1,
            q3=2,
            q4=2,
            q5=0,
            q6=1,
            ff_rating=0,
            comments="comments_20",
        )

    def test_main_rows_contain_percentages(self) -> None:
        expected_percentages = [
            ["20", "50", "25", "25"],  # q1
            ["20", "", "100", ""],  # q2
            ["20", "5", "20", "75"],  # q3
            ["20", "10", "40", "50"],  # q4
            ["20", "15", "55", "30"],  # q5
            ["18", "", "50", "50"],  # q6
        ]

        main_rows = self.report._get_main_rows(self.req)

        # MySQL does floating point division
        for row, expected in zip(main_rows, expected_percentages):
            percentages = []

            for p in row[1:]:
                if p != "":
                    p = str(int(float(p)))

                percentages.append(p)

            self.assertEqual(percentages, expected)

    def test_main_rows_formatted(self) -> None:
        expected_q1 = [20, "50.0%", "25.0%", "25.0%"]

        main_rows = self.report._get_main_rows(
            self.req, cell_format="{0:.1f}%"
        )

        self.assertEqual(main_rows[0][1:], expected_q1)

    def test_ff_rows_contain_percentages(self) -> None:
        expected_ff = [20, 25, 10, 15, 10, 5, 35]

        ff_rows = self.report._get_ff_rows(self.req)

        # MySQL does floating point division
        percentages = [int(float(p)) for p in ff_rows[0][1:]]

        self.assertEqual(percentages, expected_ff)

    def test_ff_rows_formatted(self) -> None:
        expected_ff = [20, "25.0%", "10.0%", "15.0%", "10.0%", "5.0%", "35.0%"]

        ff_rows = self.report._get_ff_rows(self.req, cell_format="{0:.1f}%")

        self.assertEqual(ff_rows[0][1:], expected_ff)

    def test_ff_why_rows_contain_reasons(self) -> None:
        expected_reasons = [
            ["Extremely unlikely", "ff_1_1"],
            ["Extremely unlikely", "ff_1_2"],
            ["Unlikely", "ff_2_1"],
            ["Unlikely", "ff_2_2"],
            ["Neither likely nor unlikely", "ff_3_1"],
            ["Likely", "ff_4_1"],
            ["Extremely likely", "ff_5_1"],
            ["Extremely likely", "ff_5_2"],
        ]

        ff_why_rows = self.report._get_ff_why_rows(self.req)

        self.assertEqual(ff_why_rows, expected_reasons)

    def test_comments(self) -> None:
        expected_comments = ["comments_2", "comments_5", "comments_20"]

        comments = self.report._get_comments(self.req)
        self.assertEqual(comments, expected_comments)


class APEQCPFTPerinatalReportDateRangeTests(APEQCPFTPerinatalReportTestCase):
    def setUp(self) -> None:
        super().setUp()

        APEQCPFTPerinatalFactory(
            q1=1,
            q2=0,
            q3=0,
            q4=0,
            q5=0,
            q6=0,
            ff_rating=0,
            ff_why="ff why 1",
            comments="comments 1",
            when_created=pendulum.parse("2018-10-01"),
        )
        APEQCPFTPerinatalFactory(
            q1=0,
            q2=0,
            q3=0,
            q4=0,
            q5=0,
            q6=0,
            ff_rating=2,
            ff_why="ff why 2",
            comments="comments 2",
            when_created=pendulum.parse("2018-10-02"),
        )
        APEQCPFTPerinatalFactory(
            q1=0,
            q2=0,
            q3=0,
            q4=0,
            q5=0,
            q6=0,
            ff_rating=2,
            ff_why="ff why 3",
            comments="comments 3",
            when_created=pendulum.parse("2018-10-03"),
        )
        APEQCPFTPerinatalFactory(
            q1=0,
            q2=0,
            q3=0,
            q4=0,
            q5=0,
            q6=0,
            ff_rating=2,
            ff_why="ff why 4",
            comments="comments 4",
            when_created=pendulum.parse("2018-10-04"),
        )
        APEQCPFTPerinatalFactory(
            q1=1,
            q2=0,
            q3=0,
            q4=0,
            q5=0,
            q6=0,
            ff_rating=0,
            ff_why="ff why 5",
            comments="comments 5",
            when_created=pendulum.parse("2018-10-05"),
        )

    def test_main_rows_filtered_by_date(self) -> None:
        self.report.start_datetime = "2018-10-02T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-10-05T00:00:00.000000+00:00"

        rows = self.report._get_main_rows(self.req, cell_format="{0:.1f}%")
        q1_row = rows[0]

        # There should be three tasks included in the calculation.
        self.assertEqual(q1_row[self.COL_TOTAL], 3)

        # For question 1 all of them answered 0 so we would expect
        # 100%. If the results aren't being filtered we will get
        # 60%
        self.assertEqual(q1_row[self.COL_RESPONSE_START + 0], "100.0%")

    def test_ff_rows_filtered_by_date(self) -> None:
        self.report.start_datetime = "2018-10-02T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-10-05T00:00:00.000000+00:00"

        rows = self.report._get_ff_rows(self.req, cell_format="{0:.1f}%")
        ff_row = rows[0]

        # There should be three tasks included in the calculation.
        self.assertEqual(ff_row[self.COL_TOTAL], 3)

        # For the ff question all of them answered 2 so we would expect
        # 100%. If the results aren't being filtered we will get
        # 60%
        self.assertEqual(ff_row[self.COL_RESPONSE_START + 2], "100.0%")

    def test_ff_why_row_filtered_by_date(self) -> None:
        self.report.start_datetime = "2018-10-02T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-10-05T00:00:00.000000+00:00"

        rows = self.report._get_ff_why_rows(self.req)
        self.assertEqual(len(rows), 3)

        self.assertEqual(rows[0][self.COL_FF_WHY], "ff why 2")
        self.assertEqual(rows[1][self.COL_FF_WHY], "ff why 3")
        self.assertEqual(rows[2][self.COL_FF_WHY], "ff why 4")

    def test_comments_filtered_by_date(self) -> None:
        self.report.start_datetime = "2018-10-02T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-10-05T00:00:00.000000+00:00"

        comments = self.report._get_comments(self.req)
        self.assertEqual(len(comments), 3)

        self.assertEqual(comments[0], "comments 2")
        self.assertEqual(comments[1], "comments 3")
        self.assertEqual(comments[2], "comments 4")
