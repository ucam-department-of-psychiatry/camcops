#!/usr/bin/env python

"""
camcops_server/alembic/versions/0081_isaaq10.py

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

isaaq10

Revision ID: 0081
Revises: 0080
Creation date: 2023-02-20 15:18:03.573249

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa

from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    SemanticVersionColType,
)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0081"
down_revision = "0080"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        "isaaq10",
        sa.Column(
            "a1",
            sa.Integer(),
            nullable=True,
            comment=(
                "a1 - losing track of time 0-5 (not at all - all the time)"
            ),
        ),
        sa.Column(
            "a2",
            sa.Integer(),
            nullable=True,
            comment=(
                "a2 - block disturbing thoughts 0-5 (not at all - all the"
                " time)"
            ),
        ),
        sa.Column(
            "a3",
            sa.Integer(),
            nullable=True,
            comment=(
                "a3 - loneliness or boredom 0-5 (not at all - all the time)"
            ),
        ),
        sa.Column(
            "a4",
            sa.Integer(),
            nullable=True,
            comment=(
                "a4 - neglect normal activities 0-5 (not at all - all the"
                " time)"
            ),
        ),
        sa.Column(
            "a5",
            sa.Integer(),
            nullable=True,
            comment=(
                "a5 - school/study suffers 0-5 (not at all - all the time)"
            ),
        ),
        sa.Column(
            "a6",
            sa.Integer(),
            nullable=True,
            comment="a6 - try to stop 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "a7",
            sa.Integer(),
            nullable=True,
            comment=(
                "a7 - preoccupied when offline 0-5 (not at all - all the time)"
            ),
        ),
        sa.Column(
            "a8",
            sa.Integer(),
            nullable=True,
            comment="a8 - lose sleep 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "a9",
            sa.Integer(),
            nullable=True,
            comment=(
                "a9 - physical or psychological problems 0-5 (not at all - all"
                " the time)"
            ),
        ),
        sa.Column(
            "a10",
            sa.Integer(),
            nullable=True,
            comment="a10 - try to cut down 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b1",
            sa.Integer(),
            nullable=True,
            comment="b1 - general surfing 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b2",
            sa.Integer(),
            nullable=True,
            comment="b2 - internet gaming 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b3",
            sa.Integer(),
            nullable=True,
            comment="b3 - skill games 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b4",
            sa.Integer(),
            nullable=True,
            comment="b4 - online shopping 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b5",
            sa.Integer(),
            nullable=True,
            comment="b5 - online gaming 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b6",
            sa.Integer(),
            nullable=True,
            comment="b6 - social networking 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b7",
            sa.Integer(),
            nullable=True,
            comment="b7 - health and medicine 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b8",
            sa.Integer(),
            nullable=True,
            comment="b8 - pornography 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b9",
            sa.Integer(),
            nullable=True,
            comment="b9 - streaming media 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "b10",
            sa.Integer(),
            nullable=True,
            comment="b10 - cyberbullying 0-5 (not at all - all the time)",
        ),
        sa.Column(
            "patient_id",
            sa.Integer(),
            nullable=False,
            comment="(TASK) Foreign key to patient.id (for this device/era)",
        ),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
            comment=(
                "(TASK) Date/time this task instance was created (ISO 8601)"
            ),
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment=(
                "(TASK) Date/time of the first exit from this task (ISO 8601)"
            ),
        ),
        sa.Column(
            "firstexit_is_finish",
            sa.Boolean(),
            nullable=True,
            comment=(
                "(TASK) Was the first exit from the task because it was"
                " finished (1)?"
            ),
        ),
        sa.Column(
            "firstexit_is_abort",
            sa.Boolean(),
            nullable=True,
            comment=(
                "(TASK) Was the first exit from this task because it was"
                " aborted (1)?"
            ),
        ),
        sa.Column(
            "editing_time_s",
            sa.Float(),
            nullable=True,
            comment="(TASK) Time spent editing (s)",
        ),
        sa.Column(
            "_pk",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="(SERVER) Primary key (on the server)",
        ),
        sa.Column(
            "_device_id",
            sa.Integer(),
            nullable=False,
            comment="(SERVER) ID of the source tablet device",
        ),
        sa.Column(
            "_era",
            sa.String(length=32),
            nullable=False,
            comment=(
                "(SERVER) 'NOW', or when this row was preserved and removed"
                " from the source device (UTC ISO 8601)"
            ),
        ),
        sa.Column(
            "_current",
            sa.Boolean(),
            nullable=False,
            comment="(SERVER) Is the row current (1) or not (0)?",
        ),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(SERVER) Date/time this row was added (ISO 8601)",
        ),
        sa.Column(
            "_when_added_batch_utc",
            sa.DateTime(),
            nullable=True,
            comment=(
                "(SERVER) Date/time of the upload batch that added this row"
                " (DATETIME in UTC)"
            ),
        ),
        sa.Column(
            "_adding_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that added this row",
        ),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment=(
                "(SERVER) Date/time this row was removed, i.e. made not"
                " current (ISO 8601)"
            ),
        ),
        sa.Column(
            "_when_removed_batch_utc",
            sa.DateTime(),
            nullable=True,
            comment=(
                "(SERVER) Date/time of the upload batch that removed this row"
                " (DATETIME in UTC)"
            ),
        ),
        sa.Column(
            "_removing_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that removed this row",
        ),
        sa.Column(
            "_preserving_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that preserved this row",
        ),
        sa.Column(
            "_forcibly_preserved",
            sa.Boolean(),
            nullable=True,
            comment=(
                "(SERVER) Forcibly preserved by superuser (rather than"
                " normally preserved by tablet)?"
            ),
        ),
        sa.Column(
            "_predecessor_pk",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) PK of predecessor record, prior to modification",
        ),
        sa.Column(
            "_successor_pk",
            sa.Integer(),
            nullable=True,
            comment=(
                "(SERVER) PK of successor record  (after modification) or NULL"
                " (whilst live, or after deletion)"
            ),
        ),
        sa.Column(
            "_manually_erased",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER) Record manually erased (content destroyed)?",
        ),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(SERVER) Date/time of manual erasure (ISO 8601)",
        ),
        sa.Column(
            "_manually_erasing_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that erased this row manually",
        ),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
            comment="(SERVER) CamCOPS version number of the uploading device",
        ),
        sa.Column(
            "_addition_pending",
            sa.Boolean(),
            nullable=False,
            comment="(SERVER) Addition pending?",
        ),
        sa.Column(
            "_removal_pending",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER) Removal pending?",
        ),
        sa.Column(
            "_group_id",
            sa.Integer(),
            nullable=False,
            comment="(SERVER) ID of group to which this record belongs",
        ),
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            comment="(TASK) Primary key (task ID) on the tablet device",
        ),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment=(
                "(STANDARD) Date/time this row was last modified on the source"
                " tablet device (ISO 8601)"
            ),
        ),
        sa.Column(
            "_move_off_tablet",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER/TABLET) Record-specific preservation pending?",
        ),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_isaaq10__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_isaaq10__device_id"),
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_isaaq10__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_isaaq10__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_isaaq10__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_isaaq10__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_isaaq10")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("isaaq10", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_isaaq10__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10__pk"), ["_pk"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_isaaq10_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )
        # https://github.com/sqlalchemy/alembic/issues/326
        batch_op.create_foreign_key(
            batch_op.f("fk_isaaq10__device_id"),
            "_security_devices",
            ["_device_id"],
            ["id"],
            use_alter=True,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table("isaaq10")
