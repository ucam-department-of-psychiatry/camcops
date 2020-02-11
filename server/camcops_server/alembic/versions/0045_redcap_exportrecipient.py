#!/usr/bin/env python

"""
camcops_server/alembic/versions/0045_redcap_exportrecipient.py

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

redcap_exportrecipient

Revision ID: 0045
Revises: 0044
Creation date: 2019-12-20 15:37:44.271863

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0045'
down_revision = '0044'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table('_export_recipients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('redcap_api_url', sa.Text(), nullable=True, comment='(REDCap) REDCap API URL, pointing to the REDCap server'))
        batch_op.add_column(sa.Column('redcap_fieldmap_filename', sa.Text(), nullable=True, comment='(REDCap) File defining CamCOPS-to-REDCap field mapping'))


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table('_export_recipients', schema=None) as batch_op:
        batch_op.drop_column('redcap_fieldmap_filename')
        batch_op.drop_column('redcap_api_url')
