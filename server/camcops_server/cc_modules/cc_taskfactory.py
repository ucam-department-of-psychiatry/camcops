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
from typing import Callable, Dict, List, Optional, Type, TYPE_CHECKING, Union

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import auto_repr
from cardinal_pythonlib.sort import MINTYPE_SINGLETON, MinType
from pendulum import Date, Pendulum
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.orm import Query

from .cc_all_models import all_models_no_op
from .cc_cache import cache_region_static, fkg
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_simpleobjects import IdNumDefinition
from .cc_task import Task

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

log = BraceStyleAdapter(logging.getLogger(__name__))
all_models_no_op()


# =============================================================================
# Sorting helpers
# =============================================================================

def task_when_created_sorter(task: Task) -> Union[Pendulum, MinType]:
    # For sorting of tasks
    when_created = task.when_created
    return MINTYPE_SINGLETON if when_created is None else when_created


class TaskSortMethod(Enum):
    NONE = 0
    CREATION_DATE_ASC = 1
    CREATION_DATE_DESC = 2


def sort_tasks_in_place(tasklist: List[Task],
                        sortmethod: TaskSortMethod) -> None:
    # Sort?
    if sortmethod == TaskSortMethod.CREATION_DATE_ASC:
        tasklist.sort(key=task_when_created_sorter)
    elif sortmethod == TaskSortMethod.CREATION_DATE_DESC:
        tasklist.sort(key=task_when_created_sorter, reverse=True)


class TaskClassSortMethod(Enum):
    NONE = 0
    TABLENAME = 1
    SHORTNAME = 2
    LONGNAME = 3


def sort_task_classes_in_place(classlist: List[Type[Task]],
                               sortmethod: TaskClassSortMethod) -> None:
    if sortmethod == TaskClassSortMethod.TABLENAME:
        classlist.sort(key=lambda c: c.tablename)
    elif sortmethod == TaskClassSortMethod.SHORTNAME:
        classlist.sort(key=lambda c: c.shortname)
    elif sortmethod == TaskClassSortMethod.LONGNAME:
        classlist.sort(key=lambda c: c.longname)


# =============================================================================
# Cache task class mapping
# =============================================================================
# Function, staticmethod, classmethod?
# https://stackoverflow.com/questions/8108688/in-python-when-should-i-use-a-function-instead-of-a-method  # noqa
# https://stackoverflow.com/questions/11788195/module-function-vs-staticmethod-vs-classmethod-vs-no-decorators-which-idiom-is  # noqa
# https://stackoverflow.com/questions/15017734/using-static-methods-in-python-best-practice  # noqa

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def tablename_to_task_class_dict() -> Dict[str, Type[Task]]:
    d = {}  # type: Dict[str, Type[Task]]
    for cls in Task.gen_all_subclasses():
        d[cls.tablename] = cls
    return d


def task_classes_from_table_names(
        tablenames: List[str],
        sortmethod: TaskClassSortMethod = TaskClassSortMethod.NONE) \
        -> List[Type[Task]]:
    """
    May raise KeyError.
    """
    d = tablename_to_task_class_dict()
    classes = []  # type: List[Type[Task]]
    for tablename in tablenames:
        cls = d[tablename]
        classes.append(cls)
    sort_task_classes_in_place(classes, sortmethod)
    return classes


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def all_tracker_task_classes() -> List[Type[Task]]:
    return [cls for cls in Task.all_subclasses_by_shortname()
            if cls.provides_trackers]


# =============================================================================
# Task query helpers
# =============================================================================

def task_query_restricted_to_permitted_users(
        req: CamcopsRequest, q: Query, cls: Type[Task]) -> Optional[Query]:
    user = req.user

    if user.superuser:
        return q  # anything goes

    # *** IMPLEMENT GROUP SECURITY HERE

    return q


# =============================================================================
# Make a single task given its base table name and server PK
# =============================================================================

def task_factory(req: CamcopsRequest, basetable: str,
                 serverpk: int) -> Optional[Task]:
    """
    Make a task; return None if the PK doesn't exist;
    raise KeyError if the table doesn't exist.
    """
    d = tablename_to_task_class_dict()
    cls = d[basetable]  # may raise KeyError
    dbsession = req.dbsession
    # noinspection PyProtectedMember
    q = dbsession.query(cls).filter(cls._pk == serverpk)
    q = task_query_restricted_to_permitted_users(req, q, cls)
    return q.first()


# =============================================================================
# Define a filter to apply to tasks
# =============================================================================

class TaskFilter(object):
    def __init__(
            self,
            ccsession: CamcopsSession = None,
            task_classes: List[Type[Task]] = None,
            trackers_only: bool = False,
            has_patient: bool = False,
            sort_method: TaskClassSortMethod = TaskClassSortMethod.NONE,
            surname: str = None,
            forename: str = None,
            dob: Date = None,
            sex: str = None,
            idnum_criteria: List[IdNumDefinition] = None,
            complete_only: bool = False,
            device_id: int = None,
            user_id: int = None,
            start_datetime: Pendulum = None,
            end_datetime: Pendulum = None,
            text_contents: List[str] = None) -> None:
        # ---------------------------------------------------------------------
        # Start with criteria from caller
        # ---------------------------------------------------------------------
        self.trackers_only = trackers_only
        self.has_patient = has_patient

        if task_classes is None:
            # Caller didn't specify, so we go for some version of "all",
            # using cached functions for speed.
            if trackers_only:
                self.task_classes = all_tracker_task_classes()
            else:
                self.task_classes = Task.all_subclasses_by_shortname()
        else:
            # Caller specified classes. Ensure they match the other criteria.
            self.task_classes = task_classes  # type: List[Type[Task]]

        if trackers_only:
            self.task_classes = [
                cls for cls in self.task_classes if cls.provides_trackers
            ]
        if has_patient:
            self.task_classes = [
                cls for cls in self.task_classes if cls.has_patient
            ]

        self.surname = surname
        self.forename = forename
        self.dob = dob
        self.sex = sex
        self.idnum_criteria = idnum_criteria or []  # type: List[IdNumDefinition]  # noqa
        self.complete_only = complete_only
        self.device_id = device_id
        self.user_id = user_id
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.text_contents = text_contents or []  # type: List[str]

        # ---------------------------------------------------------------------
        # Merge in criteria from ccsession
        # ---------------------------------------------------------------------
        self.inconsistent_so_return_nothing = False

        def merge(self_attr: str, session_attr: str) -> None:
            session_val = getattr(ccsession, session_attr)
            self_val = getattr(self, self_attr)
            self_cares = bool(self_val)
            session_cares = bool(session_val)
            # ... with some caution: note that our only boolean flag,
            # complete_only, is False for "don't care", so that's OK.

            if session_cares:
                if self_cares and self_val != session_val:
                    # We already care, and the session wants something else.
                    self.inconsistent_so_return_nothing = True
                else:
                    # Either we don't care, or we and the session want the
                    # same thing. Either way, we can use the session's value.
                    setattr(self, self_attr, session_val)

        def datetime_min_max(
                self_value: Optional[Pendulum],
                session_value: Optional[Pendulum],
                minmaxfn: Callable[[Optional[Pendulum], Optional[Pendulum]],
                                   Optional[Pendulum]]) -> Optional[Pendulum]:
            if self_value is None:
                return session_value
            elif session_value is None:
                return self_value
            else:
                return minmaxfn(self_value, session_value)

        if ccsession:
            merge(self_attr='surname', session_attr='filter_surname')
            merge(self_attr='forename', session_attr='filter_forename')
            merge(self_attr='dob', session_attr='filter_dob')
            merge(self_attr='sex', session_attr='filter_sex')
            if ccsession.filter_idnums:
                self.idnum_criteria = [idd for idd in self.idnum_criteria
                                       if idd in ccsession.filter_idnums]
            if ccsession.filter_task:
                self.task_classes = [
                    cls for cls in self.task_classes
                    if cls.tablename == ccsession.filter_task
                ]
            merge(self_attr='complete_only', session_attr='filter_complete')
            merge(self_attr='device_id', session_attr='filter_device_id')
            merge(self_attr='user_id', session_attr='filter_user_id')
            self.start_datetime = datetime_min_max(
                self.start_datetime, ccsession.filter_start_datetime, max)
            self.end_datetime = datetime_min_max(
                self.end_datetime, ccsession.filter_end_datetime, min)
            merge(self_attr='start_datetime',
                  session_attr='filter_start_datetime')
            merge(self_attr='end_datetime', session_attr='filter_end_datetime')
            if ccsession.filter_text:
                if ccsession.filter_text not in self.text_contents:
                    self.text_contents.append(ccsession.filter_text)

        # ---------------------------------------------------------------------
        # Final consistency checks
        # ---------------------------------------------------------------------
        if (self.start_datetime and self.end_datetime and
                self.end_datetime < self.start_datetime):
            self.inconsistent_so_return_nothing = True

        # ---------------------------------------------------------------------
        # Finalize our class list
        # ---------------------------------------------------------------------
        sort_task_classes_in_place(self.task_classes, sort_method)

    def __repr__(self) -> str:
        return auto_repr(self, with_addr=True)

    @property
    def task_tablename_list(self) -> List[str]:
        return [cls.__tablename__ for cls in self.task_classes]

    def any_patient_filtering(self) -> bool:
        """Is there some sort of patient filtering being applied?"""
        return (
            bool(self.surname) or
            bool(self.forename) or
            self.dob is not None or
            bool(self.sex) or
            bool(self.idnum_criteria)
        )

    def any_specific_patient_filtering(self) -> bool:
        """Are there filters that would restrict to one or a few patients?"""
        # differs from any_patient_filtering w.r.t. sex
        return (
            bool(self.surname) or
            bool(self.forename) or
            self.dob is not None or
            bool(self.idnum_criteria)
        )

    def get_only_iddef(self) -> Optional[IdNumDefinition]:
        if len(self.idnum_criteria) != 1:
            return None
        return self.idnum_criteria[0]

    def task_query_restricted_by_filter(self,
                                        req: CamcopsRequest,
                                        q: Query,
                                        cls: Type[Task]) -> Optional[Query]:
        ccsession = req.camcops_session

        if self.inconsistent_so_return_nothing:
            return None

        if cls not in self.task_classes:
            # We don't want this task
            return None

        if cls.is_anonymous:
            if self.any_patient_filtering():
                # If we're restricting by patient in any way, we don't
                # want this task class at all.
                return None
        else:
            # Not anonymous.
            if (not ccsession.user_may_view_all_patients_when_unfiltered() and
                    not self.any_specific_patient_filtering()):
                # (a) User not permitted to view all patients when
                # unfiltered. (b) Not filtered to a level that would
                # reasonably restrict to one or a small number of
                # patients. Skip the task class.
                return None

            # Patient filtering
            if self.any_patient_filtering():
                # q = q.join(Patient) # fails
                q = q.join(cls.patient)  # use explicitly configured relationship  # noqa

                if self.surname:
                    q = q.filter(func.upper(Patient.surname) ==
                                 self.surname.upper())
                if self.forename:
                    q = q.filter(func.upper(Patient.forename) ==
                                 self.forename.upper())
                if self.dob is not None:
                    q = q.filter(Patient.dob == self.dob)
                if self.sex:
                    q = q.filter(func.upper(Patient.sex) == self.sex.upper())

                if self.idnum_criteria:
                    # q = q.join(PatientIdNum) # fails
                    q = q.join(Patient.idnums)
                    id_filter_parts = []  # type: List[ColumnElement]
                    for iddef in self.idnum_criteria:
                        id_filter_parts.append(
                            and_(
                                PatientIdNum.which_idnum == iddef.which_idnum,
                                # noqa
                                PatientIdNum.idnum_value == iddef.idnum_value
                            )
                        )
                    # Use AND (conjunction) of the specified values:
                    q = q.filter(and_(*id_filter_parts))
                    # ... or_ is an alternative
                    # ... we create the more elaborate logical hierarchy here
                    #     just in case we want to use or_ in the future!

        # Patient-independent filtering

        # *** CHANGE THIS BIT; USE GROUP SECURITY INSTEAD: ***
        restricted_to_viewing_user_id = ccsession.restricted_to_viewing_user_id()  # noqa
        if restricted_to_viewing_user_id is not None:
            # noinspection PyProtectedMember
            q = q.filter(cls._adding_user_id ==
                         restricted_to_viewing_user_id)  # nopep8

        if self.device_id is not None:
            # noinspection PyProtectedMember
            q = q.filter(cls._device_id == self.device_id)

        if self.start_datetime is not None:
            q = q.filter(cls.when_created >= self.start_datetime)
        if self.end_datetime is not None:
            q = q.filter(cls.when_created <= self.end_datetime)

        if self.text_contents:
            textcols = [col for _, col in cls.gen_text_filter_columns()]
            if not textcols:
                # Text filtering requested, but there are no text columns, so
                # by definition the filter must fail.
                return None
            clauses_over_text_phrases = []  # type: List[ColumnElement]
            for textfilter in self.text_contents:
                tf_lower = textfilter.lower()
                clauses_over_columns = []  # type: List[ColumnElement]
                for textcol in textcols:
                    # Case-insensitive comparison:
                    # https://groups.google.com/forum/#!topic/sqlalchemy/331XoToT4lk
                    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/StringComparisonFilter  # noqa
                    clauses_over_columns.append(
                        func.lower(textcol).contains(tf_lower, autoescape='/')
                    )
                clauses_over_text_phrases.append(
                    or_(*clauses_over_columns)
                )
            q = q.filter(and_(*clauses_over_text_phrases))

        return q

    def has_python_parts_to_filter(self) -> bool:
        return self.complete_only

    def task_matches_python_parts_of_filter(self, task: Task) -> bool:
        # "Is task complete" filter
        if self.complete_only:
            if not task.is_complete():
                return False

        return True


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
                 taskfilter: TaskFilter,
                 sort_method_by_class: TaskSortMethod = TaskSortMethod.NONE,
                 sort_method_global: TaskSortMethod = TaskSortMethod.NONE) \
            -> None:
        self._req = req
        self._filter = taskfilter
        self._sort_method_by_class = sort_method_by_class
        self._sort_method_global = sort_method_global
        self._tasks_by_class = None  # type: OrderedDict[Type[Task], List[Task]]  # noqa
        self._all_tasks = None  # type: List[Task]
        # log.critical("TaskCollection(): taskfilter={!r}", self._filter)

    # =========================================================================
    # Interface to read
    # =========================================================================

    def tasks_for_task_class(self, cls: Type[Task]):
        self._fetch_all_tasks()
        tasklist = self._tasks_by_class.get(cls, [])
        sort_tasks_in_place(tasklist, self._sort_method_by_class)
        return tasklist

    @property
    def all_tasks(self) -> List[Task]:
        self._fetch_all_tasks()
        if self._all_tasks is None:
            self._all_tasks = []  # type: List[Task]
            for single_task_list in self._tasks_by_class.values():
                self._all_tasks += single_task_list
            sort_tasks_in_place(self._all_tasks, self._sort_method_global)
        return self._all_tasks

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
        if q:
            q = self._filter.task_query_restricted_by_filter(self._req, q, cls)

        return q

    def _fetch_all_tasks(self) -> None:
        if self._tasks_by_class is not None:
            # Already fetched
            return

        self._tasks_by_class = OrderedDict()  # type: OrderedDict[Type[Task], List[Task]]  # noqa

        # Fetch from database
        for cls in self._filter.task_classes:
            q = self._query(cls)
            if q is None:
                newtasks = []  # type: List[Task]
            else:
                newtasks = q.all()  # type: List[Task]

                # Apply Python-side filters?
                if self._filter.has_python_parts_to_filter():
                    newtasks = [
                        t for t in newtasks
                        if self._filter.task_matches_python_parts_of_filter(t)
                    ]

            self._tasks_by_class[cls] = newtasks
