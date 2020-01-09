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

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    TableNameColType,
)


class TaskSchedule(Base):
    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True,
        comment="Arbitrary primary key"
    )

    task_table_name = Column(
        "task_table_name", TableNameColType,
        index=True,
        comment="Table name of the task's base table"
    )

    # TODO: Other fields: due from, due by (relative)
