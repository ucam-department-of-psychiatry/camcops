#!/usr/bin/env python
# camcops_server/cc_modules/cc_audit.py

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

from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Integer, UnicodeText

from .cc_sqla_coltypes import (
    AuditSourceColType,
    IPAddressColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest


# =============================================================================
# AuditEntry
# =============================================================================

class AuditEntry(Base):
    __tablename__ = "_security_audit"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="Arbitrary primary key"
    )
    when_access_utc = Column(
        "when_access_utc", DateTime,
        nullable=False, index=True,
        comment="Date/time of access (UTC)"
    )
    source = Column(
        "source", AuditSourceColType,
        nullable=False,
        comment="Source (e.g. tablet, webviewer)"
    )
    remote_addr = Column(
        "remote_addr", IPAddressColType,
        comment="IP address of the remote computer"
    )
    user_id = Column(
        "user_id", Integer, ForeignKey("_security_users.id"),
        comment="ID of user, where applicable"
    )
    user = relationship("User")
    device_id = Column(
        "device_id", Integer, ForeignKey("_security_devices.id"),
        comment="Device ID, where applicable"
    )
    device = relationship("Device")
    table_name = Column(
        "table_name", TableNameColType,
        comment="Table involved, where applicable"
    )
    server_pk = Column(
        "server_pk", Integer,
        comment="Server PK (table._pk), where applicable"
    )
    patient_server_pk = Column(
        "patient_server_pk", Integer,
        comment="Server PK of the patient (patient._pk) concerned, or "
                "NULL if not applicable"
    )
    details = Column(
        "details", UnicodeText,
        comment="Details of the access"
    )


# =============================================================================
# Audit function
# =============================================================================

def audit(req: "CamcopsRequest",
          details: str,
          patient_server_pk: int = None,
          table: str = None,
          server_pk: int = None,
          device_id: int = None,
          remote_addr: str = None,
          user_id: int = None,
          from_console: bool = False,
          from_dbclient: bool = False) -> None:
    """Write an entry to the audit log."""
    dbsession = req.dbsession
    if not remote_addr:
        remote_addr = req.remote_addr if req else None
    if not user_id:
        ccsession = req.camcops_session
        if ccsession.user_id is not None:
            user_id = ccsession.user_id
    if from_console:
        source = "console"
    elif from_dbclient:
        source = "tablet"
    else:
        source = "webviewer"
    now = req.now_utc
    entry = AuditEntry(
        when_access_utc=now,
        source=source,
        remote_addr=remote_addr,
        user_id=user_id,
        device_id=device_id,
        table_name=table,
        server_pk=server_pk,
        patient_server_pk=patient_server_pk,
        details=details
    )
    dbsession.add(entry)
