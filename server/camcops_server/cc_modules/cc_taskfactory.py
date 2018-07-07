#!/usr/bin/env python
# camcops_server/cc_modules/cc_taskfactory.py

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

from collections import OrderedDict
from enum import Enum
import logging
from threading import Thread
from typing import Dict, List, Optional, Type, Union

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sort import MINTYPE_SINGLETON, MinType
from pendulum import DateTime as Pendulum
import pyramid.httpexceptions as exc
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session as SqlASession

# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa
from .cc_request import CamcopsRequest
from .cc_task import Task
from .cc_taskfilter import tablename_to_task_class_dict, TaskFilter

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_QUERY_TIMING = False

if DEBUG_QUERY_TIMING:
    log.warning("Debugging options enabled!")


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


# =============================================================================
# Task query helpers
# =============================================================================

def task_query_restricted_to_permitted_users(
        req: CamcopsRequest, q: Query, cls: Type[Task],
        as_dump: bool) -> Optional[Query]:
    user = req.user

    if user.superuser:
        return q  # anything goes

    # Implement group security. Simple:
    if as_dump:
        group_ids = user.ids_of_groups_user_may_dump
    else:
        group_ids = user.ids_of_groups_user_may_see

    if not group_ids:
        return None

    # noinspection PyProtectedMember
    q = q.filter(cls._group_id.in_(group_ids))

    return q


# =============================================================================
# Make a single task given its base table name and server PK
# =============================================================================

def task_factory(req: CamcopsRequest, basetable: str,
                 serverpk: int) -> Optional[Task]:
    """
    Make a task; return None if the PK doesn't exist;
    raise HTTPBadRequest if the table doesn't exist.
    """
    d = tablename_to_task_class_dict()
    try:
        cls = d[basetable]  # may raise KeyError
    except KeyError:
        raise exc.HTTPBadRequest("No such task table: {!r}".format(basetable))
    dbsession = req.dbsession
    # noinspection PyProtectedMember
    q = dbsession.query(cls).filter(cls._pk == serverpk)
    q = task_query_restricted_to_permitted_users(req, q, cls, as_dump=False)
    return q.first()


# =============================================================================
# Parallel fetch helper
# =============================================================================
# - Why consider a parallel fetch?
#   Because a typical fetch might involve 27ms per query (as seen by Python;
#   less as seen by MySQL) but about 100 queries, for a not-very-large
#   database.
# - Initially UNSUCCESSFUL: even after tweaking pool_size=0 in create_engine()
#   to get round the SQLAlchemy error "QueuePool limit of size 5 overflow 10
#   reached", in the parallel code, a great many queries are launched, but then
#   something goes wrong and others are started but then block -- for ages --
#   waiting for a spare database connection, or something.
# - Fixed that: I was not explicitly closing the sessions.
# - But then a major conceptual problem: anything to be lazy-loaded (e.g.
#   patient, but also patient ID, special note, BLOB...) will give this sort of
#   error: "DetachedInstanceError: Parent instance <Phq9 at 0x7fe6cce2d278> is
#   not bound to a Session; lazy load operation of attribute 'patient' cannot
#   proceed" -- for obvious reasons. And some of those operations are only
#   required on the final paginated task set, which requires aggregation across
#   all tasks.
#
# HOWEVER, the query time per table drops from ~27ms to 4-8ms if we disable
# eager loading (lazy="joined") of patients from tasks.

class FetchThread(Thread):
    """
    CURRENTLY UNUSED.
    """
    def __init__(self,
                 req: CamcopsRequest,
                 task_class: Type[Task],
                 factory: "TaskCollection",
                 **kwargs) -> None:
        self.req = req
        self.task_class = task_class
        self.factory = factory
        self.error = False
        name = task_class.__tablename__
        super().__init__(name=name, target=None, **kwargs)

    def run(self) -> None:
        log.critical("Thread starting")
        dbsession = self.req.get_bare_dbsession()
        # noinspection PyBroadException
        try:
            # noinspection PyProtectedMember
            q = self.factory._make_query(dbsession, self.task_class)
            if q:
                tasks = q.all()  # type: List[Task]
                # https://stackoverflow.com/questions/6319207/are-lists-thread-safe  # noqa
                # https://stackoverflow.com/questions/6953351/thread-safety-in-pythons-dictionary  # noqa
                # http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm  # noqa
                # noinspection PyProtectedMember
                self.factory._tasks_by_class[self.task_class] = tasks
                log.critical("Thread finishing with results")
            else:
                log.critical("Thread finishing without results")
        except:
            self.error = True
            log.critical("Thread error")
        dbsession.close()


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
                 as_dump: bool = False,
                 sort_method_by_class: TaskSortMethod = TaskSortMethod.NONE,
                 sort_method_global: TaskSortMethod = TaskSortMethod.NONE,
                 current_only: bool = True) \
            -> None:
        self._req = req
        self._filter = taskfilter
        self._as_dump = as_dump
        self._current_only = current_only
        self._sort_method_by_class = sort_method_by_class
        self._sort_method_global = sort_method_global
        self._tasks_by_class = OrderedDict()  # type: Dict[Type[Task], List[Task]]  # noqa
        self._all_tasks = None  # type: List[Task]
        # log.critical("TaskCollection(): taskfilter={!r}", self._filter)

    # =========================================================================
    # Interface to read
    # =========================================================================

    def task_classes(self) -> List[Type[Task]]:
        return self._filter.task_classes

    def tasks_for_task_class(self, task_class: Type[Task]):
        self._fetch_task_class(task_class)
        tasklist = self._tasks_by_class.get(task_class, [])
        sort_tasks_in_place(tasklist, self._sort_method_by_class)
        return tasklist

    @property
    def all_tasks(self) -> List[Task]:
        if self._all_tasks is None:
            self._fetch_all_tasks()
            self._all_tasks = []  # type: List[Task]
            for single_task_list in self._tasks_by_class.values():
                self._all_tasks += single_task_list
            sort_tasks_in_place(self._all_tasks, self._sort_method_global)
        return self._all_tasks

    # =========================================================================
    # Internals
    # =========================================================================

    def _make_query(self, dbsession: SqlASession,
                    task_class: Type[Task]) -> Optional[Query]:
        q = dbsession.query(task_class)

        # Restrict to what the web front end will supply
        # noinspection PyProtectedMember
        if self._current_only:
            # noinspection PyProtectedMember
            q = q.filter(task_class._current == True)  # nopep8

        # Restrict to what is PERMITTED
        # Cache group IDs
        q = task_query_restricted_to_permitted_users(self._req, q, task_class,
                                                     as_dump=self._as_dump)

        # Restrict to what is DESIRED
        if q:
            q = self._filter.task_query_restricted_by_filter(
                self._req, q, task_class)

        return q

    def _serial_query(self, task_class) -> Optional[Query]:
        dbsession = self._req.dbsession
        return self._make_query(dbsession, task_class)

    def _filter_through_python(self, tasks: List[Task]) -> List[Task]:
        if not self._filter.has_python_parts_to_filter():
            return tasks
        return [
            t for t in tasks
            if self._filter.task_matches_python_parts_of_filter(t)
        ]

    def forget_task_class(self, task_class: Type[Task]) -> None:
        self._tasks_by_class.pop(task_class, None)
        # https://stackoverflow.com/questions/11277432/how-to-remove-a-key-from-a-python-dictionary  # noqa

    def _fetch_task_class(self, task_class: Type[Task]) -> None:
        """Fetch one set of tasks from database."""
        if task_class in self._tasks_by_class:
            return  # already fetched
        q = self._serial_query(task_class)
        if q is None:
            newtasks = []  # type: List[Task]
        else:
            newtasks = q.all()  # type: List[Task]
            # Apply Python-side filters?
            newtasks = self._filter_through_python(newtasks)
        self._tasks_by_class[task_class] = newtasks

    def _fetch_all_tasks(self, parallel: bool = False) -> None:
        """Fetch all tasks from database."""

        # AVOID parallel=True; see notes above.
        if DEBUG_QUERY_TIMING:
            start_time = Pendulum.now()

        if parallel:
            threads = []  # type: List[FetchThread]
            for task_class in self._filter.task_classes:
                thread = FetchThread(self._req, task_class, self)
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
                if thread.error:
                    raise ValueError("Multithreaded fetch failed")

        else:
            for task_class in self._filter.task_classes:
                self._fetch_task_class(task_class)

        if DEBUG_QUERY_TIMING:
            end_time = Pendulum.now()
            # noinspection PyUnboundLocalVariable
            time_taken = end_time - start_time
            log.info("_fetch_all_tasks took {}", time_taken)
