#!/usr/bin/env python

"""
camcops_server/conftest.py

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

**Configure server self-tests for Pytest.**

"""

# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py

import os
import tempfile
from typing import Generator, TYPE_CHECKING

import pytest
from sqlalchemy import event
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session

import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa: F401,E501
from camcops_server.cc_modules.cc_baseconstants import CAMCOPS_SERVER_DIRECTORY
from camcops_server.cc_modules.cc_sqlalchemy import (
    Base,
    make_memory_sqlite_engine,
    make_file_sqlite_engine,
)

if TYPE_CHECKING:
    from sqlalchemy.engine.base import Engine
    # Should not need to import from _pytest in later versions of pytest
    # https://github.com/pytest-dev/pytest/issues/7469
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest


TEST_DATABASE_FILENAME = os.path.join(CAMCOPS_SERVER_DIRECTORY,
                                      "camcops_test.sqlite")


def pytest_addoption(parser: "Parser"):
    parser.addoption(
        "--database-in-memory",
        action="store_false",
        dest="database_on_disk",
        default=True,
        help="Make sqlite database in memory"
    )

    # Borrowed from pytest-django
    parser.addoption(
        "--create-db",
        action="store_true",
        dest="create_db",
        default=False,
        help="Create the database even if it already exists"
    )

    parser.addoption(
        "--mysql",
        action="store_true",
        dest="mysql",
        default=False,
        help="Use MySQL database instead of sqlite"
    )

    parser.addoption(
        "--db-name",
        dest="db_name",
        default="test_camcops",
        help="Test database name"
    )

    parser.addoption(
        "--db-user",
        dest="db_user",
        default="camcops",
        help="Database user"
    )

    parser.addoption(
        "--db-password",
        dest="db_password",
        default="camcops",
        help="Database user's password"
    )

    parser.addoption(
        "--echo",
        action="store_true",
        dest="echo",
        default=False,
        help="Log all SQL statments to the default log handler"
    )


# noinspection PyUnusedLocal
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def database_on_disk(request: "FixtureRequest") -> bool:
    return request.config.getvalue("database_on_disk")


@pytest.fixture(scope="session")
def create_db(request: "FixtureRequest", database_on_disk) -> bool:
    if not database_on_disk:
        return True

    if not os.path.exists(TEST_DATABASE_FILENAME):
        return True

    return request.config.getvalue("create_db")


@pytest.fixture(scope="session")
def echo(request: "FixtureRequest") -> bool:
    return request.config.getvalue("echo")


# noinspection PyUnusedLocal
@pytest.fixture(scope="session")
def mysql(request: "FixtureRequest") -> bool:
    return request.config.getvalue("mysql")


@pytest.fixture(scope="session")
def db_name(request: "FixtureRequest") -> bool:
    return request.config.getvalue("db_name")


@pytest.fixture(scope="session")
def db_user(request: "FixtureRequest") -> bool:
    return request.config.getvalue("db_user")


@pytest.fixture(scope="session")
def db_password(request: "FixtureRequest") -> bool:
    return request.config.getvalue("db_password")


@pytest.fixture(scope="session")
def tmpdir_obj(request: "FixtureRequest") -> Generator[
        tempfile.TemporaryDirectory, None, None]:
    tmpdir_obj = tempfile.TemporaryDirectory()

    yield tmpdir_obj

    tmpdir_obj.cleanup()


# https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
# Author says "no [license], feel free to use it"
@pytest.fixture(scope="session")
def engine(request: "FixtureRequest",
           create_db: bool,
           database_on_disk: bool,
           echo: bool,
           mysql: bool,
           db_name: str,
           db_user: str,
           db_password: str) -> Generator["Engine", None, None]:

    if mysql:
        engine = create_engine_mysql(db_name,
                                     db_user,
                                     db_password,
                                     create_db=create_db,
                                     echo=echo)
    else:
        engine = create_engine_sqlite()

    yield engine
    engine.dispose()


def create_engine_mysql(db_name: str,
                        db_user: str,
                        db_password: str,
                        create_db: bool,
                        echo: bool):

    # Database db_name and the user with the given password need to exist
    # mysql> CREATE DATABASE <db_name>;
    # mysql> GRANT ALL PRIVILEGES ON <db_name>.*
    #        TO <db_user>@localhost IDENTIFIED BY '<db_password>';
    db_url = (f"mysql+mysqldb://{db_user}:{db_password}@localhost:3306/"
              f"{db_name}?charset=utf8")
    engine = create_engine(db_url, echo=echo, pool_pre_ping=True)

    if create_db:
        Base.metadata.drop_all(engine)

    return engine


def create_engine_sqlite(create_db: bool,
                         echo: bool,
                         database_on_disk: bool):
    if create_db and database_on_disk:
        try:
            os.remove(TEST_DATABASE_FILENAME)
        except OSError:
            pass

    if database_on_disk:
        engine = make_file_sqlite_engine(TEST_DATABASE_FILENAME,
                                         echo=echo)
    else:
        engine = make_memory_sqlite_engine(echo=echo)

    event.listen(engine, "connect", set_sqlite_pragma)

    return engine


# noinspection PyUnusedLocal
@pytest.fixture(scope="session")
def tables(request: "FixtureRequest",
           engine: "Engine",
           create_db: bool) -> Generator[None, None, None]:
    if create_db:
        Base.metadata.create_all(engine)
    yield

    # Any post-session clean up would go here
    # Foreign key constraint on _security_devices prevents this:
    # Base.metadata.drop_all(engine)
    # This would only be useful if we wanted to clean up the database
    # after running the tests


# noinspection PyUnusedLocal
@pytest.fixture
def dbsession(request: "FixtureRequest",
              engine: "Engine",
              tables: None) -> Generator[Session, None, None]:
    """
    Returns an sqlalchemy session, and after the test tears down everything
    properly.
    """

    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


@pytest.fixture
def setup(request: "FixtureRequest",
          engine: "Engine",
          database_on_disk: bool,
          mysql: bool,
          dbsession: Session,
          tmpdir_obj: tempfile.TemporaryDirectory) -> None:
    # Pytest prefers function-based tests over unittest.TestCase subclasses and
    # methods, but it still supports the latter perfectly well.
    # We use this fixture in cc_unittest.py to store these values into
    # DemoRequestTestCase and its descendants.
    request.cls.engine = engine
    request.cls.database_on_disk = database_on_disk
    request.cls.dbsession = dbsession
    request.cls.tmpdir_obj = tmpdir_obj
    request.cls.db_filename = TEST_DATABASE_FILENAME
    request.cls.mysql = mysql
