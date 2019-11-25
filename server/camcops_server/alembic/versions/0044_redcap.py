#!/usr/bin/env python

"""
camcops_server/alembic/versions/0044_recap.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

DATABASE REVISION SCRIPT

redcap

Revision ID: 0044
Revises: 0043
Creation date: 2019-11-25 15:06:43.988209

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
import cardinal_pythonlib.sqlalchemy.list_types
import camcops_server.cc_modules.cc_sqla_coltypes


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0044'
down_revision = '0043'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    op.create_table(
        '_redcap_record',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Arbitrary primary key'),
        sa.Column('redcap_record_id', sa.Integer(), nullable=True, comment='REDCap record ID'),
        sa.Column('which_idnum', sa.Integer(), nullable=False, comment="Which of the server's ID numbers is this?"),
        sa.Column('idnum_value', sa.BigInteger(), nullable=True, comment='The value of the ID number'),
        sa.ForeignKeyConstraint(['which_idnum'], ['_idnum_definitions.which_idnum'], name=op.f('fk__redcap_record_which_idnum')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__redcap_record')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )

    op.create_table(
        '_exported_task_redcap',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Arbitrary primary key'),
        sa.Column('exported_task_id', sa.BigInteger(), nullable=False, comment='FK to _exported_tasks.id'),
        sa.Column('redcap_record_id', sa.Integer(), nullable=True, comment='FK to _redcap_record.id'),
        sa.ForeignKeyConstraint(['exported_task_id'], ['_exported_tasks.id'], name=op.f('fk__exported_task_redcap_exported_task_id')),
        sa.ForeignKeyConstraint(['redcap_record_id'], ['_redcap_record.id'], name=op.f('fk__exported_task_redcap_redcap_record_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__exported_task_redcap')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )

def downgrade():
    op.drop_table('_exported_task_redcap')
    op.drop_table('_redcap_record')
