#!/usr/bin/env python
# camcops_server/cc_modules/cc_user.py

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

import cgi
import datetime
import logging
import re
from typing import List, Optional, Set, TYPE_CHECKING

import cardinal_pythonlib.crypto as rnc_crypto
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.orm_query import (
    CountStarSpecializedQuery,
    exists_orm,
)
from pendulum import Pendulum
from sqlalchemy.orm import relationship, Session as SqlASession
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .cc_audit import audit
from .cc_constants import ACTION, MINIMUM_PASSWORD_LENGTH, PARAM, DateFormat
from .cc_dt import (
    coerce_to_pendulum,
    convert_datetime_to_local,
    format_datetime,
)
from .cc_group import Group
from .cc_html import (
    get_generic_action_url,
    get_url_enter_new_password,
    get_url_field_value_pair,
    get_yes_no,
)
from .cc_jointables import user_group_table
from .cc_sqla_coltypes import (
    EmailAddressColType,
    FullNameColType,
    HashedPasswordColType,
    PendulumDateTimeAsIsoTextColType,
    UserNameColType,
)
from .cc_sqlalchemy import Base
from .cc_storedvar import ServerStoredVar
from .cc_unittest import unit_test_ignore

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
            .first()  # type: Optional[Pendulum]
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
        now = req.now
        last_cleared_var = ServerStoredVar.get_or_create(
            dbsession=req.dbsession,
            name="lastDummyLoginFailureClearanceAt",
            type_on_creation="text",
            default_value=None
        )
        try:
            last_cleared_val = last_cleared_var.get_value()
            when_last_cleared = coerce_to_pendulum(last_cleared_val)
        except ValueError:
            when_last_cleared = None
        if when_last_cleared is not None:
            elapsed = now - when_last_cleared
            if elapsed < CLEAR_DUMMY_LOGIN_PERIOD:
                # We cleared it recently.
                return

        cls.clear_login_failures_for_nonexistent_users(req)
        log.debug("Dummy login failures cleared.")
        now_as_utc_iso_string = format_datetime(now, DateFormat.ISO8601)
        last_cleared_var.set_value(now_as_utc_iso_string)


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
    may_upload = Column(
        "may_upload", Boolean,
        default=True,
        comment="May the user upload data from a tablet device?"
    )
    may_register_devices = Column(
        "may_register_devices", Boolean,
        default=True,
        comment="May the user register tablet devices?"
    )
    may_use_webviewer = Column(
        "may_use_webviewer", Boolean,
        default=True,
        comment="May the user use the web front end to view "
                "CamCOPS data?"
    )
    view_all_patients_when_unfiltered = Column(
        "view_all_patients_when_unfiltered", Boolean,
        default=False,
        comment="When no record filters are applied, can the user see "
                "all records? (If not, then none are shown.)"
    )
    superuser = Column(
        "superuser", Boolean,
        default=False,
        comment="Superuser?"
    )
    may_dump_data = Column(
        "may_dump_data", Boolean,
        default=False,
        comment="May the user run database data dumps via the web interface?"
    )
    may_run_reports = Column(
        "may_run_reports", Boolean,
        default=False,
        comment="May the user run reports via the web interface? "
                "(Overrides other view restrictions.)"
    )
    may_add_notes = Column(
        "may_add_notes", Boolean,
        default=False,
        comment="May the user add special notes to tasks?"
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
        # upload while it is. *** implement check in database.py
    )

    groups = relationship(
        Group,
        secondary=user_group_table,
        back_populates="users"  # see Group.users
    )

    upload_group = relationship("Group", foreign_keys=[upload_group_id])

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
                         username: str,
                         create_if_not_exists: bool = False) \
            -> Optional['User']:
        if not username:
            return None
        user = dbsession.query(cls).filter(cls.username == username).first()
        if user is None and create_if_not_exists:
            user = cls(username=username)
            dbsession.add(user)
        return user

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
        dbsession = req.dbsession
        user = cls.get_user_by_name(dbsession, username, False)
        if user:
            # already exists!
            return False
        user = cls.get_user_by_name(dbsession, username, True)  # now create

        user.may_upload = True
        user.may_register_devices = True
        user.may_use_webstorage = True
        user.may_use_webviewer = True
        user.view_all_patients_when_unfiltered = True
        user.superuser = True
        user.may_dump_data = True
        user.may_run_reports = True
        user.may_add_notes = True
        user.set_password(req, password)
        audit(req, "SUPERUSER CREATED: " + user.username, from_console=True)
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

    @staticmethod
    def is_username_permissible(username: str) -> bool:
        """Is this a permissible username?"""
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
        """Set a user's password."""
        self.hashedpw = rnc_crypto.hash_password(new_password,
                                                 BCRYPT_DEFAULT_LOG_ROUNDS)
        self.last_password_change_utc = req.now_utc
        self.must_change_password = False
        audit(req, "Password changed for user " + self.username)

    def is_password_valid(self, password: str) -> bool:
        """Is the supplied password valid?"""
        return rnc_crypto.is_password_valid(password, self.hashedpw)

    def force_password_change(self) -> None:
        """Make the user change their password at next login."""
        self.must_change_password = True

    def login(self, req: "CamcopsRequest") -> None:
        """Called when the framework has determined a successful login.

        Clears any login failures.
        Requires the user to change their password if policies say they should.
        """
        self.clear_login_failures(req)
        self.set_password_change_flag_if_necessary(req)
        self.last_login_at_utc = req.now_utc

    def set_password_change_flag_if_necessary(self,
                                              req: "CamcopsRequest") -> None:
        """If we're requiring users to change their passwords, then check to
        see if they must do so now."""
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

    def group_ids(self) -> List[int]:
        return sorted(list(g.id for g in self.groups))

    def set_group_ids(self, group_ids: List[int]) -> None:
        dbsession = SqlASession.object_session(self)
        assert dbsession, ("User.set_group_ids() called on a User that's not "
                           "yet in a session")
        groups = Group.get_groups_from_id_list(dbsession, group_ids)
        self.groups = groups

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

    def groups_user_may_see(self) -> List[Group]:
        # A less efficient version, for visual display (see
        # view_own_user_info.mako)
        groups = set(self.groups)  # type: Set[Group]
        for my_group in self.groups:  # type: Group
            groups.update(set(my_group.can_see_other_groups))
        return sorted(list(groups), key=lambda g: g.name)


def set_password_directly(req: "CamcopsRequest",
                          username: str, password: str) -> bool:
    """
    If the user exists, set its password. Returns Boolean success.
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

def ccuser_unit_tests(req: "CamcopsRequest") -> None:
    """Unit tests for cc_user module."""
    dbsession = req.dbsession

    unit_test_ignore("", SecurityAccountLockout.delete_old_account_lockouts)
    unit_test_ignore("", SecurityAccountLockout.is_user_locked_out,
                     req, "dummy_user")
    unit_test_ignore("", SecurityAccountLockout.user_locked_out_until,
                     req, "dummy_user")
    # skip: lock_user_out
    # skip: unlock_user

    # skip: record_login_failure
    # skip: act_on_login_failure
    # skip: clear_login_failures
    unit_test_ignore("", SecurityLoginFailure.how_many_login_failures,
                     req, "dummy_user")
    # skip: enable_user
    unit_test_ignore("", SecurityLoginFailure.clear_login_failures_for_nonexistent_users)  # noqa
    unit_test_ignore("", SecurityLoginFailure.clear_dummy_login_failures_if_necessary)  # noqa

    unit_test_ignore("", User.take_some_time_mimicking_password_encryption)

    user = User(username="dummy_user")
    # skip: user.save
    # skip: user.set_password
    unit_test_ignore("", user.is_password_valid, "dummy_password")
    # skip: user.force_password_change
    # skip: user.login
    # skip: user.set_password_change_flag_if_necessary
    unit_test_ignore("", user.must_agree_terms)
    # skip: user.agree_terms
    # skip: user.clear_login_failures
    # skip: user.enable

    unit_test_ignore("", User.user_exists,
                     dbsession, "dummy_user")
    # skip: create_superuser
    unit_test_ignore("", User.get_user_from_username_password,
                     req, "dummy_user", "dummy_password")
    unit_test_ignore("", User.is_username_permissible,
                     "dummy_user")
