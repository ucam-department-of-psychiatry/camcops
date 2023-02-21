#!/usr/bin/env python

"""
camcops_server/alembic/versions/0082_replace_isaaq_isaaq10.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

DATABASE REVISION SCRIPT

fix_up_patient_uuids

Revision ID: 0082
Revises: 0081
Creation date: 2021-07-19 08:56:00

Replaces "isaaq" with "isaaq10" in any task schedule item rows

"""

# =============================================================================
# Imports
# =============================================================================

import logging

from alembic import op
from sqlalchemy import orm
from sqlalchemy.engine.strategies import MockEngineStrategy
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.expression import update

from camcops_server.cc_modules.cc_taskschedule import TaskScheduleItem

log = logging.getLogger(__name__)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0082"
down_revision = "0081"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    bind = op.get_bind()
    if isinstance(bind, MockEngineStrategy.MockConnection):
        log.warning("Using mock connection; skipping step")
        return
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # for echo
    # bind._echo = True  # echo on, in a hacky way
    dbsession = orm.Session(bind=bind)

    # Some shorthand:
    # noinspection PyUnresolvedReferences
    tsi_table = TaskScheduleItem.__table__  # type: Table
    # noinspection PyProtectedMember
    task_table_name_col = tsi_table.columns.task_table_name  # type: Column

    # UPDATE _task_schedule_item SET task_table_name="isaaq10"
    # WHERE task_table_name = "isaaq":
    update_statement = (
        update(tsi_table)
        .where(task_table_name_col == "isaaq")
        .values(task_table_name="isaaq10")
    )
    dbsession.execute(update_statement)
    dbsession.commit()


# noinspection PyPep8,PyTypeChecker
def downgrade():
    pass
