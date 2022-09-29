#!/usr/bin/env python

"""
camcops_server/alembic/versions/0069_manage_patient_permissions.py

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

manage_patient_permission

Revision ID: 0069
Revises: 0068
Creation date: 2021-07-06 10:42:08.062255

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("_security_user_group", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "may_manage_patients",
                sa.Boolean(),
                nullable=True,
                comment="May the user add/edit/delete patients?",
            )
        )
        batch_op.add_column(
            sa.Column(
                "may_email_patients",
                sa.Boolean(),
                nullable=True,
                comment="May the user send emails to patients?",
            )
        )


def downgrade():
    with op.batch_alter_table("_security_user_group", schema=None) as batch_op:
        batch_op.drop_column("may_manage_patients")
        batch_op.drop_column("may_email_patients")
