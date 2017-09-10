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
from typing import Optional, TYPE_CHECKING

import cardinal_pythonlib.crypto as rnc_crypto
from cardinal_pythonlib.logs import BraceStyleAdapter
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.orm_query import (
    CountStarSpecializedQuery,
    exists_orm,
)
from pendulum import Pendulum
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .cc_audit import audit
from .cc_constants import ACTION, PARAM, DateFormat
from .cc_dt import (
    coerce_to_pendulum,
    convert_datetime_to_local,
    format_datetime,
)
from .cc_html import (
    get_generic_action_url,
    get_url_enter_new_password,
    get_url_field_value_pair,
    get_yes_no,
)
from .cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    HashedPasswordColType,
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

class LABEL(object):
    MAY_USE_WEBVIEWER = (
        "May use web viewer (BEWARE: you probably don’t "
        "want to untick this for your own user!)")
    MAY_VIEW_OTHER_USERS_RECORDS = (
        "May view other users’ records (BEWARE: unticking can be clinically "
        "dangerous by hiding important information)")
    VIEW_ALL_PATIENTS_WHEN_UNFILTERED = (
        "Sees all patients’ records when unfiltered (generally: untick in a "
        "clinical context for confidentiality)")
    MAY_UPLOAD = "May upload data from tablet devices"
    SUPERUSER = (
        "SUPERUSER (ALSO BEWARE: you probably don’t  want to untick this for "
        "your own user!)")
    MAY_REGISTER_DEVICES = "May register tablet devices"
    MAY_USE_WEBSTORAGE = "May use mobileweb storage facility"
    MAY_DUMP_DATA = "May dump data"
    MAY_RUN_REPORTS = "May run reports"
    MUST_CHANGE_PASSWORD = "Must change password at next login"
    MAY_ADD_NOTES = "May add special notes to tasks"


MINIMUM_PASSWORD_LENGTH = 8
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
    # *** change to a single primary key, like:
    # id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column(
        "username", UserNameColType,
        primary_key=True,  # composite primary key
        comment="User name (which may be a non-existent user, to prevent "
                "subtle username discovery by careful timing)"
    )
    locked_until = Column(
        "locked_until", DateTime,
        primary_key=True,  # composite primary key
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
    # *** change to a single primary key, like:
    # id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column(
        "username", UserNameColType,
        primary_key=True,  # composite primary key
        comment="User name (which may be a non-existent user, to prevent "
                "subtle username discovery by careful timing)"
    )
    login_failure_at = Column(
        "login_failure_at", DateTime,
        primary_key=True,  # composite primary key
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
        nlockouts = nfailures // cfg.LOCKOUT_THRESHOLD
        nfailures_since_last_lockout = nfailures % cfg.LOCKOUT_THRESHOLD
        if nlockouts >= 1 and nfailures_since_last_lockout == 0:
            # new lockout required
            lockout_minutes = nlockouts * \
                              cfg.LOCKOUT_DURATION_INCREMENT_MINUTES
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
    hashedpw = Column(
        "hashedpw", HashedPasswordColType,
        nullable=False,
        comment="Password hash"
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
    may_use_webstorage = Column(  # *** defunct
        "may_use_webstorage", Boolean,
        default=False,
        comment="May the user use the mobileweb database to run "
                "CamCOPS tasks via a web browser?"
    )
    may_use_webviewer = Column(
        "may_use_webviewer", Boolean,
        default=True,
        comment="May the user use the web front end to view "
                "CamCOPS data?"
    )
    may_view_other_users_records = Column(  # *** replace with group system
        "may_view_other_users_records", Boolean,
        default=False,
        comment="May the user see records uploaded by another user?"
    )
    view_all_patients_when_unfiltered = Column(  # *** maybe replace with group system
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
    may_dump_data = Column(  # *** rework with group system
        "may_dump_data", Boolean,
        default=False,
        comment="May the user run database data dumps via the web "
                "interface? (Overrides other view restrictions.)"
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

    @classmethod
    def get_user_by_id(cls,
                       dbsession: SqlASession,
                       user_id: int) -> Optional['User']:
        return dbsession.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_user_by_name(cls,
                         dbsession: SqlASession,
                         username: str,
                         create_if_not_exists: bool = False) \
            -> Optional['User']:
        user = dbsession.query(cls).filter(cls.username == username).first()
        if user is None and create_if_not_exists:
            user = cls(username=username)
            dbsession.add(user)
        return user

    @classmethod
    def user_exists(cls, req: "CamcopsRequest", username: str) -> bool:
        dbsession = req.dbsession
        return exists_orm(dbsession, cls, cls.username == username)

    @classmethod
    def create_superuser(cls, req: "CamcopsRequest", username: str,
                         password: str) -> bool:
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
        user.may_view_other_users_records = True
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

    def set_password_change_flag_if_necessary(self,
                                              req: "CamcopsRequest") -> None:
        """If we're requiring users to change their passwords, then check to
        see if they must do so now."""
        if self.must_change_password:
            # already required, pointless to check again
            return
        cfg = req.config
        if cfg.PASSWORD_CHANGE_FREQUENCY_DAYS <= 0:
            # changes never required
            return
        if not self.last_password_change_utc:
            # we don't know when the last change was, so it's overdue
            self.force_password_change()
            return
        delta = req.now_utc - self.last_password_change_utc
        if delta.days >= cfg.PASSWORD_CHANGE_FREQUENCY_DAYS:
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


# =============================================================================
# Support functions
# =============================================================================

def get_user_filter_dropdown(req: "CamcopsRequest",
                             currently_selected_id: int = None) -> str:
    """Get HTML list of all known users."""
    dbsession = req.dbsession
    id_username_tuples = dbsession.query(User.id, User.username)\
        .order_by(User.username)\
        .all()
    s = """
        <select name="{}">
            <option value="">(all)</option>
    """.format(PARAM.USER)
    for user_id, username in id_username_tuples:
        s += """<option value="{user_id}"{sel}>{name}</option>""".format(
            user_id=user_id,
            name=ws.webify(username),
            sel=ws.option_selected(currently_selected_id, user_id),
        )
    s += """</select>"""
    return s


# =============================================================================
# User management
# =============================================================================

def get_url_edit_user(req: "CamcopsRequest", username: str) -> str:
    """URL to edit a specific user."""
    return (
        get_generic_action_url(req, ACTION.EDIT_USER) +
        get_url_field_value_pair(PARAM.USERNAME, username)
    )


def get_url_ask_delete_user(req: "CamcopsRequest", username: str) -> str:
    """URL to ask for confirmation to delete a specific user."""
    return (
        get_generic_action_url(req, ACTION.ASK_DELETE_USER) +
        get_url_field_value_pair(PARAM.USERNAME, username)
    )


def get_url_enable_user(req: "CamcopsRequest", username: str) -> str:
    """URL to enable a specific user."""
    return (
        get_generic_action_url(req, ACTION.ENABLE_USER) +
        get_url_field_value_pair(PARAM.USERNAME, username)
    )


def manage_users_html(req: "CamcopsRequest") -> str:
    """HTML to view/edit users."""
    cfg = req.config
    ccsession = req.camcops_session
    dbsession = req.dbsession
    allusers = dbsession.query(User).order_by(User.username).all()
    output = req.webstart_html + """
        {}
        <h1>Manage users</h1>
        <ul>
            <li><a href="{}">Add user</a></li>
        </ul>
        <table>
            <tr>
                <th>User name</th>
                <th>Actions</th>
                <th>Locked out?</th>
                <th>Last password change (UTC)</th>
                <th>May use web viewer?</th>
                <th>May view other users’ records?</th>
                <th>Sees all patients’ records when unfiltered?</th>
                <th>May upload data?</th>
                <th>May manage users?</th>
                <th>May register tablet devices?</th>
                <th>May use webstorage?</th>
                <th>May dump data?</th>
                <th>May run reports?</th>
                <th>May add notes?</th>
                <th>Click to delete use</th>
            </tr>
    """.format(
        ccsession.get_current_user_html(),
        get_generic_action_url(req, ACTION.ASK_TO_ADD_USER),
    ) + WEBEND
    for u in allusers:
        if u.is_locked_out():
            enableuser = "| <a href={}>Re-enable user</a>".format(
                get_url_enable_user(req, u.username)
            )
            lockedmsg = "Yes, until {}".format(format_datetime(
                u.locked_out_until(),
                DateFormat.ISO8601
            ))
        else:
            enableuser = ""
            lockedmsg = "No"
        output += """
            <tr>
                <td>{username}</td>
                <td>
                    <a href="{url_edit}">Edit permissions</a>
                    | <a href="{url_changepw}">Change password</a>
                    {enableuser}
                </td>
                <td>{lockedmsg}</td>
                <td>{lastpwchange}</td>
                <td>{may_use_webviewer}</td>
                <td>{may_view_other_users_records}</td>
                <td>{view_all_patients_when_unfiltered}</td>
                <td>{may_upload}</td>
                <td>{superuser}</td>
                <td>{may_register_devices}</td>
                <td>{may_use_webstorage}</td>
                <td>{may_dump_data}</td>
                <td>{may_run_reports}</td>
                <td>{may_add_notes}</td>
                <td><a href="{url_delete}">Delete user {username}</a></td>
            </tr>
        """.format(
            url_edit=get_url_edit_user(req, u.username),
            url_changepw=get_url_enter_new_password(req, u.username),
            enableuser=enableuser,
            lockedmsg=lockedmsg,
            lastpwchange=ws.webify(u.last_password_change_utc),
            may_use_webviewer=get_yes_no(u.may_use_webviewer),
            may_view_other_users_records=get_yes_no(
                u.may_view_other_users_records),
            view_all_patients_when_unfiltered=get_yes_no(
                u.view_all_patients_when_unfiltered),
            may_upload=get_yes_no(u.may_upload),
            superuser=get_yes_no(u.superuser),
            may_register_devices=get_yes_no(u.may_register_devices),
            may_use_webstorage=get_yes_no(u.may_use_webstorage),
            may_dump_data=get_yes_no(u.may_dump_data),
            may_run_reports=get_yes_no(u.may_run_reports),
            may_add_notes=get_yes_no(u.may_add_notes),
            url_delete=get_url_ask_delete_user(req, u.username),
            username=u.username,
        )
    output += """
        </table>
    """ + WEBEND
    return output


def edit_user_form(req: "CamcopsRequest", username: str) -> str:
    """HTML form to edit a single user's permissions."""
    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username)
    ccsession = req.camcops_session
    cfg = req.config
    if not user:
        return user_management_failure_message(req,
                                               "Invalid user: " + username)
    return req.webstart_html + """
        {userdetails}
        <h1>Edit user {username}</h1>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.USERNAME}" value="{username}">
            <label>
                <input type="checkbox" name="{PARAM.MAY_USE_WEBVIEWER}"
                    value="1" {may_use_webviewer}>
                {LABEL.MAY_USE_WEBVIEWER}
            </label><br>
            <label>
                <input type="checkbox"
                    name="{PARAM.MAY_VIEW_OTHER_USERS_RECORDS}"
                    value="1" {may_view_other_users_records}>
                {LABEL.MAY_VIEW_OTHER_USERS_RECORDS}
            </label><br>
            <label>
                <input type="checkbox"
                    name="{PARAM.VIEW_ALL_PTS_WHEN_UNFILTERED}"
                    value="1" {view_all_patients_when_unfiltered}>
                {LABEL.VIEW_ALL_PATIENTS_WHEN_UNFILTERED}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_UPLOAD}"
                    value="1" {may_upload}>
                {LABEL.MAY_UPLOAD}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.SUPERUSER}"
                    value="1" {superuser}>
                {LABEL.SUPERUSER}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_REGISTER_DEVICES}"
                    value="1" {may_register_devices}>
                {LABEL.MAY_REGISTER_DEVICES}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_USE_WEBSTORAGE}"
                    value="1" {may_use_webstorage}>
                {LABEL.MAY_USE_WEBSTORAGE}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_DUMP_DATA}"
                    value="1" {may_dump_data}>
                {LABEL.MAY_DUMP_DATA}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_RUN_REPORTS}"
                    value="1" {may_run_reports}>
                {LABEL.MAY_RUN_REPORTS}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_ADD_NOTES}"
                    value="1" {may_add_notes}>
                {LABEL.MAY_ADD_NOTES}
            </label><br>
            <input type="hidden" name="{PARAM.ACTION}"
                value="{ACTION.CHANGE_USER}">
            <input type="submit" value="Submit">
        </form>
    """.format(
        may_use_webviewer=ws.checkbox_checked(user.may_use_webviewer),
        may_view_other_users_records=ws.checkbox_checked(
            user.may_view_other_users_records),
        view_all_patients_when_unfiltered=ws.checkbox_checked(
            user.view_all_patients_when_unfiltered),
        may_upload=ws.checkbox_checked(user.may_upload),
        superuser=ws.checkbox_checked(user.superuser),
        may_register_devices=ws.checkbox_checked(user.may_register_devices),
        may_use_webstorage=ws.checkbox_checked(user.may_use_webstorage),
        may_dump_data=ws.checkbox_checked(user.may_dump_data),
        may_run_reports=ws.checkbox_checked(user.may_run_reports),
        may_add_notes=ws.checkbox_checked(user.may_add_notes),
        userdetails=ccsession.get_current_user_html(),
        script=req.script_name,
        username=user.username,
        PARAM=PARAM,
        ACTION=ACTION,
        LABEL=LABEL,
    ) + WEBEND


def change_user(req: "CamcopsRequest", form: cgi.FieldStorage) -> str:
    """Apply changes to a user, and return success/failure HTML."""
    username = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    may_use_webviewer = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_USE_WEBVIEWER)
    may_view_other_users_records = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_VIEW_OTHER_USERS_RECORDS)
    view_all_patients_when_unfiltered = ws.get_cgi_parameter_bool(
        form, PARAM.VIEW_ALL_PTS_WHEN_UNFILTERED)
    may_upload = ws.get_cgi_parameter_bool(form, PARAM.MAY_UPLOAD)
    superuser = ws.get_cgi_parameter_bool(form, PARAM.SUPERUSER)
    may_register_devices = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_REGISTER_DEVICES)
    may_use_webstorage = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_USE_WEBSTORAGE)
    may_dump_data = ws.get_cgi_parameter_bool(form, PARAM.MAY_DUMP_DATA)
    may_run_reports = ws.get_cgi_parameter_bool(form, PARAM.MAY_RUN_REPORTS)
    may_add_notes = ws.get_cgi_parameter_bool(form, PARAM.MAY_ADD_NOTES)

    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username)
    if not user:
        return user_management_failure_message(req,
                                               "Invalid user: " + username)

    user.may_use_webviewer = may_use_webviewer
    user.may_view_other_users_records = may_view_other_users_records
    user.view_all_patients_when_unfiltered = view_all_patients_when_unfiltered
    user.may_upload = may_upload
    user.superuser = superuser
    user.may_register_devices = may_register_devices
    user.may_use_webstorage = may_use_webstorage
    user.may_dump_data = may_dump_data
    user.may_run_reports = may_run_reports
    user.may_add_notes = may_add_notes

    audit(
        req,
        (
            "User permissions edited for user {}: "
            "may_use_webviewer={}, "
            "may_view_other_users_records={}, "
            "view_all_patients_when_unfiltered={}, "
            "may_upload={}, "
            "superuser={}, "
            "may_register_devices={}, "
            "may_use_webstorage={}, "
            "may_dump_data={}, "
            "may_run_reports={}, "
            "may_add_notes={} "
        ).format(
            user.username,
            may_use_webviewer,
            may_view_other_users_records,
            view_all_patients_when_unfiltered,
            may_upload,
            superuser,
            may_register_devices,
            may_use_webstorage,
            may_dump_data,
            may_run_reports,
            may_add_notes,
        )
    )
    return user_management_success_message(
        req, "Details updated for user " + user.username)


def ask_to_add_user_html(req: "CamcopsRequest") -> str:
    """HTML form to add a user."""
    cfg = req.config
    ccsession = req.camcops_session
    return req.webstart_html + """
        {userdetails}
        <h1>Add user</h1>
        <form name="myform" action="{script}" method="POST">
            User name:
            <input type="text" name="{PARAM.USERNAME}" autocomplete="off"><br>

            Password:
            <input type="password" name="{PARAM.PASSWORD_1}"
                    autocomplete="off">
            (minimum length {MINIMUM_PASSWORD_LENGTH} characters)<br>

            Re-enter password:
            <input type="password" name="{PARAM.PASSWORD_2}"
                    autocomplete="off"><br>

            <label>
                <input type="checkbox" name="{PARAM.MUST_CHANGE_PASSWORD}"
                        value="1" {TRUE}>
                {LABEL.MUST_CHANGE_PASSWORD}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_USE_WEBVIEWER}"
                    value="1" {TRUE}>
                {LABEL.MAY_USE_WEBVIEWER}
            </label><br>
            <label>
                <input type="checkbox"
                    name="{PARAM.MAY_VIEW_OTHER_USERS_RECORDS}"
                    value="1" {TRUE}>
                {LABEL.MAY_VIEW_OTHER_USERS_RECORDS}
            </label><br>
            <label>
                <input type="checkbox"
                    name="{PARAM.VIEW_ALL_PTS_WHEN_UNFILTERED}"
                    value="1" {FALSE}>
                {LABEL.VIEW_ALL_PATIENTS_WHEN_UNFILTERED}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_UPLOAD}"
                    value="1" {TRUE}>
                {LABEL.MAY_UPLOAD}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.SUPERUSER}"
                    value="1" {FALSE}>
                {LABEL.SUPERUSER}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_REGISTER_DEVICES}"
                    value="1" {FALSE}>
                {LABEL.MAY_REGISTER_DEVICES}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_USE_WEBSTORAGE}"
                    value="1" {FALSE}>
                {LABEL.MAY_USE_WEBSTORAGE}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_DUMP_DATA}"
                    value="1" {FALSE}>
                {LABEL.MAY_DUMP_DATA}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_RUN_REPORTS}"
                    value="1" {FALSE}>
                {LABEL.MAY_RUN_REPORTS}
            </label><br>
            <label>
                <input type="checkbox" name="{PARAM.MAY_ADD_NOTES}"
                    value="1" {FALSE}>
                {LABEL.MAY_ADD_NOTES}
            </label><br>
            <input type="hidden" name="{PARAM.ACTION}"
                value="{ACTION.ADD_USER}">
            <input type="submit" value="Submit">
        </form>
    """.format(
        TRUE=ws.checkbox_checked(True),
        FALSE=ws.checkbox_checked(False),
        LABEL=LABEL,
        userdetails=ccsession.get_current_user_html(),
        script=req.script_name,
        PARAM=PARAM,
        ACTION=ACTION,
        MINIMUM_PASSWORD_LENGTH=MINIMUM_PASSWORD_LENGTH,
    ) + WEBEND


def add_user(req: "CamcopsRequest", form: cgi.FieldStorage) -> str:
    """Add a user, and return HTML success/failure message."""
    username = ws.get_cgi_parameter_str(form, PARAM.USERNAME)
    password_1 = ws.get_cgi_parameter_str(form, PARAM.PASSWORD_1)
    password_2 = ws.get_cgi_parameter_str(form, PARAM.PASSWORD_2)
    must_change_password = ws.get_cgi_parameter_bool(
        form, PARAM.MUST_CHANGE_PASSWORD)

    may_use_webviewer = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_USE_WEBVIEWER)
    may_view_other_users_records = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_VIEW_OTHER_USERS_RECORDS)
    view_all_patients_when_unfiltered = ws.get_cgi_parameter_bool(
        form, PARAM.VIEW_ALL_PTS_WHEN_UNFILTERED)
    may_upload = ws.get_cgi_parameter_bool(form, PARAM.MAY_UPLOAD)
    superuser = ws.get_cgi_parameter_bool(form, PARAM.SUPERUSER)
    may_register_devices = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_REGISTER_DEVICES)
    may_use_webstorage = ws.get_cgi_parameter_bool(
        form, PARAM.MAY_USE_WEBSTORAGE)
    may_dump_data = ws.get_cgi_parameter_bool(form, PARAM.MAY_DUMP_DATA)
    may_run_reports = ws.get_cgi_parameter_bool(form, PARAM.MAY_RUN_REPORTS)
    may_add_notes = ws.get_cgi_parameter_bool(form, PARAM.MAY_ADD_NOTES)

    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username, False)
    if user:
        return user_management_failure_message(
            req, "User already exists: " + username)
    if not User.is_username_permissible(username):
        return user_management_failure_message(
            req, "Invalid username: " + ws.webify(username))
    if password_1 != password_2:
        return user_management_failure_message(req, "Passwords don't mach")
    if len(password_1) < MINIMUM_PASSWORD_LENGTH:
        return user_management_failure_message(
            req,
            "Password must be at least {} characters".format(
                MINIMUM_PASSWORD_LENGTH
            ))

    user = User.get_user_by_name(dbsession, username, True)  # create user
    user.set_password(req.now_utc, password_1)

    user.may_use_webviewer = may_use_webviewer
    user.may_view_other_users_records = may_view_other_users_records
    user.view_all_patients_when_unfiltered = view_all_patients_when_unfiltered
    user.may_upload = may_upload
    user.superuser = superuser
    user.may_register_devices = may_register_devices
    user.may_use_webstorage = may_use_webstorage
    user.may_dump_data = may_dump_data
    user.may_run_reports = may_run_reports
    user.may_add_notes = may_add_notes

    if must_change_password:
        user.force_password_change()

    audit(
        req,
        (
            "User created: {}: "
            "may_use_webviewer={}, "
            "may_view_other_users_records={}, "
            "view_all_patients_when_unfiltered={}, "
            "may_upload={}, "
            "superuser={}, "
            "may_register_devices={}, "
            "may_use_webstorage={}, "
            "may_dump_data={}, "
            "may_run_reports={}, "
            "may_add_notes={}, "
            "must_change_password={}"
        ).format(
            user.username,
            may_use_webviewer,
            may_view_other_users_records,
            view_all_patients_when_unfiltered,
            may_upload,
            superuser,
            may_register_devices,
            may_use_webstorage,
            may_dump_data,
            may_run_reports,
            may_add_notes,
            must_change_password
        )
    )
    return user_management_success_message(
        req, "User " + user.username + " created")


def ask_delete_user_html(req: "CamcopsRequest", username: str) -> str:
    """HTML form to delete a user."""
    cfg = req.config
    ccsession = req.camcops_session
    return req.webstart_html + """
        {userdetails}
        <h1>You are about to delete user {username}</h1>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.USERNAME}" value="{username}">
            <input type="hidden" name="{PARAM.ACTION}"
                value="{ACTION.DELETE_USER}">
            <input type="submit" value="Delete">
        </form>
    """.format(
        userdetails=ccsession.get_current_user_html(),
        username=username,
        script=req.script_name,
        ACTION=ACTION,
        PARAM=PARAM,
    ) + WEBEND


def delete_user(req: "CamcopsRequest", username: str) -> str:
    """Delete a user, and return HTML success/failure message."""
    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username)
    if not user:
        return user_management_failure_message(req,
                                               "No such user: " + username)
    dbsession.delete(user)
    audit(req, "User deleted: #{} ({})".format(user.id, user.username))
    return user_management_success_message(
        req, "User " + user.username + " deleted")


def enable_user_webview(req: "CamcopsRequest", username: str) -> str:
    """Enable a user, and return HTML success/failure message."""
    dbsession = req.dbsession
    user = User.get_user_by_name(dbsession, username)
    if not user:
        return user_management_failure_message(req,
                                               "No such user: " + username)
    user.enable(req)
    return user_management_success_message(
        req, "User " + user.username + " enabled")


def user_management_success_message(req: "CamcopsRequest",
                                    msg: str,
                                    as_manager: bool = True,
                                    additional_html: str = "") -> str:
    """Generic success HTML for user management."""
    extra_html = ""
    if as_manager:
        extra_html = """
            <div>
                <a href={}>Return to user menu</a>
            </div>
        """.format(get_generic_action_url(req, ACTION.MANAGE_USERS))
    return simple_success_message(req, msg, additional_html + extra_html)


def user_management_failure_message(req: "CamcopsRequest",
                                    msg: str, as_manager: bool = True) -> str:
    """Generic failure HTML for user management."""
    extra_html = ""
    if as_manager:
        extra_html = """
            <div>
                <a href={}>Return to user menu</a>
            </div>
        """.format(
            get_generic_action_url(req, ACTION.MANAGE_USERS)
        )
    return fail_with_error_stay_logged_in(req, msg, extra_html)


def set_password_directly(req: "CamcopsRequest",
                          username: str, password: str) -> bool:
    """If the user exists, set its password. Returns Boolean success."""
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

    unit_test_ignore("", enter_new_password_html, req, "dummy_user")
    # skip: change_password
    # skip: set_password_directly
    unit_test_ignore("", manage_users_html, req)
    unit_test_ignore("", edit_user_form, req, "dummy_user")
    # skip: change_user
    unit_test_ignore("", ask_to_add_user_html, req)
    # skip: add_user
    unit_test_ignore("", ask_delete_user_html, req, "dummy_user")
    # skip: delete_user
    unit_test_ignore("", user_management_success_message,
                     req, "test_msg", True)
    unit_test_ignore("", user_management_success_message,
                     req, "test_msg", False)
    unit_test_ignore("", user_management_failure_message,
                     req, "test_msg", True)
    unit_test_ignore("", user_management_failure_message,
                     req, "test_msg", False)
