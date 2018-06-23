#!/usr/bin/env python
# camcops_server/cc_modules/cc_all_models.py

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

The point of this is to import everything that's an SQLAlchemy model, so
they're registered (and also Task knows about all its subclasses).

"""

import logging
# from pprint import pformat
from typing import Dict, Type

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from sqlalchemy.orm import configure_mappers
from sqlalchemy.sql.schema import Table

from .cc_baseconstants import ALEMBIC_VERSION_TABLE
from .cc_db import GenericTabletRecordMixin
from .cc_sqlalchemy import Base, log_all_ddl

# =============================================================================
# Non-task model imports
# =============================================================================
# How to suppress "Unused import statement"?
# https://stackoverflow.com/questions/21139329/false-unused-import-statement-in-pycharm  # noqa
# http://codeoptimism.com/blog/pycharm-suppress-inspections-list/

from .cc_audit import AuditEntry
# noinspection PyUnresolvedReferences
from .cc_blob import Blob
from .cc_device import Device
from .cc_dirtytables import DirtyTable
from .cc_group import Group, group_group_table
from .cc_hl7 import HL7Message, HL7Run
from .cc_idnumdef import IdNumDefinition
from .cc_membership import UserGroupMembership
# noinspection PyUnresolvedReferences
from .cc_patientidnum import PatientIdNum
# noinspection PyUnresolvedReferences
from .cc_patient import Patient
from .cc_session import CamcopsSession
from .cc_specialnote import SpecialNote
from .cc_serversettings import ServerSettings
# noinspection PyUnresolvedReferences
from .cc_task import Task
from .cc_taskfilter import TaskFilter
from .cc_unittest import DemoDatabaseTestCase
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User


# =============================================================================
# Task imports
# =============================================================================

# import_submodules("..tasks", __package__)
#
# ... NO LONGER SUFFICIENT as we are using SQLAlchemy relationship clauses that
# are EVALUATED and so require the class names to be in the relevant namespace
# at the time. So doing something equivalent to "import tasks.phq9" -- which is
# what we get from 'import_submodules("..tasks", __package__)' -- isn't enough.
# We need something equivalent to "from tasks.phq9 import Phq9".

# noinspection PyUnresolvedReferences
from camcops_server.tasks import *  # see tasks/__init__.py


# =============================================================================
# Logging
# =============================================================================

log = BraceStyleAdapter(logging.getLogger(__name__))

# log.critical("Loading cc_all_models")


# =============================================================================
# Ensure that anything with an AbstractConcreteBase gets its mappers
# registered (i.e. Task).
# =============================================================================

configure_mappers()


# =============================================================================
# Tables (and fields) that clients can't touch
# =============================================================================

RESERVED_TABLE_NAMES = [
    ALEMBIC_VERSION_TABLE,
    AuditEntry.__tablename__,
    CamcopsSession.__tablename__,
    Device.__tablename__,
    DirtyTable.__tablename__,
    Group.__tablename__,
    group_group_table.name,
    HL7Message.__tablename__,
    HL7Run.__tablename__,
    IdNumDefinition.__tablename__,
    SecurityAccountLockout.__tablename__,
    SecurityLoginFailure.__tablename__,
    ServerSettings.__tablename__,
    SpecialNote.__tablename__,
    TaskFilter.__tablename__,
    User.__tablename__,
    UserGroupMembership.__tablename__,
]
RESERVED_FIELDS = GenericTabletRecordMixin.RESERVED_FIELDS


# =============================================================================
# Tables that clients use
# =============================================================================

CLIENT_TABLE_MAP = {}  # type: Dict[str, Table]

# Add all tables that clients may upload to (including ancillary tables).
for __orm_class in gen_orm_classes_from_base(Base):  # type: Type[Base]
    # noinspection PyUnresolvedReferences
    if issubclass(__orm_class, GenericTabletRecordMixin):
        __tablename = __orm_class.__tablename__
        if __tablename not in RESERVED_TABLE_NAMES:
            # noinspection PyUnresolvedReferences
            __table = __orm_class.__table__  # type: Table
            CLIENT_TABLE_MAP[__tablename] = __table


# =============================================================================
# Notes
# =============================================================================

class ModelTests(DemoDatabaseTestCase):
    def test_show_ddl(self) -> None:
        self.announce("test_show_ddl")
        log_all_ddl()
