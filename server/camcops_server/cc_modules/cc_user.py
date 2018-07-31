#!/usr/bin/env python
# camcops_server/cc_modules/cc_user.py

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

import datetime
import logging
import re
from typing import List, Optional, Set, TYPE_CHECKING

import cardinal_pythonlib.crypto as rnc_crypto
from cardinal_pythonlib.datetimefunc import convert_datetime_to_local
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import simple_repr
from cardinal_pythonlib.sqlalchemy.orm_query import (
    CountStarSpecializedQuery,
    exists_orm,
)
from pendulum import DateTime as Pendulum
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, Session as SqlASession
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .cc_audit import audit
from .cc_constants import USER_NAME_FOR_SYSTEM
from .cc_group import Group
from .cc_membership import UserGroupMembership
from .cc_sqla_coltypes import (
    EmailAddressColType,
    FullNameColType,
    HashedPasswordColType,
    PendulumDateTimeAsIsoTextColType,
    UserNameColType,
)
from .cc_sqlalchemy import Base
from .cc_unittest import DemoDatabaseTestCase

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

VALID_USERNAME_REGEX = "^[A-Za-z0-9_-]+$"
BCRYPT_DEFAULT_LOG_ROUNDS = 6
# Default is 12, but it does impact on the tablet upload speed (cost per
# transaction). Time is expected to be proportional to 2^n, i.e. incrementing 1
# increases time by a factor of 2.
# Empirically, on egret:
#   2^12 rounds takes around 400 ms
#   2^8 rounds takes around 30 ms (as expected, 1/16 of the time as for 12)
#   we'd like around 8 ms; http://security.stackexchange.com/questions/17207
#   ... so we should be using 12 + log(8/400)/log(2) = 6 rounds

CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS = 7
CLEAR_DUMMY_LOGIN_PERIOD = datetime.timedelta(
    days=CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS)


# =============================================================================
# SecurityAccountLockout
# =============================================================================
# Note that we record login failures for non-existent users, and pretend
# they're locked out (to prevent username discovery that way, by timing)

class SecurityAccountLockout(Base):
    __tablename__ = "_security_account_lockouts"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column(
        "username", UserNameColType,
        nullable=False, index=True,
        comment="User name (which may be a non-existent user, to prevent "
                "subtle username discovery by careful timing)"
    )
    locked_until = Column(
        "locked_until", DateTime,
        nullable=False, index=True,
        comment="Account is locked until (UTC)"
    )

    @classmethod
    def delete_old_account_lockouts(cls, req: "CamcopsRequest") -> None:
        """Delete all expired account lockouts."""
        dbsession = req.dbsession
        now = req.now_utc
        dbsession.query(cls)\
            .filter(cls.locked_until <= now)\
            .delete(synchronize_session=False)

    @classmethod
    def is_user_locked_out(cls, req: "CamcopsRequest", username: str) -> bool:
        dbsession = req.dbsession
        now = req.now_utc
        return exists_orm(dbsession, cls,
                          cls.username == username,
                          cls.locked_until > now)

    @classmethod
    def user_locked_out_until(cls, req: "CamcopsRequest",
                              username: str) -> Optional[Pendulum]:
        """
        When is the user locked out until?

        Returns datetime in local timezone (or None).
        """
        dbsession = req.dbsession
        now = req.now_utc
        locked_until_utc = dbsession.query(func.max(cls.locked_until))\
            .filter(cls.username == username)\
            .filter(cls.locked_until > now)\
            .scalar()  # type: Optional[Pendulum]
        # ... NOT first(), which returns (result,); we want just result
        if not locked_until_utc:
            return None
        return convert_datetime_to_local(locked_until_utc)

    @classmethod
    def lock_user_out(cls, req: "CamcopsRequest",
                      username: str, lockout_minutes: int) -> None:
        """
        Lock user out for a specified number of minutes.
        """
        dbsession = req.dbsession
        now = req.now_utc
        lock_until = now + datetime.timedelta(minutes=lockout_minutes)
        # noinspection PyArgumentList
        lock = cls(username=username, lock_until=lock_until)
        dbsession.add(lock)
        audit(req, "Account {} locked out for {} minutes".format(
            username, lockout_minutes))

    @classmethod
    def unlock_user(cls, req: "CamcopsRequest", username: str) -> None:
        dbsession = req.dbsession
        dbsession.query(cls)\
            .filter(cls.username == username)\
            .delete(synchronize_session=False)


# =============================================================================
# SecurityLoginFailure
# =============================================================================

class SecurityLoginFailure(Base):
    __tablename__ = "_security_login_failures"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column(
        "username", UserNameColType,
        nullable=False, index=True,
        comment="User name (which may be a non-existent user, to prevent "
                "subtle username discovery by careful timing)"
    )
    login_failure_at = Column(
        "login_failure_at", DateTime,
        nullable=False, index=True,
        comment="Login failure occurred at (UTC)"
    )

    @classmethod
    def record_login_failure(cls, req: "CamcopsRequest",
                             username: str) -> None:
        """Record that a user has failed to log in."""
        dbsession = req.dbsession
        now = req.now_utc
        # noinspection PyArgumentList
        failure = cls(username=username, login_failure_at=now)
        dbsession.add(failure)

    @classmethod
    def act_on_login_failure(cls, req: "CamcopsRequest",
                             username: str) -> None:
        """Record login failure and lock out user if necessary."""
        cfg = req.config
        audit(req, "Failed login as user: {}".format(username))
        cls.record_login_failure(req, username)
        nfailures = cls.how_many_login_failures(req, username)
        nlockouts = nfailures // cfg.lockout_threshold
        nfailures_since_last_lockout = nfailures % cfg.lockout_threshold
        if nlockouts >= 1 and nfailures_since_last_lockout == 0:
            # new lockout required
            lockout_minutes = nlockouts * \
                              cfg.lockout_duration_increment_minutes
            SecurityAccountLockout.lock_user_out(req, username,
                                                 lockout_minutes)

    @classmethod
    def clear_login_failures(cls, req: "CamcopsRequest",
                             username: str) -> None:
        """Clear login failures for a user."""
        dbsession = req.dbsession
        dbsession.query(cls)\
            .filter(cls.username == username)\
            .delete(synchronize_session=False)

    @classmethod
    def how_many_login_failures(cls, req: "CamcopsRequest",
                                username: str) -> int:
        """How many times has the user failed to log in (recently)?"""
        dbsession = req.dbsession
        q = CountStarSpecializedQuery([cls], session=dbsession)\
            .filter(cls.username == username)
        return q.count_star()

    @classmethod
    def enable_user(cls, req: "CamcopsRequest", username: str) -> None:
        """Unlock user and clear login failures."""
        SecurityAccountLockout.unlock_user(req, username)
        cls.clear_login_failures(req, username)
        audit(req, "User {} re-enabled".format(username))

    @classmethod
    def clear_login_failures_for_nonexistent_users(
            cls, req: "CamcopsRequest") -> None:
        """
        Clear login failures for nonexistent users.

        Login failues are recorded for nonexistent users to mimic the lockout
        seen for real users, i.e. to reduce the potential for username
        discovery.
        """
        dbsession = req.dbsession
        all_user_names = dbsession.query(User.username)
        dbsession.query(cls)\
            .filter(cls.username.notin_(all_user_names))\
            .delete(synchronize_session=False)
        # https://stackoverflow.com/questions/26182027/how-to-use-not-in-clause-in-sqlalchemy-orm-query  # noqa

    @classmethod
    def clear_dummy_login_failures_if_necessary(cls,
                                                req: "CamcopsRequest") -> None:
        """Clear dummy login failures if we haven't done so for a while.

        Not too often! See CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS.
        """
        now = req.now_utc
        ss = req.server_settings
        last_dummy_login_failure_clearance = ss.get_last_dummy_login_failure_clearance_pendulum()  # noqa
        if last_dummy_login_failure_clearance is not None:
            elapsed = now - last_dummy_login_failure_clearance
            if elapsed < CLEAR_DUMMY_LOGIN_PERIOD:
                # We cleared it recently.
                return

        cls.clear_login_failures_for_nonexistent_users(req)
        log.debug("Dummy login failures cleared.")
        ss.last_dummy_login_failure_clearance_at_utc = now


# =============================================================================
# User class
# =============================================================================

class User(Base):
    """
    Class representing a user.
    """
    __tablename__ = "_security_users"

    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="User ID"
    )
    username = Column(
        "username", UserNameColType,
        nullable=False, index=True, unique=True,
        comment="User name"
    )
    fullname = Column(
        "fullname", FullNameColType,
        comment="User's full name"
    )
    email = Column(
        "email", EmailAddressColType,
        comment="User's e-mail address"
    )
    hashedpw = Column(
        "hashedpw", HashedPasswordColType,
        nullable=False,
        comment="Password hash"
    )
    last_login_at_utc = Column(
        "last_login_at_utc", DateTime,
        comment="Date/time this user last logged in (UTC)"
    )
    last_password_change_utc = Column(
        "last_password_change_utc", DateTime,
        comment="Date/time this user last changed their password (UTC)"
    )
    superuser = Column(
        "superuser", Boolean,
        default=False,
        comment="Superuser?"
    )
    must_change_password = Column(
        "must_change_password", Boolean,
        default=False,
        comment="Must change password at next webview login"
    )
    when_agreed_terms_of_use = Column(
        "when_agreed_terms_of_use", PendulumDateTimeAsIsoTextColType,
        comment="Date/time this user acknowledged the Terms and "
                "Conditions of Use (ISO 8601)"
    )

    upload_group_id = Column(
        "upload_group_id", Integer, ForeignKey("_security_groups.id"),
        comment="ID of the group to which this user uploads at present",
        # OK to be NULL in the database, but the user will not be able to
        # upload while it is.
    )

    # groups = relationship(
    #     Group,
    #     secondary=user_group_table,
    #     back_populates="users"  # see Group.users
    # )
    user_group_memberships = relationship(
        "UserGroupMembership", back_populates="user")
    groups = association_proxy("user_group_memberships", "group")

    upload_group = relationship("Group", foreign_keys=[upload_group_id])

    def __repr__(self) -> str:
        return simple_repr(
            self,
            ["id", "username", "fullname"],
            with_addr=True
        )

    @classmethod
    def get_user_by_id(cls,
                       dbsession: SqlASession,
                       user_id: Optional[int]) -> Optional['User']:
        if user_id is None:
            return None
        return dbsession.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_user_by_name(cls,
                         dbsession: SqlASession,
                         username: str) -> Optional['User']:
        if not username:
            return None
        return dbsession.query(cls).filter(cls.username == username).first()

    @classmethod
    def user_exists(cls, req: "CamcopsRequest", username: str) -> bool:
        if not username:
            return False
        dbsession = req.dbsession
        return exists_orm(dbsession, cls, cls.username == username)

    @classmethod
    def create_superuser(cls, req: "CamcopsRequest", username: str,
                         password: str) -> bool:
        assert username, "Can't create superuser with no name"
        assert username != USER_NAME_FOR_SYSTEM, (
            "Can't create user with name {!r}".format(USER_NAME_FOR_SYSTEM))
        dbsession = req.dbsession
        user = cls.get_user_by_name(dbsession, username)
        if user:
            # already exists!
            return False
        # noinspection PyArgumentList
        user = cls(username=username)  # does work!
        user.superuser = True
        audit(req, "SUPERUSER CREATED: " + user.username, from_console=True)
        user.set_password(req, password)  # will audit
        dbsession.add(user)
        return True

    @classmethod
    def get_username_from_id(cls, req: "CamcopsRequest",
                             user_id: int) -> Optional[str]:
        dbsession = req.dbsession
        return dbsession.query(cls.username)\
            .filter(cls.id == user_id)\
            .first()\
            .scalar()

    @classmethod
    def get_user_from_username_password(
            cls,
            req: "CamcopsRequest",
            username: str,
            password: str,
            take_time_for_nonexistent_user: bool = True) -> Optional['User']:
        """
        Retrieve a User object from the supplied username, if the password is
        correct; otherwise, return None.
        """
        dbsession = req.dbsession
        user = cls.get_user_by_name(dbsession, username)
        if user is None:
            if take_time_for_nonexistent_user:
                # If the user really existed, we'd be running a somewhat
                # time-consuming bcrypt operation. So that attackers can't
                # identify fake users easily based on timing, we consume some
                # time:
                cls.take_some_time_mimicking_password_encryption()
            return None
        if not user.is_password_valid(password):
            return None
        return user

    @classmethod
    def get_system_user(cls, dbsession: SqlASession) -> "User":
        """
        Returns a user representing "command-line access".
        """
        user = cls.get_user_by_name(dbsession, USER_NAME_FOR_SYSTEM)
        if not user:
            # noinspection PyArgumentList
            user = cls(username=USER_NAME_FOR_SYSTEM)  # does work!
            dbsession.add(user)
        user.fullname = "CamCOPS system user"
        user.superuser = True
        user.hashedpw = ''  # because it's not nullable
        # ... note that no password will hash to '', in addition to the fact
        # that the system will not allow logon attempts for this user!
        return user

    @staticmethod
    def is_username_permissible(username: str) -> bool:
        """
        Is this a permissible username?
        """
        return bool(re.match(VALID_USERNAME_REGEX, username))

    @staticmethod
    def take_some_time_mimicking_password_encryption() -> None:
        """
        Waste some time. We use this when an attempt has been made to log in
        with a nonexistent user; we know the user doesn't exist very quickly,
        but we mimic the time it takes to check a real user's password.
        """
        rnc_crypto.hash_password("dummy!", BCRYPT_DEFAULT_LOG_ROUNDS)

    def set_password(self, req: "CamcopsRequest", new_password: str) -> None:
        """
        Set a user's password.
        """
        self.hashedpw = rnc_crypto.hash_password(new_password,
                                                 BCRYPT_DEFAULT_LOG_ROUNDS)
        self.last_password_change_utc = req.now_utc
        self.must_change_password = False
        audit(req, "Password changed for user " + self.username)

    def is_password_valid(self, password: str) -> bool:
        """
        Is the supplied password valid?
        """
        return rnc_crypto.is_password_valid(password, self.hashedpw)

    def force_password_change(self) -> None:
        """
        Make the user change their password at next login.
        """
        self.must_change_password = True

    def login(self, req: "CamcopsRequest") -> None:
        """
        Called when the framework has determined a successful login.

        Clears any login failures.
        Requires the user to change their password if policies say they should.
        """
        self.clear_login_failures(req)
        self.set_password_change_flag_if_necessary(req)
        self.last_login_at_utc = req.now_utc

    def set_password_change_flag_if_necessary(self,
                                              req: "CamcopsRequest") -> None:
        """
        If we're requiring users to change their passwords, then check to
        see if they must do so now.
        """
        if self.must_change_password:
            # already required, pointless to check again
            return
        cfg = req.config
        if cfg.password_change_frequency_days <= 0:
            # changes never required
            return
        if not self.last_password_change_utc:
            # we don't know when the last change was, so it's overdue
            self.force_password_change()
            return
        delta = req.now_utc - self.last_password_change_utc
        if delta.days >= cfg.password_change_frequency_days:
            self.force_password_change()

    @property
    def must_agree_terms(self) -> bool:
        """Does the user still need to agree the terms/conditions of use?"""
        return self.when_agreed_terms_of_use is None

    def agree_terms(self, req: "CamcopsRequest") -> None:
        """Mark the user as having agreed to the terms/conditions of use
        now."""
        self.when_agreed_terms_of_use = req.now

    def clear_login_failures(self, req: "CamcopsRequest") -> None:
        """Clear login failures."""
        if not self.username:
            return
        SecurityLoginFailure.clear_login_failures(req, self.username)

    def is_locked_out(self, req: "CamcopsRequest") -> bool:
        """Is the user locked out because of multiple login failures?"""
        return SecurityAccountLockout.is_user_locked_out(req, self.username)

    def locked_out_until(self,
                         req: "CamcopsRequest") -> Optional[Pendulum]:
        """
        When is the user locked out until (or None)?

        Returns datetime in local timezone (or None).
        """
        return SecurityAccountLockout.user_locked_out_until(req,
                                                            self.username)

    def enable(self, req: "CamcopsRequest") -> None:
        """Re-enables a user, unlocking them and clearing login failures."""
        SecurityLoginFailure.enable_user(req, self.username)

    @property
    def may_login_as_tablet(self) -> bool:
        return self.may_upload or self.may_register_devices

    @property
    def group_ids(self) -> List[int]:
        return sorted(list(g.id for g in self.groups))

    def set_group_ids(self, group_ids: List[int]) -> None:
        dbsession = SqlASession.object_session(self)
        assert dbsession, ("User.set_group_ids() called on a User that's not "
                           "yet in a session")
        # groups = Group.get_groups_from_id_list(dbsession, group_ids)

        # Remove groups that no longer apply
        for m in self.user_group_memberships:
            if m.group_id not in group_ids:
                dbsession.delete(m)
        # Add new groups
        current_group_ids = [m.group_id for m in self.user_group_memberships]
        new_group_ids = [gid for gid in group_ids
                         if gid not in current_group_ids]
        for gid in new_group_ids:
            self.user_group_memberships.append(UserGroupMembership(
                user_id=self.id,
                group_id=gid,
            ))

    @property
    def ids_of_groups_user_may_see(self) -> List[int]:
        # Incidentally: "list_a += list_b" vs "list_a.extend(list_b)":
        # https://stackoverflow.com/questions/3653298/concatenating-two-lists-difference-between-and-extend  # noqa
        # ... not much difference; perhaps += is slightly better (also clearer)
        # And relevant set operations:
        # https://stackoverflow.com/questions/4045403/python-how-to-add-the-contents-of-an-iterable-to-a-set  # noqa
        #
        # Process as a set rather than a list, to eliminate duplicates:
        group_ids = set()  # type: Set[int]
        for my_group in self.groups:  # type: Group
            group_ids.update(my_group.ids_of_groups_group_may_see())
        return list(group_ids)
        # Return as a list rather than a set, because SQLAlchemy's in_()
        # operator only likes lists and sets.

    @property
    def ids_of_groups_user_may_dump(self) -> List[int]:
        if self.superuser:
            return Group.all_group_ids(
                dbsession=SqlASession.object_session(self))
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return [m.group_id for m in memberships if m.may_dump_data]

    @property
    def ids_of_groups_user_may_report_on(self) -> List[int]:
        if self.superuser:
            return Group.all_group_ids(
                dbsession=SqlASession.object_session(self))
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return [m.group_id for m in memberships if m.may_run_reports]

    @property
    def ids_of_groups_user_is_admin_for(self) -> List[int]:
        if self.superuser:
            return Group.all_group_ids(
                dbsession=SqlASession.object_session(self))
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return [m.group_id for m in memberships if m.groupadmin]

    def may_administer_group(self, group_id: int) -> bool:
        if self.superuser:
            return True
        return group_id in self.ids_of_groups_user_is_admin_for

    @property
    def groups_user_may_see(self) -> List[Group]:
        # A less efficient version, for visual display (see
        # view_own_user_info.mako)
        groups = set(self.groups)  # type: Set[Group]
        for my_group in self.groups:  # type: Group
            groups.update(set(my_group.can_see_other_groups))
        return sorted(list(groups), key=lambda g: g.name)

    @property
    def groups_user_may_dump(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships if m.may_dump_data],
                      key=lambda g: g.name)

    @property
    def groups_user_may_report_on(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships if m.may_run_reports],
                      key=lambda g: g.name)

    @property
    def groups_user_may_upload_into(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships if m.may_upload],
                      key=lambda g: g.name)

    @property
    def groups_user_may_add_special_notes(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships if m.may_add_notes],
                      key=lambda g: g.name)

    @property
    def groups_user_may_see_all_pts_when_unfiltered(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships
                       if m.view_all_patients_when_unfiltered],
                      key=lambda g: g.name)

    @property
    def groups_user_is_admin_for(self) -> List[Group]:
        # For visual display (see view_own_user_info.mako).
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return sorted([m.group for m in memberships if m.groupadmin],
                      key=lambda g: g.name)

    @property
    def is_a_groupadmin(self) -> bool:
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.groupadmin for m in memberships)

    @property
    def authorized_as_groupadmin(self) -> bool:
        return self.superuser or self.is_a_groupadmin

    def membership_for_group_id(self, group_id: int) -> UserGroupMembership:
        return next(
            (m for m in self.user_group_memberships if m.group_id == group_id),
            None
        )

    @property
    def may_use_webviewer(self) -> bool:
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.may_use_webviewer for m in memberships)

    def authorized_to_add_special_note(self, group_id: int) -> bool:
        if self.superuser:
            return True
        membership = self.membership_for_group_id(group_id)
        if not membership:
            return False
        return membership.may_add_notes

    def authorized_to_erase_tasks(self, group_id: int) -> bool:
        if self.superuser:
            return True
        membership = self.membership_for_group_id(group_id)
        if not membership:
            return False
        return membership.groupadmin

    @property
    def authorized_to_dump(self) -> bool:
        """Is the user authorized to dump data?"""
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.may_dump_data for m in memberships)

    @property
    def authorized_for_reports(self) -> bool:
        """Is the user authorized to run reports?"""
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.may_run_reports for m in memberships)

    @property
    def may_view_all_patients_when_unfiltered(self) -> bool:
        """May the user view all patients when no filters are applied?"""
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return all(m.view_all_patients_when_unfiltered for m in memberships)

    @property
    def may_view_no_patients_when_unfiltered(self) -> bool:
        """May the user view *no* patients when no filters are applied?"""
        if self.superuser:
            return False
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return all(not m.view_all_patients_when_unfiltered
                   for m in memberships)

    def group_ids_that_nonsuperuser_may_see_when_unfiltered(self) -> List[int]:
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return [m.group_id for m in memberships
                if m.view_all_patients_when_unfiltered]

    def may_upload_to_group(self, group_id: int) -> bool:
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.may_upload for m in memberships if m.group_id == group_id)

    @property
    def may_upload(self) -> bool:
        if self.upload_group_id is None:
            return False
        return self.may_upload_to_group(self.upload_group_id)

    @property
    def may_register_devices(self) -> bool:
        """
        You can register a device if your chosen upload groups allow you to do
        so. (You have to have a chosen group -- even for superusers -- because
        the tablet wants group ID policies at the moment of registration, so we
        have to know which group.)
        """
        if self.upload_group_id is None:
            return False
        if self.superuser:
            return True
        memberships = self.user_group_memberships  # type: List[UserGroupMembership]  # noqa
        return any(m.may_register_devices for m in memberships
                   if m.group_id == self.upload_group_id)


def set_password_directly(req: "CamcopsRequest",
                          username: str, password: str) -> bool:
    """
    If the user exists, set its password. Returns Boolean success.
    Used from the command line.
    """
    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username)
    if not user:
        return False
    user.set_password(req, password)
    user.enable(req)
    audit(req, "Password changed for user " + user.username, from_console=True)
    return True


# =============================================================================
# Unit testing
# =============================================================================

class UserTests(DemoDatabaseTestCase):
    def test_user(self) -> None:
        self.announce("test_user")
        req = self.req

        SecurityAccountLockout.delete_old_account_lockouts(req)
        self.assertIsInstance(
            SecurityAccountLockout.is_user_locked_out(req, "dummy_user"),
            bool
        )
        self.assertIsInstanceOrNone(
            SecurityAccountLockout.user_locked_out_until(req, "dummy_user"),
            Pendulum
        )

        self.assertIsInstance(
            SecurityLoginFailure.how_many_login_failures(req, "dummy_user"),
            int
        )
        SecurityLoginFailure.clear_login_failures_for_nonexistent_users(req)
        SecurityLoginFailure.clear_dummy_login_failures_if_necessary(req)
        SecurityLoginFailure.clear_dummy_login_failures_if_necessary(req)
        # ... do it twice (we had a bug relating to offset-aware vs
        # offset-naive date/time objects).

        self.assertIsInstance(User.is_username_permissible("some_user"), bool)
        User.take_some_time_mimicking_password_encryption()

        u = self.dbsession.query(User).first()  # type: User
        assert u, "Missing user in demo database!"

        g = self.dbsession.query(Group).first()  # type: Group
        assert g, "Missing group in demo database!"

        self.assertIsInstance(u.is_password_valid("dummy_password"), bool)
        self.assertIsInstance(u.must_agree_terms, bool)
        u.agree_terms(req)
        u.clear_login_failures(req)
        self.assertIsInstance(u.is_locked_out(req), bool)
        self.assertIsInstanceOrNone(u.locked_out_until(req), Pendulum)
        u.enable(req)
        self.assertIsInstance(u.may_login_as_tablet, bool)
        # TODO: etc... could do more here
        self.assertIsInstance(u.authorized_as_groupadmin, bool)
        self.assertIsInstance(u.may_use_webviewer, bool)
        self.assertIsInstance(u.authorized_to_add_special_note(g.id), bool)
        self.assertIsInstance(u.authorized_to_erase_tasks(g.id), bool)
        self.assertIsInstance(u.authorized_to_dump, bool)
        self.assertIsInstance(u.authorized_for_reports, bool)
        self.assertIsInstance(u.may_view_all_patients_when_unfiltered, bool)
        self.assertIsInstance(u.may_view_no_patients_when_unfiltered, bool)
        self.assertIsInstance(u.may_upload_to_group(g.id), bool)
        self.assertIsInstance(u.may_upload, bool)
        self.assertIsInstance(u.may_register_devices, bool)
