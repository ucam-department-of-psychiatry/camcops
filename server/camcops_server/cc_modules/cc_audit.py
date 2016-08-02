#!/usr/bin/env python3
# cc_audit.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
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
