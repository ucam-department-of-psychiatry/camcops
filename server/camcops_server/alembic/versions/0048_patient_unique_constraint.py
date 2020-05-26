#!/usr/bin/env python

"""
camcops_server/alembic/versions/0048_patient_unique_constraint.py

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

patient_unique_constraint

Revision ID: 0048
Revises: 0047
Creation date: 2020-04-28 11:48:52.826510

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op


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
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f('uq_patient_id'), ['id', '_device_id', '_era']
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('patient', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_patient_id'), type_='unique')
