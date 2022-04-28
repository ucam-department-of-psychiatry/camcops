#!/usr/bin/env python

"""
camcops_server/alembic/versions/0071_fhir.py

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

fhir

Revision ID: 0071
Revises: 0070
Creation date: 2021-05-24 17:22:51.871622

[renamed from 0064 to 0071 at merge, 2021-11-02]

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0071"
down_revision = "0070"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        "_exported_task_fhir",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Arbitrary primary key",
        ),
        sa.Column(
            "exported_task_id",
            sa.BigInteger(),
            nullable=False,
            comment="FK to _exported_tasks.id",
        ),
        sa.ForeignKeyConstraint(
            ["exported_task_id"],
            ["_exported_tasks.id"],
            name=op.f("fk__exported_task_fhir_exported_task_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__exported_task_fhir")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    op.create_table(
        "_exported_task_fhir_entry",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Arbitrary primary key",
        ),
        sa.Column(
            "exported_task_fhir_id",
            sa.Integer(),
            nullable=False,
            comment="FK to _exported_task_fhir.id",
        ),
        sa.Column(
            "etag",
            sa.UnicodeText(),
            nullable=True,
            comment="The ETag for the resource (if relevant)",
        ),
        sa.Column(
            "last_modified",
            sa.DateTime(),
            nullable=True,
            comment="Server's date/time modified.",
        ),
        sa.Column(
            "location",
            sa.UnicodeText(),
            nullable=True,
            comment="The location (if the operation returns a location).",
        ),
        sa.Column(
            "status",
            sa.UnicodeText(),
            nullable=True,
            comment="Status response code (text optional).",
        ),
        sa.ForeignKeyConstraint(
            ["exported_task_fhir_id"],
            ["_exported_task_fhir.id"],
            name=op.f("fk__exported_task_fhir_entry_exported_task_fhir_id"),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk__exported_task_fhir_entry")
        ),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_export_recipients", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "fhir_api_url",
                sa.Text(),
                nullable=True,
                comment="(FHIR) FHIR API URL, pointing to the FHIR server",
            )
        )
        batch_op.add_column(
            sa.Column(
                "fhir_app_id",
                sa.Text(),
                nullable=True,
                comment=(
                    "(FHIR) FHIR app ID, identifying CamCOPS as the data"
                    " source"
                ),
            )
        )
        batch_op.add_column(
            sa.Column(
                "fhir_concurrent",
                sa.Boolean(),
                nullable=True,
                comment=(
                    "(FHIR) Server supports concurrency (parallel processing)?"
                ),
            )
        )
    with op.batch_alter_table("_idnum_definitions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "fhir_id_system",
                sa.String(length=255),
                nullable=True,
                comment="FHIR external ID 'system' URL",
            )
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("_idnum_definitions", schema=None) as batch_op:
        batch_op.drop_column("fhir_id_system")

    with op.batch_alter_table("_export_recipients", schema=None) as batch_op:
        batch_op.drop_column("fhir_concurrent")
        batch_op.drop_column("fhir_app_id")
        batch_op.drop_column("fhir_api_url")

    op.drop_table("_exported_task_fhir_entry")
    op.drop_table("_exported_task_fhir")
