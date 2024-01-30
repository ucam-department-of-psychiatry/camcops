#!/usr/bin/env python

"""
camcops_server/alembic/versions/0084.py

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

Compulsive Exercise Test (CET)

Revision ID: 0084
Revises: 0083
Creation date: 2023-12-21 13:12:48.840448

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

revision = "0084"
down_revision = "0083"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        "cet",
        sa.Column(
            "q1",
            sa.Integer(),
            nullable=True,
            comment="Q1 (exercise makes happier/positive) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q2",
            sa.Integer(),
            nullable=True,
            comment="Q2 (exercise to improve appearance) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q3",
            sa.Integer(),
            nullable=True,
            comment="Q3 (exercise part of organised/structured day) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q4",
            sa.Integer(),
            nullable=True,
            comment="Q4 (exercise makes less anxious) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q5",
            sa.Integer(),
            nullable=True,
            comment="Q5 (exercise a chore) " "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q6",
            sa.Integer(),
            nullable=True,
            comment="Q6 (exercise if eat too much) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q7",
            sa.Integer(),
            nullable=True,
            comment="Q7 (exercise pattern repetitive) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q8",
            sa.Integer(),
            nullable=True,
            comment="Q8 (do not exercise to be slim) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q9",
            sa.Integer(),
            nullable=True,
            comment="Q9 (low/depressed if cannot exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q10",
            sa.Integer(),
            nullable=True,
            comment="Q10 (guilty if miss exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q11",
            sa.Integer(),
            nullable=True,
            comment="Q11 (continue exercise despite injury/illness) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q12",
            sa.Integer(),
            nullable=True,
            comment="Q12 (enjoy exercise) " "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q13",
            sa.Integer(),
            nullable=True,
            comment="Q13 (exercise to burn calories/lose weight) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q14",
            sa.Integer(),
            nullable=True,
            comment="Q14 (exercise makes less stressed) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q15",
            sa.Integer(),
            nullable=True,
            comment="Q15 (compensate if miss exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q16",
            sa.Integer(),
            nullable=True,
            comment="Q16 (agitated/irritable if cannot exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q17",
            sa.Integer(),
            nullable=True,
            comment="Q17 (exercise improves mood) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q18",
            sa.Integer(),
            nullable=True,
            comment="Q18 (worry will gain weight if cannot exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q19",
            sa.Integer(),
            nullable=True,
            comment="Q19 (set routine for exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q20",
            sa.Integer(),
            nullable=True,
            comment="Q20 (angry/frustrated if cannot exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q21",
            sa.Integer(),
            nullable=True,
            comment="Q21 (do not enjoy exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q22",
            sa.Integer(),
            nullable=True,
            comment="Q22 (feel have let self down if miss exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q23",
            sa.Integer(),
            nullable=True,
            comment="Q23 (anxious if cannot exercise) "
            "(0 never true - 5 always true)",
        ),
        sa.Column(
            "q24",
            sa.Integer(),
            nullable=True,
            comment="Q24 (less depressed/low after exercise) "
            "(0 never true - 5 always true)",
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
            comment="(TASK) Date/time this task instance was created "
            "(ISO 8601)",
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(TASK) Date/time of the first exit from this task "
            "(ISO 8601)",
        ),
        sa.Column(
            "firstexit_is_finish",
            sa.Boolean(),
            nullable=True,
            comment="(TASK) Was the first exit from the task because it was "
            "finished (1)?",
        ),
        sa.Column(
            "firstexit_is_abort",
            sa.Boolean(),
            nullable=True,
            comment="(TASK) Was the first exit from this task because it was "
            "aborted (1)?",
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
            comment="(SERVER) 'NOW', or when this row was preserved and "
            "removed from the source device (UTC ISO 8601)",
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
            comment="(SERVER) Date/time of the upload batch that added this "
            "row (DATETIME in UTC)",
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
            comment="(SERVER) Date/time this row was removed, i.e. made not "
            "current (ISO 8601)",
        ),
        sa.Column(
            "_when_removed_batch_utc",
            sa.DateTime(),
            nullable=True,
            comment="(SERVER) Date/time of the upload batch that removed this "
            "row (DATETIME in UTC)",
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
            comment="(SERVER) Forcibly preserved by superuser (rather than "
            "normally preserved by tablet)?",
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
            comment="(SERVER) PK of successor record  (after modification) or "
            "NULL (whilst live, or after deletion)",
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
            comment="(STANDARD) Date/time this row was last modified on the "
            "source tablet device (ISO 8601)",
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
            name=op.f("fk_cet__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_cet__device_id"),
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_cet__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_cet__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_cet__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_cet__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_cet")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("cet", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_cet__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_cet__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_cet__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_cet__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_cet__pk"), ["_pk"], unique=False)
        batch_op.create_index(batch_op.f("ix_cet_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_cet_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_cet_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_cet__device_id"),
            "_security_devices",
            ["_device_id"],
            ["id"],
            use_alter=True,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table("cet")
