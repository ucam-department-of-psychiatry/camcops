#!/usr/bin/env python

"""
camcops_server/alembic/versions/0077.py

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

test

Revision ID: 0077
Revises: 0076
Creation date: 2022-09-23 15:57:22.804627

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0077"
down_revision = "0076"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("patient", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("test", sa.UnicodeText(), nullable=True, comment="Test")
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("patient", schema=None) as batch_op:
        batch_op.drop_column("test")
