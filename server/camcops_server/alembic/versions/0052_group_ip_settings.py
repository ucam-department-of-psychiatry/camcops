#!/usr/bin/env python

"""
camcops_server/alembic/versions/0052_group_ip_settings.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

group_ip_settings

Revision ID: 0052
Revises: 0051
Creation date: 2020-09-03 17:01:48.375095

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

revision = '0052'
down_revision = '0051'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table('_security_groups', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'ip_use_clinical', sa.Boolean(),
            nullable=False,
            comment='Group operates in a clinical setting')
        )
        batch_op.add_column(sa.Column(
            'ip_use_commercial', sa.Boolean(),
            nullable=False,
            comment='Group operates in a commercial setting')
        )
        batch_op.add_column(sa.Column(
            'ip_use_educational', sa.Boolean(),
            nullable=False,
            comment='Group operates in an educational setting')
        )
        batch_op.add_column(sa.Column(
            'ip_use_research', sa.Boolean(),
            nullable=False,
            comment='Group operates in a research setting')
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('_security_groups', schema=None) as batch_op:
        batch_op.drop_column('ip_use_research')
        batch_op.drop_column('ip_use_educational')
        batch_op.drop_column('ip_use_commercial')
        batch_op.drop_column('ip_use_clinical')
