"""
camcops_server/tasks/tests/core10_tests.py

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
from camcops_server.tasks.core10 import Core10, Core10Report
from camcops_server.tasks.tests.factories import Core10Factory


class Core10ReportTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.report = self.create_report()
        self.req._debugging_user = UserFactory(superuser=True)

    def create_report(self) -> Core10Report:
        return Core10Report(via_index=False)


class Core10ReportTotalsTests(Core10ReportTestCase):
    def setUp(self) -> None:
        super().setUp()

        patient_1 = PatientFactory()
        patient_2 = PatientFactory()
        patient_3 = PatientFactory()

        # Initial average score = (8 + 6 + 4) / 3 = 6
        # Latest average score = (2 + 3 + 4) / 3 = 3

        Core10Factory(
            patient=patient_1,
            q1=4,
            q2=4,
            when_created=pendulum.parse("2018-06-01"),
        )  # Score 8
        Core10Factory(
            patient=patient_1,
            q7=1,
            q8=1,
            when_created=pendulum.parse("2018-10-04"),
        )  # Score 2

        Core10Factory(
            patient=patient_2,
            q3=3,
            q4=3,
            when_created=pendulum.parse("2018-05-02"),
        )  # Score 6
        Core10Factory(
            patient=patient_2,
            q3=2,
            q4=1,
            when_created=pendulum.parse("2018-10-03"),
        )  # Score 3

        Core10Factory(
            patient=patient_3,
            q5=2,
            q6=2,
            when_created=pendulum.parse("2018-01-10"),
        )  # Score 4
        Core10Factory(
            patient=patient_3,
            q9=1,
            q10=3,
            when_created=pendulum.parse("2018-10-01"),
        )  # Score 4

    def test_row_has_totals_and_averages(self) -> None:
        pages = self.report.get_spreadsheet_pages(req=self.req)
        expected_rows = [
            [
                3,  # n initial
                3,  # n latest
                6.0,  # Initial average
                3.0,  # Latest average
                3.0,  # Average progress
            ]
        ]
        self.assertEqual(pages[0].plainrows, expected_rows)


class Core10ReportEmptyTests(Core10ReportTestCase):
    def test_no_rows_when_no_data(self) -> None:
        pages = self.report.get_spreadsheet_pages(req=self.req)
        no_data = self.report.no_data_value()
        expected_rows = [[0, 0, no_data, no_data, no_data]]
        self.assertEqual(pages[0].plainrows, expected_rows)


class Core10ReportDoubleCountingTests(Core10ReportTestCase):
    def setUp(self) -> None:
        super().setUp()

        patient_1 = PatientFactory()
        patient_2 = PatientFactory()
        patient_3 = PatientFactory()

        # Initial average score = (8 + 6 + 4) / 3 = 6
        # Latest average score  = (    3 + 3) / 2 = 3
        # Progress avg score    = (    3 + 1) / 2 = 2  ... NOT 3.

        Core10Factory(
            patient=patient_1,
            q1=4,
            q2=4,
            when_created=pendulum.parse("2018-06-01"),
        )  # Score 8

        Core10Factory(
            patient=patient_2,
            q3=3,
            q4=3,
            when_created=pendulum.parse("2018-05-02"),
        )  # Score 6
        Core10Factory(
            patient=patient_2,
            q3=2,
            q4=1,
            when_created=pendulum.parse("2018-10-03"),
        )  # Score 3

        Core10Factory(
            patient=patient_3,
            q5=2,
            q6=2,
            when_created=pendulum.parse("2018-01-10"),
        )  # Score 4
        Core10Factory(
            patient=patient_3,
            q9=1,
            q10=2,
            when_created=pendulum.parse("2018-10-01"),
        )  # Score 3

    def test_record_does_not_appear_in_first_and_latest(self) -> None:
        pages = self.report.get_spreadsheet_pages(req=self.req)
        expected_rows = [
            [
                3,  # n initial
                2,  # n latest
                6.0,  # Initial average
                3.0,  # Latest average
                2.0,  # Average progress
            ]
        ]
        self.assertEqual(pages[0].plainrows, expected_rows)


class Core10ReportDateRangeTests(Core10ReportTestCase):
    """
    Test code:

    .. code-block:: sql

        -- 2019-10-21
        -- For SQLite:

        CREATE TABLE core10
            (_pk INT, patient_id INT, when_created DATETIME, _current INT);

        .schema core10

        INSERT INTO core10
            (_pk,patient_id,when_created,_current)
        VALUES
            (1,1,'2018-06-01T00:00:00.000000+00:00',1),
            (2,1,'2018-08-01T00:00:00.000000+00:00',1),
            (3,1,'2018-10-01T00:00:00.000000+00:00',1),
            (4,2,'2018-06-01T00:00:00.000000+00:00',1),
            (5,2,'2018-08-01T00:00:00.000000+00:00',1),
            (6,2,'2018-10-01T00:00:00.000000+00:00',1),
            (7,3,'2018-06-01T00:00:00.000000+00:00',1),
            (8,3,'2018-08-01T00:00:00.000000+00:00',1),
            (9,3,'2018-10-01T00:00:00.000000+00:00',1);

        SELECT * from core10;

        SELECT STRFTIME('%Y-%m-%d %H:%M:%f', core10.when_created) from core10;
        -- ... gives e.g.
        -- 2018-06-01 00:00:00.000

        SELECT *
            FROM core10
            WHERE core10._current = 1
            AND STRFTIME('%Y-%m-%d %H:%M:%f', core10.when_created) >= '2018-06-01 00:00:00.000000'
            AND STRFTIME('%Y-%m-%d %H:%M:%f', core10.when_created) < '2018-09-01 00:00:00.000000';

        -- That fails. Either our date/time comparison code is wrong for SQLite, or
        -- we are inserting text in the wrong format.
        -- Ah. It's the number of decimal places:

        SELECT '2018-06-01 00:00:00.000' >= '2018-06-01 00:00:00.000000';  -- 0, false
        SELECT '2018-06-01 00:00:00.000' >= '2018-06-01 00:00:00.000';  -- 1, true

    See
    :func:`camcops_server.cc_modules.cc_sqla_coltypes.isotzdatetime_to_utcdatetime_sqlite`.

    """  # noqa

    def setUp(self) -> None:
        super().setUp()

        patient_1 = PatientFactory()
        patient_2 = PatientFactory()
        patient_3 = PatientFactory()

        # 2018-06 average score = (8 + 6 + 4) / 3 = 6
        # 2018-08 average score = (4 + 4 + 4) / 3 = 4
        # 2018-10 average score = (2 + 3 + 4) / 3 = 3

        Core10Factory(
            patient=patient_1,
            q1=4,
            q2=4,
            when_created=pendulum.parse("2018-06-01"),
        )  # Score 8
        Core10Factory(
            patient=patient_1,
            q7=3,
            q8=1,
            when_created=pendulum.parse("2018-08-01"),
        )  # Score 4
        Core10Factory(
            patient=patient_1,
            q7=1,
            q8=1,
            when_created=pendulum.parse("2018-10-01"),
        )  # Score 2

        Core10Factory(
            patient=patient_2,
            q3=3,
            q4=3,
            when_created=pendulum.parse("2018-06-01"),
        )  # Score 6
        Core10Factory(
            patient=patient_2,
            q3=2,
            q4=2,
            when_created=pendulum.parse("2018-08-01"),
        )  # Score 4
        Core10Factory(
            patient=patient_2,
            q3=1,
            q4=2,
            when_created=pendulum.parse("2018-10-01"),
        )  # Score 3

        Core10Factory(
            patient=patient_3,
            q5=2,
            q6=2,
            when_created=pendulum.parse("2018-06-01"),
        )  # Score 4
        Core10Factory(
            patient=patient_3,
            q9=1,
            q10=3,
            when_created=pendulum.parse("2018-08-01"),
        )  # Score 4
        Core10Factory(
            patient=patient_3,
            q9=1,
            q10=3,
            when_created=pendulum.parse("2018-10-01"),
        )  # Score 4

        self.dump_table(
            Core10.__tablename__,
            ["_pk", "patient_id", "when_created", "_current"],
        )

    def test_report_filtered_by_date_range(self) -> None:
        self.report.start_datetime = "2018-06-01T00:00:00.000000+00:00"
        self.report.end_datetime = "2018-09-01T00:00:00.000000+00:00"

        self.set_echo(True)
        pages = self.report.get_spreadsheet_pages(req=self.req)
        self.set_echo(False)
        expected_rows = [
            [
                3,  # n initial
                3,  # n latest
                6.0,  # Initial average
                4.0,  # Latest average
                2.0,  # Average progress
            ]
        ]
        self.assertEqual(pages[0].plainrows, expected_rows)
