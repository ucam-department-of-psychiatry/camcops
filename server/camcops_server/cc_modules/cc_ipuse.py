#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_ipuse.py

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

IP Use flags that determine the contexts in which CamCOPS is to be used (and
hence the tasks that will be permitted).

"""

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Integer

from camcops_server.cc_modules.cc_sqlalchemy import Base


class IpUse(Base):
    __tablename__ = "_security_ip_use"

    CONTEXTS = (
        "clinical",
        "commercial",
        "educational",
        "research",
    )

    id = Column(
        "id", Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="IP Use ID"
    )

    clinical = Column(
        "clinical", Boolean,
        nullable=False,
        default=False,
        comment="Applicable to a clinical context"
    )
    commercial = Column(
        "commercial", Boolean,
        nullable=False,
        default=False,
        comment="Applicable to a commercial context"
    )
    educational = Column(
        "educational", Boolean,
        nullable=False,
        default=False,
        comment="Applicable to an educational context"
    )
    research = Column(
        "research", Boolean,
        nullable=False,
        default=False,
        comment="Applicable to a research context"
    )
