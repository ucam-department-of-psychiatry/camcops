#!/usr/bin/env python

"""
camcops_server/alembic/versions/0064_task_schedule_email_extras.py

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

task_schedule_email_extras

Revision ID: 0064
Revises: 0063
Creation date: 2021-06-17 16:34:00.796829

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("_task_schedule", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_cc",
                sa.UnicodeText(),
                nullable=True,
                comment="Send a carbon copy of the email to these addresses",
            )
        )
        batch_op.add_column(
            sa.Column(
                "email_bcc",
                sa.UnicodeText(),
                nullable=True,
                comment=(
                    "Send a blind carbon copy of the email to these addresses"
                ),
            )
        )
        batch_op.add_column(
            sa.Column(
                "email_from",
                sa.Unicode(length=255),
                nullable=True,
                comment="Sender's e-mail address",
            )
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("_task_schedule", schema=None) as batch_op:
        batch_op.drop_column("email_from")
        batch_op.drop_column("email_cc")
        batch_op.drop_column("email_bcc")
