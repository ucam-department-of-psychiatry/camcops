#!/usr/bin/env python

"""
camcops_server/alembic/versions/0056_mojo_medical_infection_fields.py

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

mojo_medical_infection_fields

Revision ID: 0056
Revises: 0055
Creation date: 2020-11-16 11:28:45.597495

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa



# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0056'
down_revision = '0055'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

def upgrade():
    with op.batch_alter_table('khandaker_mojo_medical', schema=None) as batch_op:
        batch_op.add_column(sa.Column('infection_past_month', sa.Boolean(), nullable=True, comment='Do you currently have an infection, or had treatment for an infection (e.g antibiotics) in the past month?'))
        batch_op.add_column(sa.Column('infection_past_three_months', sa.Boolean(name='ck_kh2mm_had_infection'), nullable=True, comment='Have you had an infection, or had treatment for an infection (e.g antibiotics) in the 3 months? '))
        batch_op.drop_column('had_infection_two_months_preceding')
        batch_op.drop_column('has_infection_past_month')


def downgrade():
    with op.batch_alter_table('khandaker_mojo_medical', schema=None) as batch_op:
        batch_op.add_column(sa.Column('has_infection_past_month', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True, comment='Do you currently have an infection, or had treatment for an infection (e.g antibiotics) in the past month?'))
        batch_op.add_column(sa.Column('had_infection_two_months_preceding', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True, comment='Have you had an infection, or had treatment for an infection (e.g antibiotics) in the 2 months preceding last month?'))
        batch_op.drop_column('infection_past_three_months')
        batch_op.drop_column('infection_past_month')
