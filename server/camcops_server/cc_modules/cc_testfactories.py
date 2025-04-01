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

from typing import Any, cast, Optional, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import (
    convert_datetime_to_utc,
    format_datetime,
)
import factory
from faker import Faker
import pendulum

from camcops_server.cc_modules.cc_blob import Blob
from camcops_server.cc_modules.cc_constants import DateFormat, ERA_NOW
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_dirtytables import DirtyTable
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_idnumdef import IdNumDefinition
from camcops_server.cc_modules.cc_ipuse import IpUse
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_specialnote import SpecialNote
from camcops_server.cc_modules.cc_testproviders import register_all_providers
from camcops_server.cc_modules.cc_taskschedule import (
    PatientTaskSchedule,
    PatientTaskScheduleEmail,
    TaskSchedule,
    TaskScheduleItem,
)
from camcops_server.cc_modules.cc_user import User

if TYPE_CHECKING:
    from factory.builder import Resolver
    from camcops_server.cc_modules.cc_request import CamcopsRequest


# Avoid any ID clashes with objects not created with factories
ID_OFFSET = 1000
RIO_ID_OFFSET = 10000
STUDY_ID_OFFSET = 5000


class Fake:
    # Factory Boy has its own interface to Faker (factory.Faker()). This
    # takes a function to be called at object generation time and as far as I
    # can tell this doesn't support being able to create fake data based on
    # other fake attributes such as notes for a patient. You can work
    # around this by adding a lot of logic to the factories. To me it makes
    # sense to keep the factories simple and do as much as possible of the
    # content generation in the providers. So we call Faker directly instead.
    en_gb = Faker("en_GB")  # For UK postcodes, phone numbers etc
    en_us = Faker("en_US")  # en_GB gives Lorem ipsum for pad words.


register_all_providers(Fake.en_gb)


# sqlalchemy_session gets poked in by DemoRequestCase.setUp()
class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session_persistence = "commit"


class DeviceFactory(BaseFactory):
    class Meta:
        model = Device

    id = factory.Sequence(lambda n: n + ID_OFFSET)
    name = factory.Sequence(lambda n: f"test-device-{n + ID_OFFSET}")


class IpUseFactory(BaseFactory):
    class Meta:
        model = IpUse

    clinical = factory.LazyFunction(Fake.en_gb.pybool)
    commercial = factory.LazyFunction(Fake.en_gb.pybool)
    educational = factory.LazyFunction(Fake.en_gb.pybool)
    research = factory.LazyFunction(Fake.en_gb.pybool)


class GroupFactory(BaseFactory):
    class Meta:
        model = Group

    id = factory.Sequence(lambda n: n + ID_OFFSET)
    name = factory.Sequence(lambda n: f"Group {n + ID_OFFSET}")
    ip_use = factory.SubFactory(IpUseFactory)


class AnyIdNumGroupFactory(GroupFactory):
    upload_policy = "sex and anyidnum"
    finalize_policy = "sex and anyidnum"


class UserFactory(BaseFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    hashedpw = ""

    @factory.post_generation
    def password(
        obj: User,
        create: bool,
        password: Optional[str],
        request: "CamcopsRequest" = None,
        **kwargs: Any,
    ) -> None:
        if not create:
            return

        if password is None:
            return

        assert request is not None

        obj.set_password(request, password)


class GenericTabletRecordFactory(BaseFactory):
    class Meta:
        exclude = ("default_iso_datetime",)
        abstract = True

    default_iso_datetime = "1970-01-01T12:00"

    _pk = factory.Sequence(lambda n: n + ID_OFFSET)
    _device = factory.SubFactory(DeviceFactory)
    _group = factory.SubFactory(AnyIdNumGroupFactory)
    _adding_user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def _when_added_exact(obj: "Resolver") -> pendulum.DateTime:
        datetime = cast(
            pendulum.DateTime, pendulum.parse(obj.default_iso_datetime)
        )

        return datetime

    @factory.lazy_attribute
    def _when_added_batch_utc(obj: "Resolver") -> pendulum.DateTime:
        era_time = pendulum.parse(obj.default_iso_datetime)
        return convert_datetime_to_utc(era_time)  # type: ignore[arg-type]

    @factory.lazy_attribute
    def _era(obj: "Resolver") -> str:
        era_time = pendulum.parse(obj.default_iso_datetime)
        return format_datetime(era_time, DateFormat.ISO8601)  # type: ignore[arg-type]  # noqa: E501

    @factory.lazy_attribute
    def _current(obj: "Resolver") -> bool:
        # _current = True gets ignored for some reason
        return True

    @factory.lazy_attribute
    def when_last_modified(obj: "Resolver") -> str:
        era_time = pendulum.parse(obj.default_iso_datetime)
        return format_datetime(era_time, DateFormat.ISO8601)  # type: ignore[arg-type]  # noqa: E501


class PatientFactory(GenericTabletRecordFactory):
    class Meta:
        model = Patient

    id = factory.Sequence(lambda n: n + ID_OFFSET)
    sex = factory.LazyFunction(Fake.en_gb.sex)
    dob = factory.LazyFunction(Fake.en_gb.consistent_date_of_birth)
    address = factory.LazyFunction(Fake.en_gb.address)
    gp = factory.LazyFunction(Fake.en_gb.name)
    other = factory.LazyFunction(Fake.en_us.paragraph)
    email = factory.LazyFunction(Fake.en_gb.email)

    @factory.lazy_attribute
    def forename(obj: "Resolver") -> str:
        return Fake.en_gb.forename(obj.sex)

    surname = factory.LazyFunction(Fake.en_gb.last_name)


class ServerCreatedPatientFactory(PatientFactory):
    @factory.lazy_attribute
    def _device(obj: "Resolver") -> Device:
        # May have been created in BasicDatabaseTestCase.setUp
        return Device.get_server_device(
            ServerCreatedPatientFactory._meta.sqlalchemy_session
        )

    @factory.lazy_attribute
    def _era(obj: "Resolver") -> str:
        return ERA_NOW


class IdNumDefinitionFactory(BaseFactory):
    class Meta:
        model = IdNumDefinition

    which_idnum = factory.Sequence(lambda n: n + ID_OFFSET)


class NHSIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "NHS number"
    short_description = "NHS#"
    hl7_assigning_authority = "NHS"
    hl7_id_type = "NHSN"
    validation_method = "uk_nhs_number"


class StudyIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "Study number"
    short_description = "Study"


class RioIdNumDefinitionFactory(IdNumDefinitionFactory):
    description = "RiO number"
    short_description = "RiO"
    hl7_assigning_authority = "CPFT"
    hl7_id_type = "CPRiO"


class PatientIdNumFactory(GenericTabletRecordFactory):
    class Meta:
        model = PatientIdNum

    id = factory.Sequence(lambda n: n + ID_OFFSET)
    patient = factory.SubFactory(PatientFactory)
    patient_id = factory.SelfAttribute("patient.id")
    _group = factory.SelfAttribute("patient._group")
    _device = factory.SelfAttribute("patient._device")


class NHSPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("iddef",)

    iddef = factory.SubFactory(NHSIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("iddef.which_idnum")
    idnum_value = factory.LazyFunction(Fake.en_gb.nhs_number)


class RioPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("iddef",)

    iddef = factory.SubFactory(RioIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("iddef.which_idnum")
    idnum_value = factory.Sequence(lambda n: n + RIO_ID_OFFSET)


class StudyPatientIdNumFactory(PatientIdNumFactory):
    class Meta:
        exclude = PatientIdNumFactory._meta.exclude + ("iddef",)

    iddef = factory.SubFactory(StudyIdNumDefinitionFactory)

    which_idnum = factory.SelfAttribute("iddef.which_idnum")
    idnum_value = factory.Sequence(lambda n: n + STUDY_ID_OFFSET)


class ServerCreatedPatientIdNumFactory(PatientIdNumFactory):
    patient = factory.SubFactory(ServerCreatedPatientFactory)

    @factory.lazy_attribute
    def _device(obj: "Resolver") -> Device:
        # Should have been created in BasicDatabaseTestCase.setUp
        return Device.get_server_device(
            ServerCreatedPatientIdNumFactory._meta.sqlalchemy_session
        )

    @factory.lazy_attribute
    def _era(obj: "Resolver") -> str:
        return ERA_NOW


class ServerCreatedNHSPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, NHSPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + NHSPatientIdNumFactory._meta.exclude
        )


class ServerCreatedRioPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, RioPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + RioPatientIdNumFactory._meta.exclude
        )


class ServerCreatedStudyPatientIdNumFactory(
    ServerCreatedPatientIdNumFactory, StudyPatientIdNumFactory
):
    class Meta:
        exclude = (
            ServerCreatedPatientIdNumFactory._meta.exclude
            + StudyPatientIdNumFactory._meta.exclude
        )


class TaskScheduleFactory(BaseFactory):
    class Meta:
        model = TaskSchedule

    group = factory.SubFactory(GroupFactory)
    name = factory.Sequence(lambda n: f"Schedule {n + ID_OFFSET}")


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

    # Although sent and sent_at_utc are columns, they are not keyword
    # arguments to Email's constructor so they are populated after the object
    # has been created. For some reason 'sent' needs to be set explicitly
    # when creating the factory even though the default should be False. Might
    # be a SQLite thing.
    @factory.post_generation
    def sent_at_utc(
        obj: Email, create: bool, sent_at_utc: pendulum.DateTime, **kwargs: Any
    ) -> None:
        if not create:
            return

        obj.sent_at_utc = sent_at_utc

    @factory.post_generation
    def sent(obj: Email, create: bool, sent: bool, **kwargs: Any) -> None:
        if not create:
            return

        obj.sent = sent


class PatientTaskScheduleEmailFactory(BaseFactory):
    class Meta:
        model = PatientTaskScheduleEmail

    patient_task_schedule = factory.SubFactory(
        PatientTaskScheduleFactory,
    )
    email = factory.SubFactory(EmailFactory, sent=True)


class UserGroupMembershipFactory(BaseFactory):
    class Meta:
        model = UserGroupMembership


class BlobFactory(GenericTabletRecordFactory):
    class Meta:
        model = Blob

    id = factory.Sequence(lambda n: n + ID_OFFSET)


class DirtyTableFactory(BaseFactory):
    class Meta:
        model = DirtyTable


class SpecialNoteFactory(BaseFactory):
    class Meta:
        model = SpecialNote

    @classmethod
    def create(cls, *args: Any, **kwargs: Any) -> SpecialNote:
        task = kwargs.pop("task", None)
        if task is not None:
            if "task_id" in kwargs:
                raise TypeError(
                    "Both 'task' and 'task_id' keyword arguments "
                    f"unexpectedly passed to {cls.__name__}. Use one or the "
                    "other."
                )
            kwargs["task_id"] = task.id

            if "basetable" not in kwargs:
                kwargs["basetable"] = task.__tablename__
            if "device_id" not in kwargs:
                kwargs["device_id"] = task._device.id
            if "era" not in kwargs:
                kwargs["era"] = task._era

        return super().create(*args, **kwargs)


class ExportRecipientFactory(BaseFactory):
    class Meta:
        exclude = ("iddef",)
        model = ExportRecipient

    id = factory.Sequence(lambda n: n + ID_OFFSET)

    iddef = factory.SubFactory(IdNumDefinitionFactory)
    primary_idnum = factory.SelfAttribute("iddef.which_idnum")
