#!/usr/bin/env python
# camcops_server/cc_modules/cc_all_models.py

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

The point of this is to import everything that's an SQLAlchemy model, so
they're registered (and also Task knows about all its subclasses).

"""

import logging
# from pprint import pformat
from typing import Dict, Type
import unittest

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_orm_classes_from_base
from sqlalchemy.orm import configure_mappers
from sqlalchemy.sql.schema import Table

from .cc_constants import ALEMBIC_VERSION_TABLENAME
from .cc_db import GenericTabletRecordMixin
from .cc_sqlalchemy import Base, make_debug_sqlite_engine, log_all_ddl

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
from .cc_membership import UserGroupMembership
# noinspection PyUnresolvedReferences
from .cc_patientidnum import IdNumDefinition, PatientIdNum
# noinspection PyUnresolvedReferences
from .cc_patient import Patient
from .cc_session import CamcopsSession
from .cc_specialnote import SpecialNote
from .cc_serversettings import ServerSettings
from .cc_task import Task
from .cc_taskfilter import TaskFilter
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
from ..tasks import *  # see tasks/__init__.py


# =============================================================================
# Logging
# =============================================================================

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Ensure that anything with an AbstractConcreteBase gets its mappers
# registered (i.e. Task).
# =============================================================================

configure_mappers()


# =============================================================================
# Tables (and fields) that clients can't touch
# =============================================================================

RESERVED_TABLE_NAMES = [
    ALEMBIC_VERSION_TABLENAME,
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
# A silly way to suppress "Unused import statement"
# =============================================================================

def all_models_no_op() -> None:
    pass


# =============================================================================
# Notes
# =============================================================================

class ModelTests(unittest.TestCase):
    # Logging in unit tests:
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o  # noqa
    # https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o/15969985#15969985
    # ... but actually, my code below is simpler and works fine.

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    @staticmethod
    def test_show_ddl() -> None:
        # from cardinal_pythonlib.debugging import pdb_run
        log_all_ddl()
        # pdb_run(print_all_ddl)

    @staticmethod
    def test_query_phq9() -> None:
        from sqlalchemy.orm.session import sessionmaker
        from camcops_server.tasks import Phq9

        engine = make_debug_sqlite_engine()
        Base.metadata.create_all(engine)
        session = sessionmaker()(bind=engine)

        phq9_query = session.query(Phq9)
        results = phq9_query.all()
        log.info("{}", results)

    @staticmethod
    def test_query_via_command_line_request() -> None:
        from camcops_server.cc_modules.cc_request import get_command_line_request
        from camcops_server.tasks import Phq9
        all_models_no_op()

        req = get_command_line_request()
        dbsession = req.dbsession
        phq9_query = dbsession.query(Phq9)
        phq9s = phq9_query.all()
        if phq9s:
            p = phq9s[0]
            log.info("PHQ9 is_complete(): {}", p.is_complete())
        else:
            log.info("No PHQ9 instances found")

    @staticmethod
    def concrete_inheritance_disabled__test() -> None:
        from sqlalchemy.engine import create_engine
        from sqlalchemy.orm import configure_mappers
        from sqlalchemy.orm.session import sessionmaker
        from camcops_server.cc_modules.cc_task import Task
        all_models_no_op()

        engine = create_engine("sqlite://", echo=True)
        Base.metadata.create_all(engine)
        session = sessionmaker()(bind=engine)

        log.debug("configure_mappers()...")
        configure_mappers()
        log.debug("... done")

        task_query = session.query(Task)
        tasks = task_query.all()
        log.info(tasks)

    @staticmethod
    def test_task_subclasses() -> None:
        subclasses = Task.all_subclasses_by_tablename()
        tables = [cls.tablename for cls in subclasses]
        log.info("Actual task table names: {!r} (n={})", tables, len(tables))


# =============================================================================
# main
# =============================================================================
# run with "python -m camcops_server.cc_modules.cc_all_models -v" to be verbose

if __name__ == "__main__":
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    unittest.main()
    # tests = SqlalchemyTests()
    # tests.test_1()
