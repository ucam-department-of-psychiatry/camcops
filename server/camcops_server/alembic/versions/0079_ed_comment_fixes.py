#!/usr/bin/env python

"""
camcops_server/alembic/versions/0079_ed_comment_fixes.py

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

Comment fixes to EDE-Q and ISAAQ-ED

Revision ID: 0079
Revises: 0078
Creation date: 2023-02-17 15:49:58.049976

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0079"
down_revision = "0078"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("edeq", schema=None) as batch_op:
        batch_op.alter_column(
            "pill",
            existing_type=sa.Boolean(),
            comment="Taking the (oral contraceptive) pill",
            existing_comment="Taking the pill",
            existing_nullable=True,
        )

    with op.batch_alter_table("isaaqed", schema=None) as batch_op:
        batch_op.alter_column(
            "e11",
            existing_type=sa.Integer(),
            comment="e11 - pro-ED websites 0-5 (not at all - all the time)",
            existing_comment=(
                "e11 - pro-ed websites 0-5 (not at all - all the time)"
            ),
            existing_nullable=True,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("isaaqed", schema=None) as batch_op:
        batch_op.alter_column(
            "e11",
            existing_type=sa.Integer(),
            comment="e11 - pro-ed websites 0-5 (not at all - all the time)",
            existing_comment=(
                "e11 - pro-ED websites 0-5 (not at all - all the time)"
            ),
            existing_nullable=True,
        )

    with op.batch_alter_table("edeq", schema=None) as batch_op:
        batch_op.alter_column(
            "pill",
            existing_type=sa.Boolean(),
            comment="Taking the pill",
            existing_comment="Taking the (oral contraceptive) pill",
            existing_nullable=True,
        )
