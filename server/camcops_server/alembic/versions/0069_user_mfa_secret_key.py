#!/usr/bin/env python

"""
camcops_server/alembic/versions/0069_user_mfa_secret_key.py

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

DATABASE REVISION SCRIPT

user_mfa_secret_key

Revision ID: 0069
Revises: 0068
Creation date: 2021-08-09 15:56:31.987769

"""

# =============================================================================
# Imports
# =============================================================================

import logging

from alembic import op
import sqlalchemy as sa

log = logging.getLogger(__name__)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "hotp_counter",
                sa.Integer(),
                nullable=True,
                comment="Counter used for HOTP authentication",
            )
        )
        batch_op.add_column(
            sa.Column(
                "mfa_secret_key",
                sa.String(length=32),
                nullable=True,
                comment="Secret key used for multi-factor authentication",
            )
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.drop_column("mfa_secret_key")
        batch_op.drop_column("hotp_counter")
