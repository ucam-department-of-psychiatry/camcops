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
from typing import Optional, Set

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer

from .cc_jointables import user_group_table, group_group_table
from .cc_sqla_coltypes import GroupNameColType
from .cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Patient class
# =============================================================================

class Group(Base):
    """
    Represents a CamCOPS group.

    -   Users may be in one or more groups.

    -   Users have a default "upload to" group.
    -   Tasks (and other associated records) from a tablet get stashed in that
        group.

    -   Users can see records belonging to their group(s).

    -   To facilitate group working, there is one level of indirection: groups
        themselves can have permission to see other groups.

        For example, imagine a research-active hospital with these groups:

        USERS TO GROUPS:

            RA_Smith is in group            depression_crp_study
            PhDstudent_Jones is in group    depression_crp_study

            RA_Willis is in group           depression_ketamine_study
            PhDstudent_Fox is in group      depression_ketamine_study

            RA_Armstrong is in group        healthy_development_study
            PhDstudent_Bliss is in group    healthy_development_study

            PI_Cratchett is in groups:      depression_crp_study
                                            depression_ketamine_study

            PI_Boxworth is in groups:       depression_ketamine_study
                                            healthy_development_study
                                            clinical

            SHO_Amundsen is in group        clinical
            SpR_Richards is in group        clinical

        GROUPS TO OTHER GROUPS:

            clinical can see:   depression_crp_study
                                depression_ketamine_study

        Then:
                                +-- can see depression_crp_study
                                |
                                |       +-- can see depression_ketamine_study
                                |       |
                                |       |       +-- can see
                                |       |       |   healthy_development_study
                                |       |       |
                                |       |       |       +-- can see clinical
                                |       |       |       |
                                v       v       v       v

            RA_Smith            Y       n       n       n
            PhDstudent_Jones    Y       n       n       n
            RA_Willis           n       Y       n       n
            PhDstudent_Fox      n       Y       n       n
            RA_Armstrong        n       n       Y       n
            PhDstudent_Bliss    n       n       Y       n
            PI_Cratchett        Y       Y       n       n
            PI_Boxworth         Y       Y       Y       Y
            SHO_Amundsen        Y       Y       n       Y
            SpR_Richards        Y       Y       n       Y

        This example embodies these specimen principles:

            - Researchers see only the patients consented into their study.
            - A researcher may be part of one or several studies.
            - Clinicians can see all records, including research records, for
              patients consented into clinical research for the hospital.
            - There may be some studies that don't involve patients, so
              clinicians don't get some sort of superuser status.

    (Actual CamCOPS superusers can see everything. This is an administrative
    role.)

    If that's not enough, consider starting another CamCOPS database...

    """
    __tablename__ = "_security_groups"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="Group ID"
    )
    name = Column(
        "username", GroupNameColType,
        nullable=False, index=True, unique=True,
        comment="Group name"
    )

    users = relationship(
        "User",  # defined with string to avoid circular import
        secondary=user_group_table,
        back_populates="groups"  # see User.groups
    )
    can_see_other_groups = relationship(
        "Group",  # link back to our own class
        secondary=group_group_table,  # via this mapping table
        primaryjoin=(id == group_group_table.c.group_id),  # "us"
        secondaryjoin=(id == group_group_table.c.can_see_group_id),  # "them"
        backref="groups_that_can_see_us"
    )

    def ids_of_groups_group_may_see(self) -> Set[int]:
        """
        Returns a list of group IDs for groups that this group has permission
        to see. (Always includes our own group number.)
        """
        group_ids = {self.id}  # type: Set[int]
        for other_group in self.can_see_other_groups:  # type: Group
            other_group_id = other_group.id  # type: Optional[int]
            if other_group_id is not None:
                group_ids.add(other_group_id)
        return group_ids
