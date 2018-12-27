#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_taskreports.py

===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

**Server reports on CamCOPS tasks.**

"""

from typing import Any, List, Sequence, Type, TYPE_CHECKING

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.sqlalchemy.orm_query import get_rows_fieldnames_from_query  # noqa
from cardinal_pythonlib.sqlalchemy.sqlfunc import extract_month, extract_year
from sqlalchemy.sql.expression import and_, desc, func, literal, select

from camcops_server.cc_modules.cc_sqla_coltypes import (
    isotzdatetime_to_utcdatetime,
)
from camcops_server.cc_modules.cc_forms import (
    ReportParamSchema,
    ViaIndexSelector,
)
from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.cc_modules.cc_report import Report, PlainReportType
from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_taskindex import TaskIndexEntry

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


# =============================================================================
# Reports
# =============================================================================

class TaskCountReportSchema(ReportParamSchema):
    via_index = ViaIndexSelector()  # must match ViewParam.VIA_INDEX


class TaskCountReport(Report):
    """
    Report to count task instances.
    """

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "taskcount"

    # noinspection PyMethodParameters
    @classproperty
    def title(cls) -> str:
        return "(Server) Count current task instances, by creation date"

    # noinspection PyMethodParameters
    @classproperty
    def superuser_only(cls) -> bool:
        return False

    @staticmethod
    def get_paramform_schema_class() -> Type["ReportParamSchema"]:
        return TaskCountReportSchema

    @classmethod
    def get_specific_http_query_keys(cls) -> List[str]:
        return [
            ViewParam.VIA_INDEX
        ]

    def get_rows_colnames(self, req: "CamcopsRequest") -> PlainReportType:
        final_rows = []  # type: List[Sequence[Sequence[Any]]]
        colnames = []  # type: List[str]
        dbsession = req.dbsession
        group_ids = req.user.ids_of_groups_user_may_report_on
        superuser = req.user.superuser
        via_index = req.get_bool_param(ViewParam.VIA_INDEX, True)
        if via_index:
            # noinspection PyUnresolvedReferences
            query = (
                select([
                    TaskIndexEntry.task_table_name.label("task"),
                    extract_year(TaskIndexEntry.when_created_utc).label("year"),  # noqa
                    extract_month(TaskIndexEntry.when_created_utc).label("month"),  # noqa
                    func.count().label("num_tasks_added"),
                ])
                .select_from(TaskIndexEntry.__table__)
                .group_by("task", "year", "month")
                .order_by("task", desc("year"), desc("month"))
            )
            if not superuser:
                # Restrict to accessible groups
                # noinspection PyProtectedMember
                query = query.where(TaskIndexEntry.group_id.in_(group_ids))
            rows, colnames = get_rows_fieldnames_from_query(dbsession, query)
            final_rows.extend(rows)
        else:
            classes = Task.all_subclasses_by_tablename()
            for cls in classes:
                # noinspection PyProtectedMember
                select_fields = [
                    literal(cls.__tablename__).label("task"),
                    # func.year() is specific to some DBs, e.g. MySQL
                    # so is func.extract();
                    # http://modern-sql.com/feature/extract
                    extract_year(isotzdatetime_to_utcdatetime(
                        cls.when_created)).label("year"),
                    extract_month(isotzdatetime_to_utcdatetime(
                        cls.when_created)).label("month"),
                    func.count().label("num_tasks_added"),
                ]
                # noinspection PyUnresolvedReferences
                select_from = cls.__table__
                # noinspection PyProtectedMember
                wheres = [cls._current == True]  # nopep8
                if not superuser:
                    # Restrict to accessible groups
                    # noinspection PyProtectedMember
                    wheres.append(cls._group_id.in_(group_ids))
                group_by = ["year", "month"]
                order_by = [desc("year"), desc("month")]
                # ... http://docs.sqlalchemy.org/en/latest/core/tutorial.html#ordering-or-grouping-by-a-label  # noqa
                query = select(select_fields) \
                    .select_from(select_from) \
                    .where(and_(*wheres)) \
                    .group_by(*group_by) \
                    .order_by(*order_by)
                rows, colnames = get_rows_fieldnames_from_query(
                    dbsession, query)
                final_rows.extend(rows)
        return PlainReportType(rows=final_rows, column_names=colnames)
