#!/usr/bin/env python

"""
camcops_server/alembic/versions/0066_fix_up_patient_uuids.py

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

Revision ID: 0066
Revises: 0065
Creation date: 2021-07-19 08:56:00

Ensure all patients have a UUID. Any created before 0048 will not have one.

"""

# =============================================================================
# Imports
# =============================================================================

import logging
import uuid

from alembic import op
from sqlalchemy import orm
from sqlalchemy.engine.strategies import MockEngineStrategy
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.expression import bindparam, select, update

from camcops_server.cc_modules.cc_patient import Patient

log = logging.getLogger(__name__)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0066"
down_revision = "0065"
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

    # How to do this?
    # (1) One approach is to create a "cut-down" Patient class with just two
    # columns (pk_, uuid) and use the ORM. That works fine but is slightly
    # confusing in that we have two Patient classes across the code base.
    # (2) Or, we could use the main Patient class. However, a query on that,
    # like dbsession.query(Patient).filter(Patient.uuid.is_(None)), executes a
    # SELECT for all columns -- which may include columns that don't yet exist
    # in this database revision.
    # (3) Or, we could use SQLAlchemy Core, like this:

    # Some shorthand:
    # noinspection PyUnresolvedReferences
    patient_table = Patient.__table__  # type: Table
    # noinspection PyProtectedMember
    pk_col = patient_table.columns._pk  # type: Column
    uuid_col = patient_table.columns.uuid  # type: Column

    # SELECT patient._pk FROM patient WHERE patient.uuid IS NULL:
    pk_query = select([pk_col]).where(uuid_col.is_(None))
    rows = dbsession.execute(pk_query)
    pks_needing_uuid = [row[0] for row in rows]

    # Determine new UUIDs:
    update_values = [
        {"pk": _pk, "uuid": uuid.uuid4()}  # generates a random UUID
        for _pk in pks_needing_uuid
    ]

    if update_values:
        # UPDATE patient SET uuid=%(uuid)s WHERE patient._pk = %(pk)s:
        update_statement = (
            update(patient_table)
            .where(pk_col == bindparam("pk"))
            .values(uuid=bindparam("uuid"))
        )
        # ... with many parameter pairs:
        # https://docs.sqlalchemy.org/en/14/tutorial/data_update.html
        dbsession.execute(update_statement, update_values)

    # COMMIT:
    dbsession.commit()
    # bind._echo = False  # echo off, in a hacky way
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)  # echo off  # noqa


# noinspection PyPep8,PyTypeChecker
def downgrade():
    pass
