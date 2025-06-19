"""
camcops_server/alembic/versions/0086_hamd_specific_comments.py

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

hamd_specific_comments

Revision ID: 0086
Revises: 0085
Creation date: 2025-02-10 10:15:58.356359

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0086"
down_revision = "0085"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade() -> None:
    with op.batch_alter_table("hamd", schema=None) as batch_op:
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment="Q1, depressed mood (scored 0-4, higher worse)",
            existing_comment=(
                "Q1, depressed mood (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment="Q2, guilt (scored 0-4, higher worse)",
            existing_comment=(
                "Q2, guilt (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment="Q3, suicide (scored 0-4, higher worse)",
            existing_comment=(
                "Q3, suicide (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment="Q4, early insomnia (scored 0-2, higher worse)",
            existing_comment=(
                "Q4, early insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment="Q5, middle insomnia (scored 0-2, higher worse)",
            existing_comment=(
                "Q5, middle insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment="Q6, late insomnia (scored 0-2, higher worse)",
            existing_comment=(
                "Q6, late insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment="Q7, work/activities (scored 0-4, higher worse)",
            existing_comment=(
                "Q7, work/activities (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q8",
            existing_type=sa.Integer(),
            comment="Q8, psychomotor retardation (scored 0-4, higher worse)",
            existing_comment=(
                "Q8, psychomotor retardation (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q9",
            existing_type=sa.Integer(),
            comment="Q9, agitation (scored 0-4, higher worse)",
            existing_comment=(
                "Q9, agitation (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q10",
            existing_type=sa.Integer(),
            comment="Q10, anxiety, psychological (scored 0-4, higher worse)",
            existing_comment=(
                "Q10, anxiety, psychological (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q11",
            existing_type=sa.Integer(),
            comment="Q11, anxiety, somatic (scored 0-4, higher worse)",
            existing_comment=(
                "Q11, anxiety, somatic (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q12",
            existing_type=sa.Integer(),
            comment=(
                "Q12, somatic symptoms, gastointestinal (scored 0-2, higher"
                " worse)"
            ),
            existing_comment=(
                "Q12, somatic symptoms, gastointestinal (scored 0-4, except"
                " 0-2 for Q4-6/12-14, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q13",
            existing_type=sa.Integer(),
            comment=(
                "Q13, somatic symptoms, general (scored 0-2, higher worse)"
            ),
            existing_comment=(
                "Q13, somatic symptoms, general (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q14",
            existing_type=sa.Integer(),
            comment="Q14, genital symptoms (scored 0-2, higher worse)",
            existing_comment=(
                "Q14, genital symptoms (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q15",
            existing_type=sa.Integer(),
            comment="Q15, hypochondriasis (scored 0-4, higher worse)",
            existing_comment=(
                "Q15, hypochondriasis (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q19",
            existing_type=sa.Integer(),
            comment=(
                "Q19 (not scored), depersonalization/derealization (0-4,"
                " higher worse)"
            ),
            existing_comment=(
                "Q19 (not scored), depersonalization/derealization (0-4 for"
                " Q19, 0-3 for Q20, 0-2 for Q21, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q20",
            existing_type=sa.Integer(),
            comment="Q20 (not scored), paranoid symptoms (0-3, higher worse)",
            existing_comment=(
                "Q20 (not scored), paranoid symptoms (0-4 for Q19, 0-3 for"
                " Q20, 0-2 for Q21, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q21",
            existing_type=sa.Integer(),
            comment=(
                "Q21 (not scored), obsessional/compulsive symptoms (0-2,"
                " higher worse)"
            ),
            existing_comment=(
                "Q21 (not scored), obsessional/compulsive symptoms (0-4 for"
                " Q19, 0-3 for Q20, 0-2 for Q21, higher worse)"
            ),
            existing_nullable=True,
        )

    with op.batch_alter_table("hamd7", schema=None) as batch_op:
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment="Q1, depressed mood (0-4, higher worse)",
            existing_comment=(
                "Q1, depressed mood (0-4, except Q6 0-2; higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment="Q2, guilt (0-4, higher worse)",
            existing_comment="Q2, guilt (0-4, except Q6 0-2; higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment=(
                "Q3, interest/pleasure/level of activities (0-4, higher worse)"
            ),
            existing_comment=(
                "Q3, interest/pleasure/level of activities (0-4, except Q6"
                " 0-2; higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment="Q4, psychological anxiety (0-4, higher worse)",
            existing_comment=(
                "Q4, psychological anxiety (0-4, except Q6 0-2; higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment="Q5, somatic anxiety (0-4, higher worse)",
            existing_comment=(
                "Q5, somatic anxiety (0-4, except Q6 0-2; higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment="Q6, energy/somatic symptoms (0-2, higher worse)",
            existing_comment=(
                "Q6, energy/somatic symptoms (0-4, except Q6 0-2; higher"
                " worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment="Q7, suicide (0-4, higher worse)",
            existing_comment="Q7, suicide (0-4, except Q6 0-2; higher worse)",
            existing_nullable=True,
        )


# noinspection PyPep8,PyTypeChecker
def downgrade() -> None:
    with op.batch_alter_table("hamd7", schema=None) as batch_op:
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment="Q7, suicide (0-4, except Q6 0-2; higher worse)",
            existing_comment="Q7, suicide (0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment=(
                "Q6, energy/somatic symptoms (0-4, except Q6 0-2; higher"
                " worse)"
            ),
            existing_comment="Q6, energy/somatic symptoms (0-2, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment="Q5, somatic anxiety (0-4, except Q6 0-2; higher worse)",
            existing_comment="Q5, somatic anxiety (0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment=(
                "Q4, psychological anxiety (0-4, except Q6 0-2; higher worse)"
            ),
            existing_comment="Q4, psychological anxiety (0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment=(
                "Q3, interest/pleasure/level of activities (0-4, except Q6"
                " 0-2; higher worse)"
            ),
            existing_comment=(
                "Q3, interest/pleasure/level of activities (0-4, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment="Q2, guilt (0-4, except Q6 0-2; higher worse)",
            existing_comment="Q2, guilt (0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment="Q1, depressed mood (0-4, except Q6 0-2; higher worse)",
            existing_comment="Q1, depressed mood (0-4, higher worse)",
            existing_nullable=True,
        )

    with op.batch_alter_table("hamd", schema=None) as batch_op:
        batch_op.alter_column(
            "q21",
            existing_type=sa.Integer(),
            comment=(
                "Q21 (not scored), obsessional/compulsive symptoms (0-4 for"
                " Q19, 0-3 for Q20, 0-2 for Q21, higher worse)"
            ),
            existing_comment=(
                "Q21 (not scored), obsessional/compulsive symptoms (0-2,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q20",
            existing_type=sa.Integer(),
            comment=(
                "Q20 (not scored), paranoid symptoms (0-4 for Q19, 0-3 for"
                " Q20, 0-2 for Q21, higher worse)"
            ),
            existing_comment=(
                "Q20 (not scored), paranoid symptoms (0-3, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q19",
            existing_type=sa.Integer(),
            comment=(
                "Q19 (not scored), depersonalization/derealization (0-4 for"
                " Q19, 0-3 for Q20, 0-2 for Q21, higher worse)"
            ),
            existing_comment=(
                "Q19 (not scored), depersonalization/derealization (0-4,"
                " higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q15",
            existing_type=sa.Integer(),
            comment=(
                "Q15, hypochondriasis (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q15, hypochondriasis (scored 0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q14",
            existing_type=sa.Integer(),
            comment=(
                "Q14, genital symptoms (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment=(
                "Q14, genital symptoms (scored 0-2, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q13",
            existing_type=sa.Integer(),
            comment=(
                "Q13, somatic symptoms, general (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_comment=(
                "Q13, somatic symptoms, general (scored 0-2, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q12",
            existing_type=sa.Integer(),
            comment=(
                "Q12, somatic symptoms, gastointestinal (scored 0-4, except"
                " 0-2 for Q4-6/12-14, higher worse)"
            ),
            existing_comment=(
                "Q12, somatic symptoms, gastointestinal (scored 0-2, higher"
                " worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q11",
            existing_type=sa.Integer(),
            comment=(
                "Q11, anxiety, somatic (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment=(
                "Q11, anxiety, somatic (scored 0-4, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q10",
            existing_type=sa.Integer(),
            comment=(
                "Q10, anxiety, psychological (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_comment=(
                "Q10, anxiety, psychological (scored 0-4, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q9",
            existing_type=sa.Integer(),
            comment=(
                "Q9, agitation (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_comment="Q9, agitation (scored 0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q8",
            existing_type=sa.Integer(),
            comment=(
                "Q8, psychomotor retardation (scored 0-4, except 0-2 for"
                " Q4-6/12-14, higher worse)"
            ),
            existing_comment=(
                "Q8, psychomotor retardation (scored 0-4, higher worse)"
            ),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q7",
            existing_type=sa.Integer(),
            comment=(
                "Q7, work/activities (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q7, work/activities (scored 0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q6",
            existing_type=sa.Integer(),
            comment=(
                "Q6, late insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q6, late insomnia (scored 0-2, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q5",
            existing_type=sa.Integer(),
            comment=(
                "Q5, middle insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q5, middle insomnia (scored 0-2, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q4",
            existing_type=sa.Integer(),
            comment=(
                "Q4, early insomnia (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q4, early insomnia (scored 0-2, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q3",
            existing_type=sa.Integer(),
            comment=(
                "Q3, suicide (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_comment="Q3, suicide (scored 0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q2",
            existing_type=sa.Integer(),
            comment=(
                "Q2, guilt (scored 0-4, except 0-2 for Q4-6/12-14, higher"
                " worse)"
            ),
            existing_comment="Q2, guilt (scored 0-4, higher worse)",
            existing_nullable=True,
        )
        batch_op.alter_column(
            "q1",
            existing_type=sa.Integer(),
            comment=(
                "Q1, depressed mood (scored 0-4, except 0-2 for Q4-6/12-14,"
                " higher worse)"
            ),
            existing_comment="Q1, depressed mood (scored 0-4, higher worse)",
            existing_nullable=True,
        )
