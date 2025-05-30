"""
camcops_server/alembic/versions/0039_khandaker_mojo_sociodemographics.py

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

khandaker_mojo_sociodemographics

Revision ID: 0039
Revises: 0038
Creation date: 2019-08-12 17:23:42.336508

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

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        "khandaker_mojo_sociodemographics",
        sa.Column(
            "gender",
            sa.Integer(),
            nullable=True,
            comment="Gender at birth (0 Male, 1 Female, 2 Other (specify))",
        ),
        sa.Column(
            "other_gender",
            sa.UnicodeText(),
            nullable=True,
            comment="Other (specify)",
        ),
        sa.Column(
            "ethnicity",
            sa.Integer(),
            nullable=True,
            comment=(
                "Ethnicity (0 White, 1 Mixed, 2 Indian, 3 Pakistani, 4"
                " Bangladeshi, 5 Other Asian, 6 Black Caribbean, 7 Black"
                " African, 8 Black Other, 9 Chinese, 10 Other (specify))"
            ),
        ),
        sa.Column(
            "other_ethnicity",
            sa.UnicodeText(),
            nullable=True,
            comment="Other (specify)",
        ),
        sa.Column(
            "with_whom_live",
            sa.Integer(),
            nullable=True,
            comment=(
                "0 Alone, 1 Alone with children, 2 Partner/Spouse, 3"
                " Partner/Spouse and children, 4 Parents, 5 Other family, 6"
                " Friends, 7 Other (specify)"
            ),
        ),
        sa.Column(
            "other_with_whom_live",
            sa.UnicodeText(),
            nullable=True,
            comment="Other (specify)",
        ),
        sa.Column(
            "relationship_status",
            sa.Integer(),
            nullable=True,
            comment=(
                "0 Single, 1 Married / Civil partnership, 2 In steady"
                " relationship, 3 Divorced / separated, 4 Widowed"
            ),
        ),
        sa.Column(
            "education",
            sa.Integer(),
            nullable=True,
            comment=(
                "0 No qualifications, 1 GCSE/O levels, 2 A levels, 3"
                " Vocational/college (B. Tecs/NVQs etc), 4 University /"
                " Professional Qualifications"
            ),
        ),
        sa.Column(
            "employment",
            sa.Integer(),
            nullable=True,
            comment=(
                "0 No unemployed, 1 No student, 2 Yes full time, 3 Yes part"
                " time, 4 Full time homemaker, 5 Self employed, 6 Not working"
                " for medical reasons, 7 Other (specify)"
            ),
        ),
        sa.Column(
            "other_employment",
            sa.UnicodeText(),
            nullable=True,
            comment="Other (specify)",
        ),
        sa.Column(
            "accommodation",
            sa.Integer(),
            nullable=True,
            comment=(
                "0 Own outright, 1 Own with mortgage, 2 Rent from local"
                " authority etc, 3 Rent from landlord (private), 4 Shared"
                " ownership (part rent, part mortgage)5 Live rent free, 6"
                " Other (specify)"
            ),
        ),
        sa.Column(
            "other_accommodation",
            sa.UnicodeText(),
            nullable=True,
            comment="Other (specify)",
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
            name=op.f("fk_khandaker_mojo_sociodemographics__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_khandaker_mojo_sociodemographics__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_khandaker_mojo_sociodemographics__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f(
                "fk_khandaker_mojo_sociodemographics__manually_erasing_user_id"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f(
                "fk_khandaker_mojo_sociodemographics__preserving_user_id"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_khandaker_mojo_sociodemographics__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint(
            "_pk", name=op.f("pk_khandaker_mojo_sociodemographics")
        ),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table(
        "khandaker_mojo_sociodemographics", schema=None
    ) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics__current"),
            ["_current"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics__device_id"),
            ["_device_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics__era"),
            ["_era"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics__group_id"),
            ["_group_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics__pk"),
            ["_pk"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics_id"),
            ["id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_khandaker_mojo_sociodemographics_patient_id"),
            ["patient_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f(
                "ix_khandaker_mojo_sociodemographics_when_last_modified"
            ),
            ["when_last_modified"],
            unique=False,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table("khandaker_mojo_sociodemographics")
