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

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.engine import Connection, Engine, ResultProxy
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import Query
# from sqlalchemy.orm.state import InstanceState
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql import func, literal, select, table
from sqlalchemy.sql.selectable import Exists
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.visitors import VisitableType

# The base of all our model classes:
Base = declarative_base()


# =============================================================================
# Connection management
# =============================================================================

def get_engine_from_session(dbsession: SqlASession) -> Engine:
    engine = dbsession.bind
    assert isinstance(engine, Engine)
    return engine


# =============================================================================
# Inspect tables (SQLAlchemy Core)
# =============================================================================

def get_table_names(engine: Engine) -> List[str]:
    insp = Inspector.from_engine(engine)
    return insp.get_table_names()


def get_view_names(engine: Engine) -> List[str]:
    insp = Inspector.from_engine(engine)
    return insp.get_view_names()


def table_exists(engine: Engine, tablename: str) -> bool:
    return tablename in get_table_names(engine)


def view_exists(engine: Engine, viewname: str) -> bool:
    return viewname in get_view_names(engine)


def table_or_view_exists(engine: Engine, table_or_view_name: str) -> bool:
    tables_and_views = get_table_names(engine) + get_view_names(engine)
    return table_or_view_name in tables_and_views


def get_columns_info(engine: Engine, tablename: str) -> List[Dict]:
    insp = Inspector.from_engine(engine)
    return insp.get_columns(tablename)


def get_column_info(engine: Engine, tablename: str,
                    columnname: str) -> Optional[Dict]:
    # Dictionary structure: see
    # http://docs.sqlalchemy.org/en/latest/core/reflection.html#sqlalchemy.engine.reflection.Inspector.get_columns  # noqa
    columns = get_columns_info(engine, tablename)
    for x in columns:
        if x['name'] == columnname:
            return x
    return None


# =============================================================================
# Inspect ORM objects (SQLAlchemy ORM)
# =============================================================================

def get_orm_columns(cls: Type[Base]) -> List[Column]:
    mapper = inspect(cls)  # type: Mapper
    # ... returns InstanceState if called with an ORM object
    #     http://docs.sqlalchemy.org/en/latest/orm/session_state_management.html#session-object-states  # noqa
    # ... returns Mapper if called with an ORM class
    #     http://docs.sqlalchemy.org/en/latest/orm/mapping_api.html#sqlalchemy.orm.mapper.Mapper  # noqa
    return mapper.columns


def get_orm_column_names(cls: Type[Base], sort: bool = False) -> List[str]:
    colnames = [col.name for col in get_orm_columns(cls)]
    return sorted(colnames) if sort else colnames


# =============================================================================
# SQL (SQLAlchemy Core)
# =============================================================================

def count_star(session: Union[SqlASession, Engine, Connection],
               tablename: str) -> int:
    # works if you pass a connection or a session or an engine; all have
    # the execute() method
    query = select([func.count()]).select_from(table(tablename))
    return session.execute(query).scalar()


def get_rows_fieldnames_from_query(
        session: Union[SqlASession, Engine, Connection],
        query: Query) -> Tuple[Sequence[Sequence[Any]], Sequence[str]]:
    fieldnames = [cd['name'] for cd in query.column_descriptions]
    result = session.execute(query)  # type: ResultProxy
    rows = result.fetchall()
    return rows, fieldnames


def get_rows_fieldnames_from_raw_sql(
        session: Union[SqlASession, Engine, Connection],
        sql: str) -> Tuple[Sequence[Sequence[Any]], Sequence[str]]:
    result = session.execute(sql)  # type: ResultProxy
    fieldnames = result.keys()
    rows = result.fetchall()
    return rows, fieldnames


def bool_from_exists_clause(session: SqlASession,
                            exists_clause: Exists) -> bool:
    """
    Database dialects are not consistent in how EXISTS clauses can be converted
    to a boolean answer.

    See:
    - https://bitbucket.org/zzzeek/sqlalchemy/issues/3212/misleading-documentation-for-queryexists  # noqa
    - http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.exists  # noqa
    """
    if session.get_bind().dialect.name == 'mssql':
        # SQL Server
        result = session.query(literal(True)).filter(exists_clause).scalar()
        # SELECT 1 WHERE EXISTS (SELECT 1 FROM table WHERE ...)
        # ... giving 1 or None (no rows)
        # ... fine for SQL Server, but invalid for MySQL (no FROM clause)
    else:
        # MySQL, etc.
        result = session.query(exists_clause).scalar()
        # SELECT EXISTS (SELECT 1 FROM table WHERE ...)
        # ... giving 1 or 0
        # ... fine for MySQL, but invalid syntax for SQL server
    return bool(result)


# =============================================================================
# SQL (SQLAlchemy ORM)
# =============================================================================

def exists_orm(session: SqlASession,
               ormclass: DeclarativeMeta,
               *criteria: Any) -> bool:
    """
    Example usage:
        bool_exists = exists_orm(session, MyClass, MyClass.myfield == value)
    """
    # http://docs.sqlalchemy.org/en/latest/orm/query.html
    q = session.query(ormclass)
    for criterion in criteria:
        q = q.filter(criterion)
    exists_clause = q.exists()
    return bool_from_exists_clause(session=session,
                                   exists_clause=exists_clause)


def coltype_as_typeengine(coltype: Union[VisitableType,
                                         TypeEngine]) -> TypeEngine:
    """
    To explain: you can specify columns like
        a = Column("a", Integer)
        b = Column("b", Integer())
        c = Column("c", String(length=50))

    isinstance(Integer, TypeEngine)  # False
    isinstance(Integer(), TypeEngine)  # True
    isinstance(String(length=50), TypeEngine)  # True

    type(Integer)  # <class 'sqlalchemy.sql.visitors.VisitableType'>
    type(Integer())  # <class 'sqlalchemy.sql.sqltypes.Integer'>
    type(String)  # <class 'sqlalchemy.sql.visitors.VisitableType'>
    type(String(length=50))  # <class 'sqlalchemy.sql.sqltypes.String'>

    This function coerces things to a TypeEngine.
    """
    if isinstance(coltype, TypeEngine):
        return coltype
    return coltype()  # type: TypeEngine


# noinspection PyAbstractClass
class SpecializedQuery(Query):
    """
    Optimizes COUNT(*) queries.
    See
        https://stackoverflow.com/questions/12941416/how-to-count-rows-with-select-count-with-sqlalchemy  # noqa
    """
    def count_star(self):
        count_query = (self.statement.with_only_columns([func.count()])
                       .order_by(None))
        return self.session.execute(count_query).scalar()
