#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_taskschedulereports_tests.py

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

**Test server reports on CamCOPS scheduled tasks.**

"""

from pendulum import local

from camcops_server.cc_modules.cc_testfactories import (
    GroupFactory,
    PatientTaskScheduleFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
)
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase

from camcops_server.cc_modules.cc_taskschedulereports import (
    InvitationCountReport,
)


class InvitationCountReportTests(BasicDatabaseTestCase):
    def setUp(self) -> None:
        self.report = InvitationCountReport()

        super().setUp()

    def test_column_names(self) -> None:
        result = self.report.get_rows_colnames(self.req)

        self.assertEqual(
            result.column_names,
            ["year", "month", "group", "schedule", "tasks"],
        )

    def test_rows_for_no_registered_patients(self) -> None:
        group_a = GroupFactory(name="group_a")
        group_b = GroupFactory(name="group_b")

        ts1 = TaskScheduleFactory(name="ts1", group=group_a)
        TaskScheduleItemFactory(task_schedule=ts1, task_table_name="bmi")
        TaskScheduleItemFactory(task_schedule=ts1, task_table_name="phq9")

        ts2 = TaskScheduleFactory(name="ts2", group=group_a)
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="cisr")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="wsas")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="audit")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="pcl5")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="phq9")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="gad7")

        ts3 = TaskScheduleFactory(name="ts3", group=group_b)
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="phq9")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="gad7")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="wsas")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="eq5d5l")

        PatientTaskScheduleFactory.create_batch(3, task_schedule=ts1)
        PatientTaskScheduleFactory.create_batch(4, task_schedule=ts2)
        PatientTaskScheduleFactory.create_batch(5, task_schedule=ts3)

        result = self.report.get_rows_colnames(self.req)

        # 2 tasks, 3 patients
        self.assertEqual(result.rows[0], (None, None, "group_a", "ts1", 2 * 3))
        # 6 tasks, 4 patients
        self.assertEqual(result.rows[1], (None, None, "group_a", "ts2", 6 * 4))
        # 4 tasks, 5 patients
        self.assertEqual(result.rows[2], (None, None, "group_b", "ts3", 4 * 5))

        self.assertEqual(len(result.rows), 3)

    def test_rows_for_some_registered_patients(self) -> None:
        group_a = GroupFactory(name="group_a")
        group_b = GroupFactory(name="group_b")

        ts1 = TaskScheduleFactory(name="ts1", group=group_a)
        TaskScheduleItemFactory(task_schedule=ts1, task_table_name="bmi")
        TaskScheduleItemFactory(task_schedule=ts1, task_table_name="phq9")

        ts2 = TaskScheduleFactory(name="ts2", group=group_a)
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="cisr")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="wsas")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="audit")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="pcl5")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="phq9")
        TaskScheduleItemFactory(task_schedule=ts2, task_table_name="gad7")

        ts3 = TaskScheduleFactory(name="ts3", group=group_b)
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="phq9")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="gad7")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="wsas")
        TaskScheduleItemFactory(task_schedule=ts3, task_table_name="eq5d5l")

        PatientTaskScheduleFactory.create_batch(1, task_schedule=ts1)
        PatientTaskScheduleFactory.create_batch(2, task_schedule=ts2)
        PatientTaskScheduleFactory.create_batch(3, task_schedule=ts3)

        PatientTaskScheduleFactory.create_batch(
            4, task_schedule=ts1, start_datetime=local(2022, 9, 1, 12)
        )
        PatientTaskScheduleFactory.create_batch(
            5, task_schedule=ts2, start_datetime=local(2022, 9, 1, 12)
        )
        PatientTaskScheduleFactory.create_batch(
            6, task_schedule=ts3, start_datetime=local(2022, 9, 1, 12)
        )

        PatientTaskScheduleFactory.create_batch(
            7, task_schedule=ts1, start_datetime=local(2022, 10, 1, 12)
        )
        PatientTaskScheduleFactory.create_batch(
            8, task_schedule=ts2, start_datetime=local(2022, 10, 1, 12)
        )
        PatientTaskScheduleFactory.create_batch(
            9, task_schedule=ts3, start_datetime=local(2022, 10, 1, 12)
        )

        result = self.report.get_rows_colnames(self.req)

        expected = [
            (None, None, "group_a", "ts1", 2 * 1),  # 2 tasks, 1 patient
            (2022, 9, "group_a", "ts1", 2 * 4),  # 2 tasks, 4 patients
            (2022, 10, "group_a", "ts1", 2 * 7),  # 2 tasks, 7 patients
            (None, None, "group_a", "ts2", 6 * 2),  # 6 tasks, 2 patients
            (2022, 9, "group_a", "ts2", 6 * 5),  # 6 tasks, 5 patients
            (2022, 10, "group_a", "ts2", 6 * 8),  # 6 tasks, 8 patients
            (None, None, "group_b", "ts3", 4 * 3),  # 4 tasks, 3 patients
            (2022, 9, "group_b", "ts3", 4 * 6),  # 4 tasks, 6 patients
            (2022, 10, "group_b", "ts3", 4 * 9),  # 4 tasks, 9 patients
        ]

        self.assertEqual(result.rows, expected)
