#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_dirtytables.py

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

**Representation of a "dirty table" -- one that a device is in the process of
uploading to/preserving.**

"""

from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from .cc_device import Device
from .cc_sqla_coltypes import TableNameColType
from .cc_sqlalchemy import Base


# =============================================================================
# DirtyTable
# =============================================================================

class DirtyTable(Base):
    """
    Class to represent tables being modified during a client upload.
    """
    __tablename__ = "_dirty_tables"

    id = Column(
        # new in 2.1.0; ditch composite PK
        "id", Integer, primary_key=True, autoincrement=True
    )
    device_id = Column(
        "device_id", Integer,
        ForeignKey(Device.id),
        comment="Source tablet device ID"
    )
    tablename = Column(
        "tablename", TableNameColType,
        comment="Table in the process of being preserved"
    )


class UploadAdditionTable(Base):
    """
    Class to store, temporarily, server PKs being added during an upload.
    """
    __tablename__ = "_upload_addition_keys"

    id = Column(
        "id", Integer, primary_key=True, autoincrement=True
    )
    device_id = Column(
        "device_id", Integer,  # skip FK constraint
        index=True,
        comment="Source tablet device ID"
    )
    pkvalue = Column(
        "pkvalue", Integer,
        index=True,
        comment="Temporarily stored PK value of records being added"
    )


class UploadRemovalTable(Base):
    """
    Class to store, temporarily, server PKs being "removed" during an upload.
    """
    __tablename__ = "_upload_removal_keys"

    id = Column(
        "id", Integer, primary_key=True, autoincrement=True
    )
    device_id = Column(
        "device_id", Integer,  # skip FK constraint
        index=True,
        comment="Source tablet device ID"
    )
    pkvalue = Column(
        "pkvalue", Integer,
        index=True,
        comment="Temporarily stored PK value of records being removed"
    )
