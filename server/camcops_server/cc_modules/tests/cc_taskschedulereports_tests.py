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
    ServerCreatedPatientFactory,
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
        self.august = local(2022, 8, 1, 12)
        self.september = local(2022, 9, 1, 12)
        self.october = local(2022, 10, 1, 12)
        self.november = local(2022, 11, 1, 12)

        super().setUp()

    def test_column_names(self) -> None:
        result = self.report.get_rows_colnames(self.req)

        self.assertEqual(
            result.column_names,
            [
                "year",
                "month",
                "group_name",
                "schedule_name",
                "patients_created",
                "tasks",
            ],
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

        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.november
            )

            PatientTaskScheduleFactory(task_schedule=ts1, patient=patient)

        for i in range(0, 4):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.october
            )

            PatientTaskScheduleFactory(task_schedule=ts2, patient=patient)

        for i in range(0, 5):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september
            )
            PatientTaskScheduleFactory(task_schedule=ts3, patient=patient)

        result = self.report.get_rows_colnames(self.req)

        # 3 patients created, no tasks completed
        self.assertEqual(result.rows[0], (2022, 11, "group_a", "ts1", 3, 0))
        # 4 patients created, no tasks completed
        self.assertEqual(result.rows[1], (2022, 10, "group_a", "ts2", 4, 0))
        # 5 patients created, no tasks completed
        self.assertEqual(result.rows[2], (2022, 9, "group_b", "ts3", 5, 0))
        # 2 tasks assigned to 3 patients
        self.assertEqual(
            result.rows[3], (None, None, "group_a", "ts1", 0, 2 * 3)
        )
        # 6 tasks assigned to 4 patients
        self.assertEqual(
            result.rows[4], (None, None, "group_a", "ts2", 0, 6 * 4)
        )
        # 4 tasks assigned to 5 patients
        self.assertEqual(
            result.rows[5], (None, None, "group_b", "ts3", 0, 4 * 5)
        )

        self.assertEqual(len(result.rows), 6)

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

        for i in range(0, 1):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(task_schedule=ts1, patient=patient)

        for i in range(0, 2):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(task_schedule=ts2, patient=patient)

        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(task_schedule=ts3, patient=patient)

        for i in range(0, 4):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts1,
                start_datetime=self.september,
                patient=patient,
            )

        for i in range(0, 5):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts2,
                start_datetime=self.september,
                patient=patient,
            )

        for i in range(0, 6):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts3,
                start_datetime=self.september,
                patient=patient,
            )

        for i in range(0, 7):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts1, start_datetime=self.october, patient=patient
            )

        for i in range(0, 8):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts2, start_datetime=self.october, patient=patient
            )

        for i in range(0, 9):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            PatientTaskScheduleFactory(
                task_schedule=ts3, start_datetime=self.october, patient=patient
            )

        result = self.report.get_rows_colnames(self.req)

        expected = [
            (2022, 10, "group_a", "ts1", 0, 2 * 7),  # 2 tasks, 7 patients
            (2022, 10, "group_a", "ts2", 0, 6 * 8),  # 6 tasks, 8 patients
            (2022, 10, "group_b", "ts3", 0, 4 * 9),  # 4 tasks, 9 patients
            (2022, 9, "group_a", "ts1", 0, 2 * 4),  # 2 tasks, 4 patients
            (2022, 9, "group_a", "ts2", 0, 6 * 5),  # 6 tasks, 5 patients
            (2022, 9, "group_b", "ts3", 0, 4 * 6),  # 4 tasks, 6 patients
            (2022, 8, "group_a", "ts1", 7 + 4 + 1, 0),  # 12 patients created
            (2022, 8, "group_a", "ts2", 8 + 5 + 2, 0),  # 15 patients created
            (2022, 8, "group_b", "ts3", 9 + 6 + 3, 0),  # 18 patients created
            (None, None, "group_a", "ts1", 0, 2 * 1),  # 2 tasks, 1 patient
            (None, None, "group_a", "ts2", 0, 6 * 2),  # 6 tasks, 2 patients
            (None, None, "group_b", "ts3", 0, 4 * 3),  # 4 tasks, 3 patients
        ]

        self.assertEqual(result.rows, expected)
