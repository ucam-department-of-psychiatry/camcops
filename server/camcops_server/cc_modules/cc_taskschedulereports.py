#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_taskschedulereports.py

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

**Server reports on CamCOPS scheduled tasks.**

"""

from typing import List, Type, TYPE_CHECKING, Union

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.sqlalchemy.orm_query import (
    get_rows_fieldnames_from_query,
)
from cardinal_pythonlib.sqlalchemy.sqlfunc import extract_month, extract_year
from sqlalchemy import cast, Integer
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.expression import (
    desc,
    func,
    literal,
    select,
    union_all,
    Selectable,
)
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.sql.schema import Column

from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_sqla_coltypes import (
    isotzdatetime_to_utcdatetime,
)
from camcops_server.cc_modules.cc_forms import ReportParamSchema
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.cc_modules.cc_report import Report, PlainReportType
from camcops_server.cc_modules.cc_reportschema import (
    ByYearSelector,
    ByMonthSelector,
    DEFAULT_BY_MONTH,
    DEFAULT_BY_YEAR,
)
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    TaskSchedule,
    TaskScheduleItem,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class InvitationCountReportSchema(ReportParamSchema):
    by_year = ByYearSelector()  # must match ViewParam.BY_YEAR
    by_month = ByMonthSelector()  # must match ViewParam.BY_MONTH


# =============================================================================
# Reports
# =============================================================================


class InvitationCountReport(Report):
    """
    Report to count invitations to server-side patients to complete tasks.

    We don't currently record when a patient was assigned to a task schedule
    but we can provide enough clues with the task count report and:

    - Number of incomplete tasks for unregistered patients (all time)
    - Number of incomplete tasks for registered patients (by month or year)
    - Number of server-side patients created (by month or year)
    - Number of emails sent to patients (by month or year)

        SELECT substr(e.sent_at_utc, 1, 7) AS month,
            ts.group_id, ts.name, COUNT(ptse.id) AS num_emails
        FROM _patient_task_schedule pts
        JOIN _task_schedule ts ON pts.schedule_id = ts.id
        JOIN _patient_task_schedule_email ptse ON ptse.patient_task_schedule_id = pts.id
        JOIN _emails e ON ptse.email_id = e.id
        GROUP BY ts.group_id, ts.name, month;

    """  # noqa: E501

    label_year = "year"
    label_month = "month"
    label_group_id = "group_id"
    label_group_name = "group_name"
    label_schedule_id = "schedule_id"
    label_schedule_name = "schedule_name"
    label_tasks = "tasks"
    label_patients = "patients_created"

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "invitationcount"

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("(Server) Count of invitations to complete tasks")

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    @staticmethod
    def get_paramform_schema_class() -> Type["ReportParamSchema"]:
        return InvitationCountReportSchema

    @classmethod
    def get_specific_http_query_keys(cls) -> List[str]:
        return [
            ViewParam.BY_YEAR,
            ViewParam.BY_MONTH,
        ]

    def get_rows_colnames(self, req: "CamcopsRequest") -> PlainReportType:
        by_year = req.get_bool_param(ViewParam.BY_YEAR, DEFAULT_BY_YEAR)
        by_month = req.get_bool_param(ViewParam.BY_MONTH, DEFAULT_BY_MONTH)

        colnames = []  # type: List[str]  # for type checker

        tasks_query = self._get_tasks_query(req, by_year, by_month)
        tasks_query.alias("tasks_data")
        patients_query = self._get_created_patients_query(
            req, by_year, by_month
        )
        patients_query.alias("patients_data")

        selectors = []  # type: List[FunctionElement]
        sorters = []  # type: List[Union[str, UnaryExpression]]
        groupers = [
            self.label_group_id,
            self.label_schedule_id,
            self.label_group_name,
            self.label_schedule_name,
        ]  # type: List[str]

        all_data = union_all(tasks_query, patients_query).alias("all_data")

        if by_year:
            selectors.append(all_data.c.year)
            groupers.append(all_data.c.year)
            sorters.append(desc(all_data.c.year))

        if by_month:
            selectors.append(all_data.c.month)
            groupers.append(all_data.c.month)
            sorters.append(desc(all_data.c.month))

        sorters += [all_data.c.group_id, all_data.c.schedule_id]
        selectors += [
            all_data.c.group_name,
            all_data.c.schedule_name,
            func.sum(all_data.c.patients_created).label(self.label_patients),
            func.sum(all_data.c.tasks).label(self.label_tasks),
        ]
        query = (
            select(selectors)
            .select_from(all_data)
            .group_by(*groupers)
            .order_by(*sorters)
        )

        rows, colnames = get_rows_fieldnames_from_query(req.dbsession, query)

        return PlainReportType(rows=rows, column_names=colnames)

    def _get_tasks_query(
        self, req: "CamcopsRequest", by_year: bool, by_month: bool
    ) -> Query:

        pts = PatientTaskSchedule.__table__
        ts = TaskSchedule.__table__
        tsi = TaskScheduleItem.__table__
        group = Group.__table__

        tables = (
            pts.join(ts, pts.c.schedule_id == ts.c.id)
            .join(tsi, tsi.c.schedule_id == ts.c.id)
            .join(group, ts.c.group_id == group.c.id)
        )

        date_column = pts.c.start_datetime
        # Order must be consistent across queries
        count_selectors = [
            literal(0).label(self.label_patients),
            func.count().label(self.label_tasks),
        ]

        query = self._build_query(
            req, tables, by_year, by_month, date_column, count_selectors
        )

        return query

    def _get_created_patients_query(
        self, req: "CamcopsRequest", by_year: bool, by_month: bool
    ) -> Query:
        server_device = Device.get_server_device(req.dbsession)

        pts = PatientTaskSchedule.__table__
        ts = TaskSchedule.__table__
        group = Group.__table__
        patient = Patient.__table__

        tables = (
            pts.join(ts, pts.c.schedule_id == ts.c.id)
            .join(group, ts.c.group_id == group.c.id)
            .join(patient, pts.c.patient_pk == patient.c._pk)
        )

        date_column = patient.c._when_added_exact
        # Order must be consistent across queries
        count_selectors = [
            func.count().label(self.label_patients),
            literal(0).label(self.label_tasks),
        ]

        query = self._build_query(
            req, tables, by_year, by_month, date_column, count_selectors
        ).where(patient.c._device_id == server_device.id)

        return query

    def _build_query(
        self,
        req: "CamcopsRequest",
        tables: Selectable,
        by_year: bool,
        by_month: bool,
        date_column: Column,
        count_selectors: List[FunctionElement],
    ) -> Query:
        group_ids = req.user.ids_of_groups_user_may_report_on
        superuser = req.user.superuser

        ts = TaskSchedule.__table__
        group = Group.__table__

        groupers = [
            group.c.id,
            ts.c.id,
        ]
        # ... (key, reversed/descending)

        selectors = []  # type: List[FunctionElement]

        if by_year:
            selectors.append(
                cast(  # Necessary for SQLite tests
                    extract_year(isotzdatetime_to_utcdatetime(date_column)),
                    Integer(),
                ).label(self.label_year)
            )
            groupers.append(self.label_year)

        if by_month:
            selectors.append(
                cast(  # Necessary for SQLite tests
                    extract_month(isotzdatetime_to_utcdatetime(date_column)),
                    Integer(),
                ).label(self.label_month)
            )
            groupers.append(self.label_month)
        # Regardless:
        selectors.append(group.c.id.label(self.label_group_id))
        selectors.append(group.c.name.label(self.label_group_name))
        selectors.append(ts.c.id.label(self.label_schedule_id))
        selectors.append(ts.c.name.label(self.label_schedule_name))
        selectors += count_selectors
        # noinspection PyUnresolvedReferences
        query = select(selectors).select_from(tables).group_by(*groupers)
        if not superuser:
            # Restrict to accessible groups
            # noinspection PyProtectedMember
            query = query.where(group.c.id.in_(group_ids))

        return query
