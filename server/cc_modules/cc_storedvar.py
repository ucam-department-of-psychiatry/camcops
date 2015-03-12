#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

import rnc_db

from cc_constants import STANDARD_GENERIC_FIELDSPECS
import cc_db
from cc_logger import logger
from cc_pls import pls


# =============================================================================
# StoredVar classes and lookup functions
# =============================================================================

class StoredVarBase(object):
    """Abstract base class for type-varying values stored in the database."""
    def getValue(self):
        """Get the stored value."""
        if self.type == "integer":
            return self.valueInteger
        elif self.type == "text":
            return self.valueText
        elif self.type == "real":
            return self.valueReal
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")

    def setValue(self, value, save=True):
        """Sets the stored value (and optionally saves it in the database.)"""
        if self.type == "integer":
            self.valueInteger = value
        elif self.type == "text":
            self.valueText = value
        elif self.type == "real":
            self.valueReal = value
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")
        if save:
            self.save()  # must be overridden!


class DeviceStoredVar(StoredVarBase):
    """Class representing variables stored by tablet devices and copied to
    the server."""
    TABLENAME = "storedvars"
    FIELDSPECS = STANDARD_GENERIC_FIELDSPECS + [
        dict(name="id", cctype="INT_UNSIGNED", notnull=True,
             comment="Arbitrary numerical primary key on the source "
                     + "tablet device"),  # client PK
        dict(name="name", cctype="STOREDVARNAME", notnull=True,
             comment="Variable name (effectively the actual primary key on "
                     + "the source tablet device)",
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
    def make_tables(cls, drop_superfluous_columns=False):
        """Make underlying database tables."""
        cc_db.create_standard_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def dump(self):
        """Dump to the logger."""
        rnc_db.dump_database_object(self, DeviceStoredVar.FIELDS)

    def __init__(self, serverpk):
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
    def make_tables(cls, drop_superfluous_columns=False):
        """Make underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def dump(self):
        """Dump to the logger."""
        rnc_db.dump_database_object(self, ServerStoredVar.FIELDS)

    def __init__(self, namepk, typeOnCreation="integer", defaultValue=None):
        """Initialize (fetch from database or create)."""
        if not pls.db.fetch_object_from_db_by_pk(
                self,
                ServerStoredVar.TABLENAME,
                ServerStoredVar.FIELDS,
                namepk):
            # Doesn't exist; create it
            self.name = namepk
            self.type = typeOnCreation
            self.setValue(defaultValue, False)
            pls.db.insert_object_into_db_pk_known(
                self, ServerStoredVar.TABLENAME, ServerStoredVar.FIELDS)

    def save(self):
        """Store to database."""
        pls.db.update_object_in_db(
            self, ServerStoredVar.TABLENAME, ServerStoredVar.FIELDS)


def get_device_storedvar(device, name, era):
    """Fetches a DeviceStoredVar() object, or None."""
    # lookup by name, not client ID
    try:
        row = pls.db.fetchone(
            """
                SELECT _pk
                FROM {table}
                WHERE _current AND _device=? AND name=? AND _era=?
            """.format(table=DeviceStoredVar.TABLENAME),
            device,
            name,
            era
        )
    except Exception as inst:
        # May fail if e.g. no storedvar table created yet
        logger.error(str(inst))
        return None
    if row is None or row[0] is None:
        return None
    return DeviceStoredVar(row[0])


def get_device_storedvar_value(device, name, era):
    """Fetches a DeviceStoredVar() object and returns its value, or None."""
    sv = get_device_storedvar(device, name, era)
    return sv.getValue() if sv is not None else ""


def get_server_storedvar(name):
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
        logger.error(str(inst))
        return None
    if row is None or row[0] is None:
        return None
    return ServerStoredVar(name)


def get_server_storedvar_value(name):
    """Fetches a ServerStoredVar() object and returns its value, or None."""
    sv = get_server_storedvar(name)
    return sv.getValue() if sv is not None else ""
