#!/usr/bin/env python

"""
camcops_server/alembic/versions/0048_patientidnum_uuid.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

DATABASE REVISION SCRIPT

patientidnum_uuid

Revision ID: 0048
Revises: 0047
Creation date: 2020-04-03 14:28:32.774314

"""

# =============================================================================
# Imports
# =============================================================================

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table
from camcops_server.cc_modules.cc_sqla_coltypes import EraColType, UuidColType


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0048'
down_revision = '0047'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table('patient_idnum', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'patient_uuid',
                UuidColType(length=32),
                nullable=True,
                comment='FK to patient.uuid')
        )

    patient_idnum = table(
        "patient_idnum",
        sa.Column(
            "patient_id",
            sa.Integer,
            nullable=False
        ),
        sa.Column(
            "patient_uuid",
            UuidColType,
            nullable=True
        ),
        sa.Column(
            "_device_id",
            sa.Integer,
            nullable=False
        ),
        sa.Column(
            "_era",
            EraColType,
            nullable=False
        ),
        sa.Column(
            "_current",
            sa.Boolean,
            nullable=False
        )
    )

    patient = table(
        "patient",
        sa.Column(
            "_pk",
            sa.Integer,
            primary_key=True,
            autoincrement=True,
            index=True,
            nullable=False
        ),
        sa.Column(
            "id",
            sa.Integer,
            nullable=False
        ),
        sa.Column(
            "uuid",
            UuidColType,
        ),
        sa.Column(
            "_device_id",
            sa.Integer,
            nullable=False
        ),
        sa.Column(
            "_era",
            EraColType,
            nullable=False
        ),
        sa.Column(
            "_current",
            sa.Boolean,
            nullable=False
        )
    )
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Add a UUID to patients that are missing one
    for p in session.query(patient).filter(
            patient.c.uuid == None  # noqa: E711
    ):
        new_uuid = uuid.uuid4()
        op.execute(
            patient.update().
            where(patient.c._pk == p._pk)
            .values({"uuid": new_uuid})
        )

    # Now copy the UUID into all patientidnum records
    for p in session.query(patient):
        op.execute(
            patient_idnum.update()
            .where(patient_idnum.c.patient_id == p.id)
            .where(patient_idnum.c._device_id == p._device_id)
            .where(patient_idnum.c._era == p._era)
            .where(p._current == True)  # noqa: E711
            .values({"patient_uuid": p.uuid})
        )

    session.commit()


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('patient_idnum', schema=None) as batch_op:
        batch_op.drop_column('patient_uuid')
