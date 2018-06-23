#!/usr/bin/env python
# camcops_server/cc_modules/cc_group.py

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
from typing import List, Optional, Set

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_query import exists_orm
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey, Table
from sqlalchemy.sql.sqltypes import Integer

from .cc_policy import TokenizedPolicy
from .cc_sqla_coltypes import (
    GroupNameColType,
    GroupDescriptionColType,
    IdPolicyColType,
)
from .cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


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


# =============================================================================
# Group
# =============================================================================

class Group(Base):
    """
    Represents a CamCOPS group.

    ---------------------------------------------------------------------------
    Basic group security concepts
    ---------------------------------------------------------------------------

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

    ---------------------------------------------------------------------------
    Per-group ID policy
    ---------------------------------------------------------------------------

    Then, we want a per-group ID policy. The prototypical example is where
    clinical studies are hosted from a clinical organization; all group may be
    required to share a common institutional ID, but individual studies may
    want to enforce their own ID, so ID policies cannot be global.

    ---------------------------------------------------------------------------
    Group administrators
    ---------------------------------------------------------------------------

    For a large-scale system, it'd be desirable to be able to delegate user
    management to group administrators, such that groupadmins can manage their
    own users WITHOUT being able to see all records on the system.
    This is a bit tricky.

    - The superuser, alone, should be able to set groupadmin status, and to
      create/delete groups.

    - We'd want them to be able to add users
        => add if user doesn't exist already (=> some information leakage)

    - We can't let them delete users arbitrarily. We could say that they could
      delete a user if all the users' groups were administered by this
      groupadmin.

    - The groupadmin should be able to grant/revoke access for their groups
      only.

    - This would entail some permissions being group-specific:
        - login     [can login if "login" permission set for ANY group]
        - upload    [can upload to a group only if "upload" permission for
                     that group]
        - register devices  [similar to upload]
        - view_all_patients_when_unfiltered
                    [if you're in >1 group, this per-group setting would be
                     applied to patients belonging to that group]
        - may_dump_data
                    [applies to data for that group only]
        - may_run_reports   [also per-group]
        - may_add_notes [also per-group]

    - A certain amount of crosstalk is hard to avoid: e.g.
        must_change_password

    """
    __tablename__ = "_security_groups"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="Group ID"
    )
    name = Column(
        "name", GroupNameColType,
        nullable=False, index=True, unique=True,
        comment="Group name"
    )
    description = Column(
        "description", GroupDescriptionColType,
        comment="Description of the group"
    )
    upload_policy = Column(
        "upload_policy", IdPolicyColType,
        comment="Upload policy for the group, as a string"
    )
    finalize_policy = Column(
        "finalize_policy", IdPolicyColType,
        comment="Finalize policy for the group, as a string"
    )

    # users = relationship(
    #     "User",  # defined with string to avoid circular import
    #     secondary=user_group_table,  # link via this mapping table
    #     back_populates="groups"  # see User.groups
    # )
    user_group_memberships = relationship(
        "UserGroupMembership", back_populates="group")
    users = association_proxy("user_group_memberships", "user")

    can_see_other_groups = relationship(
        "Group",  # link back to our own class
        secondary=group_group_table,  # via this mapping table
        primaryjoin=(id == group_group_table.c.group_id),  # "us"
        secondaryjoin=(id == group_group_table.c.can_see_group_id),  # "them"
        backref="groups_that_can_see_us",
        lazy="joined"  # not sure this does anything here
    )

    def ids_of_other_groups_group_may_see(self) -> Set[int]:
        """
        Returns a list of group IDs for groups that this group has permission
        to see. (Always includes our own group number.)
        """
        group_ids = set()  # type: Set[int]
        for other_group in self.can_see_other_groups:  # type: Group
            other_group_id = other_group.id  # type: Optional[int]
            if other_group_id is not None:
                group_ids.add(other_group_id)
        return group_ids

    def ids_of_groups_group_may_see(self) -> Set[int]:
        """
        Returns a list of group IDs for groups that this group has permission
        to see. (Always includes our own group number.)
        """
        ourself = {self.id}  # type: Set[int]
        return ourself.union(self.ids_of_other_groups_group_may_see())

    @classmethod
    def get_groups_from_id_list(cls, dbsession: SqlASession,
                                group_ids: List[int]) -> List["Group"]:
        return dbsession.query(Group).filter(Group.id.in_(group_ids)).all()

    @classmethod
    def get_group_by_name(cls, dbsession: SqlASession,
                          name: str) -> Optional["Group"]:
        if not name:
            return None
        return dbsession.query(cls).filter(cls.name == name).first()

    @classmethod
    def get_group_by_id(cls, dbsession: SqlASession,
                        group_id: int) -> Optional["Group"]:
        if group_id is None:
            return None
        return dbsession.query(cls).filter(cls.id == group_id).first()

    @classmethod
    def all_group_ids(cls, dbsession: SqlASession) -> List[int]:
        query = dbsession.query(cls).order_by(cls.id)
        return [g.id for g in query]

    @classmethod
    def group_exists(cls, dbsession: SqlASession, group_id: int) -> bool:
        return exists_orm(dbsession, cls, cls.id == group_id)

    def tokenized_upload_policy(self) -> TokenizedPolicy:
        return TokenizedPolicy(self.upload_policy)

    def tokenized_finalize_policy(self) -> TokenizedPolicy:
        return TokenizedPolicy(self.finalize_policy)
