#!/usr/bin/env python
# camcops_server/cc_modules/cc_unittest.py

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
"""

import base64
import logging
import unittest
from typing import Type, TYPE_CHECKING

from cardinal_pythonlib.httpconst import MimeType
from cardinal_pythonlib.logs import BraceStyleAdapter
import pendulum
from pendulum import DateTime as Pendulum
from sqlalchemy.orm import Session as SqlASession

from .cc_idnumdef import IdNumDefinition
from .cc_sqlalchemy import Base, make_debug_sqlite_engine
from .cc_version import CAMCOPS_SERVER_VERSION

if TYPE_CHECKING:
    from .cc_db import GenericTabletRecordMixin
    from .cc_task import Task

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
    # Logging in unit tests:
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o  # noqa
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o/15969985#15969985
    # ... but actually, my code below is simpler and works fine.

    @classmethod
    def announce(cls, msg: str) -> None:
        log.info(cls.__module__ + "." + cls.__name__ + ":" + msg)

    def assertIsInstanceOrNone(self, obj: object, cls: Type, msg: str = None):
        if obj is None:
            return
        self.assertIsInstance(obj, cls, msg)


class DemoRequestTestCase(ExtendedTestCase):
    def setUp(self) -> None:
        self.announce("setUp")
        from sqlalchemy.orm.session import sessionmaker
        from camcops_server.cc_modules.cc_request import get_unittest_request
        from camcops_server.cc_modules.cc_recipdef import RecipientDefinition

        # Create SQLite in-memory database
        self.engine = make_debug_sqlite_engine(echo=False)
        self.dbsession = sessionmaker()(bind=self.engine)  # type: SqlASession

        self.req = get_unittest_request(self.dbsession)
        self.recipdef = RecipientDefinition()


class DemoDatabaseTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()
        from cardinal_pythonlib.datetimefunc import (
            convert_datetime_to_utc,
            format_datetime,
        )
        from camcops_server.cc_modules.cc_blob import Blob
        from camcops_server.cc_modules.cc_constants import DateFormat
        from camcops_server.cc_modules.cc_device import Device
        from camcops_server.cc_modules.cc_group import Group
        from camcops_server.cc_modules.cc_patient import Patient
        from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
        from camcops_server.cc_modules.cc_task import Task
        from camcops_server.cc_modules.cc_user import User
        from camcops_server.tasks.photo import Photo

        Base.metadata.create_all(self.engine)

        self.era_time = pendulum.parse("2010-07-07T13:40+0100")
        self.era_time_utc = convert_datetime_to_utc(self.era_time)
        self.era = format_datetime(self.era_time, DateFormat.ISO8601)

        # Set up groups, users, etc.
        # ... ID number definitions
        iddef1 = IdNumDefinition(which_idnum=1,
                                 description="NHS number",
                                 short_description="NHS#",
                                 hl7_assigning_authority="NHS",
                                 hl7_id_type="NHSN")
        self.dbsession.add(iddef1)
        iddef2 = IdNumDefinition(which_idnum=2,
                                 description="RiO number",
                                 short_description="RiO",
                                 hl7_assigning_authority="CPFT",
                                 hl7_id_type="CPFT_RiO")
        self.dbsession.add(iddef2)
        # ... group
        self.group = Group()
        self.group.name = "testgroup"
        self.group.description = "Test group"
        self.group.upload_policy = "sex AND anyidnum"
        self.group.finalize_policy = "sex AND idnum1"
        self.dbsession.add(self.group)
        self.dbsession.flush()  # sets PK fields

        # ... users

        self.user = User.get_system_user(self.dbsession)
        self.user.upload_group_id = self.group.id
        self.req._debugging_user = self.user  # improve our debugging user

        # ... devices
        self.server_device = Device.get_server_device(self.dbsession)
        self.other_device = Device()
        self.other_device.name = "other_device"
        self.other_device.friendly_name = "Test device that may upload"
        self.other_device.registered_by_user = self.user
        self.other_device.when_registered_utc = self.era_time_utc
        self.other_device.camcops_version = CAMCOPS_SERVER_VERSION
        self.dbsession.add(self.other_device)

        self.dbsession.flush()  # sets PK fields

        # Populate database with two of everything
        p1 = Patient()
        p1.id = 1
        self._apply_standard_db_fields(p1)
        p1.forename = "Forename1"
        p1.surname = "Surname1"
        p1.dob = pendulum.parse("1950-01-01")
        self.dbsession.add(p1)
        p1_idnum1 = PatientIdNum()
        p1_idnum1.id = 1
        self._apply_standard_db_fields(p1_idnum1)
        p1_idnum1.patient_id = p1.id
        p1_idnum1.which_idnum = iddef1.which_idnum
        p1_idnum1.idnum_value = 333
        self.dbsession.add(p1_idnum1)
        p1_idnum2 = PatientIdNum()
        p1_idnum2.id = 2
        self._apply_standard_db_fields(p1_idnum2)
        p1_idnum2.patient_id = p1.id
        p1_idnum2.which_idnum = iddef2.which_idnum
        p1_idnum2.idnum_value = 444
        self.dbsession.add(p1_idnum2)

        p2 = Patient()
        p2.id = 2
        self._apply_standard_db_fields(p2)
        p2.forename = "Forename2"
        p2.surname = "Surname2"
        p2.dob = pendulum.parse("1975-12-12")
        self.dbsession.add(p2)
        p2_idnum1 = PatientIdNum()
        p2_idnum1.id = 3
        self._apply_standard_db_fields(p2_idnum1)
        p2_idnum1.patient_id = p2.id
        p2_idnum1.which_idnum = iddef1.which_idnum
        p2_idnum1.idnum_value = 555
        self.dbsession.add(p2_idnum1)

        self.dbsession.flush()

        for cls in Task.all_subclasses_by_tablename():
            t1 = cls()
            t1.id = 1
            self._apply_standard_task_fields(t1)
            if t1.has_patient:
                t1.patient_id = p1.id

            if isinstance(t1, Photo):
                b = Blob()
                b.id = 1
                self._apply_standard_db_fields(b)
                b.tablename = t1.tablename
                b.tablepk = t1.id
                b.fieldname = 'photo_blobid'
                b.filename = "some_picture.png"
                b.mimetype = MimeType.PNG
                b.image_rotation_deg_cw = 0
                b.theblob = DEMO_PNG_BYTES
                self.dbsession.add(b)

                t1.photo_blobid = b.id

            self.dbsession.add(t1)

            t2 = cls()
            t2.id = 2
            self._apply_standard_task_fields(t2)
            if t2.has_patient:
                t2.patient_id = p2.id
            self.dbsession.add(t2)

        self.dbsession.commit()

    def _apply_standard_task_fields(self, task: "Task") -> None:
        self._apply_standard_db_fields(task)
        task.when_created = self.era_time

    def _apply_standard_db_fields(self,
                                  obj: "GenericTabletRecordMixin") -> None:
        obj._device_id = self.server_device.id
        obj._era = self.era
        obj._group_id = self.group.id
        obj._current = True
        obj._adding_user_id = self.user.id
        obj._when_added_batch_utc = self.era_time_utc

    def tearDown(self) -> None:
        pass
