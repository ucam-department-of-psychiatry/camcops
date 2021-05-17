#!/usr/bin/env python

"""
camcops_server/alembic/versions/0063_fhir.py

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

fhir

Revision ID: 0063
Revises: 0061
Creation date: 2021-03-30 11:08:21.258344

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0063'
down_revision = '0062'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        '_exported_task_fhir',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Arbitrary primary key'),
        sa.Column('exported_task_id', sa.BigInteger(), nullable=False,
                  comment='FK to _exported_tasks.id'),
        sa.ForeignKeyConstraint(
            ['exported_task_id'], ['_exported_tasks.id'],
            name=op.f('fk__exported_task_fhir_exported_task_id')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__exported_task_fhir')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('_export_recipients', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'fhir_api_url', sa.Text(), nullable=True,
                comment='(FHIR) FHIR API URL, pointing to the FHIR server'
            )
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('_export_recipients', schema=None) as batch_op:
        batch_op.drop_column('fhir_api_url')

    op.drop_table('_exported_task_fhir')
