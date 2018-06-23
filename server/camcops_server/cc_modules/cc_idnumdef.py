#!/usr/bin/env python
# camcops_server/cc_modules/cc_idnumdef.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
from typing import List

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import simple_repr
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer

from .cc_sqla_coltypes import (
    HL7AssigningAuthorityType,
    HL7IdTypeType,
    IdDescriptorColType,
)
from .cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# IdNumDefinition
# =============================================================================
# Stores the server's master ID number definitions

class IdNumDefinition(Base):
    __tablename__ = "_idnum_definitions"

    which_idnum = Column(
        "which_idnum", Integer, primary_key=True, index=True,
        comment="Which of the server's ID numbers is this?"
    )
    description = Column(
        "description", IdDescriptorColType,
        comment="Full description of the ID number"
    )
    short_description = Column(
        "short_description", IdDescriptorColType,
        comment="Short description of the ID number"
    )
    hl7_id_type = Column(
        "hl7_id_type", HL7IdTypeType,
        comment="HL7: Identifier Type code: 'a code corresponding to the type "
                "of identifier. In some cases, this code may be used as a "
                "qualifier to the \"Assigning Authority\" component.'"
    )
    hl7_assigning_authority = Column(
        "hl7_assigning_authority", HL7AssigningAuthorityType,
        comment="HL7: Assigning Authority for ID number (unique name of the "
                "system/organization/agency/department that creates the data)."
    )

    def __init__(self,
                 which_idnum: int,
                 description: str,
                 short_description: str,
                 hl7_id_type: str = "",
                 hl7_assigning_authority: str = ""):
        self.which_idnum = which_idnum
        self.description = description
        self.short_description = short_description
        self.hl7_id_type = hl7_id_type
        self.hl7_assigning_authority = hl7_assigning_authority

    def __repr__(self) -> str:
        return simple_repr(self,
                           ["which_idnum", "description", "short_description"],
                           with_addr=False)


# =============================================================================
# Caching IdNumDefinition
# =============================================================================

# CACHE_KEY_IDNUMDEFS = "id_num_definitions"


# def get_idnum_definitions(dbsession: SqlASession) -> List[IdNumDefinition]:
#     def creator() -> List[IdNumDefinition]:
#         defs = list(
#             dbsession.query(IdNumDefinition)
#             .order_by(IdNumDefinition.which_idnum)
#         )
#         # Now make these objects persist outside the scope of a session:
#         # https://stackoverflow.com/questions/8253978/sqlalchemy-get-object-not-bound-to-a-session  # noqa
#         # http://docs.sqlalchemy.org/en/latest/orm/session_state_management.html#expunging  # noqa
#         for iddef in defs:
#             dbsession.expunge(iddef)
#         return defs
#
#     return cache_region_static.get_or_create(CACHE_KEY_IDNUMDEFS, creator)


# def clear_idnum_definition_cache() -> None:
#     cache_region_static.delete(CACHE_KEY_IDNUMDEFS)


def get_idnum_definitions(dbsession: SqlASession) -> List[IdNumDefinition]:
    return list(
        dbsession.query(IdNumDefinition)
        .order_by(IdNumDefinition.which_idnum)
    )
