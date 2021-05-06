#!/usr/bin/env python

"""
camcops_server/alembic/versions/0062_task_schedule_delete_related.py

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

task_schedule_delete_related

Revision ID: 0062
Revises: 0061
Creation date: 2021-04-27 15:20:01.945933

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0062'
down_revision = '0061'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table(
            '_patient_task_schedule', schema=None) as batch_op:
        batch_op.alter_column('patient_pk',
                              existing_type=sa.Integer(),
                              nullable=False)
        batch_op.alter_column('schedule_id',
                              existing_type=sa.Integer(),
                              nullable=False)

    with op.batch_alter_table('_task_schedule_item', schema=None) as batch_op:
        batch_op.drop_constraint('fk__task_schedule_item_schedule_id',
                                 type_='foreignkey')
        batch_op.create_foreign_key(
            batch_op.f('fk__task_schedule_item_schedule_id'),
            '_task_schedule', ['schedule_id'], ['id'], ondelete='CASCADE'
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('_task_schedule_item', schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f('fk__task_schedule_item_schedule_id'),
            type_='foreignkey'
        )
        batch_op.create_foreign_key(
            'fk__task_schedule_item_schedule_id',
            '_task_schedule', ['schedule_id'], ['id']
        )

    with op.batch_alter_table(
            '_patient_task_schedule', schema=None) as batch_op:
        batch_op.alter_column('schedule_id',
                              existing_type=sa.Integer(),
                              nullable=True)
        batch_op.alter_column('patient_pk',
                              existing_type=sa.Integer(),
                              nullable=True)
