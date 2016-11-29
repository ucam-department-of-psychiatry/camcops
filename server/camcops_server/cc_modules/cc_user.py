#!/usr/bin/env python3
# cc_user.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import cgi
import datetime
import re
from typing import Optional

import cardinal_pythonlib.rnc_crypto as rnc_crypto
from cardinal_pythonlib.rnc_lang import AttrDict
import cardinal_pythonlib.rnc_web as ws

from .cc_audit import audit
from .cc_constants import ACTION, PARAM, DATEFORMAT, WEBEND
from . import cc_db
from . import cc_dt
from . import cc_html
from .cc_logger import log
from .cc_pls import pls
# NO: CIRCULAR # from .cc_session import Session
from . import cc_storedvar
from .cc_unittest import unit_test_ignore

SESSION_FWD_REF = "Session"

# =============================================================================
# Constants
# =============================================================================

LABEL = AttrDict({
    "MAY_USE_WEBVIEWER": (
        "May use web viewer (BEWARE: you probably don’t "
        "want to untick this for your own user!)"),
    "MAY_VIEW_OTHER_USERS_RECORDS": (
        "May view other users’ records (BEWARE: unticking can be clinically "
        "dangerous by hiding important information)"),
    "VIEW_ALL_PATIENTS_WHEN_UNFILTERED": (
        "Sees all patients’ records when unfiltered (generally: untick in a "
        "clinical context for confidentiality)"),
    "MAY_UPLOAD": "May upload data from tablet devices",
    "SUPERUSER": (
        "SUPERUSER (ALSO BEWARE: you probably don’t  want to untick this for "
        "your own user!)"),
    "MAY_REGISTER_DEVICES": "May register tablet devices",
    "MAY_USE_WEBSTORAGE": "May use mobileweb storage facility",
    "MAY_DUMP_DATA": "May dump data",
    "MAY_RUN_REPORTS": "May run reports",
    "MUST_CHANGE_PASSWORD": "Must change password at next login",
    "MAY_ADD_NOTES": "May add special notes to tasks",
})

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

SECURITY_ACCOUNT_LOCKOUT_TABLENAME = "_security_account_lockouts"
SECURITY_ACCOUNT_LOCKOUT_FIELDSPECS = [
    dict(name="username", cctype="USERNAME",  # NB not PK
         comment="User name (which may be a non-existent user, to prevent "
                 "username discovery)"),
    dict(name="locked_until", cctype="DATETIME", notnull=True,
         comment="Account is locked until (UTC)", indexed=True),
]

SECURITY_LOGIN_FAILURE_TABLENAME = "_security_login_failures"
SECURITY_LOGIN_FAILURE_FIELDSPECS = [
    dict(name="username", cctype="USERNAME",
         comment="User name (which may be a non-existent user, to prevent "
                 "username discovery)"),
    dict(name="login_failure_at", cctype="DATETIME", notnull=True,
         comment="Login failure occurred at (UTC)", indexed=True),
]

CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS = 7
CLEAR_DUMMY_LOGIN_PERIOD = datetime.timedelta(
    days=CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS)


# =============================================================================
# Security for users
# =============================================================================
# These functions are independent of the class, in part because we record
# login failures for non-existent users, and pretend they're locked out
# (to prevent username discovery that way)

def delete_old_account_lockouts() -> None:
    """Delete all expired account lockouts."""
    pls.db.db_exec("DELETE FROM " + SECURITY_ACCOUNT_LOCKOUT_TABLENAME +
                   " WHERE locked_until <= ?", pls.NOW_UTC_NO_TZ)


def is_user_locked_out(username: str) -> bool:
    """Is the user currently locked out?"""
    count = pls.db.fetchvalue(
        "SELECT COUNT(*) FROM " + SECURITY_ACCOUNT_LOCKOUT_TABLENAME +
        " WHERE username = ? AND locked_until > ?",
        username,
        pls.NOW_UTC_NO_TZ)
    return count > 0


def user_locked_out_until(username: str) -> Optional[datetime.datetime]:
    """When is the user locked out until?

    Returns datetime in local timezone (or None).
    """
    utc_no_tz = pls.db.fetchvalue(
        "SELECT MAX(locked_until) FROM " + SECURITY_ACCOUNT_LOCKOUT_TABLENAME +
        " WHERE username = ?",
        username)
    if not utc_no_tz:
        return None
    return cc_dt.convert_utc_datetime_without_tz_to_local(utc_no_tz)


def lock_user_out(username: str, lockout_minutes: int) -> None:
    """Lock user out for a specified number of minutes."""
    lock_until = pls.NOW_UTC_NO_TZ + datetime.timedelta(
        minutes=lockout_minutes)
    pls.db.db_exec(
        "INSERT INTO " + SECURITY_ACCOUNT_LOCKOUT_TABLENAME +
        " (username, locked_until) VALUES (?, ?)",
        username,
        lock_until)
    audit("Account {} locked out for {} minutes".format(username,
                                                        lockout_minutes))


def unlock_user(username: str) -> None:
    """Unlock a user."""
    pls.db.db_exec(
        "DELETE FROM " + SECURITY_ACCOUNT_LOCKOUT_TABLENAME +
        " WHERE username = ?",
        username)


def record_login_failure(username: str) -> None:
    """Record that a user has failed to log in."""
    pls.db.db_exec(
        "INSERT INTO " + SECURITY_LOGIN_FAILURE_TABLENAME +
        " (username, login_failure_at) VALUES (?, ?)",
        username,
        pls.NOW_UTC_NO_TZ)


def act_on_login_failure(username: str) -> None:
    """Record login failure and lock out user if necessary."""
    audit("Failed login as user: {}".format(username))
    record_login_failure(username)
    nfailures = how_many_login_failures(username)
    nlockouts = nfailures // pls.LOCKOUT_THRESHOLD
    nfailures_since_last_lockout = nfailures % pls.LOCKOUT_THRESHOLD
    if nlockouts >= 1 and nfailures_since_last_lockout == 0:
        # new lockout required
        lockout_minutes = nlockouts * pls.LOCKOUT_DURATION_INCREMENT_MINUTES
        lock_user_out(username, lockout_minutes)


def clear_login_failures(username: str) -> None:
    """Clear login failures for a user."""
    pls.db.db_exec(
        "DELETE FROM " + SECURITY_LOGIN_FAILURE_TABLENAME +
        " WHERE username = ?",
        username)


def how_many_login_failures(username: str) -> int:
    """How many times has the user failed to log in (recently)?"""
    return pls.db.fetchvalue(
        "SELECT COUNT(*) FROM " + SECURITY_LOGIN_FAILURE_TABLENAME +
        " WHERE username = ?",
        username)


def enable_user(username: str) -> None:
    """Unlock user and clear login failures."""
    unlock_user(username)
    clear_login_failures(username)
    audit("User {} re-enabled".format(username))


def clear_login_failures_for_nonexistent_users() -> None:
    """Clear login failures for nonexistent users.

    Login failues are recorded for nonexistent users to mimic the lockout seen
    for real users, i.e. to reduce the potential for username discovery.
    """
    pls.db.db_exec("""
        DELETE FROM """ + SECURITY_LOGIN_FAILURE_TABLENAME + """
        WHERE username NOT IN (
            SELECT username
            FROM """ + User.TABLENAME + """
        )
    """)


def clear_dummy_login_failures_if_necessary() -> None:
    """Clear dummy login failures if we haven't done so for a while.

    Not too often! See CLEAR_DUMMY_LOGIN_FREQUENCY_DAYS.
    """
    last_cleared_var = cc_storedvar.ServerStoredVar(
        "lastDummyLoginFailureClearanceAt", "text", None)
    last_cleared_val = last_cleared_var.get_value()
    if last_cleared_val:
        elapsed = pls.NOW_UTC_WITH_TZ - cc_dt.get_datetime_from_string(
            last_cleared_val)
        if elapsed < CLEAR_DUMMY_LOGIN_PERIOD:
            # We cleared it recently.
            return

    clear_login_failures_for_nonexistent_users()
    log.debug("Dummy login failures cleared.")
    now_as_utc_iso_string = cc_dt.format_datetime(pls.NOW_UTC_WITH_TZ,
                                                  DATEFORMAT.ISO8601)
    last_cleared_var.set_value(now_as_utc_iso_string)


def take_some_time_mimicking_password_encryption() -> None:
    """Waste some time. We use this when an attempt has been made to log in
    with a nonexistent user; we know the user doesn't exist very quickly, but
    we mimic the time it takes to check a real user's password."""
    rnc_crypto.hash_password("dummy!", BCRYPT_DEFAULT_LOG_ROUNDS)


# =============================================================================
# User class
# =============================================================================

class User:
    """Class representing a user."""
    TABLENAME = "_security_users"
    FIELDSPECS = [
        dict(name="id", cctype="INT_UNSIGNED", pk=True,
             comment="User ID"),
        dict(name="username", cctype="USERNAME", indexed=True,
             comment="User name"),
        dict(name="hashedpw", cctype="HASHEDPASSWORD",
             comment="Password hash"),
        dict(name="last_password_change_utc", cctype="DATETIME",
             comment="Date/time this user last changed their password (UTC)"),
        dict(name="may_upload", cctype="BOOL",
             comment="May the user upload data from a tablet device?"),
        dict(name="may_register_devices", cctype="BOOL",
             comment="May the user register tablet devices?"),
        dict(name="may_use_webstorage", cctype="BOOL",
             comment="May the user use the mobileweb database to run "
                     "CamCOPS tasks via a web browser?"),
        dict(name="may_use_webviewer", cctype="BOOL",
             comment="May the user use the web front end to view "
                     "CamCOPS data?"),
        dict(name="may_view_other_users_records", cctype="BOOL",
             comment="May the user see records uploaded by another user?"),
        dict(name="view_all_patients_when_unfiltered", cctype="BOOL",
             comment="When no record filters are applied, can the user see "
                     "all records? (If not, then none are shown.)"),
        dict(name="superuser", cctype="BOOL", comment="Superuser?"),
        dict(name="may_dump_data", cctype="BOOL",
             comment="May the user run database data dumps via the web "
                     "interface? (Overrides other view restrictions.)"),
        dict(name="may_run_reports", cctype="BOOL",
             comment="May the user run reports via the web interface? "
                     "(Overrides other view restrictions.)"),
        dict(name="may_add_notes", cctype="BOOL",
             comment="May the user add special notes to tasks?"),
        dict(name="must_change_password", cctype="BOOL",
             comment="Must change password at next webview login"),
        dict(name="when_agreed_terms_of_use", cctype="ISO8601",
             comment="Date/time this user acknowledged the Terms and "
                     "Conditions of Use (ISO 8601)"),
    ]
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying database tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)
        # But also:
        cc_db.create_or_update_table(
            SECURITY_ACCOUNT_LOCKOUT_TABLENAME,
            SECURITY_ACCOUNT_LOCKOUT_FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)
        cc_db.create_or_update_table(
            SECURITY_LOGIN_FAILURE_TABLENAME,
            SECURITY_LOGIN_FAILURE_FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self, user_id: int = None) -> None:
        """Initialize. Lower case usernames are enforced internally."""
        pls.db.fetch_object_from_db_by_pk(
            self, User.TABLENAME, User.FIELDS, user_id)  # last is the pk

    def get_id(self) -> Optional[int]:
        return self.id

    def save(self) -> bool:
        """Save to database."""
        if self.username is None or self.hashedpw is None:
            log.warning("Refusing to save a user with no name/password")
            return False  # can't save a user with no name or password
        if self.id is not None:
            sql = (
                "SELECT COUNT(*) FROM {table} "
                "WHERE id <> ? "
                "AND username = ? ".format(table=User.TABLENAME)
            )
            args = [self.id, self.username]
            count = pls.db.fetchone(sql, *args)[0]
            if count > 0:
                log.warning("Refusing to save user: other user has same name")
                return False  # another user exists with the same username
        already_exists = self.id is not None
        pls.db.save_object_to_db(self, User.TABLENAME, User.FIELDS,
                                 not already_exists)
        return True

    def set_password(self, new_password: str) -> None:
        """Set a user's password."""
        self.hashedpw = rnc_crypto.hash_password(new_password,
                                                 BCRYPT_DEFAULT_LOG_ROUNDS)
        self.last_password_change_utc = pls.NOW_UTC_NO_TZ
        self.must_change_password = False

    def is_password_valid(self, password: str) -> bool:
        """Is the supplied password valid?"""
        return rnc_crypto.is_password_valid(password, self.hashedpw)

    def force_password_change(self) -> None:
        """Make the user change their password at next login."""
        self.must_change_password = True
        self.save()

    def login(self) -> None:
        """Called when the framework has determined a successful login.

        Clears any login failures.
        Requires the user to change their password if policies say they should.
        """
        self.clear_login_failures()
        self.set_password_change_flag_if_necessary()

    def set_password_change_flag_if_necessary(self) -> None:
        """If we're requiring users to change their passwords, then check to
        see if they must do so now."""
        if self.must_change_password:
            # already required, pointless to check again
            return
        if pls.PASSWORD_CHANGE_FREQUENCY_DAYS <= 0:
            # changes never required
            return
        if not self.last_password_change_utc:
            # we don't know when the last change was, so it's overdue
            self.force_password_change()
            return
        delta = pls.NOW_UTC_NO_TZ - self.last_password_change_utc
        if delta.days >= pls.PASSWORD_CHANGE_FREQUENCY_DAYS:
            self.force_password_change()

    def must_agree_terms(self) -> bool:
        """Does the user still need to agree the terms/conditions of use?"""
        return self.when_agreed_terms_of_use is None

    def agree_terms(self) -> None:
        """Mark the user as having agreed to the terms/conditions of use
        now."""
        self.when_agreed_terms_of_use = cc_dt.format_datetime(
            pls.NOW_LOCAL_TZ, DATEFORMAT.ISO8601)
        self.save()

    def clear_login_failures(self) -> None:
        """Clear login failures."""
        if not self.username:
            return
        clear_login_failures(self.username)

    def is_locked_out(self) -> bool:
        """Is the user locked out because of multiple login failures?"""
        if not self.username:
            return False
        return is_user_locked_out(self.username)

    def locked_out_until(self) -> Optional[datetime.datetime]:
        """When is the user locked out until (or None)?

        Returns datetime in local timezone (or None).
        """
        if not self.username:
            return None
        return user_locked_out_until(self.username)

    def enable(self) -> None:
        """Re-enables a user, unlocking them and clearing login failures."""
        if not self.username:
            return
        enable_user(self.username)


def get_user_by_name(username: str,
                     create_if_not_exists: bool = False) -> Optional[User]:
    if not username:
        return None
    username = username.lower()  # CASE CONVERSION HERE: ENFORCE LOWER CASE
    userobj = User()
    if pls.db.fetch_object_from_db_by_other_field(userobj,
                                                  User.TABLENAME,
                                                  User.FIELDS,
                                                  "username",
                                                  username):
        return userobj
    elif create_if_not_exists:
        userobj.name = username
        return userobj
    else:
        return None


# =============================================================================
# Ancillary functions
# =============================================================================

def user_exists(username: str) -> bool:
    """Does the user exist?"""
    userobj = get_user_by_name(username, False)
    if userobj:
        return True
    return False


def create_superuser(username: str, password: str) -> bool:
    """Create a superuser."""
    user = get_user_by_name(username, False)
    if user:
        # already exists!
        return False
    user = get_user_by_name(username, True)  # now create

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

    user.set_password(password)
    user.save()
    audit("SUPERUSER CREATED: " + user.username, from_console=True)
    return True


def get_user(username: str,
             password: str,
             take_time_for_nonexistent_user: bool = True) -> Optional[User]:
    """Retrieve a User object from the supplied username, if the password is
    correct; otherwise, return None."""
    user = get_user_by_name(username, False)
    if user is None:
        if take_time_for_nonexistent_user:
            # If the user really existed, we'd be running a somewhat
            # time-consuming bcrypt operation. So that attackers can't
            # identify fake users easily based on timing, we consume some
            # time:
            take_some_time_mimicking_password_encryption()
        return None
    if not user.is_password_valid(password):
        return None
    return user


def get_username_from_id(user_id: int) -> Optional[str]:
    user = User(user_id)
    return user.username


def is_username_permissible(username: str) -> bool:
    """Is this a permissible username?"""
    return bool(re.match(VALID_USERNAME_REGEX, username))


# =============================================================================
# Support functions
# =============================================================================

def get_user_filter_dropdown(currently_selected_id: int = None) -> str:
    """Get HTML list of all known tablet devices."""
    s = """
        <select name="{}">
            <option value="">(all)</option>
    """.format(PARAM.USER)
    rows = pls.db.fetchall("SELECT id FROM {table}".format(
        table=User.TABLENAME))
    for pk in [row[0] for row in rows]:
        user = User(pk)
        s += """<option value="{pk}"{sel}>{name}</option>""".format(
            pk=pk,
            name=ws.webify(user.username),
            sel=ws.option_selected(currently_selected_id, pk),
        )
    s += """</select>"""
    return s


# =============================================================================
# User management
# =============================================================================

def get_url_edit_user(username: str) -> str:
    """URL to edit a specific user."""
    return (
        cc_html.get_generic_action_url(ACTION.EDIT_USER) +
        cc_html.get_url_field_value_pair(PARAM.USERNAME, username)
    )


def get_url_ask_delete_user(username: str) -> str:
    """URL to ask for confirmation to delete a specific user."""
    return (
        cc_html.get_generic_action_url(ACTION.ASK_DELETE_USER) +
        cc_html.get_url_field_value_pair(PARAM.USERNAME, username)
    )


def get_url_enable_user(username: str) -> str:
    """URL to enable a specific user."""
    return (
        cc_html.get_generic_action_url(ACTION.ENABLE_USER) +
        cc_html.get_url_field_value_pair(PARAM.USERNAME, username)
    )


def enter_new_password(session: SESSION_FWD_REF,
                       username: str,
                       as_manager: bool = False,
                       because_password_expired: bool = False) -> str:
    """HTML to change password."""
    if as_manager:
        changepw = """
            <label>
                <input type="checkbox" name="{PARAM.MUST_CHANGE_PASSWORD}"
                        value="1" checked>
                {LABEL.MUST_CHANGE_PASSWORD}
            </label><br>
        """.format(
            PARAM=PARAM,
            LABEL=LABEL,
        )
    else:
        changepw = ""
    return pls.WEBSTART + """
        {userdetails}
        {if_expired}
        <h1>Change password for {username}</h1>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.CHANGE_PASSWORD}">
            <input type="hidden" name="{PARAM.USERNAME}" value="{username}">
            {oldpw}
            New password:
            <input type="password" name="{PARAM.NEW_PASSWORD_1}">
            (minimum length {MINIMUM_PASSWORD_LENGTH} characters)<br>
            Re-enter new password:
            <input type="password" name="{PARAM.NEW_PASSWORD_2}"><br>
            {changepw}
            <input type="submit" value="Submit">
        </form>
    """.format(
        userdetails=session.get_current_user_html(),
        if_expired=("""
            <div class="important">
                Your password has expired and must be changed.
            </div>""" if because_password_expired else ""),
        username=username,
        ACTION=ACTION,
        script=pls.SCRIPT_NAME,
        oldpw="" if as_manager else """
            Old password: <input type="password" name="{}"><br>
        """.format(PARAM.OLD_PASSWORD),
        PARAM=PARAM,
        MINIMUM_PASSWORD_LENGTH=MINIMUM_PASSWORD_LENGTH,
        changepw=changepw,
    ) + WEBEND


def change_password(username: str,
                    form: cgi.FieldStorage,
                    as_manager: bool = False) -> str:
    """Change password, and return success/failure HTML."""
    user = get_user_by_name(username, False)
    if not user:
        return user_management_failure_message(
            "Problem: can't find user " + username, as_manager)
    old_password = ws.get_cgi_parameter_str(form, PARAM.OLD_PASSWORD)
    new_password_1 = ws.get_cgi_parameter_str(form, PARAM.NEW_PASSWORD_1)
    new_password_2 = ws.get_cgi_parameter_str(form, PARAM.NEW_PASSWORD_2)
    must_change_password = ws.get_cgi_parameter_bool(
        form, PARAM.MUST_CHANGE_PASSWORD)
    if new_password_1 != new_password_2:
        return user_management_failure_message("New passwords don't match",
                                               as_manager)
    if len(new_password_1) < MINIMUM_PASSWORD_LENGTH:
        return user_management_failure_message(
            "New password must be at least {} characters; not changed.".format(
                MINIMUM_PASSWORD_LENGTH
            ),
            as_manager
        )
    if old_password == new_password_1 and not as_manager:
        return user_management_failure_message(
            "Old/new passwords are the same",
            as_manager
        )
    if (not as_manager) and (not user.is_password_valid(old_password)):
        return user_management_failure_message("Old password incorrect",
                                               as_manager)

    # OK
    user.set_password(new_password_1)
    user.save()

    if not as_manager:
        must_change_password = False
    if must_change_password:
        user.force_password_change()

    audit("Password changed for user " + user.username)
    return user_management_success_message(
        "Password updated for user {}.".format(user.username),
        as_manager,
        """<div class="important">
            If you store your password in your CamCOPS tablet application,
            remember to change it there as well.
        </div>"""
    )


def set_password_directly(username: str, password: str) -> bool:
    """If the user exists, set its password. Returns Boolean success."""
    user = get_user_by_name(username, False)
    if not user:
        return False
    user.set_password(password)
    user.save()
    user.enable()
    audit("Password changed for user " + user.username, from_console=True)
    return True


def manage_users(session: SESSION_FWD_REF) -> str:
    """HTML to view/edit users."""
    allusers = pls.db.fetch_all_objects_from_db(User, User.TABLENAME,
                                                User.FIELDS, True)
    allusers = sorted(allusers, key=lambda k: k.username)
    output = pls.WEBSTART + """
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
        session.get_current_user_html(),
        cc_html.get_generic_action_url(ACTION.ASK_TO_ADD_USER),
    ) + WEBEND
    for u in allusers:
        if u.is_locked_out():
            enableuser = "| <a href={}>Re-enable user</a>".format(
                get_url_enable_user(u.username)
            )
            lockedmsg = "Yes, until {}".format(cc_dt.format_datetime(
                u.locked_out_until(),
                DATEFORMAT.ISO8601
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
            url_edit=get_url_edit_user(u.username),
            url_changepw=cc_html.get_url_enter_new_password(u.username),
            enableuser=enableuser,
            lockedmsg=lockedmsg,
            lastpwchange=ws.webify(u.last_password_change_utc),
            may_use_webviewer=cc_html.get_yes_no(u.may_use_webviewer),
            may_view_other_users_records=cc_html.get_yes_no(
                u.may_view_other_users_records),
            view_all_patients_when_unfiltered=cc_html.get_yes_no(
                u.view_all_patients_when_unfiltered),
            may_upload=cc_html.get_yes_no(u.may_upload),
            superuser=cc_html.get_yes_no(u.superuser),
            may_register_devices=cc_html.get_yes_no(u.may_register_devices),
            may_use_webstorage=cc_html.get_yes_no(u.may_use_webstorage),
            may_dump_data=cc_html.get_yes_no(u.may_dump_data),
            may_run_reports=cc_html.get_yes_no(u.may_run_reports),
            may_add_notes=cc_html.get_yes_no(u.may_add_notes),
            url_delete=get_url_ask_delete_user(u.username),
            username=u.username,
        )
    output += """
        </table>
    """ + WEBEND
    return output


def edit_user(session: SESSION_FWD_REF, username: str) -> str:
    """HTML form to edit a single user's permissions."""
    user = get_user_by_name(username, False)
    if not user:
        return user_management_failure_message("Invalid user: " + username)
    return pls.WEBSTART + """
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
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        username=user.username,
        PARAM=PARAM,
        ACTION=ACTION,
        LABEL=LABEL,
    ) + WEBEND


def change_user(form: cgi.FieldStorage) -> str:
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

    user = get_user_by_name(username, False)
    if not user:
        return user_management_failure_message("Invalid user: " + username)

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

    user.save()
    audit(
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
        "Details updated for user " + user.username)


def ask_to_add_user(session: SESSION_FWD_REF) -> str:
    """HTML form to add a user."""
    return pls.WEBSTART + """
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
        userdetails=session.get_current_user_html(),
        script=pls.SCRIPT_NAME,
        PARAM=PARAM,
        ACTION=ACTION,
        MINIMUM_PASSWORD_LENGTH=MINIMUM_PASSWORD_LENGTH,
    ) + WEBEND


def add_user(form: cgi.FieldStorage) -> str:
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

    user = get_user_by_name(username, False)
    if user:
        return user_management_failure_message(
            "User already exists: " + username)
    if not is_username_permissible(username):
        return user_management_failure_message(
            "Invalid username: " + ws.webify(username))
    if password_1 != password_2:
        return user_management_failure_message("Passwords don't mach")
    if len(password_1) < MINIMUM_PASSWORD_LENGTH:
        return user_management_failure_message(
            "Password must be at least {} characters".format(
                MINIMUM_PASSWORD_LENGTH
            ))

    user = get_user_by_name(username, True)  # create user
    user.set_password(password_1)

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

    user.save()
    if must_change_password:
        user.force_password_change()

    audit(
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
    return user_management_success_message("User " + user.username +
                                           " created")


def ask_delete_user(session: SESSION_FWD_REF, username: str) -> str:
    """HTML form to delete a user."""
    return pls.WEBSTART + """
        {userdetails}
        <h1>You are about to delete user {username}</h1>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.USERNAME}" value="{username}">
            <input type="hidden" name="{PARAM.ACTION}"
                value="{ACTION.DELETE_USER}">
            <input type="submit" value="Delete">
        </form>
    """.format(
        userdetails=session.get_current_user_html(),
        username=username,
        script=pls.SCRIPT_NAME,
        ACTION=ACTION,
        PARAM=PARAM,
    ) + WEBEND


def delete_user(username: str) -> str:
    """Delete a user, and return HTML success/failure message."""
    user = get_user_by_name(username, False)
    if not user:
        return user_management_failure_message("No such user: " + username)
    pls.db.delete_by_field(User.TABLENAME, "id", user.id)
    audit("User deleted: #{} ({})".format(user.id, user.username))
    return user_management_success_message("User " + user.username +
                                           " deleted")


def enable_user_webview(username: str) -> str:
    """Enable a user, and return HTML success/failure message."""
    user = get_user_by_name(username, False)
    if not user:
        return user_management_failure_message("No such user: " + username)
    user.enable()
    return user_management_success_message("User " + user.username +
                                           " enabled")


def user_management_success_message(msg: str,
                                    as_manager: bool = True,
                                    additional_html: str = "") -> str:
    """Generic success HTML for user management."""
    extra_html = ""
    if as_manager:
        extra_html = """
            <div>
                <a href={}>Return to user menu</a>
            </div>
        """.format(
            cc_html.get_generic_action_url(ACTION.MANAGE_USERS)
        )
    return cc_html.simple_success_message(msg, additional_html + extra_html)


def user_management_failure_message(msg: str, as_manager: bool = True) -> str:
    """Generic failure HTML for user management."""
    extra_html = ""
    if as_manager:
        extra_html = """
            <div>
                <a href={}>Return to user menu</a>
            </div>
        """.format(
            cc_html.get_generic_action_url(ACTION.MANAGE_USERS)
        )
    return cc_html.fail_with_error_stay_logged_in(msg, extra_html)


# =============================================================================
# Unit testing
# =============================================================================

def unit_tests() -> None:
    """Unit tests for cc_user module."""
    # -------------------------------------------------------------------------
    # Delayed imports (UNIT TESTING ONLY)
    # -------------------------------------------------------------------------
    from . import cc_session

    unit_test_ignore("", delete_old_account_lockouts)
    unit_test_ignore("", is_user_locked_out, "dummy_user")
    unit_test_ignore("", user_locked_out_until, "dummy_user")
    # skip: lock_user_out
    # skip: unlock_user
    # skip: record_login_failure
    # skip: act_on_login_failure
    # skip: clear_login_failures
    unit_test_ignore("", how_many_login_failures, "dummy_user")
    # skip: enable_user
    unit_test_ignore("", clear_login_failures_for_nonexistent_users)
    unit_test_ignore("", clear_dummy_login_failures_if_necessary)
    unit_test_ignore("", take_some_time_mimicking_password_encryption)

    user = User()
    user.username = "dummy_user"
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

    unit_test_ignore("", user_exists, "dummy_user")
    # skip: create_superuser
    unit_test_ignore("", get_user, "dummy_user", "dummy_password")
    unit_test_ignore("", is_username_permissible, "dummy_user")
    unit_test_ignore("", is_username_permissible, "dummy_user")

    session = cc_session.Session()
    # form = cgi.FieldStorage()

    unit_test_ignore("", enter_new_password, session, "dummy_user")
    # skip: change_password
    # skip: set_password_directly
    unit_test_ignore("", manage_users, session)
    unit_test_ignore("", edit_user, session, "dummy_user")
    # skip: change_user
    unit_test_ignore("", ask_to_add_user, session)
    # skip: add_user
    unit_test_ignore("", ask_delete_user, session, "dummy_user")
    # skip: delete_user
    unit_test_ignore("", user_management_success_message, "test_msg", True)
    unit_test_ignore("", user_management_success_message, "test_msg", False)
    unit_test_ignore("", user_management_failure_message, "test_msg", True)
    unit_test_ignore("", user_management_failure_message, "test_msg", False)
