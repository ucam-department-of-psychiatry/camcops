"""
camcops_server/cc_modules/cc_taskschedule.py

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

"""

import logging
from typing import Any, List, Optional, Tuple, TYPE_CHECKING
from urllib.parse import urlencode, urlunsplit

from cardinal_pythonlib.uriconst import UriSchemes
from pendulum import DateTime as Pendulum, Duration

from sqlalchemy import cast, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, UnicodeText

from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_formatter import SafeFormatter
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_pyramid import Routes
from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_sqla_coltypes import (
    EmailAddressColType,
    JsonColType,
    PendulumDateTimeAsIsoTextColType,
    PendulumDurationAsIsoTextColType,
    TableNameColType,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    tablename_to_task_class_dict,
)
from camcops_server.cc_modules.cc_taskcollection import (
    TaskFilter,
    TaskCollection,
    TaskSortMethod,
)


if TYPE_CHECKING:
    from sqlalchemy.sql.elements import Cast
    from camcops_server.cc_modules.cc_request import CamcopsRequest

log = logging.getLogger(__name__)


# =============================================================================
# ScheduledTaskInfo
# =============================================================================


class ScheduledTaskInfo(object):
    """
    Simple representation of a scheduled task (which may also contain the
    actual completed task, in its ``task`` member, if there is one).
    """

    def __init__(
        self,
        shortname: str,
        tablename: str,
        is_anonymous: bool,
        task: Optional[Task] = None,
        start_datetime: Optional[Pendulum] = None,
        end_datetime: Optional[Pendulum] = None,
    ) -> None:
        self.shortname = shortname
        self.tablename = tablename
        self.is_anonymous = is_anonymous
        self.task = task
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    @property
    def due_now(self) -> bool:
        """
        Are we in the range [start_datetime, end_datetime)?
        """
        if not self.start_datetime or not self.end_datetime:
            return False
        return self.start_datetime <= Pendulum.now() < self.end_datetime

    @property
    def is_complete(self) -> bool:
        """
        Returns whether its associated task is complete..
        """
        if not self.task:
            return False
        return self.task.is_complete()

    @property
    def is_identifiable_and_incomplete(self) -> bool:
        """
        If this is an anonymous task, returns ``False``.
        If this is an identifiable task, returns ``not is_complete``.
        """
        if self.is_anonymous:
            return False
        return not self.is_complete

    @property
    def due_now_identifiable_and_incomplete(self) -> bool:
        """
        Is this task currently due, identifiable, and incomplete?
        """
        return self.due_now and self.is_identifiable_and_incomplete


# =============================================================================
# PatientTaskSchedule
# =============================================================================


class PatientTaskSchedule(Base):
    """
    Joining table that associates a patient with a task schedule
    """

    __tablename__ = "_patient_task_schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_pk: Mapped[int] = mapped_column(ForeignKey("patient._pk"))
    schedule_id: Mapped[int] = mapped_column(ForeignKey("_task_schedule.id"))
    start_datetime: Mapped[Optional[Pendulum]] = mapped_column(
        PendulumDateTimeAsIsoTextColType,
        comment=(
            "Schedule start date for the patient. Due from/within "
            "durations for a task schedule item are relative to this."
        ),
    )
    settings: Mapped[Optional[Any]] = mapped_column(
        JsonColType,
        comment="Task-specific settings for this patient",
    )

    patient = relationship("Patient", back_populates="task_schedules")
    task_schedule: Mapped["TaskSchedule"] = relationship(
        back_populates="patient_task_schedules",
        cascade_backrefs=False,
    )

    emails = relationship(
        "PatientTaskScheduleEmail",
        back_populates="patient_task_schedule",
        cascade="all, delete",
        cascade_backrefs=False,
    )

    def get_list_of_scheduled_tasks(
        self, req: "CamcopsRequest"
    ) -> List[ScheduledTaskInfo]:
        """
        Tasks scheduled for this patient.
        """

        task_list = []

        task_class_lookup = tablename_to_task_class_dict()

        for tsi in self.task_schedule.items:
            start_datetime = None
            end_datetime = None
            task = None

            if self.start_datetime is not None:
                start_datetime = self.start_datetime.add(
                    days=tsi.due_from.days
                )
                end_datetime = self.start_datetime.add(days=tsi.due_by.days)

                task = self.find_scheduled_task(
                    req, tsi, start_datetime, end_datetime
                )

            task_class = task_class_lookup[tsi.task_table_name]

            task_list.append(
                ScheduledTaskInfo(
                    task_class.shortname,
                    tsi.task_table_name,
                    is_anonymous=task_class.is_anonymous,
                    task=task,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                )
            )

        return task_list

    def find_scheduled_task(
        self,
        req: "CamcopsRequest",
        tsi: "TaskScheduleItem",
        start_datetime: Pendulum,
        end_datetime: Pendulum,
    ) -> Optional[Task]:
        """
        Returns the most recently uploaded task that matches the patient (by
        any ID number, i.e. via OR), task type and timeframe
        """
        taskfilter = TaskFilter()
        for idnum in self.patient.idnums:
            idnum_ref = IdNumReference(
                which_idnum=idnum.which_idnum, idnum_value=idnum.idnum_value
            )
            taskfilter.idnum_criteria.append(idnum_ref)

        taskfilter.task_types = [tsi.task_table_name]

        taskfilter.start_datetime = start_datetime
        taskfilter.end_datetime = end_datetime

        # TODO: Improve error reporting
        # Shouldn't happen in normal operation as the task schedule item form
        # validation will ensure the dates are correct.
        # However, it's quite easy to write tests with unintentionally
        # inconsistent dates.
        # If we don't assert this here, we get a more cryptic assertion
        # failure later:
        #
        # cc_taskcollection.py _fetch_tasks_from_indexes()
        # assert self._all_indexes is not None
        assert not taskfilter.dates_inconsistent()

        collection = TaskCollection(
            req=req,
            taskfilter=taskfilter,
            sort_method_global=TaskSortMethod.CREATION_DATE_DESC,
        )

        if len(collection.all_tasks) > 0:
            return collection.all_tasks[0]

        return None

    def email_body(self, req: "CamcopsRequest") -> str:
        """
        Body content (HTML) for an e-mail to the patient -- the schedule's
        template, populated with patient-specific information.
        """
        template_dict = dict(
            access_key=self.patient.uuid_as_proquint,
            android_launch_url=self.launch_url(req, UriSchemes.HTTPS),
            ios_launch_url=self.launch_url(req, "camcops"),
            forename=self.patient.forename,
            server_url=req.route_url(Routes.CLIENT_API),
            surname=self.patient.surname,
        )

        formatter = TaskScheduleEmailTemplateFormatter()
        return formatter.format(
            self.task_schedule.email_template, **template_dict
        )

    def launch_url(self, req: "CamcopsRequest", scheme: str) -> str:
        # Matches intent-filter in AndroidManifest.xml
        # And CFBundleURLSchemes in Info.plist

        # iOS doesn't care about these:
        netloc = "ucam-department-of-psychiatry.github.io"
        path = "/camcops/register"
        fragment = ""

        query_dict = {
            "default_single_user_mode": "true",
            "default_server_location": req.route_url(Routes.CLIENT_API),
            "default_access_key": self.patient.uuid_as_proquint,
        }
        query = urlencode(query_dict)

        return urlunsplit((scheme, netloc, path, query, fragment))

    @property
    def email_sent(self) -> bool:
        """
        Has an e-mail been sent to the patient for this schedule?
        """
        return any(e.email.sent for e in self.emails)


def task_schedule_item_sort_order() -> Tuple["Cast", "Cast"]:
    """
    Returns a tuple of sorting functions for use with SQLAlchemy ORM queries,
    to sort task schedule items.

    The durations are currently stored as seconds e.g. P0Y0MT2594592000.0S
    and the seconds aren't zero padded, so we need to do some processing
    to get them in the order we want.

    This will fail if durations ever get stored any other way.

    Note that MySQL does not permit "CAST(... AS DOUBLE)" or "CAST(... AS
    FLOAT)"; you need to use NUMERIC or DECIMAL. However, this raises a warning
    when running self-tests under SQLite: "SAWarning: Dialect sqlite+pysqlite
    does *not* support Decimal objects natively, and SQLAlchemy must convert
    from floating point - rounding errors and other issues may occur. Please
    consider storing Decimal numbers as strings or integers on this platform
    for lossless storage."
    """
    due_from_order = cast(func.substr(TaskScheduleItem.due_from, 7), Numeric())
    due_by_order = cast(func.substr(TaskScheduleItem.due_by, 7), Numeric())

    return due_from_order, due_by_order


# =============================================================================
# Emails sent to patient
# =============================================================================


class PatientTaskScheduleEmail(Base):
    """
    Represents an email send to a patient for a particular task schedule.
    """

    __tablename__ = "_patient_task_schedule_email"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Arbitrary primary key",
    )
    patient_task_schedule_id: Mapped[int] = mapped_column(
        ForeignKey(PatientTaskSchedule.id),
        comment=(
            f"FK to {PatientTaskSchedule.__tablename__}."
            f"{PatientTaskSchedule.id.name}"
        ),
    )
    email_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Email.id),
        comment=f"FK to {Email.__tablename__}.{Email.id.name}",
    )

    patient_task_schedule = relationship(
        PatientTaskSchedule,
        back_populates="emails",
        cascade_backrefs=False,
    )
    email = relationship(Email, cascade="all, delete")


# =============================================================================
# Task schedule
# =============================================================================


class TaskSchedule(Base):
    """
    A named collection of task schedule items
    """

    __tablename__ = "_task_schedule"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Arbitrary primary key",
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey(Group.id),
        comment="FK to {}.{}".format(Group.__tablename__, Group.id.name),
    )

    name: Mapped[Optional[str]] = mapped_column(UnicodeText, comment="name")

    email_subject: Mapped[str] = mapped_column(
        UnicodeText,
        comment="email subject",
        default="",
    )
    email_template: Mapped[str] = mapped_column(
        UnicodeText,
        comment="email template",
        default="",
    )
    email_from: Mapped[Optional[str]] = mapped_column(
        EmailAddressColType, comment="Sender's e-mail address"
    )
    email_cc: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="Send a carbon copy of the email to these addresses",
    )
    email_bcc: Mapped[Optional[str]] = mapped_column(
        UnicodeText,
        comment="Send a blind carbon copy of the email to these addresses",
    )

    items: Mapped[list["TaskScheduleItem"]] = relationship(
        back_populates="task_schedule",
        order_by=task_schedule_item_sort_order,
        cascade="all, delete",
        cascade_backrefs=False,
    )

    group = relationship(Group)

    patient_task_schedules = relationship(
        "PatientTaskSchedule",
        back_populates="task_schedule",
        cascade="all, delete",
        cascade_backrefs=False,
    )

    def user_may_edit(self, req: "CamcopsRequest") -> bool:
        """
        May the current user edit this schedule?
        """
        return req.user.may_administer_group(self.group_id)


class TaskScheduleItem(Base):
    """
    An individual item in a task schedule
    """

    __tablename__ = "_task_schedule_item"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Arbitrary primary key",
    )

    schedule_id: Mapped[int] = mapped_column(
        ForeignKey(TaskSchedule.id),
        comment="FK to {}.{}".format(
            TaskSchedule.__tablename__, TaskSchedule.id.name
        ),
    )

    task_table_name: Mapped[Optional[str]] = mapped_column(
        TableNameColType,
        index=True,
        comment="Table name of the task's base table",
    )

    due_from: Mapped[Optional[Duration]] = mapped_column(
        PendulumDurationAsIsoTextColType,
        comment=(
            "Relative time from the start date by which the task may be "
            "started"
        ),
    )

    due_by: Mapped[Optional[Duration]] = mapped_column(
        PendulumDurationAsIsoTextColType,
        comment=(
            "Relative time from the start date by which the task must be "
            "completed"
        ),
    )

    task_schedule = relationship(
        "TaskSchedule", back_populates="items", cascade_backrefs=False
    )

    @property
    def task_shortname(self) -> str:
        """
        Short name of the task being scheduled.
        """
        task_class_lookup = tablename_to_task_class_dict()

        return task_class_lookup[self.task_table_name].shortname

    @property
    def due_within(self) -> Optional[Duration]:
        """
        Returns the "due within" property, e.g. "due within 7 days (of being
        scheduled to start)". This is calculated from due_from and due_by.
        """
        if self.due_by is None:
            # Should not be possible if created through the form
            return None

        if self.due_from is None:
            return self.due_by

        return self.due_by - self.due_from

    def description(self, req: "CamcopsRequest") -> str:
        """
        Description of this schedule item -- which task, due when.
        """
        _ = req.gettext

        if self.due_from is None:
            # Should not be possible if created through the form
            due_days = "?"
        else:
            due_days = str(self.due_from.in_days())

        return _("{task_name} @ {due_days} days").format(
            task_name=self.task_shortname, due_days=due_days
        )


class TaskScheduleEmailTemplateFormatter(SafeFormatter):
    """
    Safe template formatter for task schedule e-mails.
    """

    def __init__(self) -> None:
        super().__init__(
            [
                "access_key",
                "android_launch_url",
                "forename",
                "ios_launch_url",
                "server_url",
                "surname",
            ]
        )
