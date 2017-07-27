#!/usr/bin/env python
# camcops_server/cc_modules/cc_storedvar.py

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

import logging
from typing import Optional, Union

import cardinal_pythonlib.rnc_db as rnc_db

from .cc_constants import STANDARD_GENERIC_FIELDSPECS
from . import cc_db
from .cc_logger import BraceStyleAdapter
from .cc_pls import pls

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# StoredVar classes and lookup functions
# =============================================================================

VALUE_TYPE = Union[int, str, float, None]


class StoredVarBase(object):
    """Abstract base class for type-varying values stored in the database."""

    TYPE_INTEGER = "integer"
    TYPE_TEXT = "text"
    TYPE_REAL = "real"

    def get_value(self) -> VALUE_TYPE:
        """Get the stored value."""
        if self.type == self.TYPE_INTEGER:
            return self.valueInteger
        elif self.type == self.TYPE_TEXT:
            return self.valueText
        elif self.type == self.TYPE_REAL:
            return self.valueReal
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")

    def set_value(self, value: VALUE_TYPE, save: bool = True) -> None:
        """Sets the stored value (and optionally saves it in the database.)"""
        if self.type == self.TYPE_INTEGER:
            self.valueInteger = value
            self.valueText = None
            self.valueReal = None
        elif self.type == self.TYPE_TEXT:
            self.valueInteger = None
            self.valueText = value
            self.valueReal = None
        elif self.type == self.TYPE_REAL:
            self.valueInteger = None
            self.valueText = None
            self.valueReal = value
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")
        if save:
            self.save()  # must be overridden!


class DeviceStoredVar(StoredVarBase):
    """Class representing variables stored by tablet devices and copied to
    the server."""
    # *** DITCH THIS WHEN OLD TABLET VERSIONS GONE; NO NEED FOR IT.
    TABLENAME = "storedvars"
    FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
        dict(name="id", cctype="INT_UNSIGNED", notnull=True,
             comment="Arbitrary numerical primary key on the source "
                     "tablet device"),  # client PK
        dict(name="name", cctype="STOREDVARNAME", notnull=True,
             comment="Variable name (effectively the actual primary key on "
                     "the source tablet device)",
             indexed=True, index_nchar=50),
        dict(name="type", cctype="STOREDVARTYPE", notnull=True,
             comment="Variable type ('integer', 'real', 'text')"),
        dict(name="valueInteger", cctype="INT",
             comment="Value of an integer variable"),
        dict(name="valueText", cctype="TEXT",
             comment="Value of a text variable"),
        dict(name="valueReal", cctype="FLOAT",
             comment="Value of a real (floating-point) variable"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying database tables."""
        cc_db.create_standard_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    @classmethod
    def drop_views(cls) -> None:
        pls.db.drop_view(cls.TABLENAME + "_current")

    def dump(self):
        """Dump to the log."""
        rnc_db.dump_database_object(self, DeviceStoredVar.FIELDS)

    def __init__(self, serverpk: Optional[int]) -> None:
        """Initialize and load from database."""
        pls.db.fetch_object_from_db_by_pk(self, DeviceStoredVar.TABLENAME,
                                          DeviceStoredVar.FIELDS, serverpk)


class ServerStoredVar(StoredVarBase):
    """Class representing variables stored by the server itself."""
    TABLENAME = "_server_storedvars"
    FIELDSPECS = [
        dict(name="name", cctype="STOREDVARNAME", pk=True,
             comment="Variable name", indexed=True, index_nchar=50),
        dict(name="type", cctype="STOREDVARTYPE", notnull=True,
             comment="Variable type ('integer', 'real', 'text')"),
        dict(name="valueInteger", cctype="INT",
             comment="Value of an integer variable"),
        dict(name="valueText", cctype="TEXT",
             comment="Value of a text variable"),
        dict(name="valueReal", cctype="FLOAT",
             comment="Value of a real (floating-point) variable"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    @classmethod
    def drop_views(cls) -> None:
        pass

    def dump(self) -> None:
        """Dump to the log."""
        rnc_db.dump_database_object(self, ServerStoredVar.FIELDS)

    def __init__(self,
                 namepk: str,
                 type_on_creation: str = StoredVarBase.TYPE_INTEGER,
                 default_value: VALUE_TYPE = None) -> None:
        """Initialize (fetch from database or create)."""
        if not pls.db.fetch_object_from_db_by_pk(
                self,
                ServerStoredVar.TABLENAME,
                ServerStoredVar.FIELDS,
                namepk):
            # Doesn't exist; create it
            self.name = namepk
            self.type = type_on_creation
            self.set_value(default_value, False)
            pls.db.insert_object_into_db_pk_known(
                self, ServerStoredVar.TABLENAME, ServerStoredVar.FIELDS)
        else:
            # Just in case we've changed a type, make sure we use the one
            # that the requestor wants now.
            self.type = type_on_creation

    def save(self) -> None:
        """Store to database."""
        pls.db.update_object_in_db(
            self, ServerStoredVar.TABLENAME, ServerStoredVar.FIELDS)


def get_device_storedvar(device_id: int, name: str, era: str) \
        -> Optional[DeviceStoredVar]:
    """Fetches a DeviceStoredVar() object, or None."""
    # lookup by name, not client ID
    try:
        row = pls.db.fetchone(
            """
                SELECT _pk
                FROM {table}
                WHERE _current AND _device_id=? AND name=? AND _era=?
            """.format(table=DeviceStoredVar.TABLENAME),
            device_id,
            name,
            era
        )
    except Exception as inst:
        # May fail if e.g. no storedvar table created yet
        log.error(str(inst))
        return None
    if row is None or row[0] is None:
        return None
    return DeviceStoredVar(row[0])


def get_device_storedvar_value(device_id: int,
                               name: str,
                               era: str) -> VALUE_TYPE:
    """Fetches a DeviceStoredVar() object and returns its value, or None."""
    sv = get_device_storedvar(device_id, name, era)
    return sv.get_value() if sv is not None else ""


def get_server_storedvar(name: str) -> Optional[ServerStoredVar]:
    """Fetches a ServerStoredVar() object, or None."""
    # lookup by name, not client ID
    try:
        row = pls.db.fetchone(
            "SELECT name FROM {table} WHERE name=?".format(
                table=ServerStoredVar.TABLENAME),
            name
        )
    except Exception as inst:
        # May fail if e.g. no storedvar table created yet
        log.error(str(inst))
        return None
    if row is None or row[0] is None:
        return None
    return ServerStoredVar(name)


def get_server_storedvar_value(name: str) -> VALUE_TYPE:
    """Fetches a ServerStoredVar() object and returns its value, or None."""
    sv = get_server_storedvar(name)
    return sv.get_value() if sv is not None else ""
