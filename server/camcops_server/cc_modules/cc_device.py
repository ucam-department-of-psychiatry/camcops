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

from typing import Optional

import cardinal_pythonlib.rnc_web as ws

from .cc_constants import PARAM
from . import cc_db
from .cc_pls import pls
from .cc_report import expand_id_descriptions, Report, REPORT_RESULT_TYPE
from .cc_unittest import unit_test_ignore


# =============================================================================
# Device class
# =============================================================================

class Device(object):
    """Represents a tablet device."""
    TABLENAME = "_security_devices"
    FIELDSPECS = [
        dict(name="id", cctype="INT_UNSIGNED", pk=True, autoincrement=True,
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
        dict(name="camcops_version", cctype="SEMANTICVERSIONTYPE",
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
                registered_by_user_id,
                when_registered_utc,
                friendly_name,
                camcops_version,
                last_upload_batch_utc
            FROM {tablename}
        """.format(
            tablename=Device.TABLENAME,
        )
        (rows, fieldnames) = pls.db.fetchall_with_fieldnames(sql)
        fieldnames = expand_id_descriptions(fieldnames)
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


def ccdevice_unit_tests() -> None:
    """Unit tests for cc_device module."""
    current_pks = pls.db.fetchallfirstvalues(
        "SELECT id FROM {}".format(Device.TABLENAME)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        d = Device(pk)
        unit_tests_device(d)

    unit_test_ignore("", get_device_filter_dropdown)
