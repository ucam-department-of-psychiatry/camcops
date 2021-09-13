#!/usr/bin/env python

"""
camcops_server/alembic/versions/0070_user_mfa.py

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

user_mfa

Revision ID: 0070
Revises: 0069
Creation date: 2021-09-13 23:03:00.729047

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa

from camcops_server.cc_modules.cc_sqla_coltypes import PhoneNumberColType

# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0070"
down_revision = "0069"
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
                server_default=sa.text("0"),
                nullable=False,
                comment="Counter used for HOTP authentication",
            )
        )
        batch_op.add_column(
            sa.Column(
                "mfa_method",
                sa.String(length=20),
                server_default="none",
                nullable=False,
                comment="Preferred method of multi-factor authentication",
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
        batch_op.add_column(
            sa.Column(
                "phone_number",
                PhoneNumberColType(length=128),
                nullable=True,
                comment="User's phone number",
            )
        )

    with op.batch_alter_table(
        "_security_webviewer_sessions", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "mfa_time",
                sa.Integer(),
                nullable=True,
                comment="To determine multi-factor authentication session expiry",
            )
        )
        batch_op.add_column(
            sa.Column(
                "mfa_user_id",
                sa.Integer(),
                nullable=True,
                comment="Temporary ID of User during multi-factor authentication",
            )
        )
        batch_op.create_foreign_key(
            batch_op.f("fk__security_webviewer_sessions_mfa_user_id"),
            "_security_users",
            ["mfa_user_id"],
            ["id"],
            ondelete="CASCADE",
        )


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table(
        "_security_webviewer_sessions", schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk__security_webviewer_sessions_mfa_user_id"),
            type_="foreignkey",
        )
        batch_op.drop_column("mfa_user_id")
        batch_op.drop_column("mfa_time")

    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.drop_column("phone_number")
        batch_op.drop_column("mfa_secret_key")
        batch_op.drop_column("mfa_method")
        batch_op.drop_column("hotp_counter")
