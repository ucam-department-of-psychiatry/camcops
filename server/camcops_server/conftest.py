#!/usr/bin/env python

"""
camcops_server/conftest.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Configure server self-tests for Pytest.**

"""

# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py

import configparser
from io import StringIO
import os
import tempfile
from typing import Generator, TYPE_CHECKING

import pytest
from sqlalchemy import event
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session

import camcops_server.cc_modules.cc_all_models  # noqa: F401

# ... import side effects (ensure all models registered)

from camcops_server.cc_modules.cc_baseconstants import CAMCOPS_SERVER_DIRECTORY
from camcops_server.cc_modules.cc_config import get_demo_config
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


TEST_DATABASE_FILENAME = os.path.join(
    CAMCOPS_SERVER_DIRECTORY, "camcops_test.sqlite"
)


def pytest_addoption(parser: "Parser"):
    parser.addoption(
        "--database-in-memory",
        action="store_false",
        dest="database_on_disk",
        default=True,
        help="Make SQLite database in memory",
    )

    # Borrowed from pytest-django
    parser.addoption(
        "--create-db",
        action="store_true",
        dest="create_db",
        default=False,
        help="Create the database even if it already exists",
    )

    parser.addoption(
        "--mysql",
        action="store_true",
        dest="mysql",
        default=False,
        help="Use MySQL database instead of SQLite",
    )

    parser.addoption(
        "--db-url",
        dest="db_url",
        default=(
            "mysql+mysqldb://camcops:camcops@localhost:3306/test_camcops"
            "?charset=utf8"
        ),
        help="SQLAlchemy test database URL (MySQL only)",
    )

    parser.addoption(
        "--echo",
        action="store_true",
        dest="echo",
        default=False,
        help="Log all SQL statments to the default log handler",
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
def db_url(request: "FixtureRequest") -> bool:
    return request.config.getvalue("db_url")


@pytest.fixture(scope="session")
def tmpdir_obj(
    request: "FixtureRequest",
) -> Generator[tempfile.TemporaryDirectory, None, None]:
    tmpdir_obj = tempfile.TemporaryDirectory()

    yield tmpdir_obj

    tmpdir_obj.cleanup()


@pytest.fixture(scope="session")
def config_file(
    request: "FixtureRequest", tmpdir_obj: tempfile.TemporaryDirectory
) -> str:
    # We're going to be using a test (SQLite) database, but we want to
    # be very sure that nothing writes to a real database! Also, we will
    # want to read from this dummy config at some point.

    tmpconfigfilename = os.path.join(tmpdir_obj.name, "dummy_config.conf")
    with open(tmpconfigfilename, "w") as file:
        file.write(get_config_text())

    return tmpconfigfilename


def get_config_text() -> str:
    config_text = get_demo_config()
    parser = configparser.ConfigParser()
    parser.read_string(config_text)

    with StringIO() as buffer:
        parser.write(buffer)
        config_text = buffer.getvalue()

    return config_text


# https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
# Author says "no [license], feel free to use it"
# noinspection PyUnusedLocal
@pytest.fixture(scope="session")
def engine(
    request: "FixtureRequest",
    create_db: bool,
    database_on_disk: bool,
    echo: bool,
    mysql: bool,
    db_url: str,
) -> Generator["Engine", None, None]:

    if mysql:
        engine = create_engine_mysql(db_url, create_db, echo)
    else:
        engine = create_engine_sqlite(create_db, echo, database_on_disk)

    yield engine
    engine.dispose()


def create_engine_mysql(db_url: str, create_db: bool, echo: bool):

    # The database and the user with the given password from db_url
    # need to exist.
    # mysql> CREATE DATABASE <db_name>;
    # mysql> GRANT ALL PRIVILEGES ON <db_name>.*
    #        TO <db_user>@localhost IDENTIFIED BY '<db_password>';
    engine = create_engine(db_url, echo=echo, pool_pre_ping=True)

    if create_db:
        Base.metadata.drop_all(engine)

    return engine


def create_engine_sqlite(create_db: bool, echo: bool, database_on_disk: bool):
    if create_db and database_on_disk:
        try:
            os.remove(TEST_DATABASE_FILENAME)
        except OSError:
            pass

    if database_on_disk:
        engine = make_file_sqlite_engine(TEST_DATABASE_FILENAME, echo=echo)
    else:
        engine = make_memory_sqlite_engine(echo=echo)

    event.listen(engine, "connect", set_sqlite_pragma)

    return engine


# noinspection PyUnusedLocal
@pytest.fixture(scope="session")
def tables(
    request: "FixtureRequest", engine: "Engine", create_db: bool
) -> Generator[None, None, None]:
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
def dbsession(
    request: "FixtureRequest", engine: "Engine", tables: None
) -> Generator[Session, None, None]:
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
def setup(
    request: "FixtureRequest",
    engine: "Engine",
    database_on_disk: bool,
    mysql: bool,
    dbsession: Session,
    tmpdir_obj: tempfile.TemporaryDirectory,
    config_file: str,
) -> None:
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
    request.cls.config_file = config_file
