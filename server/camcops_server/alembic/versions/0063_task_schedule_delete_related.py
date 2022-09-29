#!/usr/bin/env python

"""
camcops_server/alembic/versions/0063_task_schedule_delete_related.py

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

task_schedule_delete_related

Revision ID: 0063
Revises: 0062
Creation date: 2021-05-11 17:29:42.967888

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table(
        "_patient_task_schedule", schema=None
    ) as batch_op:
        batch_op.alter_column(
            "patient_pk", existing_type=sa.Integer(), nullable=False
        )
        batch_op.alter_column(
            "schedule_id", existing_type=sa.Integer(), nullable=False
        )

        batch_op.drop_constraint(
            "fk__patient_task_schedule_patient_pk", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk__patient_task_schedule_schedule_id", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("fk__patient_task_schedule_schedule_id"),
            "_task_schedule",
            ["schedule_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk__patient_task_schedule_patient_pk"),
            "patient",
            ["patient_pk"],
            ["_pk"],
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table(
        "_patient_task_schedule", schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk__patient_task_schedule_patient_pk"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f("fk__patient_task_schedule_schedule_id"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk__patient_task_schedule_schedule_id",
            "_task_schedule",
            ["schedule_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk__patient_task_schedule_patient_pk",
            "patient",
            ["patient_pk"],
            ["_pk"],
            ondelete="CASCADE",
        )
        batch_op.alter_column(
            "schedule_id", existing_type=sa.Integer(), nullable=True
        )
        batch_op.alter_column(
            "patient_pk", existing_type=sa.Integer(), nullable=True
        )
