#!/usr/bin/env python
# camcops_server/cc_modules/cc_ancillary.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
"""

from sqlalchemy.sql.schema import Column

from .cc_db import GenericTabletRecordMixin
from .cc_sqla_coltypes import IntUnsigned


class AncillaryMixin(GenericTabletRecordMixin):
    id = Column(
        "id", IntUnsigned,
        nullable=True, index=True,
        comment="(ANCILLARY) Primary key on the tablet device"
    )
