"""
camcops_server/cc_modules/cc_membership.py

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

**Represents a user's membership of a group.**

"""

import logging
from typing import Optional

from cardinal_pythonlib.logs import BraceStyleAdapter
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    Session as SqlASession,
)
from sqlalchemy.sql.schema import ForeignKey

from camcops_server.cc_modules.cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# User-to-group association table
# =============================================================================
# This is many-to-many:
#   A user can [be in] many groups.
#   A group can [contain] many users.

# -----------------------------------------------------------------------------
# First version:
# -----------------------------------------------------------------------------
# https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#many-to-many
# user_group_table = Table(
#     "_security_user_group",
#     Base.metadata,
#     Column("user_id", Integer, ForeignKey("_security_users.id"),
#            primary_key=True),
#     Column("group_id", Integer, ForeignKey("_security_groups.id"),
#            primary_key=True)
# )


# -----------------------------------------------------------------------------
# Second version, when we want more information in the relationship:
# -----------------------------------------------------------------------------
# https://stackoverflow.com/questions/7417906/sqlalchemy-manytomany-secondary-table-with-additional-fields  # noqa: E501
# ... no, association_proxy isn't quite what we want
# ... https://docs.sqlalchemy.org/en/latest/orm/extensions/associationproxy.html  # noqa: E501
# https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#association-object  # noqa: E501
# ... yes
# ... ah, but that AND association_proxy:
# https://docs.sqlalchemy.org/en/latest/orm/extensions/associationproxy.html#simplifying-association-objects  # noqa: E501
# ... no, not association_proxy!


class UserGroupMembership(Base):
    """
    Represents a user's membership of a group, and associated per-group
    permissions.
    """

    __tablename__ = "_security_user_group"

    # PK, so we can use this object easily on its own via the ORM.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Many-to-many mapping between User and Group
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("_security_users.id")
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("_security_groups.id")
    )

    # User attributes that are specific to their group membership
    groupadmin: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="Is the user a privileged administrator for this group?",
    )
    may_upload: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user upload data from a tablet device?",
    )
    may_register_devices: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user register tablet devices?",
    )
    may_use_webviewer: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user use the web front end to view " "CamCOPS data?",
    )
    view_all_patients_when_unfiltered: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="When no record filters are applied, can the user see "
        "all records? (If not, then none are shown.)",
    )
    may_dump_data: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user run database data dumps via the web interface?",
    )
    may_run_reports: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user run reports via the web interface? "
        "(Overrides other view restrictions.)",
    )
    may_add_notes: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user add special notes to tasks?",
    )
    may_manage_patients: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user add/edit/delete patients?",
    )
    may_email_patients: Mapped[Optional[bool]] = mapped_column(
        default=False,
        comment="May the user send emails to patients?",
    )

    group = relationship("Group", back_populates="user_group_memberships")
    user = relationship("User", back_populates="user_group_memberships")

    @classmethod
    def get_ugm_by_id(
        cls, dbsession: SqlASession, ugm_id: Optional[int]
    ) -> Optional["UserGroupMembership"]:
        """
        Fetches a :class:`UserGroupMembership` by its ID.
        """
        if ugm_id is None:
            return None
        return dbsession.query(cls).filter(cls.id == ugm_id).first()
