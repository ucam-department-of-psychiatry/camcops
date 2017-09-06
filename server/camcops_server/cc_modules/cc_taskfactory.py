#!/usr/bin/env python
# camcops_server/cc_modules/cc_taskfactory.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
"""

from collections import OrderedDict
from enum import Enum
import logging
from typing import Dict, List, Optional, Type, Union

from arrow import Arrow
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sort import MINTYPE_SINGLETON, MinType
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.orm import Query

from .cc_cache import cache_region_static, fkg
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_task import Task

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Helpers
# =============================================================================
# Function, staticmethod, classmethod?
# https://stackoverflow.com/questions/8108688/in-python-when-should-i-use-a-function-instead-of-a-method  # noqa
# https://stackoverflow.com/questions/11788195/module-function-vs-staticmethod-vs-classmethod-vs-no-decorators-which-idiom-is  # noqa
# https://stackoverflow.com/questions/15017734/using-static-methods-in-python-best-practice  # noqa

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def tablename_to_task_class() -> Dict[str, Type[Task]]:
    d = {}  # type: Dict[str, Type[Task]]
    for cls in Task.gen_all_subclasses():
        d[cls.tablename] = cls
    return d


def task_when_created_sorter(task: Task) -> Union[Arrow, MinType]:
    # For sorting of tasks
    when_created = task.when_created
    return MINTYPE_SINGLETON if when_created is None else when_created


class TaskSortMethod(Enum):
    NONE = 0
    CREATION_DATE_ASC = 1
    CREATION_DATE_DESC = 2


def task_matches_python_parts_of_session_filter(
        task: Task, ccsession: CamcopsSession) -> bool:
    """
    Is the task allowed through the filter?
    We presume that permissions have already been dealt with, and that the
    database part of the query handled the SQL-side filters.
    Just the slow things here:
    """

    # Medium speed:
    if (ccsession.filter_complete is not None and
            ccsession.filter_complete != task.is_complete()):
        return False

    # Slow:
    if ccsession.filter_text is not None:
        if not task.compatible_with_text_filter(ccsession.filter_text):
            return False

    return True


def task_query_restricted_to_permitted_users(req: CamcopsRequest,
                                             query: Query,
                                             task_class: Type[Task]) -> Query:
    user = req.user

    if user.superuser:
        return query  # anything goes

    # *** IMPLEMENT GROUP SECURITY HERE

    return query


# =============================================================================
# Make a single task given its base table name and server PK
# =============================================================================

def task_factory(req: CamcopsRequest, basetable: str,
                 serverpk: int) -> Optional[Task]:
    """
    Make a task; return None if the PK doesn't exist;
    raise KeyError if the table doesn't exist.
    """
    d = tablename_to_task_class()
    cls = d[basetable]  # may raise KeyError
    dbsession = req.dbsession
    # noinspection PyProtectedMember
    q = dbsession.query(cls).filter(cls._pk == serverpk)
    q = task_query_restricted_to_permitted_users(req, q, cls)
    return q.first()


# =============================================================================
# Make a set of tasks, deferring work until things are needed
# =============================================================================
class TaskCollection(object):
    """
    Represent a potential or instantiated call to fetch tasks from the
    database.
    The caller may want them in a giant list (e.g. task viewer, CTVs), or split
    by task class (e.g. trackers).
    """
    def __init__(self,
                 req: CamcopsRequest,
                 task_classes: List[Type[Task]] = None,
                 restrict_by_session_filter: bool = False,
                 sort_method: TaskSortMethod = TaskSortMethod.NONE) -> None:
        self._req = req
        self._task_classes = task_classes
        self._restrict_by_session_filter = restrict_by_session_filter
        self._sort_method = sort_method
        self._tasks_by_class = None  # type: OrderedDict[Type[Task], List[Task]]  # noqa

    # =========================================================================
    # Interface to set options
    # =========================================================================

    def set_restrict_by_session_filter(self, restrict: bool = True) -> None:
        self._restrict_by_session_filter = restrict

    def set_task_classes(self, task_classes: List[Type[Task]]) -> None:
        self._task_classes = task_classes

    def set_single_class(self, task_class: Type[Task]) -> None:
        self._task_classes = [task_class]

    def set_all_task_classes(self) -> None:
        self._task_classes = None

    # =========================================================================
    # Interface to read
    # =========================================================================

    @property
    def task_classes(self) -> List[Type[Task]]:
        if self._task_classes is None:
            self._task_classes = Task.all_subclasses_by_shortname()
        # noinspection PyTypeChecker
        return self._task_classes

    def tasks_for_task_class(self, cls: Type[Task]):
        self._fetch_all_tasks()
        tasklist = self._tasks_by_class.get(cls, [])
        self._sort_in_place(tasklist)
        return tasklist

    @property
    def all_tasks(self) -> List[Task]:
        self._fetch_all_tasks()
        all_tasks_list = []  # type: List[Task]
        for single_task_list in self._tasks_by_class.values():
            all_tasks_list += single_task_list
        self._sort_in_place(all_tasks_list)
        return all_tasks_list

    # =========================================================================
    # Internals
    # =========================================================================

    def _query(self, cls) -> Optional[Query]:
        dbsession = self._req.dbsession
        q = dbsession.query(cls)

        # Restrict to what the web front end will supply
        # noinspection PyProtectedMember
        q = q.filter(cls._current == True)  # nopep8

        # Restrict to what is PERMITTED
        q = task_query_restricted_to_permitted_users(self._req, q, cls)

        # Restrict to what is DESIRED
        if self._restrict_by_session_filter:
            ccsession = self._req.camcops_session

            if cls.is_anonymous:
                if ccsession.any_patient_filtering():
                    # If we're restricting by patient in any way, we don't
                    # want this task class at all.
                    return None
            else:
                # Not anonymous.
                if (not ccsession.user_may_view_all_patients_when_unfiltered()
                        and not ccsession.any_specific_patient_filtering()):
                    # (a) User not permitted to view all patients when
                    # unfiltered. (b) Not filtered to a level that would
                    # reasonably restrict to one or a small number of
                    # patients. Skip the task class.
                    return None

                # Patient filtering
                if ccsession.any_patient_filtering():
                    q = q.join(Patient)

                    if ccsession.filter_surname is not None:
                        q = q.filter(func.upper(Patient.surname) ==
                                     ccsession.filter_surname.upper())
                    if ccsession.filter_forename is not None:
                        q = q.filter(func.upper(Patient.forename) ==
                                     ccsession.filter_forename.upper())
                    if ccsession.filter_dob_iso8601 is not None:
                        q = q.filter(Patient.dob ==
                                     ccsession.filter_dob_iso8601)
                    if ccsession.filter_sex is not None:
                        q = q.filter(func.upper(Patient.sex) ==
                                     ccsession.filter_sex.upper())

                    idnum_filters = ccsession.get_idnum_filters()
                    if idnum_filters:
                        q = q.join(PatientIdNum)
                        id_filter_parts = []
                        for which_idnum, idnum_value in idnum_filters:
                            id_filter_parts.append(
                                and_(
                                    PatientIdNum.which_idnum == which_idnum,  # noqa
                                    PatientIdNum.idnum_value == idnum_value
                                )
                            )
                        # Use OR (disjunction) of the specified values:
                        q = q.filter(or_(*id_filter_parts))

            # Patient-independent filtering

            # *** CHANGE THIS BIT; USE GROUP SECURITY INSTEAD: ***
            restricted_to_viewing_user_id = ccsession.restricted_to_viewing_user_id()  # noqa
            if restricted_to_viewing_user_id is not None:
                # noinspection PyProtectedMember
                q = q.filter(cls._adding_user_id ==
                             restricted_to_viewing_user_id)  # nopep8

            if ccsession.filter_device_id is not None:
                # noinspection PyProtectedMember
                q = q.filter(cls._device_id == ccsession.filter_device_id)

            start_datetime = ccsession.get_filter_start_datetime()
            end_datetime = ccsession.get_filter_end_datetime_corrected_1day()
            if start_datetime is not None:
                q = q.filter(cls.when_created >= start_datetime)
            if end_datetime is not None:
                q = q.filter(cls.when_created <= end_datetime)

        return q

    def _fetch_all_tasks(self) -> None:
        if self._tasks_by_class is not None:
            # Already fetched
            return

        self._tasks_by_class = OrderedDict()  # type: OrderedDict[Type[Task], List[Task]]  # noqa
        ccsession = self._req.camcops_session

        # Fetch from database
        for cls in self.task_classes:
            q = self._query(cls)
            if q is None:
                newtasks = []  # type: List[Task]
            else:
                newtasks = q.all()

                # Apply Python-side filters?
                if self._restrict_by_session_filter:
                    newtasks = [
                        t for t in newtasks
                        if task_matches_python_parts_of_session_filter(
                            t, ccsession)
                    ]

            self._tasks_by_class[cls] = newtasks

    def _sort_in_place(self, tasklist: List[Task]) -> None:
        # Sort?
        if self._sort_method == TaskSortMethod.CREATION_DATE_ASC:
            tasklist.sort(key=task_when_created_sorter)
        elif self._sort_method == TaskSortMethod.CREATION_DATE_DESC:
            tasklist.sort(key=task_when_created_sorter, reverse=True)
