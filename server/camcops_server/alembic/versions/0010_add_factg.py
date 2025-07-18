"""
camcops_server/alembic/versions/0010_add_factg.py

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

add factg

Revision ID: 0010
Revises: 0009
Creation date: 2018-10-16 09:15:16.914729

DATABASE REVISION SCRIPT

"""

# =============================================================================
# Imports
# =============================================================================

import sqlalchemy as sa
from alembic import op

from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    SemanticVersionColType,
)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "factg",
        sa.Column("ignore_s_q7", sa.Boolean(), nullable=True),
        sa.Column("p_q1", sa.Integer(), nullable=True),
        sa.Column("p_q2", sa.Integer(), nullable=True),
        sa.Column("p_q3", sa.Integer(), nullable=True),
        sa.Column("p_q4", sa.Integer(), nullable=True),
        sa.Column("p_q5", sa.Integer(), nullable=True),
        sa.Column("p_q6", sa.Integer(), nullable=True),
        sa.Column("p_q7", sa.Integer(), nullable=True),
        sa.Column("s_q1", sa.Integer(), nullable=True),
        sa.Column("s_q2", sa.Integer(), nullable=True),
        sa.Column("s_q3", sa.Integer(), nullable=True),
        sa.Column("s_q4", sa.Integer(), nullable=True),
        sa.Column("s_q5", sa.Integer(), nullable=True),
        sa.Column("s_q6", sa.Integer(), nullable=True),
        sa.Column("s_q7", sa.Integer(), nullable=True),
        sa.Column("e_q1", sa.Integer(), nullable=True),
        sa.Column("e_q2", sa.Integer(), nullable=True),
        sa.Column("e_q3", sa.Integer(), nullable=True),
        sa.Column("e_q4", sa.Integer(), nullable=True),
        sa.Column("e_q5", sa.Integer(), nullable=True),
        sa.Column("e_q6", sa.Integer(), nullable=True),
        sa.Column("f_q1", sa.Integer(), nullable=True),
        sa.Column("f_q2", sa.Integer(), nullable=True),
        sa.Column("f_q3", sa.Integer(), nullable=True),
        sa.Column("f_q4", sa.Integer(), nullable=True),
        sa.Column("f_q5", sa.Integer(), nullable=True),
        sa.Column("f_q6", sa.Integer(), nullable=True),
        sa.Column("f_q7", sa.Integer(), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("firstexit_is_finish", sa.Boolean(), nullable=True),
        sa.Column("firstexit_is_abort", sa.Boolean(), nullable=True),
        sa.Column("editing_time_s", sa.Float(), nullable=True),
        sa.Column("_pk", sa.Integer(), nullable=False),
        sa.Column("_device_id", sa.Integer(), nullable=False),
        sa.Column("_era", sa.String(length=32), nullable=False),
        sa.Column("_current", sa.Boolean(), nullable=False),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_added_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_adding_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_removed_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_removing_user_id", sa.Integer(), nullable=True),
        sa.Column("_preserving_user_id", sa.Integer(), nullable=True),
        sa.Column("_forcibly_preserved", sa.Boolean(), nullable=True),
        sa.Column("_predecessor_pk", sa.Integer(), nullable=True),
        sa.Column("_successor_pk", sa.Integer(), nullable=True),
        sa.Column("_manually_erased", sa.Boolean(), nullable=True),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_manually_erasing_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
        ),
        sa.Column("_addition_pending", sa.Boolean(), nullable=False),
        sa.Column("_removal_pending", sa.Boolean(), nullable=True),
        sa.Column("_group_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_move_off_tablet", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_factg__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_factg__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_factg__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_factg__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_factg__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_factg__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_factg")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("factg", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_factg__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_factg__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_factg__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_factg__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_factg__pk"), ["_pk"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_factg_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_factg_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_factg_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    # ### end Alembic commands ###


# noinspection PyPep8,PyTypeChecker
def downgrade() -> None:
    op.drop_table("factg")
