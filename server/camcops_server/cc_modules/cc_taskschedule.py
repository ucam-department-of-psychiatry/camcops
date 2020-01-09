#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_patient.py

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

**Task schedule**

"""

from sqlalchemy.orm import relationship

from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

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

    items = relationship("TaskScheduleItem")


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
