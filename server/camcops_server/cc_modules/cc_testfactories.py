#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_testfactories.py

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

**Factory Boy SQL Alchemy test factories.**

"""

from cardinal_pythonlib.datetimefunc import (
    convert_datetime_to_utc,
    format_datetime,
)
import factory
import pendulum

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_user import User


# sqlalchemy_session gets poked in by DemoRequestCase.setUp()
class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    pass


class DeviceFactory(BaseFactory):
    class Meta:
        model = Device

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Test device {n}")


class GroupFactory(BaseFactory):
    class Meta:
        model = Group

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Group {n}")


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    username = factory.Sequence(lambda n: f"user{n}")
    hashedpw = ""


class GenericTabletRecordFactory(BaseFactory):
    default_iso_datetime = "1970-01-01T12:00"

    _device = factory.SubFactory(DeviceFactory)
    _group = factory.SubFactory(GroupFactory)
    _adding_user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def _when_added_exact(self) -> pendulum.DateTime:
        return pendulum.parse(self.default_iso_datetime)

    @factory.lazy_attribute
    def _when_added_batch_utc(self) -> pendulum.DateTime:
        era_time = pendulum.parse(self.default_iso_datetime)
        return convert_datetime_to_utc(era_time)

    @factory.lazy_attribute
    def _era(self) -> str:
        era_time = pendulum.parse(self.default_iso_datetime)
        return format_datetime(era_time, DateFormat.ISO8601)

    @factory.lazy_attribute
    def _current(self) -> bool:
        # _current = True gets ignored for some reason
        return True

    class Meta:
        exclude = ("default_iso_datetime",)
        abstract = True


class PatientFactory(GenericTabletRecordFactory):
    class Meta:
        model = Patient

    id = factory.Sequence(lambda n: n)


class ServerCreatedPatientFactory(PatientFactory):
    @factory.lazy_attribute
    def _device(self) -> Device:
        # Should have been created in BasicDatabaseTestCase.setUp
        return Device.get_server_device(
            ServerCreatedPatientFactory._meta.sqlalchemy_session
        )


class TaskScheduleFactory(BaseFactory):
    class Meta:
        model = TaskSchedule

    group = factory.SubFactory(GroupFactory)


class TaskScheduleItemFactory(BaseFactory):
    class Meta:
        model = TaskScheduleItem

    task_schedule = factory.SubFactory(TaskScheduleFactory)


class PatientTaskScheduleFactory(BaseFactory):
    class Meta:
        model = PatientTaskSchedule

    task_schedule = factory.SubFactory(TaskScheduleFactory)
    # If patient has not been set explicitly,
    # ensure Patient and TaskSchedule end up in the same group
    start_datetime = None
    patient = factory.SubFactory(
        ServerCreatedPatientFactory,
        _group=factory.SelfAttribute("..task_schedule.group"),
    )


class EmailFactory(BaseFactory):
    class Meta:
        model = Email

    @factory.post_generation
    def sent_at_utc(
        self, create: bool, sent_at_utc: pendulum.DateTime, **kwargs
    ) -> None:
        if not create:
            return

        self.sent_at_utc = sent_at_utc

    @factory.post_generation
    def sent(self, create: bool, sent: bool, **kwargs) -> None:
        if not create:
            return

        self.sent = sent


class PatientTaskScheduleEmailFactory(BaseFactory):
    class Meta:
        model = PatientTaskScheduleEmail


class UserGroupMembershipFactory(BaseFactory):
    class Meta:
        model = UserGroupMembership

    @factory.post_generation
    def may_run_reports(
        self, create: bool, may_run_reports: bool, **kwargs
    ) -> None:
        if not create:
            return

        self.may_run_reports = may_run_reports
