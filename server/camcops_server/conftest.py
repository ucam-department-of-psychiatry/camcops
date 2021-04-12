# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py

import os
import tempfile

from cardinal_pythonlib.sqlalchemy.session import make_sqlite_url
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
import pytest

import camcops_server.cc_modules.cc_all_models  # import side effects (ensure all models registered)  # noqa: F401,E501
from camcops_server.cc_modules.cc_sqlalchemy import Base

# TODO: Options as per:
# https://stackoverflow.com/questions/58660378/how-use-pytest-to-unit-test-sqlalchemy-orm-classes
# - create or reuse db
# - echo on / off
# - memory or file based

SERVER_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATABASE_FILENAME = os.path.join(SERVER_DIR, "camcops_test.sqlite")


def pytest_addoption(parser):
    # Borrowed from pytest-django
    parser.addoption(
        "--create-db",
        action="store_true",
        dest="create_db",
        default=False,
        help="Create the database even if it already exists"
    )


def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def create_db(request):
    if not os.path.exists(TEST_DATABASE_FILENAME):
        return True

    return request.config.getvalue("create_db")


@pytest.fixture(scope="session")
def tmpdir_obj(request):
    tmpdir_obj = tempfile.TemporaryDirectory()

    yield tmpdir_obj

    tmpdir_obj.cleanup()


# https://gist.githubusercontent.com/kissgyorgy/e2365f25a213de44b9a2/raw/f8b5bbf06c4969bc6bbe5316defef64137c9b1e3/sqlalchemy_conftest.py
@pytest.fixture(scope="session")
def engine(request, create_db):
    if create_db:
        try:
            os.remove(TEST_DATABASE_FILENAME)
        except OSError:
            pass

    engine = create_engine(make_sqlite_url(TEST_DATABASE_FILENAME), echo=False)
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
def setup(request, dbsession, tmpdir_obj):
    request.cls.dbsession = dbsession
    request.cls.tmpdir_obj = tmpdir_obj
    yield
