#!/usr/bin/env python
# cc_session.py

"""
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
"""

import cgi
import http.cookies
import datetime
import math
from typing import Any, Dict, List, Optional

import cardinal_pythonlib.rnc_crypto as rnc_crypto
import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws

from . import cc_analytics
from .cc_constants import ACTION, DATEFORMAT, NUMBER_OF_IDNUMS, PARAM
from . import cc_db
# from . import cc_device
from . import cc_dt
from . import cc_html
from .cc_logger import log
from .cc_pls import pls
from .cc_unittest import unit_test_ignore
from . import cc_task
from . import cc_user

# =============================================================================
# Constants
# =============================================================================

DEFAULT_NUMBER_OF_TASKS_TO_VIEW = 25


# =============================================================================
# Security for web sessions
# =============================================================================

def delete_old_sessions() -> None:
    """Delete all expired sessions."""
    log.info("Deleting expired sessions")
    cutoff = pls.NOW_UTC_NO_TZ - pls.SESSION_TIMEOUT
    pls.db.db_exec("DELETE FROM " + Session.TABLENAME +
                   " WHERE last_activity_utc < ?", cutoff)


def is_token_in_use(token: str) -> bool:
    """Is the session token already present in the database?"""
    return pls.db.does_row_exist(Session.TABLENAME, "token", token)


def generate_token(num_bytes: int = 16) -> str:
    """Make a new session token that's not in use."""
    # http://stackoverflow.com/questions/817882/unique-session-id-in-python
    while True:
        token = rnc_crypto.create_base64encoded_randomness(num_bytes)
        if not is_token_in_use(token):
            return token
        # ... otherwise try another one
    # NB code not flawless (locking with other processes; no lock held) but
    # 2^(8*16) = 2^128 = 3.4e38 so the chances of a problem are small!


# =============================================================================
# Establishing sessions
# =============================================================================

def establish_session(env: Dict) -> None:
    """Look up details from the HTTP environment. Load existing session or
    create a new one. Session is then stored in pls.session (pls being
    process-local storage)."""
    log.debug("establish_session")
    # log.critical(repr(env))
    ip_address = env["REMOTE_ADDR"]
    try:
        # log.debug('HTTP_COOKIE: {}'.format(repr(env["HTTP_COOKIE"])))
        cookie = http.cookies.SimpleCookie(env["HTTP_COOKIE"])
        session_id = int(cookie["session_id"].value)
        session_token = cookie["session_token"].value
        log.debug("Found cookie token: ID {}, token {}".format(
            session_id, session_token))
    except (http.cookies.CookieError, KeyError):
        log.debug("No cookie yet. Creating new one.")
        session_id = None
        session_token = None
    pls.session = Session(session_id, session_token, ip_address)
    # Creates a new session if necessary


def establish_session_for_tablet(session_id: Optional[int],
                                 session_token: Optional[str],
                                 ip_address: str,
                                 username: str,
                                 password: str) -> None:
    """As for establish_session, but without using HTTP cookies.
    Resulting session is stored in pls.session."""
    if not session_id or not session_token:
        log.debug("No session yet for tablet. Creating new one.")
        session_id = None
        session_token = None
    pls.session = Session(session_id, session_token, ip_address)
    # Creates a new session if necessary
    if pls.session.userobject and pls.session.username != username:
        # We found a session, and it's associated with a user, but with
        # the wrong user. This is unlikely to happen!
        # Wipe the old one:
        pls.session.logout()
        # Create a fresh session.
        pls.session = Session(None, None, ip_address)
    if not pls.session.userobject and username:
        userobject = cc_user.get_user(username, password)  # checks password
        if userobject is not None and (userobject.may_upload or
                                       userobject.may_use_webstorage):
            # Successful login.
            pls.session.login(userobject)


# =============================================================================
# Session class
# =============================================================================

class Session:
    """Class representing HTTPS session."""
    TABLENAME = "_security_webviewer_sessions"
    FIELDSPECS = [
        # no TEXT fields here; this is a performance-critical table
        dict(name="id", cctype="INT_UNSIGNED", pk=True,
             autoincrement=True,
             comment="Session ID (internal number for insertion speed)"),
        dict(name="token", cctype="TOKEN",
             comment="Token (base 64 encoded random number)"),
        # ... not unique, for speed (slows down updates markedly)
        dict(name="user_id", cctype="INT_UNSIGNED",
             comment="User ID"),
        dict(name="ip_address", cctype="IPADDRESS",
             comment="IP address of user"),
        dict(name="last_activity_utc", cctype="DATETIME",
             comment="Date/time of last activity (UTC)"),
        dict(name="filter_surname", cctype="PATIENTNAME",
             comment="Task filter in use: surname"),
        dict(name="filter_forename", cctype="PATIENTNAME",
             comment="Task filter in use: forename"),
        dict(name="filter_dob_iso8601", cctype="ISO8601",
             comment="Task filter in use: DOB"),  # e.g. "2013-02-04"
        dict(name="filter_sex", cctype="SEX",
             comment="Task filter in use: sex"),
        dict(name="filter_task", cctype="TABLENAME",
             comment="Task filter in use: task type"),
        dict(name="filter_complete", cctype="BOOL",
             comment="Task filter in use: task complete?"),
        dict(name="filter_include_old_versions", cctype="BOOL",
             comment="Task filter in use: allow old versions?"),
        dict(name="filter_device_id", cctype="INT_UNSIGNED",
             comment="Task filter in use: source device ID"),
        dict(name="filter_user_id", cctype="INT_UNSIGNED",
             comment="Task filter in use: adding user ID"),
        dict(name="filter_start_datetime_iso8601", cctype="ISO8601",
             comment="Task filter in use: start date/time (UTC as ISO8601)"),
        dict(name="filter_end_datetime_iso8601", cctype="ISO8601",
             comment="Task filter in use: end date/time (UTC as ISO8601)"),
        dict(name="filter_text", cctype="FILTER_TEXT",
             comment="Task filter in use: filter text fields"),
        dict(name="number_to_view", cctype="INT_UNSIGNED",
             comment="Number of records to view"),
        dict(name="first_task_to_view", cctype="INT_UNSIGNED",
             comment="First record number to view"),
    ]
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        nstr = str(n)
        FIELDSPECS.append(
            dict(name="filter_idnum" + nstr,
                 cctype="INT_UNSIGNED",
                 comment="Task filter in use: ID#" + nstr + " number")
        )
    FIELDS = [x["name"] for x in FIELDSPECS]

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying tables."""
        cc_db.create_or_update_table(
            cls.TABLENAME, cls.FIELDSPECS,
            drop_superfluous_columns=drop_superfluous_columns)

    def __init__(self,
                 pk: int = None,
                 token: str = None,
                 ip_address: str = None) -> None:
        """Initialize. Fetch existing session from database, or create a new
        session. Perform security checks if retrieving an existing session."""
        # Fetch-or-create process. Fetching requires a PK and a matching token.
        pls.db.fetch_object_from_db_by_pk(self, Session.TABLENAME,
                                          Session.FIELDS, pk)
        expiry_if_before = pls.NOW_UTC_NO_TZ - pls.SESSION_TIMEOUT
        make_new_session = False
        if self.id is None:  # couldn't find one...
            log.debug("session id missing")
            make_new_session = True
        elif self.token is None:  # something went wrong...
            log.debug("no token")
            make_new_session = True
        elif self.token != token:  # token not what we were expecting
            log.debug(
                "token mismatch (existing = {}, incoming = {})".format(
                    self.token, token))
            make_new_session = True
        elif self.ip_address != ip_address:  # from wrong IP address
            log.debug(
                "IP address mismatch (existing = {}, incoming = {}".format(
                    self.ip_address, ip_address))
            make_new_session = True
        elif self.last_activity_utc < expiry_if_before:  # expired
            log.debug("session expired")
            make_new_session = True
        else:
            log.debug("session {} successfully loaded".format(pk))

        if make_new_session:
            # new one (meaning new not-logged-in one) for you!
            rnc_db.blank_object(self, Session.FIELDS)
            self.__set_defaults()
            self.token = generate_token()
            self.ip_address = ip_address
        self.save()  # assigns self.id if it was blank
        if make_new_session:  # after self.id has been set
            log.debug("Making new session. ID: {}. Token: {}".format(
                self.id, self.token))

        if self.user_id:
            self.userobject = cc_user.User(self.user_id)
            if self.userobject.id is not None:
                log.debug("found user: {}".format(self.username))
            else:
                log.debug("userobject had blank ID; wiping user")
                self.userobject = None
        else:
            log.debug("no user yet associated with this session")
            self.userobject = None

    @property
    def username(self) -> Optional[str]:
        if self.userobject:
            return self.userobject.username
        return None

    def __set_defaults(self) -> None:
        """Set some sensible default values."""
        self.number_to_view = DEFAULT_NUMBER_OF_TASKS_TO_VIEW
        self.first_task_to_view = 0

    def logout(self) -> None:
        """Log out, wiping session details. Also, perform periodic
        maintenance for the server, as this is a good time."""
        # First, the logout process.
        pk = self.id
        rnc_db.blank_object(self, Session.FIELDS)
        # ... wipes out any user details, plus the token, so there's no way
        # this token is being re-used
        self.id = pk
        self.save()

        # Secondly, some other things unrelated to logging out. Users will not
        # always log out manually. But sometimes they will. So we may as well
        # do some slow non-critical things:
        delete_old_sessions()
        cc_user.delete_old_account_lockouts()
        cc_user.clear_dummy_login_failures_if_necessary()
        cc_analytics.send_analytics_if_necessary()

    def save(self) -> None:
        """Save to database."""
        self.last_activity_utc = pls.NOW_UTC_NO_TZ
        if self.id is None:
            pls.db.insert_object_into_db_pk_unknown(self, Session.TABLENAME,
                                                    Session.FIELDS)
        else:
            pls.db.update_object_in_db(self, Session.TABLENAME, Session.FIELDS)

    def get_cookies(self):
        """Get list of cookies, each a tuple of ("Set-Cookie", datastring)."""
        # Use cookies for session security:
        # http://security.stackexchange.com/questions/9133
        cookie = http.cookies.SimpleCookie()
        # No expiration date, making it a session cookie
        cookie["session_id"] = self.id
        cookie["session_id"]["HttpOnly"] = True  # HTTP(S) only; no Javascript
        cookie["session_token"] = self.token
        cookie["session_token"]["HttpOnly"] = True  # HTTP(S) only; no JS; etc.
        if not pls.ALLOW_INSECURE_COOKIES:
            cookie["session_id"]["secure"] = True  # HTTPS only
            cookie["session_token"]["secure"] = True  # HTTPS only
        return [
            ("Set-Cookie", morsel.OutputString())
            for morsel in cookie.values()
        ]
        # http://stackoverflow.com/questions/14107260

    def login(self, userobject: cc_user.User) -> None:
        """Log in. Associates the user with the session and makes a new
        token."""
        log.debug("login: username = {}".format(userobject.username))
        self.user_id = userobject.id
        self.userobject = userobject
        self.token = generate_token()
        # fresh token: https://www.owasp.org/index.php/Session_fixation
        self.save()

    def authorized_as_viewer(self) -> bool:
        """Is the user authorized as a viewer?"""
        if self.userobject is None:
            log.debug("not authorized as viewer: userobject is None")
            return False
        return self.userobject.may_use_webviewer or self.userobject.superuser

    def authorized_to_add_special_note(self) -> bool:
        """Is the user authorized to add special notes?"""
        if self.userobject is None:
            return False
        return self.userobject.may_add_notes or self.userobject.superuser

    def authorized_to_upload(self) -> bool:
        """Is the user authorized to upload from tablet devices?"""
        if self.userobject is None:
            return False
        return self.userobject.may_upload or self.userobject.superuser

    def authorized_for_webstorage(self) -> bool:
        """Is the user authorized to upload for web storage?"""
        if self.userobject is None:
            return False
        return self.userobject.may_use_webstorage or self.userobject.superuser

    def authorized_for_registration(self) -> bool:
        """Is the user authorized to register tablet devices??"""
        if self.userobject is None:
            return False
        return (self.userobject.may_register_devices or
                self.userobject.superuser)

    def user_must_change_password(self) -> bool:
        """Must the user change their password now?"""
        if self.userobject is None:
            return False
        return self.userobject.must_change_password

    def user_must_agree_terms(self) -> bool:
        """Must the user agree to the terms/conditions now?"""
        if self.userobject is None:
            return False
        return self.userobject.must_agree_terms()

    def agree_terms(self) -> None:
        """Marks the user as having agreed to the terms/conditions now."""
        if self.userobject is None:
            return
        self.userobject.agree_terms()

    def authorized_as_superuser(self) -> bool:
        """Is the user authorized as a superuser?"""
        if self.userobject is None:
            return False
        return self.userobject.superuser

    def authorized_to_dump(self) -> bool:
        """Is the user authorized to dump data?"""
        if self.userobject is None:
            return False
        return self.userobject.may_dump_data or self.userobject.superuser

    def authorized_for_reports(self) -> bool:
        """Is the user authorized to run reports?"""
        if self.userobject is None:
            return False
        return self.userobject.may_run_reports or self.userobject.superuser

    def restricted_to_viewing_user(self) -> Optional[str]:
        """If the user is restricted to viewing only their own records, returns
        the name of the user to which they're restricted. Otherwise, returns
        None."""
        if self.userobject is None:
            return None
        if self.userobject.may_view_other_users_records:
            return None
        if self.userobject.superuser:
            return None
        return self.userobject.id

    def user_may_view_all_patients_when_unfiltered(self) -> bool:
        """May the user view all patients when no filters are applied?"""
        if self.userobject is None:
            return False
        return self.userobject.view_all_patients_when_unfiltered
        # For superusers, this is a preference.

    def get_current_user_html(self, offer_main_menu: bool = True) -> str:
        """HTML showing current database/user, +/- link to main menu."""
        if self.username:
            user = "Logged in as <b>{}</b>.".format(ws.webify(self.username))
        else:
            user = ""
        database = cc_html.get_database_title_string()
        if offer_main_menu:
            menu = """ <a href="{}">Return to main menu</a>.""".format(
                cc_html.get_url_main_menu())
        else:
            menu = ""
        if not user and not database and not menu:
            return ""
        return "<div>{} {}{}</div>".format(database, user, menu)

    # -------------------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------------------

    def any_patient_filtering(self) -> bool:
        """Is there some sort of patient filtering being applied?"""
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            if getattr(self, "filter_idnum" + str(n)) is not None:
                return True
        return (
            self.filter_surname is not None or
            self.filter_forename is not None or
            self.filter_dob_iso8601 is not None or
            self.filter_sex is not None
        )

    def any_specific_patient_filtering(self) -> bool:
        """Are there filters that would restrict to one or a few patients?"""
        # differs from any_patient_filtering w.r.t. sex
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            if getattr(self, "filter_idnum" + str(n)) is not None:
                return True
        return (
            self.filter_surname is not None or
            self.filter_forename is not None or
            self.filter_dob_iso8601 is not None
        )

    def get_current_filter_html(self) -> str:
        """HTML showing current filters and offering ways to set them."""
        # Consider also multiple buttons in a single form:
        # http://stackoverflow.com/questions/942772
        # ... might allow "apply all things entered here" button
        # ... HOWEVER, I think this would break the ability to press Enter
        # after entering information in any box (which is nice).
        found_one = False
        filters = []
        id_filter_values = []
        id_filter_descs = []
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            nstr = str(n)
            id_filter_values.append(getattr(self, "filter_idnum" + nstr))
            id_filter_descs.append(pls.get_id_desc(n))
        id_filter_value = None
        id_filter_name = "ID number"
        for index, value in enumerate(id_filter_values):
            if value is not None:
                id_filter_value = value
                id_filter_name = id_filter_descs[index]
        which_idnum_temp = """
                {picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}">
        """.format(
            picker=cc_html.get_html_which_idnum_picker(PARAM.WHICH_IDNUM),
            PARAM=PARAM,
        )
        found_one = get_filter_html(
            id_filter_name,
            id_filter_value,
            ACTION.CLEAR_FILTER_IDNUMS,
            which_idnum_temp,
            ACTION.APPLY_FILTER_IDNUMS,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Surname",
            self.filter_surname,
            ACTION.CLEAR_FILTER_SURNAME,
            """<input type="text" name="{}">""".format(PARAM.SURNAME),
            ACTION.APPLY_FILTER_SURNAME,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Forename",
            self.filter_forename,
            ACTION.CLEAR_FILTER_FORENAME,
            """<input type="text" name="{}">""".format(PARAM.FORENAME),
            ACTION.APPLY_FILTER_FORENAME,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Date of birth",
            cc_dt.format_datetime(self.get_filter_dob(), DATEFORMAT.LONG_DATE),
            ACTION.CLEAR_FILTER_DOB,
            """<input type="date" name="{}">""".format(PARAM.DOB),
            ACTION.APPLY_FILTER_DOB,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Sex",
            self.filter_sex,
            ACTION.CLEAR_FILTER_SEX,
            cc_html.get_html_sex_picker(param=PARAM.SEX,
                                        selected=self.filter_sex,
                                        offer_all=True),
            ACTION.APPLY_FILTER_SEX,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Task type",
            self.filter_task,
            ACTION.CLEAR_FILTER_TASK,
            cc_task.get_task_filter_dropdown(self.filter_task),
            ACTION.APPLY_FILTER_TASK,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Task completed",
            cc_html.get_yes_no_none(self.filter_complete),
            ACTION.CLEAR_FILTER_COMPLETE,
            """
                <select name="{PARAM.COMPLETE}">
                    <option value="">(all)</option>
                    <option value="1"{selected_1}>Complete</option>
                    <option value="0"{selected_0}>Incomplete</option>
                </select>
            """.format(PARAM=PARAM,
                       selected_1=ws.option_selected(self.filter_complete, 1),
                       selected_0=ws.option_selected(self.filter_complete, 0)),
            ACTION.APPLY_FILTER_COMPLETE,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Include old (overwritten) versions",
            cc_html.get_yes_no_none(self.filter_include_old_versions),
            ACTION.CLEAR_FILTER_INCLUDE_OLD_VERSIONS,
            """
                <select name="{PARAM.INCLUDE_OLD_VERSIONS}">
                    <option value="">(exclude)</option>
                    <option value="1"{y}>Include</option>
                    <option value="0"{n}>Exclude</option>
                </select>
            """.format(PARAM=PARAM,
                       y=ws.option_selected(self.filter_include_old_versions,
                                            1),
                       n=ws.option_selected(self.filter_include_old_versions,
                                            0)),
            ACTION.APPLY_FILTER_INCLUDE_OLD_VERSIONS,
            filters
        ) or found_one
        # found_one = get_filter_html(
        #     "Tablet device",
        #     self.filter_device_id,
        #     ACTION.CLEAR_FILTER_DEVICE,
        #     cc_device.get_device_filter_dropdown(self.filter_device_id),
        #     ACTION.APPLY_FILTER_DEVICE,
        #     filters
        # ) or found_one
        found_one = get_filter_html(
            "Adding user",
            cc_user.get_username_from_id(self.filter_user_id),
            ACTION.CLEAR_FILTER_USER,
            cc_user.get_user_filter_dropdown(self.filter_user_id),
            ACTION.APPLY_FILTER_USER,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Start date (UTC)",
            cc_dt.format_datetime(self.get_filter_start_datetime(),
                                  DATEFORMAT.LONG_DATE),
            ACTION.CLEAR_FILTER_START_DATETIME,
            """<input type="date" name="{}">""".format(PARAM.START_DATETIME),
            ACTION.APPLY_FILTER_START_DATETIME,
            filters
        ) or found_one
        found_one = get_filter_html(
            "End date (UTC)",
            cc_dt.format_datetime(self.get_filter_end_datetime(),
                                  DATEFORMAT.LONG_DATE),
            ACTION.CLEAR_FILTER_END_DATETIME,
            """<input type="date" name="{}">""".format(PARAM.END_DATETIME),
            ACTION.APPLY_FILTER_END_DATETIME,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Text contents",
            ws.webify(self.filter_text),
            ACTION.CLEAR_FILTER_TEXT,
            """<input type="text" name="{}">""".format(PARAM.TEXT),
            ACTION.APPLY_FILTER_TEXT,
            filters
        ) or found_one

        clear_filter_html = """
                <input type="submit" name="{ACTION.CLEAR_FILTERS}"
                        value="Clear all filters">
                <br>
        """.format(
            ACTION=ACTION,
        )
        no_filters_applied = "<p><b><i>No filters applied</i></b></p>"
        html = """
            <form class="filter" method="POST" action="{script}">

                <input type="hidden" name="{PARAM.ACTION}"
                        value="{ACTION.FILTER}">

                <input type="submit" class="important"
                        name="{ACTION.APPLY_FILTERS}"
                        value="Apply new filters">
                <br>
                <!-- First submit button is default on pressing Enter,
                which is why the Apply button is at the top of the form -->

                {clearbutton}

                {filters}
            </form>
        """.format(
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
            clearbutton=clear_filter_html if found_one else no_filters_applied,
            filters="".join(filters),
        )
        return html

    # -------------------------------------------------------------------------
    # Apply filters
    # -------------------------------------------------------------------------

    def apply_filters(self, form: cgi.FieldStorage) -> None:
        """Apply filters from details in the CGI form."""
        filter_surname = ws.get_cgi_parameter_str_or_none(form, PARAM.SURNAME)
        if filter_surname:
            self.filter_surname = filter_surname.upper()
        filter_forename = ws.get_cgi_parameter_str_or_none(form,
                                                           PARAM.FORENAME)
        if filter_forename:
            self.filter_forename = filter_forename.upper()
        dt = ws.get_cgi_parameter_datetime(form, PARAM.DOB)
        if dt:
            self.filter_dob_iso8601 = cc_dt.format_datetime(
                dt, DATEFORMAT.ISO8601_DATE_ONLY)  # NB date only
        filter_sex = ws.get_cgi_parameter_str_or_none(form, PARAM.SEX)
        if filter_sex:
            self.filter_sex = filter_sex.upper()
        which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
        idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
        if (which_idnum and
                idnum_value is not None and
                1 <= which_idnum <= NUMBER_OF_IDNUMS):
            self.clear_filter_idnums()  # Only filter on one ID at a time.
            setattr(self, "filter_idnum" + str(which_idnum), idnum_value)
        filter_task = ws.get_cgi_parameter_str_or_none(form, PARAM.TASK)
        if filter_task:
            self.filter_task = filter_task
        filter_complete = ws.get_cgi_parameter_bool_or_none(form,
                                                            PARAM.COMPLETE)
        if filter_complete is not None:
            self.filter_complete = filter_complete
        filter_include_old_versions = ws.get_cgi_parameter_bool_or_none(
            form, PARAM.INCLUDE_OLD_VERSIONS)
        if filter_include_old_versions is not None:
            self.filter_include_old_versions = filter_include_old_versions
        filter_device_id = ws.get_cgi_parameter_int(form, PARAM.DEVICE)
        if filter_device_id is not None:
            self.filter_device_id = filter_device_id
        filter_user_id = ws.get_cgi_parameter_int(form, PARAM.USER)
        if filter_user_id:
            self.filter_user_id = filter_user_id
        dt = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
        if dt:
            self.filter_start_datetime_iso8601 = cc_dt.format_datetime(
                dt, DATEFORMAT.ISO8601)
        dt = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
        if dt:
            self.filter_end_datetime_iso8601 = cc_dt.format_datetime(
                dt, DATEFORMAT.ISO8601)
        filter_text = ws.get_cgi_parameter_str_or_none(form, PARAM.TEXT)
        if filter_text:
            self.filter_text = filter_text
        self.reset_pagination()

    def apply_filter_surname(self, form: cgi.FieldStorage) -> None:
        """Apply the surname filter."""
        self.filter_surname = ws.get_cgi_parameter_str_or_none(form,
                                                               PARAM.SURNAME)
        if self.filter_surname:
            self.filter_surname = self.filter_surname.upper()
        self.reset_pagination()

    def apply_filter_forename(self, form: cgi.FieldStorage) -> None:
        """Apply the forename filter."""
        self.filter_forename = ws.get_cgi_parameter_str_or_none(form,
                                                                PARAM.FORENAME)
        if self.filter_forename:
            self.filter_forename = self.filter_forename.upper()
        self.reset_pagination()

    def apply_filter_dob(self, form: cgi.FieldStorage) -> None:
        """Apply the DOB filter."""
        dt = ws.get_cgi_parameter_datetime(form, PARAM.DOB)
        self.filter_dob_iso8601 = cc_dt.format_datetime(
            dt, DATEFORMAT.ISO8601_DATE_ONLY)  # NB date only
        self.reset_pagination()

    def apply_filter_sex(self, form: cgi.FieldStorage) -> None:
        """Apply the sex filter."""
        self.filter_sex = ws.get_cgi_parameter_str_or_none(form, PARAM.SEX)
        if self.filter_sex:
            self.filter_sex = self.filter_sex.upper()
        self.reset_pagination()

    def apply_filter_idnums(self, form: cgi.FieldStorage) -> None:
        """Apply the ID number filter. Only one ID number filter at a time."""
        self.clear_filter_idnums()  # Only filter on one ID at a time.
        which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
        idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
        if 1 <= which_idnum <= NUMBER_OF_IDNUMS:
            setattr(self, "filter_idnum" + str(which_idnum), idnum_value)
            self.reset_pagination()

    def apply_filter_task(self, form: cgi.FieldStorage) -> None:
        """Apply the task filter."""
        self.filter_task = ws.get_cgi_parameter_str_or_none(form, PARAM.TASK)
        self.reset_pagination()

    def apply_filter_complete(self, form: cgi.FieldStorage) -> None:
        """Apply the "complete Y/N" filter."""
        self.filter_complete = ws.get_cgi_parameter_bool_or_none(
            form, PARAM.COMPLETE)
        self.reset_pagination()

    def apply_filter_include_old_versions(self, form: cgi.FieldStorage) -> None:
        """Apply "allow old versions" unusual filter."""
        self.filter_include_old_versions = ws.get_cgi_parameter_bool_or_none(
            form, PARAM.INCLUDE_OLD_VERSIONS)
        self.reset_pagination()

    def apply_filter_device(self, form: cgi.FieldStorage) -> None:
        """Apply the device filter."""
        self.filter_device_id = ws.get_cgi_parameter_int(form, PARAM.DEVICE)
        self.reset_pagination()

    def apply_filter_user(self, form: cgi.FieldStorage) -> None:
        """Apply the uploading user filter."""
        self.filter_user_id = ws.get_cgi_parameter_int(form, PARAM.USER)
        self.reset_pagination()

    def apply_filter_start_datetime(self, form: cgi.FieldStorage) -> None:
        """Apply the start date filter."""
        dt = ws.get_cgi_parameter_datetime(form, PARAM.START_DATETIME)
        self.filter_start_datetime_iso8601 = cc_dt.format_datetime(
            dt, DATEFORMAT.ISO8601)
        self.reset_pagination()

    def apply_filter_end_datetime(self, form: cgi.FieldStorage) -> None:
        """Apply the end date filter."""
        dt = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
        self.filter_end_datetime_iso8601 = cc_dt.format_datetime(
            dt, DATEFORMAT.ISO8601)
        self.reset_pagination()

    def apply_filter_text(self, form: cgi.FieldStorage) -> None:
        """Apply the text contents filter."""
        self.filter_text = ws.get_cgi_parameter_str_or_none(form, "text")
        self.reset_pagination()

    # -------------------------------------------------------------------------
    # Clear filters
    # -------------------------------------------------------------------------

    def clear_filters(self) -> None:
        """Clear all filters."""
        self.filter_surname = None
        self.filter_forename = None
        self.filter_dob_iso8601 = None
        self.filter_sex = None
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            setattr(self, "filter_idnum" + str(n), None)
        self.filter_task = None
        self.filter_complete = None
        self.filter_include_old_versions = None
        self.filter_device_id = None
        self.filter_user_id = None
        self.filter_start_datetime_iso8601 = None
        self.filter_end_datetime_iso8601 = None
        self.filter_text = None
        self.reset_pagination()

    def clear_filter_surname(self) -> None:
        """Clear surname filter."""
        self.filter_surname = None
        self.reset_pagination()

    def clear_filter_forename(self) -> None:
        """Clear forename filter."""
        self.filter_forename = None
        self.reset_pagination()

    def clear_filter_dob(self) -> None:
        """Clear DOB filter."""
        self.filter_dob_iso8601 = None
        self.reset_pagination()

    def clear_filter_sex(self) -> None:
        """Clear sex filter."""
        self.filter_sex = None
        self.reset_pagination()

    def clear_filter_idnums(self) -> None:
        """Clear all ID number filters."""
        for n in range(1, NUMBER_OF_IDNUMS + 1):
            setattr(self, "filter_idnum" + str(n), None)
        self.reset_pagination()

    def clear_filter_task(self) -> None:
        """Clear task filter."""
        self.filter_task = None
        self.reset_pagination()

    def clear_filter_complete(self) -> None:
        """Clear "complete Y/N" filter."""
        self.filter_complete = None
        self.reset_pagination()

    def clear_filter_include_old_versions(self) -> None:
        """Clear "allow old versions" unusual filter."""
        self.filter_include_old_versions = None
        self.reset_pagination()

    def clear_filter_device(self) -> None:
        """Clear device filter."""
        self.filter_device_id = None
        self.reset_pagination()

    def clear_filter_user(self) -> None:
        """Clear uploading user filter."""
        self.filter_user_id = None
        self.reset_pagination()

    def clear_filter_start_datetime(self) -> None:
        """Clear start date filter."""
        self.filter_start_datetime_iso8601 = None
        self.reset_pagination()

    def clear_filter_end_datetime(self) -> None:
        """Clear end date filter."""
        self.filter_end_datetime_iso8601 = None
        self.reset_pagination()

    def clear_filter_text(self) -> None:
        """Clear text contents filter."""
        self.filter_text = None
        self.reset_pagination()

    # -------------------------------------------------------------------------
    # Additional for date/time filters
    # -------------------------------------------------------------------------

    def get_filter_dob(self) -> Optional[datetime.datetime]:
        """Get filtering DOB as a datetime."""
        return cc_dt.get_datetime_from_string(self.filter_dob_iso8601)

    def get_filter_start_datetime(self) -> Optional[datetime.datetime]:
        """Get start date filter as a datetime."""
        return cc_dt.get_datetime_from_string(
            self.filter_start_datetime_iso8601)

    def get_filter_end_datetime(self) -> Optional[datetime.datetime]:
        """Get end date filter as a datetime."""
        return cc_dt.get_datetime_from_string(self.filter_end_datetime_iso8601)

    def get_filter_end_datetime_corrected_1day(self) \
            -> Optional[datetime.datetime]:
        """When we say "From Monday to Tuesday", we mean "including all of
        Tuesday", i.e. up to the start of Wednesday."""
        # End date will be midnight at the START of the day;
        # we want 24h later.
        end_datetime = self.get_filter_end_datetime()
        if end_datetime is not None:
            end_datetime = end_datetime + datetime.timedelta(days=1)
        return end_datetime

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def get_first_task_to_view(self) -> int:
        """Task number to start the page with."""
        if self.first_task_to_view is None:
            return 0
        return self.first_task_to_view

    def get_last_task_to_view(self, ntasks: int) -> int:
        """Task number to end the page with."""
        if self.number_to_view is None:
            return ntasks
        return min(ntasks, self.get_first_task_to_view() + self.number_to_view)

    def get_npages(self, ntasks: int) -> int:
        """Number of pages."""
        if not ntasks or not self.number_to_view:
            return 1
        return math.ceil(ntasks / self.number_to_view)

    def get_current_page(self) -> int:
        """Current page we're on."""
        if not self.number_to_view:
            return 1
        return (self.get_first_task_to_view() // self.number_to_view) + 1

    def change_number_to_view(self, form: cgi.FieldStorage) -> None:
        """Set how many tasks to view per page (from CGI form)."""
        self.number_to_view = ws.get_cgi_parameter_int(form,
                                                       PARAM.NUMBER_TO_VIEW)
        self.reset_pagination()

    def get_number_to_view_selector(self) -> str:
        """HTML form to choose how many tasks to view."""
        options = [5, 25, 50, 100]
        html = """
            <form class="filter" method="POST" action="{script}">
                <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.CHANGE_NUMBER_TO_VIEW}">
                <select name="{PARAM.NUMBER_TO_VIEW}">
                    <option value="">all</option>
        """.format(
            script=pls.SCRIPT_NAME,
            ACTION=ACTION,
            PARAM=PARAM,
        )
        for n in options:
            html += """
                    <option{selected} value="{n}">{n}</option>
            """.format(
                selected=ws.option_selected(self.number_to_view, n),
                n=n,
            )
        html += """
                </select>
                <input type="submit" value="Submit">
            </form>
        """
        return html

    def reset_pagination(self) -> None:
        """Return to first page. Use whenever page length changes."""
        self.first_task_to_view = 0
        self.save()

    def first_page(self) -> None:
        """Go to first page."""
        self.reset_pagination()

    def previous_page(self) -> None:
        """Go to previous page."""
        if self.number_to_view:
            self.first_task_to_view = max(
                0,
                self.first_task_to_view - self.number_to_view)
            self.save()

    def next_page(self, ntasks: int) -> None:
        """Go to next page."""
        if self.number_to_view:
            self.first_task_to_view = min(
                (self.get_npages(ntasks) - 1) * self.number_to_view,
                self.first_task_to_view + self.number_to_view
            )
            self.save()

    def last_page(self, ntasks: int) -> None:
        """Go to last page."""
        if self.number_to_view and ntasks:
            self.first_task_to_view = (
                (self.get_npages(ntasks) - 1) * self.number_to_view
            )
            self.save()


# =============================================================================
# More on filters
# =============================================================================

# noinspection PyUnusedLocal
def get_filter_html(filter_name: str,
                    filter_value: Any,
                    clear_action: str,
                    apply_field_html: str,
                    apply_action: str,
                    filter_list: List[str]) -> bool:
    """HTML to view or change a filter."""
    # returns: found a filter?
    no_filter_value = (
        filter_value is None or (isinstance(filter_value, str) and
                                 not filter_value)
    )
    if no_filter_value:
        filter_list.append("""
                    {filter_name}: {apply_field_html}
                    <br>
        """.format(
            filter_name=filter_name,
            apply_field_html=apply_field_html,
            # apply_action=apply_action,
        ))
        #            <input type="submit" name="{apply_action}" value="Filter">
        return False
    else:
        filter_list.append("""
                    {filter_name}: <b>{filter_value}</b>
                    <input type="submit" name="{clear_action}" value="Clear">
                    {apply_field_html}
                    <br>
        """.format(
            filter_name=filter_name,
            filter_value=ws.webify(filter_value),
            clear_action=clear_action,
            apply_field_html=apply_field_html,
            # apply_action=apply_action
        ))
        #            <input type="submit" name="{apply_action}" value="Filter">
        return True


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_session(s: Session) -> None:
    """Unit tests for Session class."""
    ntasks = 75

    # skip: make_tables
    # __set_defaults: not visible to outside world
    # skip: logout
    # skip: save
    unit_test_ignore("", s.get_cookies)
    # skip: login
    unit_test_ignore("", s.authorized_as_viewer)
    unit_test_ignore("", s.authorized_to_add_special_note)
    unit_test_ignore("", s.user_must_change_password)
    unit_test_ignore("", s.user_must_agree_terms)
    # skip: agree_terms
    unit_test_ignore("", s.authorized_as_superuser)
    unit_test_ignore("", s.authorized_to_dump)
    unit_test_ignore("", s.authorized_for_reports)
    unit_test_ignore("", s.restricted_to_viewing_user)
    unit_test_ignore("", s.user_may_view_all_patients_when_unfiltered)
    unit_test_ignore("", s.get_current_user_html, True)
    unit_test_ignore("", s.get_current_user_html, False)
    unit_test_ignore("", s.any_patient_filtering)
    unit_test_ignore("", s.any_specific_patient_filtering)
    unit_test_ignore("", s.get_current_filter_html)
    # skip: apply_filters
    # skip: apply_filter_surname
    # skip: apply_filter_forename
    # skip: apply_filter_dob
    # skip: apply_filter_sex
    # skip: apply_filter_idnums
    # skip: apply_filter_task
    # skip: apply_filter_complete
    # skip: apply_filter_include_old_versions
    # skip: apply_filter_device
    # skip: apply_filter_user
    # skip: apply_filter_start_datetime
    # skip: apply_filter_end_datetime
    # skip: apply_filter_text
    # skip: clear_filters
    # skip: clear_filter_surname
    # skip: clear_filter_forename
    # skip: clear_filter_dob
    # skip: clear_filter_sex
    # skip: clear_filter_idnums
    # skip: clear_filter_task
    # skip: clear_filter_complete
    # skip: clear_filter_include_old_versions
    # skip: clear_filter_device
    # skip: clear_filter_user
    # skip: clear_filter_start_datetime
    # skip: clear_filter_end_datetime
    # skip: clear_filter_text
    unit_test_ignore("", s.get_filter_dob)
    unit_test_ignore("", s.get_filter_start_datetime)
    unit_test_ignore("", s.get_filter_end_datetime)
    unit_test_ignore("", s.get_filter_end_datetime_corrected_1day)
    unit_test_ignore("", s.get_first_task_to_view)
    unit_test_ignore("", s.get_last_task_to_view, ntasks)
    unit_test_ignore("", s.get_npages, ntasks)
    unit_test_ignore("", s.get_current_page)
    # skip: change_number_to_view
    unit_test_ignore("", s.get_number_to_view_selector)
    # skip: reset_pagination
    # skip: first_page
    # skip: previous_page
    # skip: next_page
    # skip: last_page

    # get_filter_html: tested implicitly


def unit_tests() -> None:
    """Unit tests for cc_session module."""
    unit_test_ignore("", delete_old_sessions)
    unit_test_ignore("", is_token_in_use, "dummytoken")
    unit_test_ignore("", generate_token)
    # skip: establish_session

    current_pks = pls.db.fetchallfirstvalues(
        "SELECT id FROM {}".format(Session.TABLENAME)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        s = Session(pk)
        unit_tests_session(s)
