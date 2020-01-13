#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_taskschedule.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

from sqlalchemy.orm import relationship

from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDurationAsIsoTextColType,
    TableNameColType,
)


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

    description = Column(
        "description", UnicodeText,
        comment="description"
    )

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

    def __str__(self) -> str:
        return (f"{self.task_table_name} "
                f"due from {self.due_from}, "
                f"must be completed by {self.due_by}")
