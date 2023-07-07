#!/usr/bin/env python

"""
camcops_server/alembic/versions/0080_chit_update.py.py

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

chit_update

Revision ID: 0080
Revises: 0079
Creation date: 2023-02-14 17:03:07.159418

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0080"
down_revision = "0079"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("chit", schema=None) as batch_op:
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment=(
                "Q1 (hate unfinished task) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q1 (hate unfinished task) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q10",
            existing_type=sa.Integer(),
            comment=(
                "Q10 (hard moving) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_comment=(
                "Q10 (hard moving) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q11",
            existing_type=sa.Integer(),
            comment=(
                "Q11 (higher standards) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q11 (higher standards) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q12",
            existing_type=sa.Integer(),
            comment=(
                "Q12 (improvement) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_comment=(
                "Q12 (improvement) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q13",
            existing_type=sa.Integer(),
            comment="Q13 (complete) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q13 (complete) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q14",
            existing_type=sa.Integer(),
            comment=(
                "Q14 (avoid situations) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q14 (avoid situations) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q15",
            existing_type=sa.Integer(),
            comment="Q15 (hobby) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q15 (hobby) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment="Q2 (just right) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q2 (just right) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment=(
                "Q3 (keep doing task) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_comment=(
                "Q3 (keep doing task) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment="Q4 (get stuck) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q4 (get stuck) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment="Q5 (habit) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q5 (habit) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment="Q6 (addictive) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q6 (addictive) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment=(
                "Q7 (stubborn rigid) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_comment=(
                "Q7 (stubborn rigid) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q8",
            existing_type=sa.Integer(),
            comment="Q8 (urges) (0 strongly disagree - 4 strongly agree)",
            existing_comment=(
                "Q8 (urges) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q9",
            existing_type=sa.Integer(),
            comment=(
                "Q9 (rewarding things) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q9 (rewarding things) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.drop_column("q16")


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("chit", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "q16",
                sa.Boolean(),
                autoincrement=False,
                nullable=True,
                comment="Q16 (negative effect) (0 no, 1 yes)",
            )
        )
        batch_op.alter_column(
            "q9",
            existing_type=sa.Integer(),
            comment=(
                "Q9 (rewarding things) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q9 (rewarding things) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q8",
            existing_type=sa.Integer(),
            comment="Q8 (urges) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q8 (urges) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment=(
                "Q7 (stubborn rigid) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_comment=(
                "Q7 (stubborn rigid) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment="Q6 (addictive) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q6 (addictive) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment="Q5 (habit) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q5 (habit) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment="Q4 (get stuck) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q4 (get stuck) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment=(
                "Q3 (keep doing task) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_comment=(
                "Q3 (keep doing task) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment="Q2 (just right) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q2 (just right) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q15",
            existing_type=sa.Integer(),
            comment="Q15 (hobby) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q15 (hobby) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q14",
            existing_type=sa.Integer(),
            comment=(
                "Q14 (avoid situations) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q14 (avoid situations) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q13",
            existing_type=sa.Integer(),
            comment="Q13 (complete) (0 strongly disagree - 3 strongly agree)",
            existing_comment=(
                "Q13 (complete) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q12",
            existing_type=sa.Integer(),
            comment=(
                "Q12 (improvement) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_comment=(
                "Q12 (improvement) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q11",
            existing_type=sa.Integer(),
            comment=(
                "Q11 (higher standards) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q11 (higher standards) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q10",
            existing_type=sa.Integer(),
            comment=(
                "Q10 (hard moving) (0 strongly disagree - 3 strongly agree)"
            ),
            existing_comment=(
                "Q10 (hard moving) (0 strongly disagree - 4 strongly agree)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment=(
                "Q1 (hate unfinished task) (0 strongly disagree - 3 strongly"
                " agree)"
            ),
            existing_comment=(
                "Q1 (hate unfinished task) (0 strongly disagree - 4 strongly"
                " agree)"
            ),
            existing_nullable=True,
        )
