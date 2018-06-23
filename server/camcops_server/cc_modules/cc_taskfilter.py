#!/usr/bin/env python
# camcops_server/cc_modules/cc_taskfilter.py

"""
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
"""

from enum import Enum
import logging
from typing import Dict, List, Optional, Type, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import auto_repr
from cardinal_pythonlib.sqlalchemy.list_types import (
    IntListType,
    StringListType,
)
from pendulum import Date
from sqlalchemy.orm import reconstructor
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Date, Integer
from sqlalchemy.orm import Query

from .cc_cache import cache_region_static, fkg
from .cc_device import Device
from .cc_group import Group
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_request import CamcopsRequest
from .cc_simpleobjects import IdNumReference
from .cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    IdNumReferenceListColType,
    PatientNameColType,
    SexColType,
)
from .cc_sqlalchemy import Base
from .cc_task import Task
from .cc_user import User

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Sorting helpers
# =============================================================================

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
# Define a filter to apply to tasks
# =============================================================================

class TaskFilter(Base):
    __tablename__ = "_task_filters"

    # Lots of these could be changed into lists; for example, filtering to
    # multiple devices, multiple users, multiple text patterns. For
    # AND-joining, there is little clear benefit (one could always AND-join
    # multiple filters with SQL). For OR-joining, this is more useful.
    # - surname: use ID numbers instead; not very likely to have >1 surname
    # - forename: ditto
    # - DOB: ditto
    # - sex: just eliminate the filter if you don't care about sex
    # - task_types: needs a list
    # - device_id: might as well make it a list
    # - user_id: might as well make it a list
    # - group_id: might as well make it a list
    # - start_datetime: single only
    # - end_datetime: single only
    # - text_contents: might as well make it a list
    # - ID numbers: a list, joined with OR.
    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="Task filter ID (arbitrary integer)"
    )
    # Task type filters
    task_types = Column(
        "task_types", StringListType,
        comment="Task filter: task type(s), as CSV list of table names"
    )
    tasks_offering_trackers_only = Column(
        "tasks_offering_trackers_only", Boolean,
        comment="Task filter: restrict to tasks offering trackers only?"
    )
    tasks_with_patient_only = Column(
        "tasks_with_patient_only", Boolean,
        comment="Task filter: restrict to tasks with a patient (non-anonymous "
                "tasks) only?"
    )
    # Patient-related filters
    surname = Column(
        "surname", PatientNameColType,
        comment="Task filter: surname"
    )
    forename = Column(
        "forename", PatientNameColType,
        comment="Task filter: forename"
    )
    dob = Column(
        "dob", Date,
        comment="Task filter: DOB"
    )
    sex = Column(
        "sex", SexColType,
        comment="Task filter: sex"
    )
    idnum_criteria = Column(  # new in v2.0.1
        "idnum_criteria", IdNumReferenceListColType,
        comment="ID filters as JSON; the ID number definitions are joined "
                "with OR"
    )
    # Other filters
    device_ids = Column(
        "device_ids", IntListType,
        comment="Task filter: source device ID(s), as CSV"
    )
    adding_user_ids = Column(
        "user_ids", IntListType,
        comment="Task filter: adding (uploading) user ID(s), as CSV"
    )
    group_ids = Column(
        "group_ids", IntListType,
        comment="Task filter: group ID(s), as CSV"
    )
    start_datetime = Column(
        "start_datetime_iso8601", PendulumDateTimeAsIsoTextColType,
        comment="Task filter: start date/time (UTC as ISO8601)"
    )
    end_datetime = Column(
        "end_datetime_iso8601", PendulumDateTimeAsIsoTextColType,
        comment="Task filter: end date/time (UTC as ISO8601)"
    )
    text_contents = Column(
        "text_contents", StringListType,
        comment="Task filter: filter text fields"
    )
    # Implemented on the Python side
    complete_only = Column(
        "complete_only", Boolean,
        comment="Task filter: task complete?"
    )

    def __init__(self) -> None:
        # We need to initialize these explicitly, because if we create an
        # instance via "x = TaskFilter()", they will be initialized to None,
        # without any recourse to our database to-and-fro conversion code for
        # each fieldtype.
        # (If we load from a database, things will be fine.)
        self.idnum_criteria = []  # type: List[IdNumReference]
        self.device_ids = []  # type: List[int]
        self.adding_user_ids = []  # type: List[int]
        self.group_ids = []  # type: List[int]
        self.text_contents = []  # type: List[str]

        # ANYTHING YOU ADD BELOW HERE MUST ALSO BE IN init_on_load().
        # Or call it, of course, but we like to keep on the happy side of the
        # PyCharm type checker.

        # Python-only (non-database) filtering attributes:
        self.era = None  # type: str
        self.patient_ids = []  # type: List[int]

        # Other Python-only attributes
        self.sort_method = TaskClassSortMethod.NONE
        self._task_classes = None  # type: List[Type[Task]]

    @reconstructor
    def init_on_load(self):
        self.era = None  # type: str
        self.patient_ids = []  # type: List[int]

        self.sort_method = TaskClassSortMethod.NONE
        self._task_classes = None  # type: List[Type[Task]]

    def __repr__(self) -> str:
        return auto_repr(self, with_addr=True)

    def set_sort_method(self, sort_method: TaskClassSortMethod) -> None:
        self.sort_method = sort_method

    @property
    def task_classes(self) -> List[Type[Task]]:
        # Cached, since the filter will be called repeatedly
        if self._task_classes is None:
            self._task_classes = []  # type: List[Type[Task]]
            if self.task_types:
                starting_classes = task_classes_from_table_names(
                    self.task_types)
            else:
                starting_classes = Task.all_subclasses_by_shortname()
            for cls in starting_classes:
                if (self.tasks_offering_trackers_only and
                        not cls.provides_trackers):
                    continue
                if self.tasks_with_patient_only and not cls.has_patient:
                    continue
                self._task_classes.append(cls)
            sort_task_classes_in_place(self._task_classes, self.sort_method)
        return self._task_classes

    @property
    def task_tablename_list(self) -> List[str]:
        return [cls.__tablename__ for cls in self.task_classes]

    def any_patient_filtering(self) -> bool:
        """Is there some sort of patient filtering being applied?"""
        return (
            bool(self.surname) or
            bool(self.forename) or
            (self.dob is not None) or
            bool(self.sex) or
            bool(self.idnum_criteria) or
            bool(self.patient_ids)
        )

    def any_specific_patient_filtering(self) -> bool:
        """Are there filters that would restrict to one or a few patients?"""
        # differs from any_patient_filtering w.r.t. sex
        return (
            bool(self.surname) or
            bool(self.forename) or
            self.dob is not None or
            bool(self.idnum_criteria) or
            bool(self.patient_ids)
        )

    def get_only_iddef(self) -> Optional[IdNumReference]:
        if len(self.idnum_criteria) != 1:
            return None
        return self.idnum_criteria[0]

    def get_group_names(self, req: CamcopsRequest) -> List[str]:
        names = []  # type: List[str]
        dbsession = req.dbsession
        for group_id in self.group_ids:
            group = dbsession.query(Group).filter(Group.id == group_id).first()
            names.append(group.name if group and group.name else "")
        return names

    def get_user_names(self, req: CamcopsRequest) -> List[str]:
        names = []  # type: List[str]
        dbsession = req.dbsession
        for user_id in self.adding_user_ids:
            user = dbsession.query(User).filter(User.id == user_id).first()
            names.append(user.username if user and user.username else "")
        return names

    def get_device_names(self, req: CamcopsRequest) -> List[str]:
        names = []  # type: List[str]
        dbsession = req.dbsession
        for dev_id in self.device_ids:
            dev = dbsession.query(Device).filter(Device.id == dev_id).first()
            names.append(dev.name if dev and dev.name else "")
        return names

    def task_query_restricted_by_filter(self,
                                        req: CamcopsRequest,
                                        q: Query,
                                        cls: Type[Task]) -> Optional[Query]:
        user = req.user
        if self.group_ids:
            permitted_group_ids = self.group_ids.copy()
        else:
            permitted_group_ids = None  # unrestricted

        if (self.start_datetime and self.end_datetime and
                self.end_datetime < self.start_datetime):
            # Inconsistent
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
            if not self.any_specific_patient_filtering():
                if user.may_view_all_patients_when_unfiltered:
                    pass
                elif user.may_view_no_patients_when_unfiltered:
                    # (a) User not permitted to view any patients when
                    # unfiltered. (b) Not filtered to a level that would
                    # reasonably restrict to one or a small number of
                    # patients. Skip the task class.
                    return None
                else:
                    liberal_group_ids = user.group_ids_that_nonsuperuser_may_see_when_unfiltered()  # noqa
                    if not permitted_group_ids:  # was unrestricted
                        permitted_group_ids = liberal_group_ids
                    else:  # was restricted; restrict further
                        permitted_group_ids = [
                            gid for gid in permitted_group_ids
                            if gid in liberal_group_ids
                        ]
                        if not permitted_group_ids:
                            return None  # down to zero; no point continuing

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
                                PatientIdNum.idnum_value == iddef.idnum_value
                            )
                        )
                    # Use OR (disjunction) of the specified values:
                    q = q.filter(or_(*id_filter_parts))

                if self.patient_ids:
                    q = q.filter(cls.patient_id.in_(self.patient_ids))

        # Patient-independent filtering

        if self.device_ids:
            # noinspection PyProtectedMember
            q = q.filter(cls._device_id.in_(self.device_ids))

        if self.era:
            # noinspection PyProtectedMember
            q = q.filter(cls._era == self.era)

        if self.adding_user_ids:
            # noinspection PyProtectedMember
            q = q.filter(cls._adding_user_id.in_(self.adding_user_ids))

        if permitted_group_ids:
            # noinspection PyProtectedMember
            q = q.filter(cls._group_id.in_(permitted_group_ids))

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

    def clear(self) -> None:
        self.task_types = []  # type: List[str]

        self.surname = None
        self.forename = None
        self.dob = None
        self.sex = None
        self.idnum_criteria = []  # type: List[IdNumReference]

        self.device_ids = []  # type: List[int]
        self.adding_user_ids = []  # type: List[int]
        self.group_ids = []  # type: List[int]
        self.start_datetime = None
        self.end_datetime = None
        self.text_contents = []  # type: List[str]

        self.complete_only = None
