#!/usr/bin/env python
# camcops_server/cc_modules/cc_group.py

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

import logging

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.sql.schema import Column, ForeignKey, Table
from sqlalchemy.sql.sqltypes import Integer

from .cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# User-to-group association table
# =============================================================================
# This is many-to-many:
#   A user can [be in] many groups.
#   A group can [contain] many users.

# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#many-to-many
user_group_table = Table(
    "_security_user_group",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("_security_users.id"),
           primary_key=True),
    Column("group_id", Integer, ForeignKey("_security_groups.id"),
           primary_key=True)
)


# =============================================================================
# Group-to-group association table
# =============================================================================
# A group can always see itself, but may also have permission to see others;
# see help(Group).

# http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#self-referential-many-to-many-relationship  # noqa
group_group_table = Table(
    "_security_group_group",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("_security_groups.id"),
           primary_key=True),
    Column("can_see_group_id", Integer, ForeignKey("_security_groups.id"),
           primary_key=True)
)
