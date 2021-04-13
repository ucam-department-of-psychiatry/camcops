# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py

import os
import tempfile

from camcops_server.cc_modules.cc_sqlalchemy import (
    make_memory_sqlite_engine,
    make_file_sqlite_engine,
)
from sqlalchemy import event
from sqlalchemy.orm import Session
import pytest

import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa: F401,E501
from camcops_server.cc_modules.cc_sqlalchemy import Base

SERVER_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATABASE_FILENAME = os.path.join(SERVER_DIR, "camcops_test.sqlite")


def pytest_addoption(parser):
    parser.addoption(
        "--database-in-memory",
        action="store_false",
        dest="database_on_disk",
        default=True,
        help="Make database in memory"
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
        "--echo",
        action="store_true",
        dest="echo",
        default=False,
        help="Log all SQL statments to the default log handler"
    )


def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def database_on_disk(request):
    return request.config.getvalue("database_on_disk")


@pytest.fixture(scope="session")
def create_db(request, database_on_disk):
    if not database_on_disk:
        return True

    if not os.path.exists(TEST_DATABASE_FILENAME):
        return True

    return request.config.getvalue("create_db")


@pytest.fixture(scope="session")
def echo(request):
    return request.config.getvalue("echo")


@pytest.fixture(scope="session")
def tmpdir_obj(request):
    tmpdir_obj = tempfile.TemporaryDirectory()

    yield tmpdir_obj

    tmpdir_obj.cleanup()


# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py
@pytest.fixture(scope="session")
def engine(request, create_db, database_on_disk, echo):
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

    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tables(request, engine, create_db):
    if create_db:
        Base.metadata.create_all(engine)
    yield
    # TODO: Foreign key constraint on _security_devices prevents this
    # Base.metadata.drop_all(engine)


@pytest.fixture
def dbsession(request, engine, tables):
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
def setup(request, engine, database_on_disk, dbsession, tmpdir_obj):
    # Pytest prefers function-based tests over unittest.TestCase subclasses and
    # methods, but it still supports the latter perfectly well.
    # We use this fixture in cc_unittest.py to store these values into
    # DemoRequestTestCase and its descendants.
    request.cls.engine = engine
    request.cls.database_on_disk = database_on_disk
    request.cls.dbsession = dbsession
    request.cls.tmpdir_obj = tmpdir_obj
    request.cls.db_filename = TEST_DATABASE_FILENAME
    yield
