#!/usr/bin/env python
# camcops_server/cc_modules/cc_sqlalchemy.py

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

from typing import TYPE_CHECKING

from cardinal_pythonlib.sqlalchemy.dump import dump_ddl

from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import MetaData


# The base of all our model classes:
Base = declarative_base()


def make_memory_sqlite_engine() -> Engine:
    return create_engine('sqlite://')


def make_debug_sqlite_engine() -> Engine:
    return create_engine('sqlite://', echo=True)


def print_all_ddl(dialect_name: str = "mysql"):
    metadata = Base.metadata  # type: MetaData
    dump_ddl(metadata, dialect_name=dialect_name)


TEST_CODE = """

from camcops_server.cc_modules.cc_sqlalchemy import print_all_ddl
from camcops_server.cc_modules.cc_all_models import *

print_all_ddl()

"""