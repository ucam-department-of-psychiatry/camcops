"""
camcops_server/cc_modules/cc_dirtytables.py

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

**Representation of a "dirty table" -- one that a device is in the process of
uploading to/preserving.**

"""

from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import ForeignKey

from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_sqla_coltypes import TableNameColType
from camcops_server.cc_modules.cc_sqlalchemy import Base


# =============================================================================
# DirtyTable
# =============================================================================


class DirtyTable(Base):
    """
    Class to represent tables being modified during a client upload.
    """

    __tablename__ = "_dirty_tables"

    id: Mapped[int] = mapped_column(
        # new in 2.1.0; ditch composite PK
        primary_key=True,
        autoincrement=True,
    )
    device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Device.id),
        comment="Source tablet device ID",
    )
    tablename: Mapped[Optional[str]] = mapped_column(
        TableNameColType,
        comment="Table in the process of being preserved",
    )
