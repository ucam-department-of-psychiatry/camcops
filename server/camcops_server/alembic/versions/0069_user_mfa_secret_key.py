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
import pyotp
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.engine.strategies import MockEngineStrategy
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.expression import bindparam, select, update

from camcops_server.cc_modules.cc_user import User

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

    bind = op.get_bind()
    if isinstance(bind, MockEngineStrategy.MockConnection):
        log.warning("Using mock connection; skipping step")
        return
    dbsession = orm.Session(bind=bind)

    # noinspection PyUnresolvedReferences
    user_table = User.__table__  # type: Table
    # noinspection PyProtectedMember
    id_col = user_table.columns.id  # type: Column
    mfa_secret_key_col = user_table.columns.mfa_secret_key  # type: Column

    # SELECT user.id FROM user WHERE user.mfa_secret_key IS NULL:
    id_query = select([id_col]).where(mfa_secret_key_col.is_(None))
    rows = dbsession.execute(id_query)
    ids_needing_secret_key = [row[0] for row in rows]

    if len(ids_needing_secret_key) > 0:
        # Determine new secret keys:
        update_values = [
            {
                "user_id": user_id,
                "mfa_secret_key": pyotp.random_base32()
            }
            for user_id in ids_needing_secret_key
        ]

        # UPDATE user SET mfa_secret_key=%(mfa_secret_key)s
        # WHERE user.id = %(user_id)s:
        update_statement = (
            update(user_table).
            where(id_col == bindparam("user_id")).
            values(mfa_secret_key=bindparam("mfa_secret_key"))
        )
        # ... with many parameter pairs:
        # https://docs.sqlalchemy.org/en/14/tutorial/data_update.html
        dbsession.execute(update_statement, update_values)

        # COMMIT:
        dbsession.commit()


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.drop_column("mfa_secret_key")
        batch_op.drop_column("hotp_counter")
