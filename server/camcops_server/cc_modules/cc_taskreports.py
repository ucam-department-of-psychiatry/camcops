#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_taskreports.py

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

**Server reports on CamCOPS tasks.**

"""

from collections import Counter, namedtuple
from operator import attrgetter
from typing import Any, List, Sequence, Tuple, Type, TYPE_CHECKING, Union

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.sqlalchemy.orm_query import (
    get_rows_fieldnames_from_query,
)
from cardinal_pythonlib.sqlalchemy.sqlfunc import extract_month, extract_year
from sqlalchemy.engine.result import RowProxy
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.expression import desc, func, literal, select
from sqlalchemy.sql.functions import FunctionElement

from camcops_server.cc_modules.cc_sqla_coltypes import (
    isotzdatetime_to_utcdatetime,
)
from camcops_server.cc_modules.cc_forms import (
    ReportParamSchema,
    ViaIndexSelector,
)
from camcops_server.cc_modules.cc_pyramid import ViewParam
from camcops_server.cc_modules.cc_report import Report, PlainReportType
from camcops_server.cc_modules.cc_reportschema import (
    ByYearSelector,
    ByMonthSelector,
    ByTaskSelector,
    ByUserSelector,
    DEFAULT_BY_MONTH,
    DEFAULT_BY_TASK,
    DEFAULT_BY_USER,
    DEFAULT_BY_YEAR,
)

from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_taskindex import TaskIndexEntry
from camcops_server.cc_modules.cc_user import User

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


# =============================================================================
# Parameter schema
# =============================================================================


class TaskCountReportSchema(ReportParamSchema):
    by_year = ByYearSelector()  # must match ViewParam.BY_YEAR
    by_month = ByMonthSelector()  # must match ViewParam.BY_MONTH
    by_task = ByTaskSelector()  # must match ViewParam.BY_TASK
    by_user = ByUserSelector()  # must match ViewParam.BY_USER
    via_index = ViaIndexSelector()  # must match ViewParam.VIA_INDEX


# =============================================================================
# Reports
# =============================================================================


class TaskCountReport(Report):
    """
    Report to count task instances.
    """

    # noinspection PyMethodParameters
    @classproperty
    def report_id(cls) -> str:
        return "taskcount"

    @classmethod
    def title(cls, req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("(Server) Count current task instances")

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
            ViewParam.BY_YEAR,
            ViewParam.BY_MONTH,
            ViewParam.BY_TASK,
            ViewParam.BY_USER,
            ViewParam.VIA_INDEX,
        ]

    def get_rows_colnames(self, req: "CamcopsRequest") -> PlainReportType:
        dbsession = req.dbsession
        group_ids = req.user.ids_of_groups_user_may_report_on
        superuser = req.user.superuser

        by_year = req.get_bool_param(ViewParam.BY_YEAR, DEFAULT_BY_YEAR)
        by_month = req.get_bool_param(ViewParam.BY_MONTH, DEFAULT_BY_MONTH)
        by_task = req.get_bool_param(ViewParam.BY_TASK, DEFAULT_BY_TASK)
        by_user = req.get_bool_param(ViewParam.BY_USER, DEFAULT_BY_USER)
        via_index = req.get_bool_param(ViewParam.VIA_INDEX, True)

        label_year = "year"
        label_month = "month"
        label_task = "task"
        label_user = "adding_user_name"
        label_n = "num_tasks_added"

        final_rows = []  # type: List[Sequence[Sequence[Any]]]
        colnames = []  # type: List[str]  # for type checker

        if via_index:
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Indexed method (preferable)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            selectors = []  # type: List[FunctionElement]
            groupers = []  # type: List[str]
            sorters = []  # type: List[Union[str, UnaryExpression]]
            if by_year:
                selectors.append(
                    extract_year(TaskIndexEntry.when_created_utc).label(
                        label_year
                    )
                )
                groupers.append(label_year)
                sorters.append(desc(label_year))
            if by_month:
                selectors.append(
                    extract_month(TaskIndexEntry.when_created_utc).label(
                        label_month
                    )
                )
                groupers.append(label_month)
                sorters.append(desc(label_month))
            if by_task:
                selectors.append(
                    TaskIndexEntry.task_table_name.label(label_task)
                )
                groupers.append(label_task)
                sorters.append(label_task)
            if by_user:
                selectors.append(User.username.label(label_user))
                groupers.append(label_user)
                sorters.append(label_user)
            # Regardless:
            selectors.append(func.count().label(label_n))

            # noinspection PyUnresolvedReferences
            query = (
                select(selectors)
                .select_from(TaskIndexEntry.__table__)
                .group_by(*groupers)
                .order_by(*sorters)
                # ... https://docs.sqlalchemy.org/en/latest/core/tutorial.html#ordering-or-grouping-by-a-label  # noqa
            )
            if by_user:
                # noinspection PyUnresolvedReferences
                query = query.select_from(User.__table__).where(
                    TaskIndexEntry.adding_user_id == User.id
                )
            if not superuser:
                # Restrict to accessible groups
                # noinspection PyProtectedMember
                query = query.where(TaskIndexEntry.group_id.in_(group_ids))
            rows, colnames = get_rows_fieldnames_from_query(dbsession, query)
            # noinspection PyTypeChecker
            final_rows = rows
        else:
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Without using the server method (worse)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            groupers = []  # type: List[str]
            sorters = []  # type: List[Tuple[str, bool]]
            # ... (key, reversed/descending)

            if by_year:
                groupers.append(label_year)
                sorters.append((label_year, True))
            if by_month:
                groupers.append(label_month)
                sorters.append((label_month, True))
            if by_task:
                groupers.append(label_task)
                # ... redundant in the SQL, which involves multiple queries
                # (one per task type), but useful for the Python
                # aggregation.
                sorters.append((label_task, False))
            if by_user:
                groupers.append(label_user)
                sorters.append((label_user, False))

            classes = Task.all_subclasses_by_tablename()
            counter = Counter()
            for cls in classes:
                selectors = []  # type: List[FunctionElement]

                if by_year:
                    selectors.append(
                        # func.year() is specific to some DBs, e.g. MySQL
                        # so is func.extract();
                        # http://modern-sql.com/feature/extract
                        extract_year(
                            isotzdatetime_to_utcdatetime(cls.when_created)
                        ).label(label_year)
                    )
                if by_month:
                    selectors.append(
                        extract_month(
                            isotzdatetime_to_utcdatetime(cls.when_created)
                        ).label(label_month)
                    )
                if by_task:
                    selectors.append(
                        literal(cls.__tablename__).label(label_task)
                    )
                if by_user:
                    selectors.append(User.username.label(label_user))
                # Regardless:
                selectors.append(func.count().label(label_n))

                # noinspection PyUnresolvedReferences
                query = (
                    select(selectors)
                    .select_from(cls.__table__)
                    .where(cls._current == True)  # noqa: E712
                    .group_by(*groupers)
                )
                if by_user:
                    # noinspection PyUnresolvedReferences
                    query = query.select_from(User.__table__).where(
                        cls._adding_user_id == User.id
                    )
                if not superuser:
                    # Restrict to accessible groups
                    # noinspection PyProtectedMember
                    query = query.where(cls._group_id.in_(group_ids))
                rows, colnames = get_rows_fieldnames_from_query(
                    dbsession, query
                )
                if by_task:
                    final_rows.extend(rows)
                else:
                    for row in rows:  # type: RowProxy
                        key = tuple(row[keyname] for keyname in groupers)
                        count = row[label_n]
                        counter.update({key: count})
            if not by_task:
                PseudoRow = namedtuple("PseudoRow", groupers + [label_n])
                for key, total in counter.items():
                    values = list(key) + [total]
                    final_rows.append(PseudoRow(*values))
            # Complex sorting:
            # https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts  # noqa
            for key, descending in reversed(sorters):
                final_rows.sort(key=attrgetter(key), reverse=descending)

        return PlainReportType(rows=final_rows, column_names=colnames)
