#!/usr/bin/env python
# camcops_server/cc_modules/cc_sqlalchemy.py

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

A few random notes:

- SQLAlchemy will automatically warn about clashing columns:

.. :code-block:: python

    from sqlalchemy import Column, Integer
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class Thing(Base):
        __tablename__ = "thing"
        a = Column("a", Integer, primary_key=True)
        b = Column("b", Integer)
        c = Column("b", Integer)  # produces a warning:

SAWarning: On class 'Thing', Column object 'b' named directly multiple times,
only one will be used: b, c. Consider using orm.synonym instead

"""

from io import StringIO
import logging

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.dialect import SqlaDialectName
from cardinal_pythonlib.sqlalchemy.dump import dump_ddl
from cardinal_pythonlib.sqlalchemy.session import SQLITE_MEMORY_URL
from pendulum import DateTime as Pendulum

from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import MetaData

from .cc_cache import cache_region_static, fkg

log = BraceStyleAdapter(logging.getLogger(__name__))

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
    # SQLAlchemy __table_args__:
    #   http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/table_config.html  # noqa
    # SQLAlchemy sends keyword arguments like 'mysql_keyword_name' to be
    # rendered as KEYWORD_NAME in the CREATE TABLE statement:
    #   http://docs.sqlalchemy.org/en/latest/dialects/mysql.html

    # Engine: InnoDB
    'mysql_engine': 'InnoDB',

    # Barracuda: COMPRESSED or DYNAMIC
    # https://dev.mysql.com/doc/refman/5.7/en/innodb-row-format-dynamic.html
    # https://xenforo.com/community/threads/anyone-running-their-innodb-tables-with-row_format-compressed.99606/  # noqa
    # We shouldn't compress everything by default; performance hit.
    'mysql_row_format': 'DYNAMIC',

    # SEE server_troubleshooting.rst FOR BUG DISCUSSION

    'mysql_charset': 'utf8mb4 COLLATE utf8mb4_unicode_ci',

    # Character set
    # REPLACED # 'mysql_charset': 'utf8mb4',
    # https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-utf8mb4.html

    # Collation
    # Which collation for MySQL? See
    # - https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci  # noqa
    # REPLACED # 'mysql_collate': 'utf8mb4_unicode_ci'
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
    #
    # To check a MySQL database, and connection/server settings:
    #       SHOW VARIABLES LIKE '%character%';
    #       SHOW VARIABLES LIKE '%collation%';
    # To check tables:
    #       SHOW TABLE STATUS WHERE NAME LIKE 'my_tablename'\G
    # ... note use of \G to produce long-form output!
    # To check columns:
    #       SHOW FULL COLUMNS FROM my_tablename;
    #
    # ONE THING IN PARTICULAR TO BEWARE: utf8mb4_unicode_ci produces
    # CASE-INSENSITIVE COMPARISON. For example:
    #       SELECT 'a' = 'A';  -- produces 1
    #       SELECT 'a' = 'B';  -- produces 0
    #       SELECT BINARY 'a' = BINARY 'A';  -- produces 0
    # This is a PROBLEM FOR PASSWORD FIELDS IF WE INTEND TO DO DATABASE-LEVEL
    # COMPARISONS WITH THEM. In that case we must ensure a different collation
    # is set; specifically, use
    #
    #       utf8mb4_bin
    #
    # and see also
    #       SHOW COLLATION WHERE `Collation` LIKE 'utf8mb4%';
    # and
    #   https://dev.mysql.com/doc/refman/5.6/en/charset-binary-collations.html
    #
    # To check, run
    #       SHOW FULL COLUMNS FROM _security_users;
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
    return create_engine(SQLITE_MEMORY_URL)


def make_debug_sqlite_engine(echo: bool = True) -> Engine:
    return create_engine(SQLITE_MEMORY_URL, echo=echo)


@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def get_all_ddl(dialect_name: str = SqlaDialectName.MYSQL) -> str:
    metadata = Base.metadata  # type: MetaData
    with StringIO() as f:
        dump_ddl(metadata, dialect_name=dialect_name, fileobj=f)
        f.flush()
        text = f.getvalue()
    return text


def log_all_ddl(dialect_name: str = SqlaDialectName.MYSQL) -> None:
    text = get_all_ddl(dialect_name)
    log.info(text)
    log.info("DDL length: {} characters", len(text))


# =============================================================================
# Database engine hacks
# =============================================================================

def hack_pendulum_into_pymysql() -> None:
    # https://pendulum.eustace.io/docs/#limitations
    try:
        # noinspection PyUnresolvedReferences
        from pymysql.converters import encoders, escape_datetime
        encoders[Pendulum] = escape_datetime
    except ImportError:
        pass


hack_pendulum_into_pymysql()
