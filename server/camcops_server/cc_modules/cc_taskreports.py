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
from typing import Any, Tuple, Type, TYPE_CHECKING

from cardinal_pythonlib.classes import classproperty
from cardinal_pythonlib.sqlalchemy.core_query import (
    get_rows_fieldnames_from_select,
)
from cardinal_pythonlib.sqlalchemy.sqlfunc import (
    extract_month,
    extract_year,
    extract_day_of_month,
)
from sqlalchemy import cast, ColumnExpressionArgument, Integer
from sqlalchemy.engine import Row
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import asc, desc, func, literal, select

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
    ByDayOfMonthSelector,
    ByMonthSelector,
    ByTaskSelector,
    ByUserSelector,
    ByYearSelector,
    DEFAULT_BY_DAY_OF_MONTH,
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
    # must match ViewParam.BY_DAY_of_MONTH
    by_day_of_month = ByDayOfMonthSelector()
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

    label_year = "year"
    label_month = "month"
    label_day_of_month = "day_of_month"
    label_task = "task"
    label_user = "adding_user_name"
    label_n = "num_tasks_added"

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
    def get_specific_http_query_keys(cls) -> list[str]:
        return [
            ViewParam.BY_YEAR,
            ViewParam.BY_MONTH,
            ViewParam.BY_DAY_OF_MONTH,
            ViewParam.BY_TASK,
            ViewParam.BY_USER,
            ViewParam.VIA_INDEX,
        ]

    def get_rows_colnames(self, req: "CamcopsRequest") -> PlainReportType:
        self.dbsession = req.dbsession
        self.group_ids = req.user.ids_of_groups_user_may_report_on
        self.superuser = req.user.superuser

        self.by_year = req.get_bool_param(ViewParam.BY_YEAR, DEFAULT_BY_YEAR)
        self.by_month = req.get_bool_param(
            ViewParam.BY_MONTH, DEFAULT_BY_MONTH
        )
        self.by_day_of_month = req.get_bool_param(
            ViewParam.BY_DAY_OF_MONTH, DEFAULT_BY_DAY_OF_MONTH
        )
        self.by_task = req.get_bool_param(ViewParam.BY_TASK, DEFAULT_BY_TASK)
        self.by_user = req.get_bool_param(ViewParam.BY_USER, DEFAULT_BY_USER)
        via_index = req.get_bool_param(ViewParam.VIA_INDEX, True)

        if via_index:
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Indexed method (preferable)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            rows, colnames = self._get_rows_colnames_via_index()
        else:
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # Without using the server method (worse)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            rows, colnames = self._get_rows_colnames_without_index()

        return PlainReportType(rows=rows, column_names=colnames)

    def _get_rows_colnames_via_index(self) -> Tuple[list[Row], list[str]]:
        selectors: list[ColumnElement[Any]] = []
        groupers = []
        sorters: list[ColumnExpressionArgument[Any]] = []
        if self.by_year:
            selectors.append(
                cast(  # Necessary for SQLite tests
                    extract_year(TaskIndexEntry.when_created_utc),
                    Integer(),
                ).label(self.label_year)
            )
            groupers.append(self.label_year)
            sorters.append(desc(self.label_year))
        if self.by_month:
            selectors.append(
                cast(  # Necessary for SQLite tests
                    extract_month(TaskIndexEntry.when_created_utc),
                    Integer(),
                ).label(self.label_month)
            )
            groupers.append(self.label_month)
            sorters.append(desc(self.label_month))
        if self.by_day_of_month:
            selectors.append(
                cast(  # Necessary for SQLite tests
                    extract_day_of_month(TaskIndexEntry.when_created_utc),
                    Integer(),
                ).label(self.label_day_of_month)
            )
            groupers.append(self.label_day_of_month)
            sorters.append(desc(self.label_day_of_month))
        if self.by_task:
            selectors.append(
                TaskIndexEntry.task_table_name.label(self.label_task)
            )
            groupers.append(self.label_task)
            sorters.append(asc(self.label_task))
        if self.by_user:
            selectors.append(User.username.label(self.label_user))
            groupers.append(self.label_user)
            sorters.append(asc(self.label_user))
        # Regardless:
        selectors.append(func.count().label(self.label_n))

        # noinspection PyUnresolvedReferences
        statement = (
            select(*selectors)
            .select_from(TaskIndexEntry.__table__)
            .group_by(*groupers)
            .order_by(*sorters)
            # ... https://docs.sqlalchemy.org/en/latest/core/tutorial.html#ordering-or-grouping-by-a-label  # noqa
        )
        if self.by_user:
            # noinspection PyUnresolvedReferences
            statement = statement.select_from(User.__table__).where(
                TaskIndexEntry.adding_user_id == User.id
            )
        if not self.superuser:
            # Restrict to accessible groups
            # noinspection PyProtectedMember
            statement = statement.where(
                TaskIndexEntry.group_id.in_(self.group_ids)
            )
        rows, colnames = get_rows_fieldnames_from_select(
            self.dbsession, statement
        )
        return rows, colnames

    def _get_rows_colnames_without_index(self) -> Tuple[list[Row], list[str]]:
        final_rows = []
        colnames = []  # type: ignore[var-annotated]

        groupers: list[str] = []
        sorters: list[Tuple[str, bool]] = []
        # ... (key, reversed/descending)

        if self.by_year:
            groupers.append(self.label_year)
            sorters.append((self.label_year, True))
        if self.by_month:
            groupers.append(self.label_month)
            sorters.append((self.label_month, True))
        if self.by_day_of_month:
            groupers.append(self.label_day_of_month)
            sorters.append((self.label_day_of_month, True))
        if self.by_task:
            groupers.append(self.label_task)
            # ... redundant in the SQL, which involves multiple queries
            # (one per task type), but useful for the Python
            # aggregation.
            sorters.append((self.label_task, False))
        if self.by_user:
            groupers.append(self.label_user)
            sorters.append((self.label_user, False))

        classes = Task.all_subclasses_by_tablename()
        counter: Counter = Counter()
        for cls in classes:
            selectors: list[ColumnElement[Any]] = []

            if self.by_year:
                selectors.append(
                    # func.year() is specific to some DBs, e.g. MySQL
                    # so is func.extract();
                    # http://modern-sql.com/feature/extract
                    cast(  # Necessary for SQLite tests
                        extract_year(
                            isotzdatetime_to_utcdatetime(cls.when_created)
                        ),
                        Integer(),
                    ).label(self.label_year)
                )
            if self.by_month:
                selectors.append(
                    cast(  # Necessary for SQLite tests
                        extract_month(
                            isotzdatetime_to_utcdatetime(cls.when_created)
                        ),
                        Integer(),
                    ).label(self.label_month)
                )
            if self.by_day_of_month:
                selectors.append(
                    cast(  # Necessary for SQLite tests
                        extract_day_of_month(
                            isotzdatetime_to_utcdatetime(cls.when_created)
                        ),
                        Integer(),
                    ).label(self.label_day_of_month)
                )
            if self.by_task:
                selectors.append(
                    literal(cls.__tablename__).label(self.label_task)
                )
            if self.by_user:
                selectors.append(User.username.label(self.label_user))
            # Regardless:
            selectors.append(func.count().label(self.label_n))

            # noinspection PyUnresolvedReferences
            statement = (
                select(*selectors)
                .select_from(cls.__table__)
                .where(cls._current == True)  # noqa: E712
                .group_by(*groupers)
            )
            if self.by_user:
                # noinspection PyUnresolvedReferences
                statement = statement.select_from(User.__table__).where(
                    cls._adding_user_id == User.id
                )
            if not self.superuser:
                # Restrict to accessible groups
                # noinspection PyProtectedMember
                statement = statement.where(cls._group_id.in_(self.group_ids))
            rows, colnames = get_rows_fieldnames_from_select(
                self.dbsession, statement
            )
            if self.by_task:
                final_rows.extend(rows)
            else:
                for row in rows:  # type: Row
                    key = tuple(getattr(row, keyname) for keyname in groupers)
                    count = getattr(row, self.label_n)
                    counter.update({key: count})
        if not self.by_task:
            PseudoRow = namedtuple("PseudoRow", groupers + [self.label_n])  # type: ignore[misc]  # noqa: E501
            for key, total in counter.items():
                values = list(key) + [total]
                final_rows.append(PseudoRow(*values))  # type: ignore[arg-type]

        self._sort_final_rows(final_rows, sorters)
        return final_rows, colnames

    @staticmethod
    def _sort_final_rows(
        final_rows: list[Row],
        sorters: list[Tuple[str, bool]],
    ) -> None:
        # Complex sorting:
        # https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts  # noqa
        for key, descending in reversed(sorters):
            final_rows.sort(key=attrgetter(key), reverse=descending)
