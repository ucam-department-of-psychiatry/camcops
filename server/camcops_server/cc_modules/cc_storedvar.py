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

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Float, Integer, UnicodeText

from .cc_db import GenericTabletRecordMixin
from .cc_sqla_coltypes import (
    StoredVarNameColType,
    StoredVarTypeColType,
)
from .cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# StoredVar classes and lookup functions
# =============================================================================

VALUE_TYPE = Union[int, str, float, None]


class StoredVarTypes(object):
    TYPE_INTEGER = "integer"
    TYPE_TEXT = "text"
    TYPE_REAL = "real"


class ServerStoredVarNames(object):
    SERVER_CAMCOPS_VERSION = "serverCamcopsVersion"
    DATABASE_TITLE = "databaseTitle"
    LAST_ANALYTICS_SENT_AT = "lastAnalyticsSentAt"


class DeviceStoredVar(GenericTabletRecordMixin, Base):
    """Class representing variables stored by tablet devices and copied to
    the server."""
    # *** DITCH THIS WHEN OLD TABLET VERSIONS GONE; NO NEED. FUNCTIONS REMOVED.
    __tablename__ = "storedvars"

    id = Column(
        "id", Integer,
        nullable=False,
        comment="Arbitrary numerical primary key on the source tablet device"
        # client PK
    )
    name = Column(
        "name", StoredVarNameColType,
        nullable=False, index=True,
        comment="Variable name (effectively the actual primary key on "
                "the source tablet device)"
    )
    type = Column(
        "type", StoredVarTypeColType,
        nullable=False,
        comment="Variable type ('integer', 'real', 'text')"
    )
    value_integer = Column(
        "valueInteger", Integer,
        comment="Value of an integer variable"
    )
    value_text = Column(
        "valueText", UnicodeText,
        comment="Value of a text variable"
    )
    value_real = Column(
        "valueReal", Float,
        comment="Value of a real (floating-point) variable"
    )


class ServerStoredVar(Base):
    """
    Class representing variables stored by the server itself.
    """
    __tablename__ = "_server_storedvars"

    name = Column(
        "name", StoredVarNameColType,
        primary_key=True, index=True,
        comment="Variable name"
    )
    type = Column(
        "type", StoredVarTypeColType,
        nullable=False,
        comment="Variable type ('integer', 'real', 'text')"
    )
    value_integer = Column(
        "valueInteger", Integer,
        comment="Value of an integer variable"
    )
    value_text = Column(
        "valueText", UnicodeText,
        comment="Value of a text variable"
    )
    value_real = Column(
        "valueReal", Float,
        comment="Value of a real (floating-point) variable"
    )

    @classmethod
    def get_server_storedvar(cls, dbsession: SqlASession,
                             name: str) -> Optional['ServerStoredVar']:
        """
        Fetches a ServerStoredVar() object, or returns None.
        """
        var = dbsession.query(cls)\
            .filter(cls.name == name)\
            .first()  # type: Optional[ServerStoredVar]
        return var

    @classmethod
    def get_server_storedvar_value(cls, dbsession: SqlASession,
                                   name: str) -> VALUE_TYPE:
        """
        Fetches a ServerStoredVar() object and returns its value, or None.
        """
        var = cls.get_server_storedvar(dbsession, name)
        if var is None:
            return None
        return var.get_value()

    @classmethod
    def get_or_create(cls,
                      dbsession: SqlASession,
                      name: str,
                      type_on_creation: str = StoredVarTypes.TYPE_INTEGER,
                      default_value: VALUE_TYPE = None) -> 'ServerStoredVar':
        var = dbsession.query(cls)\
            .filter(cls.name == name)\
            .first()  # type: Optional[ServerStoredVar]
        if var is None:
            var = ServerStoredVar(name=name, type=type_on_creation)
            var.set_value(default_value)
            dbsession.add(var)
        else:
            # Just in case we've changed a type, make sure we use the one
            # that the requestor wants now.
            var.type = type_on_creation
        return var

    def get_value(self) -> VALUE_TYPE:
        """Get the stored value."""
        if self.type == StoredVarTypes.TYPE_INTEGER:
            return self.value_integer  # type: int
        elif self.type == StoredVarTypes.TYPE_TEXT:
            return self.value_text  # type: str
        elif self.type == StoredVarTypes.TYPE_REAL:
            return self.value_real  # type: float
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")

    def set_value(self, value: VALUE_TYPE) -> None:
        """Sets the stored value (and optionally saves it in the database.)"""
        if value is None:
            self.value_integer = None
            self.value_text = None
            self.value_real = None
        elif self.type == StoredVarTypes.TYPE_INTEGER:
            self.value_integer = int(value)
            self.value_text = None
            self.value_real = None
        elif self.type == StoredVarTypes.TYPE_TEXT:
            self.value_integer = None
            self.value_text = str(value)
            self.value_real = None
        elif self.type == StoredVarTypes.TYPE_REAL:
            self.value_integer = None
            self.value_text = None
            self.value_real = float(value)
        else:
            raise RuntimeError("UNKNOWN_TYPE_IN_STOREDVAR")
