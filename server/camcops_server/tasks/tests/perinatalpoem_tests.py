"""
camcops_server/tasks/tests/perinatalpoem_tests.py

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

from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.tasks.perinatalpoem import PerinatalPoemReport
from camcops_server.tasks.tests.factories import PerinatalPoemFactory

# =============================================================================
# Unit tests
# =============================================================================


class PerinatalPoemReportTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.report = PerinatalPoemReport()

        # Really only needed for tests
        self.report.start_datetime = None
        self.report.end_datetime = None


class PerinatalPoemReportTests(PerinatalPoemReportTestCase):
    """
    Most of the base class tested in APEQCPFT Perinatal so just some basic
    sanity checking here
    """

    def setUp(self) -> None:
        super().setUp()

        t1 = PerinatalPoemFactory(general_comments="comment 1")
        t2 = PerinatalPoemFactory(general_comments="comment 2")
        t3 = PerinatalPoemFactory(general_comments="comment 3")

        self.dbsession.add(t1)
        self.dbsession.add(t2)
        self.dbsession.add(t3)

        self.dbsession.commit()

    def test_qa_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[0].rows

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_qb_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[1].rows

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_q1_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[2].rows

        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 7)

    def test_q2_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[3].rows

        self.assertEqual(len(rows), 12)
        self.assertEqual(len(rows[0]), 6)

    def test_q3_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[4].rows

        self.assertEqual(len(rows), 6)
        self.assertEqual(len(rows[0]), 6)

    def test_participation_rows_counts(self) -> None:
        tables = self.report._get_html_tables(self.req)

        rows = tables[5].rows

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 4)

    def test_comments(self) -> None:
        expected_comments = ["comment 1", "comment 2", "comment 3"]
        comments = self.report._get_comments(self.req)
        self.assertEqual(comments, expected_comments)


class PerinatalPoemReportDateRangeTests(PerinatalPoemReportTestCase):
    def setUp(self) -> None:
        super().setUp()

        t1 = PerinatalPoemFactory(
            general_comments="comments 1",
            when_created="2018-10-01T00:00:00.000000+00:00",
        )
        t2 = PerinatalPoemFactory(
            general_comments="comments 2",
            when_created="2018-10-02T00:00:00.000000+00:00",
        )
        t3 = PerinatalPoemFactory(
            general_comments="comments 3",
            when_created="2018-10-03T00:00:00.000000+00:00",
        )
        t4 = PerinatalPoemFactory(
            general_comments="comments 4",
            when_created="2018-10-04T00:00:00.000000+00:00",
        )
        t5 = PerinatalPoemFactory(
            general_comments="comments 5",
            when_created="2018-10-05T00:00:00.000000+00:00",
        )
        self.dbsession.add(t1)
        self.dbsession.add(t2)
        self.dbsession.add(t3)
        self.dbsession.add(t4)
        self.dbsession.add(t5)

        self.dbsession.commit()

    def test_comments_filtered_by_date(self) -> None:
        self.report.start_datetime = "2018-10-02T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-10-05T00:00:00.000000+00:00"

        comments = self.report._get_comments(self.req)
        self.assertEqual(len(comments), 3)

        self.assertEqual(comments[0], "comments 2")
        self.assertEqual(comments[1], "comments 3")
        self.assertEqual(comments[2], "comments 4")
