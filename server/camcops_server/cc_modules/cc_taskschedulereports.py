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

from typing import List, Tuple, Type, TYPE_CHECKING

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.sqlalchemy.orm_query import (
    get_rows_fieldnames_from_query,
)
from cardinal_pythonlib.sqlalchemy.sqlfunc import extract_month, extract_year
from sqlalchemy import cast, Integer
from sqlalchemy.sql.expression import func, select
from sqlalchemy.sql.functions import FunctionElement

from camcops_server.cc_modules.cc_sqla_coltypes import (
    isotzdatetime_to_utcdatetime,
)
from camcops_server.cc_modules.cc_forms import ReportParamSchema
from camcops_server.cc_modules.cc_group import Group
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
    - Number of incomplete tasks for registered patients (by month)::

        SELECT substr(start_datetime, 1, 7) AS month,
            ts.group_id, ts.name, COUNT(tsi.id) AS num_tasks
        FROM _patient_task_schedule pts
        JOIN _task_schedule ts ON pts.schedule_id = ts.id
        JOIN _task_schedule_item tsi ON tsi.schedule_id = ts.id
        GROUP BY ts.group_id, ts.name, month;

    and, for a particular time frame:

    - Number of server-side patients created::

        SELECT substr(_when_added_exact, 1, 7) AS month,
            p._group_id, COUNT(p.id) AS num_patients
        FROM patient p WHERE p._device_id = 1 GROUP BY p._group_id, month;

    - Number of emails sent to patients::

        SELECT substr(e.sent_at_utc, 1, 7) AS month,
            ts.group_id, ts.name, COUNT(ptse.id) AS num_emails
        FROM _patient_task_schedule pts
        JOIN _task_schedule ts ON pts.schedule_id = ts.id
        JOIN _patient_task_schedule_email ptse ON ptse.patient_task_schedule_id = pts.id
        JOIN _emails e ON ptse.email_id = e.id
        GROUP BY ts.group_id, ts.name, month;

    """  # noqa: E501

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
        dbsession = req.dbsession
        group_ids = req.user.ids_of_groups_user_may_report_on
        superuser = req.user.superuser

        by_year = req.get_bool_param(ViewParam.BY_YEAR, DEFAULT_BY_YEAR)
        by_month = req.get_bool_param(ViewParam.BY_MONTH, DEFAULT_BY_MONTH)

        label_year = "year"
        label_month = "month"
        label_group = "group"
        label_schedule = "schedule"
        label_n = "tasks"

        colnames = []  # type: List[str]  # for type checker

        groupers = [label_group, label_schedule]  # type: List[str]
        sorters = ["group", "schedule"]  # type: List[Tuple[str, bool]]
        # ... (key, reversed/descending)

        if by_year:
            groupers.append(label_year)
            sorters.append((label_year, True))
        if by_month:
            groupers.append(label_month)
            sorters.append((label_month, True))

        selectors = []  # type: List[FunctionElement]

        pts = PatientTaskSchedule.__table__.alias("pts")
        ts = TaskSchedule.__table__.alias("ts")
        tsi = TaskScheduleItem.__table__.alias("tsi")
        group = Group.__table__.alias("group")

        if by_year:
            selectors.append(
                cast(  # Necessary for SQLite
                    extract_year(
                        isotzdatetime_to_utcdatetime(pts.c.start_datetime)
                    ),
                    Integer(),
                ).label(label_year)
            )
        if by_month:
            selectors.append(
                cast(  # Necessary for SQLite
                    extract_month(
                        isotzdatetime_to_utcdatetime(pts.c.start_datetime)
                    ),
                    Integer(),
                ).label(label_month)
            )
        # Regardless:
        selectors.append(group.c.name.label(label_group))
        selectors.append(ts.c.name.label(label_schedule))
        selectors.append(func.count().label(label_n))

        # noinspection PyUnresolvedReferences

        query = (
            select(selectors)
            .select_from(
                pts.join(ts, pts.c.schedule_id == ts.c.id)
                .join(tsi, tsi.c.schedule_id == ts.c.id)
                .join(group, ts.c.group_id == group.c.id)
            )
            .group_by(*groupers)
        )
        if not superuser:
            # Restrict to accessible groups
            # noinspection PyProtectedMember
            query = query.where(group.c.id.in_(group_ids))

        rows, colnames = get_rows_fieldnames_from_query(dbsession, query)

        return PlainReportType(rows=rows, column_names=colnames)
