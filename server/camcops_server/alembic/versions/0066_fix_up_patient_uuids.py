#!/usr/bin/env python

"""
camcops_server/alembic/versions/0066_fix_up_patient_uuids.py

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

fix_up_patient_uuids

Revision ID: 0066
Revises: 0065
Creation date: 2021-07-19 08:56:00

Ensure all patients have a UUID. Any created before 0048 will not have one.

"""

# =============================================================================
# Imports
# =============================================================================

from typing import Optional
import uuid

from alembic import op
from sqlalchemy import orm

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import ERA_NOW
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    UuidColType,
)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0066'
down_revision = '0065'
branch_labels = None
depends_on = None


Base = declarative_base()


class Patient(Base):
    __tablename__ = "patient"

    _pk = Column(
        "_pk", Integer,
        primary_key=True,
        autoincrement=True
    )

    uuid = CamcopsColumn(
        "uuid", UuidColType,
        comment="UUID",
        default=uuid.uuid4  # generates a random UUID
    )  # type: Optional[uuid.UUID]


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    bind = op.get_bind()
    dbsession = orm.Session(bind=bind)

    for patient in dbsession.query(Patient):
        if patient.uuid is None:
            patient.uuid = uuid.uuid4()
            dbsession.add(patient)

    dbsession.commit()


# noinspection PyPep8,PyTypeChecker
def downgrade():
    pass
