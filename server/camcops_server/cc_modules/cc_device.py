#!/usr/bin/env python3
# cc_device.py

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

from typing import Optional

import cardinal_pythonlib.rnc_web as ws

from .cc_constants import PARAM
from . import cc_db
from .cc_pls import pls
from . import cc_report
from .cc_report import Report, REPORT_RESULT_TYPE
from .cc_unittest import unit_test_ignore


# =============================================================================
# Device class
# =============================================================================

class Device(object):
    """Represents a tablet device."""
    TABLENAME = "_security_devices"
    FIELDSPECS = [
        dict(name="id", cctype="INT_UNSIGNED", pk=True,
             comment="ID of the source tablet device"),
        dict(name="name", cctype="DEVICE", indexed=True,
             # TODO: make index unique
             comment="Short cryptic name of the source tablet device"),
        dict(name="registered_by_user_id", cctype="INT_UNSIGNED",
             comment="ID of user that registered the device"),
        dict(name="when_registered_utc", cctype="DATETIME",
             comment="Date/time when the device was registered (UTC)"),
        dict(name="friendly_name", cctype="TEXT",
             comment="Friendly name of the device"),
        dict(name="camcops_version", cctype="FLOAT",
             comment="CamCOPS version number on the tablet device"),
        dict(name="last_upload_batch_utc", cctype="DATETIME",
             comment="Date/time when the device's last upload batch "
                     "started (UTC)"),
        dict(name="ongoing_upload_batch_utc", cctype="DATETIME",
             comment="Date/time when the device's ongoing upload batch "
                     "started (UTC)"),
        dict(name="uploading_user_id", cctype="INT_UNSIGNED",
             comment="ID of user in the process of uploading right now"),
        dict(name="currently_preserving", cctype="BOOL",
             comment="Preservation currently in progress"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Create underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, device_id: int = None) -> None:
        """Initializes, reading from database if necessary."""
        pls.db.fetch_object_from_db_by_pk(self, Device.TABLENAME,
                                          Device.FIELDS, device_id)

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
        """Valid device (having been instantiated with Device(device_id), i.e.
        is it in the database?"""
        return self.id is not None


def get_device_by_name(device_name: str) -> Optional[Device]:
    if not device_name:
        return None
    device = Device()
    if pls.db.fetch_object_from_db_by_other_field(device,
                                                  Device.TABLENAME,
                                                  Device.FIELDS,
                                                  "name",
                                                  device_name):
        return device
    else:
        return None


# =============================================================================
# Support functions
# =============================================================================

def get_device_filter_dropdown(currently_selected_id: int = None) -> str:
    """Get HTML list of all known tablet devices."""
    s = """
        <select name="{}">
            <option value="">(all)</option>
    """.format(PARAM.DEVICE)
    rows = pls.db.fetchall("SELECT id FROM {table}".format(
        table=Device.TABLENAME))
    for pk in [row[0] for row in rows]:
        device = Device(pk)
        s += """<option value="{pk}"{sel}>{name}</option>""".format(
            pk=pk,
            name=ws.webify(device.get_friendly_name_and_id()),
            sel=ws.option_selected(currently_selected_id, pk),
        )
    s += """</select>"""
    return s


# =============================================================================
# Reports
# =============================================================================

class DeviceReport(Report):
    """Report to show registered devices."""
    report_id = "devices"
    report_title = "(Server) Devices registered with the server"
    param_spec_list = []

    def get_rows_descriptions(self) -> REPORT_RESULT_TYPE:
        sql = """
            SELECT
                id,
                name,
                registered_by_user,
                when_registered_utc,
                friendly_name,
                camcops_version,
                last_upload_batch_utc
            FROM {tablename}
        """.format(
            tablename=Device.TABLENAME,
        )
        (rows, fieldnames) = pls.db.fetchall_with_fieldnames(sql)
        fieldnames = cc_report.expand_id_descriptions(fieldnames)
        return rows, fieldnames


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_device(d: Device) -> None:
    """Unit tests for Device class."""
    # skip make_tables
    unit_test_ignore("", d.get_friendly_name)
    unit_test_ignore("", d.get_friendly_name_and_id)
    unit_test_ignore("", d.get_id)


def unit_tests() -> None:
    """Unit tests for cc_device module."""
    current_pks = pls.db.fetchallfirstvalues(
        "SELECT device FROM {}".format(Device.TABLENAME)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        d = Device(pk)
        unit_tests_device(d)

    unit_test_ignore("", get_device_filter_dropdown)
