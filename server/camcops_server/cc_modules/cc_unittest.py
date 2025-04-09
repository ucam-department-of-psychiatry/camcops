"""
camcops_server/cc_modules/cc_unittest.py

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

**Framework and support functions for unit tests.**

"""

import base64
import copy
from faker import Faker
import logging
import os
import random
import sqlite3
from typing import Any, Dict, List, Type, TYPE_CHECKING
from unittest import mock, TestCase

from cardinal_pythonlib.classes import all_subclasses
from cardinal_pythonlib.dbfunc import get_fieldnames_from_cursor
from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.logs import BraceStyleAdapter
import pytest
from sqlalchemy.engine.base import Engine

from camcops_server.cc_modules.cc_baseconstants import ENVVAR_CONFIG_FILE
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_request import (
    CamcopsRequest,
    get_unittest_request,
)
from camcops_server.cc_modules.cc_sqlalchemy import sql_from_sqlite_database
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin
from camcops_server.cc_modules.cc_user import User
from camcops_server.cc_modules.cc_testfactories import (
    BaseFactory,
    GroupFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    RioPatientIdNumFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.tasks.tests import factories as task_factories

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DEMO_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="  # noqa
    # https://stackoverflow.com/questions/6018611
    # 1x1 pixel, black
)


# =============================================================================
# Unit testing
# =============================================================================


class ExtendedTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()

        # Arbitrary seed
        Faker.seed(1234)
        random.seed(1234)

    """
    A subclass of :class:`unittest.TestCase` that provides some additional
    functionality.
    """

    # Logging in unit tests:
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o  # noqa
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o/15969985#15969985
    # ... but actually, my code below is simpler and works fine.

    @classmethod
    def announce(cls, msg: str) -> None:
        """
        Logs a message to the Python log.
        """
        log.info("{}.{}:{}", cls.__module__, cls.__name__, msg)

    def assertIsInstanceOrNone(
        self, obj: object, cls: Type, msg: str = None
    ) -> None:
        """
        Asserts that ``obj`` is an instance of ``cls`` or is None. The
        parameter ``msg`` is used as part of the failure message if it isn't.
        """
        if obj is None:
            return
        self.assertIsInstance(obj, cls, msg)


@pytest.mark.usefixtures("setup")
class DemoRequestTestCase(ExtendedTestCase):
    """
    Test case that creates a demo Pyramid request that refers to a database.
    See server/camcops_server/conftest.py
    """

    dbsession: "Session"
    config_file: str
    engine: Engine
    database_on_disk: bool
    db_filename: str

    def setUp(self) -> None:
        super().setUp()

        for factory in all_subclasses(BaseFactory):
            factory._meta.sqlalchemy_session = self.dbsession

        # config file has already been set up for the session in conftest.py
        os.environ[ENVVAR_CONFIG_FILE] = self.config_file
        self.req = get_unittest_request(self.dbsession)

        # request.config is a class property. We want to be able to override
        # config settings in a test by setting them directly on the config
        # object (e.g. self.req.config.foo = "bar"), then restore the defaults
        # afterwards.
        self.old_config = copy.copy(self.req.config)

        self.req.matched_route = mock.Mock()
        self.recipdef = ExportRecipient()

    def tearDown(self) -> None:
        CamcopsRequest.config = self.old_config  # type: ignore[method-assign]

    def set_echo(self, echo: bool) -> None:
        """
        Changes the database echo status.
        """
        self.engine.echo = echo

    def dump_database(self, loglevel: int = logging.INFO) -> None:
        """
        Writes the test in-memory SQLite database to the logging stream.

        Args:
            loglevel: log level to use
        """
        if not self.database_on_disk:
            log.warning("Cannot dump database (use database_on_disk for that)")
            return
        log.info("Dumping database; please wait...")
        connection = sqlite3.connect(self.db_filename)
        sql_text = sql_from_sqlite_database(connection)
        connection.close()
        log.log(loglevel, "SQLite database:\n{}", sql_text)

    def dump_table(
        self,
        tablename: str,
        column_names: List[str] = None,
        loglevel: int = logging.INFO,
    ) -> None:
        """
        Writes one table of the in-memory SQLite database to the logging
        stream.

        Args:
            tablename: table to dump
            column_names: column names to dump, or ``None`` for all
            loglevel: log level to use
        """
        if not self.database_on_disk:
            log.warning("Cannot dump database (use database_on_disk for that)")
            return
        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()
        columns = ",".join(column_names) if column_names else "*"
        sql = f"SELECT {columns} FROM {tablename}"
        cursor.execute(sql)
        # noinspection PyTypeChecker
        fieldnames = get_fieldnames_from_cursor(cursor)  # type: ignore[arg-type]  # noqa: E501
        results = (
            ",".join(fieldnames)
            + "\n"
            + "\n".join(
                ",".join(str(value) for value in row)
                for row in cursor.fetchall()
            )
        )
        connection.close()
        log.log(loglevel, "Contents of table {}:\n{}", tablename, results)


class BasicDatabaseTestCase(DemoRequestTestCase):
    """
    Test case that sets up some minimal database records for testing.
    """

    def setUp(self) -> None:
        super().setUp()

        self.group = GroupFactory()
        self.groupadmin = UserFactory()

        self.superuser = UserFactory(superuser=True)

        UserGroupMembershipFactory(
            group_id=self.group.id, user_id=self.groupadmin.id, groupadmin=True
        )

        self.system_user = User.get_system_user(self.dbsession)
        self.system_user.upload_group_id = self.group.id

        self.req._debugging_user = self.superuser  # improve our debugging user

        self.server_device = Device.get_server_device(self.dbsession)
        self.dbsession.commit()


class DemoDatabaseTestCase(BasicDatabaseTestCase):
    """
    Test case that sets up a demonstration CamCOPS database with two tasks of
    each type
    """

    def setUp(self) -> None:
        super().setUp()

        self.demo_database_group = GroupFactory()

        patient_with_two_idnums = PatientFactory(
            _group=self.demo_database_group
        )
        NHSPatientIdNumFactory(patient=patient_with_two_idnums)
        RioPatientIdNumFactory(patient=patient_with_two_idnums)

        patient_with_one_idnum = PatientFactory(
            _group=self.demo_database_group
        )
        NHSPatientIdNumFactory(patient=patient_with_one_idnum)

        for cls in Task.all_subclasses_by_tablename():
            factory_class = getattr(task_factories, f"{cls.__name__}Factory")

            t1_kwargs: Dict[str, Any] = dict(_group=self.demo_database_group)
            t2_kwargs = t1_kwargs.copy()
            if issubclass(cls, TaskHasPatientMixin):
                t1_kwargs.update(patient=patient_with_two_idnums)
                t2_kwargs.update(patient=patient_with_one_idnum)

            if cls.__name__ == "Photo":
                blobargs = dict(
                    create_blob__fieldname="photo_blobid",
                    create_blob__filename="some_picture.png",
                    create_blob__mimetype=MimeType.PNG,
                    create_blob__image_rotation_deg_cw=0,
                    create_blob__theblob=DEMO_PNG_BYTES,
                )
                t1_kwargs.update(blobargs)
                t2_kwargs.update(blobargs)

            factory_class(**t1_kwargs)
            factory_class(**t2_kwargs)
