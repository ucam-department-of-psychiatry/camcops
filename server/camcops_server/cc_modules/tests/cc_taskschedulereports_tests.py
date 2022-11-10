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

from pendulum import datetime

from camcops_server.cc_modules.cc_testfactories import (
    EmailFactory,
    GroupFactory,
    PatientTaskScheduleFactory,
    PatientTaskScheduleEmailFactory,
    ServerCreatedPatientFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase

from camcops_server.cc_modules.cc_taskschedulereports import (
    TaskAssignmentReport,
)


class TaskAssignmentReportTests(BasicDatabaseTestCase):
    YEAR_COLUMN = 0
    MONTH_COLUMN = 1
    GROUP_COLUMN = 2
    SCHEDULE_COLUMN = 3
    PATIENTS_COLUMN = 4
    TASKS_COLUMN = 5
    EMAILS_COLUMN = 6

    def setUp(self) -> None:
        super().setUp()

        self.group_a = GroupFactory(name="group_a")
        self.group_b = GroupFactory(name="group_b")

        self.ts1 = TaskScheduleFactory(name="ts1", group=self.group_a)
        self.ts1_task_names = ["bmi", "phq9"]
        for task_name in self.ts1_task_names:
            TaskScheduleItemFactory(
                task_schedule=self.ts1, task_table_name=task_name
            )

        self.ts2 = TaskScheduleFactory(name="ts2", group=self.group_a)
        self.ts2_task_names = [
            "cisr",
            "wsas",
            "audit",
            "pcl5",
            "phq9",
            "gad7",
        ]
        for task_name in self.ts2_task_names:
            TaskScheduleItemFactory(
                task_schedule=self.ts2, task_table_name=task_name
            )

        self.ts3 = TaskScheduleFactory(name="ts3", group=self.group_b)
        self.ts3_task_names = [
            "phq9",
            "gad7",
            "wsas",
            "eq5d5l",
        ]
        for task_name in self.ts3_task_names:
            TaskScheduleItemFactory(
                task_schedule=self.ts3, task_table_name=task_name
            )

        self.august = datetime(2022, 8, 1, 12)
        self.september = datetime(2022, 9, 1, 12)
        self.october = datetime(2022, 10, 1, 12)
        self.november = datetime(2022, 11, 1, 12)

        self.report = TaskAssignmentReport()

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
                "tasks_assigned",
                "emails_sent",
            ],
        )

    def test_task_patient_counts_for_no_registered_patients(self) -> None:
        sep_patients = []
        oct_patients = []
        nov_patients = []
        ts1_patients = []
        ts2_patients = []
        ts3_patients = []
        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.november
            )
            nov_patients.append(patient)
            ts1_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts1, patient=patient)

        for i in range(0, 4):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.october
            )
            oct_patients.append(patient)
            ts2_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts2, patient=patient)

        for i in range(0, 5):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september
            )
            sep_patients.append(patient)
            ts3_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts3, patient=patient)

        result = self.report.get_rows_colnames(self.req)

        # patients created, no tasks completed
        row = 0
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 11)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN], len(nov_patients)
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # patients created, no tasks completed
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 10)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN], len(oct_patients)
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # patients created, no tasks completed
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN], len(sep_patients)
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # tasks assigned to patients not yet registered
        # it should not be possible to have patients without a
        # creation date (_when_added_exact attribute)
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0, 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts1_task_names) * len(ts1_patients),
        )
        row += 1

        # tasks assigned to patients not yet registered
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0, 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts2_task_names) * len(ts2_patients),
        )
        row += 1

        # tasks assigned to patients not yet registered
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0, 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts3_task_names) * len(ts3_patients),
        )
        row += 1

        # Check there's nothing else
        self.assertEqual(len(result.rows), row)

    def test_task_patient_counts_for_some_registered_patients(self) -> None:
        ts1_unregistered_patients = []
        ts2_unregistered_patients = []
        ts3_unregistered_patients = []
        ts1_aug_created_patients = []
        ts2_aug_created_patients = []
        ts3_aug_created_patients = []
        ts1_sep_registered_patients = []
        ts2_sep_registered_patients = []
        ts3_sep_registered_patients = []
        ts1_oct_registered_patients = []
        ts2_oct_registered_patients = []
        ts3_oct_registered_patients = []

        for i in range(0, 1):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts1_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts1, patient=patient)
            ts1_unregistered_patients.append(patient)

        for i in range(0, 2):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts2_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts2, patient=patient)
            ts2_unregistered_patients.append(patient)

        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts3_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(task_schedule=self.ts3, patient=patient)
            ts3_unregistered_patients.append(patient)

        for i in range(0, 4):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts1_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts1,
                start_datetime=self.september,
                patient=patient,
            )
            ts1_sep_registered_patients.append(patient)

        for i in range(0, 5):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts2_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts2,
                start_datetime=self.september,
                patient=patient,
            )
            ts2_sep_registered_patients.append(patient)

        for i in range(0, 6):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts3_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts3,
                start_datetime=self.september,
                patient=patient,
            )
            ts3_sep_registered_patients.append(patient)

        for i in range(0, 7):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts1_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts1,
                start_datetime=self.october,
                patient=patient,
            )
            ts1_oct_registered_patients.append(patient)

        for i in range(0, 8):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts2_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts2,
                start_datetime=self.october,
                patient=patient,
            )
            ts2_oct_registered_patients.append(patient)

        for i in range(0, 9):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.august
            )
            ts3_aug_created_patients.append(patient)
            PatientTaskScheduleFactory(
                task_schedule=self.ts3,
                start_datetime=self.october,
                patient=patient,
            )
            ts3_oct_registered_patients.append(patient)

        result = self.report.get_rows_colnames(self.req)

        row = 0
        # tasks assigned to ts1 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 10)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts1_task_names) * len(ts1_oct_registered_patients),
        )
        row += 1

        # tasks assigned to ts2 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 10)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts2_task_names) * len(ts2_oct_registered_patients),
        )
        row += 1

        # tasks assigned to ts3 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 10)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts3_task_names) * len(ts3_oct_registered_patients),
        )
        row += 1

        # tasks assigned to ts1 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts1_task_names) * len(ts1_sep_registered_patients),
        )
        row += 1

        # tasks assigned to ts2 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts2_task_names) * len(ts2_sep_registered_patients),
        )
        row += 1

        # tasks assigned to ts3 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts3_task_names) * len(ts3_sep_registered_patients),
        )
        row += 1

        # ts1 patients created, no tasks
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 8)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN],
            len(ts1_aug_created_patients),
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # ts2 patients created, no tasks
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 8)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN],
            len(ts2_aug_created_patients),
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # tasks assigned to ts3 patients
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 8)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(
            result.rows[row][self.PATIENTS_COLUMN],
            len(ts3_aug_created_patients),
        )
        self.assertEqual(result.rows[row][self.TASKS_COLUMN], 0)
        row += 1

        # tasks assigned to ts1 patients not yet registered
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts1_task_names) * len(ts1_unregistered_patients),
        )
        row += 1

        # tasks assigned to ts2 patients not yet registered
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts2_task_names) * len(ts2_unregistered_patients),
        )
        row += 1

        # tasks assigned to ts3 patients not yet registered
        self.assertIsNone(result.rows[row][self.YEAR_COLUMN])
        self.assertIsNone(result.rows[row][self.MONTH_COLUMN])
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(result.rows[row][self.PATIENTS_COLUMN], 0)
        self.assertEqual(
            result.rows[row][self.TASKS_COLUMN],
            len(self.ts3_task_names) * len(ts3_unregistered_patients),
        )
        row += 1

        self.assertEqual(len(result.rows), row)

    def test_email_counts(self) -> None:
        ts1_emails = []
        ts2_emails = []
        ts3_emails = []

        for i in range(0, 1):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september
            )
            pts = PatientTaskScheduleFactory(
                task_schedule=self.ts1,
                patient=patient,
                start_datetime=self.september,
            )
            email = EmailFactory(sent_at_utc=self.september, sent=True)
            ts1_emails.append(
                PatientTaskScheduleEmailFactory(
                    patient_task_schedule=pts, email=email
                )
            )
            email = EmailFactory(sent_at_utc=self.september, sent=True)
            ts1_emails.append(
                PatientTaskScheduleEmailFactory(
                    patient_task_schedule=pts, email=email
                )
            )

        for i in range(0, 2):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september
            )
            pts = PatientTaskScheduleFactory(
                task_schedule=self.ts2,
                patient=patient,
                start_datetime=self.september,
            )
            email = EmailFactory(sent_at_utc=self.september, sent=True)
            ts2_emails.append(
                PatientTaskScheduleEmailFactory(
                    patient_task_schedule=pts, email=email
                )
            )

        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september
            )
            pts = PatientTaskScheduleFactory(
                task_schedule=self.ts3,
                patient=patient,
                start_datetime=self.september,
            )
            email = EmailFactory(sent_at_utc=self.september, sent=True)
            ts3_emails.append(
                PatientTaskScheduleEmailFactory(
                    patient_task_schedule=pts, email=email
                )
            )
            # These should not be included (sent=False)
            email = EmailFactory(sent_at_utc=self.september, sent=False)
            PatientTaskScheduleEmailFactory(
                patient_task_schedule=pts, email=email
            )

        result = self.report.get_rows_colnames(self.req)

        row = 0
        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts1.name)
        self.assertEqual(result.rows[row][self.EMAILS_COLUMN], len(ts1_emails))
        row += 1

        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_a.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts2.name)
        self.assertEqual(result.rows[row][self.EMAILS_COLUMN], len(ts2_emails))
        row += 1

        self.assertEqual(result.rows[row][self.YEAR_COLUMN], 2022)
        self.assertEqual(result.rows[row][self.MONTH_COLUMN], 9)
        self.assertEqual(
            result.rows[row][self.GROUP_COLUMN], self.group_b.name
        )
        self.assertEqual(result.rows[row][self.SCHEDULE_COLUMN], self.ts3.name)
        self.assertEqual(result.rows[row][self.EMAILS_COLUMN], len(ts3_emails))
        row += 1

        self.assertEqual(len(result.rows), row)

    def test_groups_restricted_when_not_superuser(self) -> None:
        user = UserFactory()
        UserGroupMembershipFactory(
            group_id=self.ts1.group.id, user_id=user.id, may_run_reports=True
        )

        self.req._debugging_user = user

        # Should include these
        for i in range(0, 3):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september, _group=self.ts1.group
            )
            PatientTaskScheduleFactory(
                task_schedule=self.ts1,
                patient=patient,
                start_datetime=self.september,
            )

        # Should ignore these
        for i in range(0, 2):
            patient = ServerCreatedPatientFactory(
                _when_added_exact=self.september, _group=self.ts3.group
            )
            PatientTaskScheduleFactory(
                task_schedule=self.ts3,
                patient=patient,
                start_datetime=self.september,
            )

        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(len(result.rows), 1)
