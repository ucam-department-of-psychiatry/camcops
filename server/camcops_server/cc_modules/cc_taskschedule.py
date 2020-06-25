#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_taskschedule.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

**Task schedule item**

"""
from typing import List, Optional, TYPE_CHECKING

from pendulum import DateTime as Pendulum

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    PendulumDurationAsIsoTextColType,
    TableNameColType,
)
from camcops_server.cc_modules.cc_task import Task, tablename_to_task_class_dict
from camcops_server.cc_modules.cc_taskcollection import (
    TaskFilter,
    TaskCollection,
    TaskSortMethod,
)

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class ScheduledTaskInfo(object):
    def __init__(self,
                 shortname: str,
                 tablename: str,
                 task: Optional[Task] = None,
                 start_datetime: Optional[Pendulum] = None,
                 end_datetime: Optional[Pendulum] = None) -> None:
        self.shortname = shortname
        self.tablename = tablename
        self.task = task
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime


class PatientTaskSchedule(Base):
    __tablename__ = "_patient_task_schedule"

    # TODO: remove and make the foreign keys primary keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    patient_pk = Column(
        "patient_pk", Integer,
        ForeignKey("patient._pk", ondelete="CASCADE")
    )
    schedule_id = Column(
        "schedule_id", Integer,
        ForeignKey("_task_schedule.id", ondelete="CASCADE")
    )
    start_date = Column(
        "start_date", PendulumDateTimeAsIsoTextColType,
        comment=(
            "Schedule start date for the patient. Due from/within "
            "durations for a task schedule item are relative to this."
        )
    )
    patient = relationship("Patient", backref="task_schedules")
    task_schedule = relationship("TaskSchedule", backref="patients")

    def get_list_of_scheduled_tasks(
            self,
            req: "CamcopsRequest",
            include_task_objects=True
    ) -> List[ScheduledTaskInfo]:

        task_list = []

        task_class_lookup = tablename_to_task_class_dict()

        for tsi in self.task_schedule.items:
            start_datetime = None
            end_datetime = None
            task = None

            if self.patient.idnums and self.start_date is not None:
                start_datetime = self.start_date.add(days=tsi.due_from.days)
                end_datetime = self.start_date.add(days=tsi.due_by.days)

                if include_task_objects:
                    task = self.find_scheduled_task(
                        req, tsi, start_datetime, end_datetime
                    )

            task_list.append(
                ScheduledTaskInfo(
                    task_class_lookup[tsi.task_table_name].shortname,
                    tsi.task_table_name,
                    task=task,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime
                )
            )

        return task_list

    def find_scheduled_task(self,
                            req: "CamcopsRequest",
                            tsi: "TaskScheduleItem",
                            start_datetime: Pendulum,
                            end_datetime: Pendulum) -> Optional[Task]:
        taskfilter = TaskFilter()
        for idnum in self.patient.idnums:
            idnum_ref = IdNumReference(which_idnum=idnum.which_idnum,
                                       idnum_value=idnum.idnum_value)
            taskfilter.idnum_criteria.append(idnum_ref)

        taskfilter.task_types = [tsi.task_table_name]

        taskfilter.start_datetime = start_datetime
        taskfilter.end_datetime = end_datetime

        collection = TaskCollection(
            req=req,
            taskfilter=taskfilter,
            sort_method_global=TaskSortMethod.CREATION_DATE_DESC
        )

        if len(collection.all_tasks) > 0:
            return collection.all_tasks[0]

        return None


class TaskSchedule(Base):
    __tablename__ = "_task_schedule"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )

    group_id = Column(
        "group_id", Integer, ForeignKey(Group.id),
        nullable=False,
        comment="FK to {}.{}".format(Group.__tablename__,
                                     Group.id.name)
    )

    name = Column("name", UnicodeText, comment="name")

    items = relationship("TaskScheduleItem")

    group = relationship(Group)


class TaskScheduleItem(Base):
    __tablename__ = "_task_schedule_item"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )

    schedule_id = Column(
        "schedule_id", Integer, ForeignKey(TaskSchedule.id),
        nullable=False,
        comment="FK to {}.{}".format(TaskSchedule.__tablename__,
                                     TaskSchedule.id.name)
    )

    task_table_name = Column(
        "task_table_name", TableNameColType,
        index=True,
        comment="Table name of the task's base table"
    )

    due_from = Column(
        "due_from", PendulumDurationAsIsoTextColType,
        comment=("Relative time from the start date by which the task may be "
                 "started")
    )

    due_by = Column(
        "due_by", PendulumDurationAsIsoTextColType,
        comment=("Relative time from the start date by which the task must be "
                 "completed")
    )

    @property
    def task_shortname(self) -> str:
        task_class_lookup = tablename_to_task_class_dict()

        return task_class_lookup[self.task_table_name].shortname

    def __str__(self) -> str:
        return (f"{self.task_shortname} @ {self.due_from.in_days()} days")
