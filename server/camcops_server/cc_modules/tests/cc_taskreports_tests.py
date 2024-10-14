"""
camcops_server/cc_modules/tests/cc_tasksreports_tests.py

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

**Test server reports on CamCOPS tasks.**

"""

from typing import Optional

from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.cc_modules.cc_taskindex import TaskIndexEntry
from camcops_server.cc_modules.cc_taskreports import TaskCountReport
from camcops_server.cc_modules.cc_testfactories import (
    GroupFactory,
    PatientFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import BasicDatabaseTestCase
from camcops_server.tasks.tests.factories import BmiFactory, Phq9Factory

from pendulum import DateTime as Pendulum, datetime


class TaskCountReportTestBase(BasicDatabaseTestCase):
    # pytest will collect tests that are derived from unitest.TestCase
    # regardless of what python_classes says in pytest.ini so we need to set
    # this to stop tests being run in the baseclass and override in the derived
    # class.
    __test__ = False

    def setUp(self) -> None:
        super().setUp()

        self.date_01_oct_2022 = datetime(2022, 10, 1, 12)
        self.date_01_nov_2022 = datetime(2022, 11, 1, 12)
        self.date_30_nov_2022 = datetime(2022, 11, 30, 12)
        self.date_01_jan_2023 = datetime(2023, 1, 1, 12)

        self.num_01_nov_2022_phq9_tasks = 4
        self.num_30_nov_2022_phq9_tasks = 5
        self.num_01_oct_2022_bmi_tasks = 2
        self.num_01_nov_2022_bmi_tasks = 3
        self.num_01_jan_2023_bmi_tasks = 1

        # Freda and Jim are both members of Group A. Freda took over from Jim
        # in Nov 2022
        self.group_a = GroupFactory(name="Group A")
        self.group_b = GroupFactory(name="Group B")

        self.freda = UserFactory(username="freda")
        self.jim = UserFactory(username="jim")

        UserGroupMembershipFactory(
            group_id=self.group_a.id,
            user_id=self.freda.id,
            may_run_reports=True,
        )
        UserGroupMembershipFactory(
            group_id=self.group_a.id, user_id=self.jim.id, may_run_reports=True
        )

        self.num_jim_tasks = self.num_01_oct_2022_bmi_tasks = 2
        self.num_freda_tasks = (
            self.num_01_nov_2022_phq9_tasks
            + self.num_30_nov_2022_phq9_tasks
            + self.num_01_nov_2022_bmi_tasks
            + self.num_01_jan_2023_bmi_tasks
        )

        self.num_group_a_tasks = self.num_jim_tasks + self.num_freda_tasks

        all_tasks = []

        for i in range(0, self.num_01_oct_2022_bmi_tasks):
            patient = PatientFactory(
                _when_added_exact=self.date_01_oct_2022,
            )
            all_tasks.append(
                BmiFactory(
                    _group=self.group_a,
                    patient_id=patient.id,
                    when_created=self.date_01_oct_2022,
                    _when_added_exact=self.date_01_oct_2022,
                    _adding_user=self.jim,
                )
            )

        for i in range(0, self.num_01_nov_2022_bmi_tasks):
            patient = PatientFactory(
                _when_added_exact=self.date_01_nov_2022,
            )
            all_tasks.append(
                BmiFactory(
                    _group=self.group_a,
                    patient_id=patient.id,
                    when_created=self.date_01_nov_2022,
                    _when_added_exact=self.date_01_nov_2022,
                    _adding_user=self.freda,
                )
            )

        for i in range(0, self.num_01_nov_2022_phq9_tasks):
            patient = PatientFactory(
                _when_added_exact=self.date_01_nov_2022,
            )
            all_tasks.append(
                Phq9Factory(
                    _group=self.group_a,
                    patient_id=patient.id,
                    when_created=self.date_01_nov_2022,
                    _when_added_exact=self.date_01_nov_2022,
                    _adding_user=self.freda,
                )
            )

        for i in range(0, self.num_30_nov_2022_phq9_tasks):
            patient = PatientFactory(
                _when_added_exact=self.date_30_nov_2022,
            )
            all_tasks.append(
                Phq9Factory(
                    _group=self.group_a,
                    patient_id=patient.id,
                    when_created=self.date_30_nov_2022,
                    _when_added_exact=self.date_30_nov_2022,
                    _adding_user=self.freda,
                )
            )

        for i in range(0, self.num_01_jan_2023_bmi_tasks):
            patient = PatientFactory(
                _when_added_exact=self.date_01_jan_2023,
            )
            all_tasks.append(
                BmiFactory(
                    _group=self.group_a,
                    patient_id=patient.id,
                    when_created=self.date_01_jan_2023,
                    _when_added_exact=self.date_01_jan_2023,
                    _adding_user=self.freda,
                )
            )

        # A task in another group, which won't be seen by group A
        self.shabeen = UserFactory(username="shabeen")

        UserGroupMembershipFactory(
            group_id=self.group_b.id, user_id=self.shabeen.id
        )

        patient = PatientFactory(
            _when_added_exact=self.date_01_jan_2023,
        )

        all_tasks.append(
            BmiFactory(
                _group=self.group_b,
                patient_id=patient.id,
                _when_added_exact=self.date_01_jan_2023,
                _adding_user=self.shabeen,
            )
        )
        self.num_group_b_tasks = 1

        if self.via_index:
            # There might be a better way of doing this automatically in
            # TaskFactory though in the real world indexing is a manual
            # process.
            for task in all_tasks:
                TaskIndexEntry.index_task(
                    task, self.dbsession, indexed_at_utc=Pendulum.utcnow()
                )

        self.report = TaskCountReport()

    @property
    def via_index(self) -> Optional[bool]:
        raise NotImplementedError("via_index must return True or False")

    def test_task_counts_by_year_and_month(self) -> None:
        year_column = 0
        month_column = 1
        task_column = 2
        num_tasks_added_column = 3

        num_nov_2022_phq9_tasks = (
            self.num_01_nov_2022_phq9_tasks + self.num_30_nov_2022_phq9_tasks
        )

        # Default is by year and month but better to be explicit
        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "true",
                ViewParam.BY_MONTH: "true",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        self.req._debugging_user = self.freda
        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "year",
                "month",
                "task",
                "num_tasks_added",
            ],
        )

        row = 0

        self.assertEqual(result.rows[row][year_column], 2023)
        self.assertEqual(result.rows[row][month_column], 1)
        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column],
            self.num_01_jan_2023_bmi_tasks,
        )

        row += 1

        self.assertEqual(result.rows[row][year_column], 2022)
        self.assertEqual(result.rows[row][month_column], 11)
        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column],
            self.num_01_nov_2022_bmi_tasks,
        )

        row += 1

        self.assertEqual(result.rows[row][year_column], 2022)
        self.assertEqual(result.rows[row][month_column], 11)
        self.assertEqual(result.rows[row][task_column], "phq9")
        self.assertEqual(
            result.rows[row][num_tasks_added_column],
            num_nov_2022_phq9_tasks,
        )

        row += 1

        self.assertEqual(result.rows[row][year_column], 2022)
        self.assertEqual(result.rows[row][month_column], 10)
        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column],
            self.num_01_oct_2022_bmi_tasks,
        )

        row += 1

        self.assertEqual(len(result.rows), row)

    def test_task_counts_by_year(self) -> None:
        num_2022_bmi_tasks = (
            self.num_01_oct_2022_bmi_tasks + self.num_01_nov_2022_bmi_tasks
        )
        num_2022_phq9_tasks = (
            self.num_01_nov_2022_phq9_tasks + self.num_30_nov_2022_phq9_tasks
        )
        num_2023_bmi_tasks = self.num_01_jan_2023_bmi_tasks

        year_column = 0
        task_column = 1
        num_tasks_added_column = 2

        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "true",
                ViewParam.BY_MONTH: "false",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        self.req._debugging_user = self.freda
        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "year",
                "task",
                "num_tasks_added",
            ],
        )

        row = 0

        self.assertEqual(result.rows[row][year_column], 2023)
        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_2023_bmi_tasks
        )

        row += 1

        self.assertEqual(result.rows[row][year_column], 2022)
        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_2022_bmi_tasks
        )

        row += 1

        self.assertEqual(result.rows[row][year_column], 2022)
        self.assertEqual(result.rows[row][task_column], "phq9")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_2022_phq9_tasks
        )

        row += 1

        self.assertEqual(len(result.rows), row)

    def test_task_counts_by_task(self) -> None:
        num_bmi_tasks = (
            self.num_01_oct_2022_bmi_tasks
            + self.num_01_nov_2022_bmi_tasks
            + self.num_01_jan_2023_bmi_tasks
        )
        num_phq9_tasks = (
            self.num_01_nov_2022_phq9_tasks + self.num_30_nov_2022_phq9_tasks
        )

        task_column = 0
        num_tasks_added_column = 1

        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "false",
                ViewParam.BY_MONTH: "false",
                ViewParam.BY_TASK: "true",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        self.req._debugging_user = self.freda

        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "task",
                "num_tasks_added",
            ],
        )

        row = 0

        self.assertEqual(result.rows[row][task_column], "bmi")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_bmi_tasks
        )

        row += 1

        self.assertEqual(result.rows[row][task_column], "phq9")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_phq9_tasks
        )

        row += 1

        self.assertEqual(len(result.rows), row)

    def test_task_counts_by_user(self) -> None:
        user_column = 0
        num_tasks_added_column = 1

        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "false",
                ViewParam.BY_MONTH: "false",
                ViewParam.BY_TASK: "false",
                ViewParam.BY_USER: "true",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        self.req._debugging_user = self.freda
        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "adding_user_name",
                "num_tasks_added",
            ],
        )

        row = 0

        self.assertEqual(result.rows[row][user_column], "freda")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], self.num_freda_tasks
        )

        row += 1

        self.assertEqual(result.rows[row][user_column], "jim")
        self.assertEqual(
            result.rows[row][num_tasks_added_column], self.num_jim_tasks
        )

        row += 1

        self.assertEqual(len(result.rows), row)

    def test_total_task_count_for_superuser(self) -> None:
        num_tasks_added_column = 0

        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "false",
                ViewParam.BY_MONTH: "false",
                ViewParam.BY_TASK: "false",
                ViewParam.BY_USER: "false",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "num_tasks_added",
            ],
        )

        row = 0

        total_tasks = self.num_group_a_tasks + self.num_group_b_tasks

        self.assertEqual(result.rows[row][num_tasks_added_column], total_tasks)

        row += 1

        self.assertEqual(len(result.rows), row)

    def test_task_counts_by_day_of_month(self) -> None:
        # Not a very realistic scenario. Would normally
        # be combined with month and year but these are
        # covered in other tests.
        num_day_01_tasks = (
            self.num_01_oct_2022_bmi_tasks
            + self.num_01_nov_2022_bmi_tasks
            + self.num_01_nov_2022_phq9_tasks
            + self.num_01_jan_2023_bmi_tasks
        )
        num_day_30_tasks = self.num_30_nov_2022_phq9_tasks

        day_of_month_column = 0
        num_tasks_added_column = 1

        self.req.add_get_params(
            {
                ViewParam.BY_YEAR: "false",
                ViewParam.BY_MONTH: "false",
                ViewParam.BY_DAY_OF_MONTH: "true",
                ViewParam.BY_TASK: "false",
                ViewParam.VIA_INDEX: "true" if self.via_index else "false",
            }
        )

        self.req._debugging_user = self.freda
        result = self.report.get_rows_colnames(self.req)
        self.assertEqual(
            result.column_names,
            [
                "day_of_month",
                "num_tasks_added",
            ],
        )

        row = 0

        self.assertEqual(result.rows[row][day_of_month_column], 30)
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_day_30_tasks
        )

        row += 1

        self.assertEqual(result.rows[row][day_of_month_column], 1)
        self.assertEqual(
            result.rows[row][num_tasks_added_column], num_day_01_tasks
        )

        row += 1

        self.assertEqual(len(result.rows), row)


class TaskCountReportNoIndexTests(TaskCountReportTestBase):
    __test__ = True

    @property
    def via_index(self) -> Optional[bool]:
        return False


class TaskCountReportWithIndexTests(TaskCountReportTestBase):
    __test__ = True

    @property
    def via_index(self) -> Optional[bool]:
        return True
