#!/usr/bin/env python

"""
camcops_server/alembic/versions/0051.py

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

auto_generated_user

Revision ID: 0051
Revises: 0050
Creation date: 2020-08-06 10:29:35.135033

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0051'
down_revision = '0050'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table('_security_users', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'auto_generated', sa.Boolean(),
            nullable=False,
            comment='Is automatically generated user with random password')
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('_security_users', schema=None) as batch_op:
        batch_op.drop_column('auto_generated')
