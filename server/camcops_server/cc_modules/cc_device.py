#!/usr/bin/env python
# camcops_server/cc_modules/cc_device.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Optional, TYPE_CHECKING

from cardinal_pythonlib.classes import classproperty
from sqlalchemy.orm import Query, relationship, Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, Text

from .cc_report import Report
from .cc_unittest import unit_test_ignore
from .cc_sqla_coltypes import (
    DeviceNameColType,
    SemanticVersionColType,
)
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest


# =============================================================================
# Device class
# =============================================================================

class Device(Base):
    """Represents a tablet device."""
    __tablename__ = "_security_devices"
    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True,
        comment="ID of the source tablet device"
    )
    name = Column(
        "name", DeviceNameColType,
        unique=True, index=True,
        comment="Short cryptic unique name of the source tablet device"
    )
    registered_by_user_id = Column(
        "registered_by_user_id", Integer, ForeignKey("_security_users.id"),
        comment="ID of user that registered the device"
    )
    registered_by_user = relationship("User",
                                      foreign_keys=[registered_by_user_id])
    when_registered_utc = Column(
        "when_registered_utc", DateTime,
        comment="Date/time when the device was registered (UTC)"
    )
    friendly_name = Column(
        "friendly_name", Text,
        comment="Friendly name of the device"
    )
    camcops_version = Column(
        "camcops_version", SemanticVersionColType,
        comment="CamCOPS version number on the tablet device"
    )
    last_upload_batch_utc = Column(
        "last_upload_batch_utc", DateTime,
        comment="Date/time when the device's last upload batch started (UTC)"
    )
    ongoing_upload_batch_utc = Column(
        "ongoing_upload_batch_utc", DateTime,
        comment="Date/time when the device's ongoing upload batch "
                "started (UTC)"
    )
    uploading_user_id = Column(
        "uploading_user_id", Integer, ForeignKey("_security_users.id"),
        comment="ID of user in the process of uploading right now"
    )
    uploading_user = relationship("User", foreign_keys=[uploading_user_id])
    currently_preserving = Column(
        "currently_preserving", Boolean,
        comment="Preservation currently in progress"
    )

    @classmethod
    def get_device_by_name(cls, dbsession: SqlASession,
                           device_name: str) -> Optional['Device']:
        if not device_name:
            return None
        device = dbsession.query(cls)\
            .filter(cls.name == device_name)\
            .first()  # type: Optional[Device]
        return device

    def get_friendly_name(self) -> str:
        """Get device friendly name (or failing that, device name)."""
        if self.friendly_name is None:
            return self.name
        return self.friendly_name

    def get_friendly_name_and_id(self) -> str:
        """Get device ID with friendly name (or failing that, device name)."""
        if self.friendly_name is None:
            return self.name
        return "{} (device# {}, {})".format(self.name,
                                            self.id,
                                            self.friendly_name)

    def get_id(self) -> int:
        """Get device ID."""
        return self.id

    def is_valid(self) -> bool:
        """
        Valid device (having been instantiated with Device(device_id), i.e.
        is it in the database?
        """
        return self.id is not None


# =============================================================================
# Reports
# =============================================================================

class DeviceReport(Report):
    """Report to show registered devices."""
    @classproperty
    def report_id(cls) -> str:
        return "devices"

    @classproperty
    def title(cls) -> str:
        return "(Server) Devices registered with the server"

    def get_query(self, req: "CamcopsRequest") -> Query:
        dbsession = req.dbsession
        query = dbsession.query(Device.id,
                                Device.name,
                                Device.registered_by_user_id,
                                Device.when_registered_utc,
                                Device.friendly_name,
                                Device.camcops_version,
                                Device.last_upload_batch_utc)\
            .order_by(Device.id)
        return query


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_device(d: Device) -> None:
    """Unit tests for Device class."""
    # skip make_tables
    unit_test_ignore("", d.get_friendly_name)
    unit_test_ignore("", d.get_friendly_name_and_id)
    unit_test_ignore("", d.get_id)


def ccdevice_unit_tests(dbsession: SqlASession) -> None:
    """Unit tests for cc_device module."""
    device = dbsession.query(Device)\
        .order_by(Device.id)\
        .first()  # type: Optional[Device]
    if device is None:
        device = Device()
    unit_tests_device(device)

    unit_test_ignore("", get_device_filter_dropdown)
