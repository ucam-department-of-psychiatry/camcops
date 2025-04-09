"""
camcops_server/alembic/versions/0085_aq.py

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

aq

Revision ID: 0085
Revises: 0084
Creation date: 2024-06-17 11:30:57.183986

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

revision = "0085"
down_revision = "0084"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade() -> None:
    op.create_table(
        "aq",
        sa.Column(
            "q1",
            sa.Integer(),
            nullable=True,
            comment="q1 - prefer doing things with others",
        ),
        sa.Column(
            "q2",
            sa.Integer(),
            nullable=True,
            comment="q2 - prefer doing things the same way",
        ),
        sa.Column(
            "q3",
            sa.Integer(),
            nullable=True,
            comment="q3 - can create picture in mind",
        ),
        sa.Column(
            "q4",
            sa.Integer(),
            nullable=True,
            comment="q4 - get strongly absorbed in one thing",
        ),
        sa.Column(
            "q5",
            sa.Integer(),
            nullable=True,
            comment="q5 - notice small sounds",
        ),
        sa.Column(
            "q6",
            sa.Integer(),
            nullable=True,
            comment="q6 - notice car number plates",
        ),
        sa.Column(
            "q7",
            sa.Integer(),
            nullable=True,
            comment="q7 - what I’ve said is impolite",
        ),
        sa.Column(
            "q8",
            sa.Integer(),
            nullable=True,
            comment="q8 - can imagine what story characters look like",
        ),
        sa.Column(
            "q9",
            sa.Integer(),
            nullable=True,
            comment="q9 - fascinated by dates",
        ),
        sa.Column(
            "q10",
            sa.Integer(),
            nullable=True,
            comment="q10 - can keep track of conversations",
        ),
        sa.Column(
            "q11",
            sa.Integer(),
            nullable=True,
            comment="q11 - find social situations easy",
        ),
        sa.Column(
            "q12", sa.Integer(), nullable=True, comment="q12 - notice details"
        ),
        sa.Column(
            "q13",
            sa.Integer(),
            nullable=True,
            comment="q13 - prefer library to party",
        ),
        sa.Column(
            "q14",
            sa.Integer(),
            nullable=True,
            comment="q14 - find making up stories easy",
        ),
        sa.Column(
            "q15",
            sa.Integer(),
            nullable=True,
            comment="q15 - drawn more strongly to people",
        ),
        sa.Column(
            "q16",
            sa.Integer(),
            nullable=True,
            comment="q16 - upset if can't pursue strong interests",
        ),
        sa.Column(
            "q17", sa.Integer(), nullable=True, comment="q17 - enjoy chit-chat"
        ),
        sa.Column(
            "q18",
            sa.Integer(),
            nullable=True,
            comment="q18 - not easy for others to get a word in edgeways",
        ),
        sa.Column(
            "q19",
            sa.Integer(),
            nullable=True,
            comment="q19 - fascinated by numbers",
        ),
        sa.Column(
            "q20",
            sa.Integer(),
            nullable=True,
            comment="q20 - can't work out story characters’ intentions",
        ),
        sa.Column(
            "q21",
            sa.Integer(),
            nullable=True,
            comment="q21 - don’t enjoy fiction",
        ),
        sa.Column(
            "q22",
            sa.Integer(),
            nullable=True,
            comment="q22 - hard to make new friends",
        ),
        sa.Column(
            "q23", sa.Integer(), nullable=True, comment="q23 - notice patterns"
        ),
        sa.Column(
            "q24",
            sa.Integer(),
            nullable=True,
            comment="q24 - prefer theatre to museum",
        ),
        sa.Column(
            "q25",
            sa.Integer(),
            nullable=True,
            comment="q25 - not upset if daily routine disturbed",
        ),
        sa.Column(
            "q26",
            sa.Integer(),
            nullable=True,
            comment="q26 - don't know how to keep conversation going",
        ),
        sa.Column(
            "q27",
            sa.Integer(),
            nullable=True,
            comment="q27 - easy to read between the lines",
        ),
        sa.Column(
            "q28",
            sa.Integer(),
            nullable=True,
            comment="q28 - concentrate more on whole picture",
        ),
        sa.Column(
            "q29",
            sa.Integer(),
            nullable=True,
            comment="q29 - can't remember phone numbers",
        ),
        sa.Column(
            "q30",
            sa.Integer(),
            nullable=True,
            comment="q30 - don’t notice small changes",
        ),
        sa.Column(
            "q31",
            sa.Integer(),
            nullable=True,
            comment="q31 - can tell if person listening is bored",
        ),
        sa.Column(
            "q32",
            sa.Integer(),
            nullable=True,
            comment="q32 - easy to do more than one thing",
        ),
        sa.Column(
            "q33",
            sa.Integer(),
            nullable=True,
            comment="q33 - not sure when to speak on phone",
        ),
        sa.Column(
            "q34",
            sa.Integer(),
            nullable=True,
            comment="q34 - enjoy doing things spontaneously",
        ),
        sa.Column(
            "q35",
            sa.Integer(),
            nullable=True,
            comment="q35 - last to understand joke",
        ),
        sa.Column(
            "q36",
            sa.Integer(),
            nullable=True,
            comment="q36 - can work out thinking or feeling from face",
        ),
        sa.Column(
            "q37",
            sa.Integer(),
            nullable=True,
            comment="q37 - can switch back after interruption",
        ),
        sa.Column(
            "q38",
            sa.Integer(),
            nullable=True,
            comment="q38 - good at chit-chat",
        ),
        sa.Column(
            "q39",
            sa.Integer(),
            nullable=True,
            comment="q39 - keep going on and on about the same thing",
        ),
        sa.Column(
            "q40",
            sa.Integer(),
            nullable=True,
            comment="q40 - used to enjoy pretending games with other children",
        ),
        sa.Column(
            "q41",
            sa.Integer(),
            nullable=True,
            comment=(
                "q41 - like to collect information about categories of things"
            ),
        ),
        sa.Column(
            "q42",
            sa.Integer(),
            nullable=True,
            comment="q42 - difficult to imagine being someone else",
        ),
        sa.Column(
            "q43",
            sa.Integer(),
            nullable=True,
            comment="q43 - like to plan activities carefully",
        ),
        sa.Column(
            "q44",
            sa.Integer(),
            nullable=True,
            comment="q44 - enjoy social occasions",
        ),
        sa.Column(
            "q45",
            sa.Integer(),
            nullable=True,
            comment="q45 - difficult to work out people’s intentions",
        ),
        sa.Column(
            "q46",
            sa.Integer(),
            nullable=True,
            comment="q46 - new situations make me anxious",
        ),
        sa.Column(
            "q47",
            sa.Integer(),
            nullable=True,
            comment="q47 - enjoy meeting new people",
        ),
        sa.Column(
            "q48",
            sa.Integer(),
            nullable=True,
            comment="q48 - am a good diplomat",
        ),
        sa.Column(
            "q49",
            sa.Integer(),
            nullable=True,
            comment=(
                "q49 - not very good at remembering people’s date of birth"
            ),
        ),
        sa.Column(
            "q50",
            sa.Integer(),
            nullable=True,
            comment="q50 - easy to play pretending games with children",
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
                "(SERVER) Date/time this row was removed, i.e. made not "
                "current (ISO 8601)"
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
                "(SERVER) Forcibly preserved by superuser (rather than "
                "normally preserved by tablet)?"
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
            name=op.f("fk_aq__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_aq__device_id"),
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_aq__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_aq__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_aq__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_aq__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_aq")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("aq", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_aq__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_aq__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_aq__era"), ["_era"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_aq__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_aq__pk"), ["_pk"], unique=False)
        batch_op.create_index(batch_op.f("ix_aq_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_aq_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_aq_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    with op.batch_alter_table("aq", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_aq__device_id"),
            "_security_devices",
            ["_device_id"],
            ["id"],
            use_alter=True,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade() -> None:
    op.drop_table("aq")
