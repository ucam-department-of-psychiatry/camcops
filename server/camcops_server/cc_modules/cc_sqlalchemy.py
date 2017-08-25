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

from cardinal_pythonlib.sqlalchemy.dump import dump_ddl

from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import MetaData

# =============================================================================
# Naming convention; metadata; Base
# =============================================================================
# https://alembic.readthedocs.org/en/latest/naming.html
# http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions  # noqa

NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',

    "uq": "uq_%(table_name)s_%(column_0_name)s",

    # "ck": "ck_%(table_name)s_%(constraint_name)s",  # too long for MySQL
    # ... https://groups.google.com/forum/#!topic/sqlalchemy/SIT4D8S9dUg
    "ck": "ck_%(table_name)s_%(column_0_name)s",

    # "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # too long for MySQL sometimes!  # noqa
    "fk": "fk_%(table_name)s_%(column_0_name)s",

    "pk": "pk_%(table_name)s"
}
MASTER_META = MetaData(naming_convention=NAMING_CONVENTION)

# The base of all our model classes:
Base = declarative_base(metadata=MASTER_META)

# Special options:
Base.__table_args__ = {
    # -------------------------------------------------------------------------
    # MySQL special options
    # -------------------------------------------------------------------------
    # Engine: InnoDB
    'mysql_engine': 'InnoDB',

    # Barracuda: COMPRESSED or DYNAMIC
    # https://dev.mysql.com/doc/refman/5.7/en/innodb-row-format-dynamic.html
    # https://xenforo.com/community/threads/anyone-running-their-innodb-tables-with-row_format-compressed.99606/  # noqa
    # We shouldn't compress everything by default; performance hit.
    'mysql_row_format': 'DYNAMIC',

    # Character set
    'mysql_charset': 'utf8mb4',
    # https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-utf8mb4.html

    # Collation
    # Which collation for MySQL? See
    # - https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci  # noqa
    'mysql_collate': 'utf8mb4_unicode_ci'
    # Note that COLLATION rules are, from least to greatest precedence:
    #       Server collation
    #       Connection-specific collation
    #       Database collation
    #       Table collation
    #       Column collation
    #       Query collation (using CAST or CONVERT)
    # - https://stackoverflow.com/questions/24356090/difference-between-database-table-column-collation  # noqa
    # Therefore, we can set the table collation for all our tables, and not
    # worry about the column collation, e.g. Text(collation=...).
}

# MySQL things we can't set via SQLAlchemy, but would like to be set:
# - max_allowed_packet: should be at least 32M
# - innodb_strict_mode: should be 1, but less of a concern with SQLAlchemy

# MySQL things we don't care about too much:
# - innodb_file_per_table: desirable, but up to the user.


# =============================================================================
# Convenience functions
# =============================================================================

def make_memory_sqlite_engine() -> Engine:
    return create_engine('sqlite://')


def make_debug_sqlite_engine() -> Engine:
    return create_engine('sqlite://', echo=True)


def print_all_ddl(dialect_name: str = "mysql"):
    metadata = Base.metadata  # type: MetaData
    dump_ddl(metadata, dialect_name=dialect_name)


TEST_CODE = """

PRINT_DDL = False

from sqlalchemy.orm.session import sessionmaker
from camcops_server.cc_modules.cc_sqlalchemy import *
from camcops_server.cc_modules.cc_all_models import *

if PRINT_DDL:
    print_all_ddl()

engine = make_debug_sqlite_engine()
Base.metadata.create_all(engine)
session = sessionmaker()(bind=engine)  # will also show DDL (debug engine)

phq9_query = session.query(Phq9)

phq9_query.all()

"""
