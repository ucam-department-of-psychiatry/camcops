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
from typing import Any, List, Type, TYPE_CHECKING
import unittest

from cardinal_pythonlib.classes import all_subclasses
from cardinal_pythonlib.dbfunc import get_fieldnames_from_cursor
from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.logs import BraceStyleAdapter
import pendulum
import pytest
from sqlalchemy.engine.base import Engine

from camcops_server.cc_modules.cc_baseconstants import ENVVAR_CONFIG_FILE
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_ipuse import IpUse
from camcops_server.cc_modules.cc_request import (
    CamcopsRequest,
    get_unittest_request,
)
from camcops_server.cc_modules.cc_sqlalchemy import sql_from_sqlite_database
from camcops_server.cc_modules.cc_user import User
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_testfactories import (
    BaseFactory,
    DeviceFactory,
    GroupFactory,
    IdNumDefinitionFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    RioPatientIdNumFactory,
    ServerCreatedPatientFactory,
    ServerCreatedNHSPatientIdNumFactory,
    ServerCreatedRioPatientIdNumFactory,
    ServerCreatedStudyPatientIdNumFactory,
    UserFactory,
)
from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from camcops_server.cc_modules.cc_db import GenericTabletRecordMixin
    from camcops_server.cc_modules.cc_patient import Patient
    from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
    from camcops_server.cc_modules.cc_task import Task

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


class ExtendedTestCase(unittest.TestCase):

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
    Test case that creates a demo Pyramid request that refers to a bare
    in-memory SQLite database.
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

        self.req.matched_route = unittest.mock.Mock()
        self.recipdef = ExportRecipient()

    def tearDown(self) -> None:
        CamcopsRequest.config = self.old_config

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
        fieldnames = get_fieldnames_from_cursor(cursor)
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
    Test case that sets up some useful database records for testing:
    ID numbers, user, group, devices etc and has helper methods for
    creating patients and tasks
    """

    def setUp(self) -> None:
        super().setUp()

        self.set_era("2010-07-07T13:40+0100")

        # Set up groups, users, etc.
        # ... ID number definitions
        idnum_type_nhs = 1
        idnum_type_rio = 2
        idnum_type_study = 3
        self.nhs_iddef = IdNumDefinition(
            which_idnum=idnum_type_nhs,
            description="NHS number",
            short_description="NHS#",
            hl7_assigning_authority="NHS",
            hl7_id_type="NHSN",
        )
        self.dbsession.add(self.nhs_iddef)
        self.rio_iddef = IdNumDefinition(
            which_idnum=idnum_type_rio,
            description="RiO number",
            short_description="RiO",
            hl7_assigning_authority="CPFT",
            hl7_id_type="CPRiO",
        )
        self.dbsession.add(self.rio_iddef)
        self.study_iddef = IdNumDefinition(
            which_idnum=idnum_type_study,
            description="Study number",
            short_description="Study",
        )
        self.dbsession.add(self.study_iddef)
        # ... group
        self.group = Group()
        self.group.name = "testgroup"
        self.group.description = "Test group"
        self.group.upload_policy = "sex AND anyidnum"
        self.group.finalize_policy = "sex AND idnum1"
        self.group.ip_use = IpUse()
        self.dbsession.add(self.group)
        self.dbsession.flush()  # sets PK fields
        GroupFactory.reset_sequence(self.group.id + 1)

        # ... users

        self.user = User.get_system_user(self.dbsession)
        self.user.upload_group_id = self.group.id
        self.req._debugging_user = self.user  # improve our debugging user

        # ... devices
        self.server_device = Device.get_server_device(self.dbsession)
        DeviceFactory.reset_sequence(self.server_device.id + 1)
        self.other_device = DeviceFactory(
            name="other_device",
            friendly_name="Test device that may upload",
            registered_by_user=self.user,
            when_registered_utc=self.era_time_utc,
            camcops_version=CAMCOPS_SERVER_VERSION,
        )
        DeviceFactory.reset_sequence(self.other_device.id + 1)
        # ... export recipient definition (the minimum)
        self.recipdef.primary_idnum = idnum_type_nhs

        self.dbsession.flush()  # sets PK fields
        UserFactory.reset_sequence(self.user.id + 1)

        IdNumDefinitionFactory.reset_sequence(idnum_type_study + 1)

        self.create_tasks()

    def set_era(self, iso_datetime: str) -> None:
        from cardinal_pythonlib.datetimefunc import (
            convert_datetime_to_utc,
            format_datetime,
        )
        from camcops_server.cc_modules.cc_constants import DateFormat

        self.era_time = pendulum.parse(iso_datetime)
        self.era_time_utc = convert_datetime_to_utc(self.era_time)
        self.era = format_datetime(self.era_time, DateFormat.ISO8601)

    def create_patient_with_two_idnums(self) -> "Patient":
        patient = PatientFactory()
        NHSPatientIdNumFactory(patient=patient)
        RioPatientIdNumFactory(patient=patient)

        return patient

    def create_patient_with_one_idnum(self) -> "Patient":
        patient = PatientFactory()
        NHSPatientIdNumFactory(patient=patient)

        return patient

    def create_server_nhs_patient_idnum(self, **kwargs: Any) -> "PatientIdNum":
        return self.create_nhs_patient_idnum(as_server_patient=True, **kwargs)

    def create_server_rio_patient_idnum(self, **kwargs: Any) -> "PatientIdNum":
        return self.create_patient_idnum(
            ServerCreatedRioPatientIdNumFactory, **kwargs
        )

    def create_rio_patient_idnum(self, **kwargs: Any) -> "PatientIdNum":
        return self.create_patient_idnum(RioPatientIdNumFactory, **kwargs)

    def create_server_study_patient_idnum(
        self, **kwargs: Any
    ) -> "PatientIdNum":
        return self.create_patient_idnum(
            ServerCreatedStudyPatientIdNumFactory, **kwargs
        )

    def create_nhs_patient_idnum(
        self, as_server_patient: bool = False, **kwargs: Any
    ) -> "PatientIdNum":
        if as_server_patient:
            return self.create_patient_idnum(
                ServerCreatedNHSPatientIdNumFactory, **kwargs
            )
        return self.create_patient_idnum(NHSPatientIdNumFactory, **kwargs)

    def create_patient_idnum(self, factory, **kwargs) -> "PatientIdNum":
        patient_idnum = factory(**kwargs)

        self.dbsession.add(patient_idnum)
        self.dbsession.commit()

        return patient_idnum

    def create_server_patient(self, **kwargs: Any) -> "Patient":
        return self.create_patient(as_server_patient=True, **kwargs)

    def create_patient(
        self, as_server_patient: bool = False, **kwargs: Any
    ) -> "Patient":
        if as_server_patient:
            patient = ServerCreatedPatientFactory(**kwargs)
        else:
            patient = PatientFactory(**kwargs)

        self.dbsession.add(patient)
        self.dbsession.commit()

        return patient

    def create_tasks(self) -> None:
        # Override in subclass
        pass

    def apply_standard_task_fields(
        self, task: "Task", era: str, device: Device = None
    ) -> None:
        """
        Writes some default values to an SQLAlchemy ORM object representing
        a task.
        """
        self.apply_standard_db_fields(task, era, device=device)
        task.when_created = self.era_time

    def apply_standard_db_fields(
        self,
        obj: "GenericTabletRecordMixin",
        era: str,
        device: Device = None,
    ) -> None:
        """
        Writes some default values to an SQLAlchemy ORM object representing a
        record uploaded from a client (tablet) device.

        Though we use the server device ID.
        """
        if device is None:
            device = self.server_device
        obj._device_id = device.id
        obj._era = era
        obj._group_id = self.group.id
        obj._current = True
        obj._adding_user_id = self.user.id
        obj._when_added_batch_utc = self.era_time_utc

    def create_user(self, **kwargs) -> User:
        user = User()
        user.hashedpw = ""

        for key, value in kwargs.items():
            setattr(user, key, value)

        self.dbsession.add(user)

        return user

    def create_group(self, name: str, **kwargs) -> Group:
        group = Group()
        group.name = name

        for key, value in kwargs.items():
            setattr(group, key, value)

        self.dbsession.add(group)

        return group

    def create_membership(
        self, user: User, group: Group, **kwargs
    ) -> UserGroupMembership:
        ugm = UserGroupMembership(user_id=user.id, group_id=group.id)

        for key, value in kwargs.items():
            setattr(ugm, key, value)

        self.dbsession.add(ugm)

        return ugm

    def tearDown(self) -> None:
        pass


class DemoDatabaseTestCase(BasicDatabaseTestCase):
    """
    Test case that sets up a demonstration CamCOPS database with two tasks of
    each type
    """

    def create_tasks(self) -> None:
        from camcops_server.cc_modules.cc_blob import Blob
        from camcops_server.tasks.photo import Photo
        from camcops_server.cc_modules.cc_task import Task

        patient_with_two_idnums = self.create_patient_with_two_idnums()
        patient_with_one_idnum = self.create_patient_with_one_idnum()

        for cls in Task.all_subclasses_by_tablename():
            t1 = cls()
            t1.id = 1
            self.apply_standard_task_fields(
                t1,
                patient_with_two_idnums._era,
                device=patient_with_two_idnums._device,
            )
            if t1.has_patient:
                t1.patient_id = patient_with_two_idnums.id

            if isinstance(t1, Photo):
                b = Blob()
                b.id = 1
                self.apply_standard_db_fields(
                    b,
                    patient_with_two_idnums._era,
                    device=patient_with_two_idnums._device,
                )
                b.tablename = t1.tablename
                b.tablepk = t1.id
                b.fieldname = "photo_blobid"
                b.filename = "some_picture.png"
                b.mimetype = MimeType.PNG
                b.image_rotation_deg_cw = 0
                b.theblob = DEMO_PNG_BYTES
                self.dbsession.add(b)

                t1.photo_blobid = b.id

            self.dbsession.add(t1)

            t2 = cls()
            t2.id = 2
            self.apply_standard_task_fields(
                t2,
                patient_with_one_idnum._era,
                device=patient_with_one_idnum._device,
            )
            if t2.has_patient:
                t2.patient_id = patient_with_one_idnum.id
            self.dbsession.add(t2)

        self.dbsession.commit()
