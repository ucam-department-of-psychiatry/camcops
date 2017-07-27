#!/usr/bin/env python
# camcops_server/cc_modules/cc_audit.py

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

from .cc_pls import pls

# =============================================================================
# Constants
# =============================================================================

SECURITY_AUDIT_TABLENAME = "_security_audit"
SECURITY_AUDIT_FIELDSPECS = [
    dict(name="id", cctype="INT_UNSIGNED", pk=True, autoincrement=True,
         comment="Arbitrary primary key"),
    dict(name="when_access_utc", cctype="DATETIME", notnull=True,
         comment="Date/time of access (UTC)", indexed=True),
    dict(name="source", cctype="AUDITSOURCE", notnull=True,
         comment="Source (e.g. tablet, webviewer)"),
    dict(name="remote_addr", cctype="IPADDRESS",
         comment="IP address of the remote computer"),
    dict(name="user_id", cctype="INT_UNSIGNED",
         comment="ID of user, where applicable"),
    dict(name="device_id", cctype="INT_UNSIGNED",
         comment="Device ID, where applicable"),
    dict(name="table_name", cctype="TABLENAME",
         comment="Table involved, where applicable"),
    dict(name="server_pk", cctype="INT_UNSIGNED",
         comment="Server PK (table._pk), where applicable"),
    dict(name="patient_server_pk", cctype="INT_UNSIGNED",
         comment="Server PK of the patient (patient._pk) concerned, or "
                 "NULL if not applicable"),
    dict(name="details", cctype="TEXT",
         comment="Details of the access"),
]


# =============================================================================
# Audit function
# =============================================================================

def audit(details: str,
          patient_server_pk: int = None,
          table: str = None,
          server_pk: int = None,
          device_id: int = None,
          remote_addr: str = None,
          user_id: int = None,
          from_console: bool = False,
          from_dbclient: bool = False) -> None:
    """Write an entry to the audit log."""
    if not remote_addr:
        remote_addr = pls.session.ip_address if pls.session else None
    if not user_id:
        if pls.session and pls.session.userobject:
            user_id = pls.session.userobject.id
    if from_console:
        source = "console"
    elif from_dbclient:
        source = "tablet"
    else:
        source = "webviewer"
    pls.db.db_exec(
        """
            INSERT INTO {table}
                (when_access_utc, source, remote_addr, user_id, device_id,
                patient_server_pk, table_name, server_pk, details)
            VALUES
                (?,?,?,?,?,
                ?,?,?,?)
        """.format(table=SECURITY_AUDIT_TABLENAME),
        pls.NOW_UTC_NO_TZ,  # when_access_utc
        source,
        remote_addr,
        user_id,
        device_id,  # device
        patient_server_pk,
        table,
        server_pk,
        details
    )
