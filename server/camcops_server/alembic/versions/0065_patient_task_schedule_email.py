#!/usr/bin/env python

"""
camcops_server/alembic/versions/0065_patient_task_schedule_email.py

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

patient_task_schedule_email

Revision ID: 0065
Revises: 0064
Creation date: 2021-06-18 11:58:50.883220

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0065"
down_revision = "0064"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        "_patient_task_schedule_email",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Arbitrary primary key",
        ),
        sa.Column(
            "patient_task_schedule_id",
            sa.Integer(),
            nullable=False,
            comment="FK to _patient_task_schedule.id",
        ),
        sa.Column(
            "email_id",
            sa.BigInteger(),
            nullable=False,
            comment="FK to _emails.id",
        ),
        sa.ForeignKeyConstraint(
            ["email_id"],
            ["_emails.id"],
            name=op.f("fk__patient_task_schedule_email_email_id"),
        ),
        sa.ForeignKeyConstraint(
            ["patient_task_schedule_id"],
            ["_patient_task_schedule.id"],
            name=op.f(
                "fk__patient_task_schedule_email_patient_task_schedule_id"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk__patient_task_schedule_email")
        ),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table("_patient_task_schedule_email")
