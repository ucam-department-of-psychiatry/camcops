#!/usr/bin/env python
# camcops_server/cc_modules/cc_session.py

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
import json
import logging
import math
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from cardinal_pythonlib.reprfunc import simple_repr
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.randomness import create_base64encoded_randomness
import cardinal_pythonlib.rnc_web as ws
from pyramid.interfaces import ISession
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer

from .cc_analytics import send_analytics_if_necessary
from .cc_constants import (
    ACTION,
    DATEFORMAT,
    PARAM,
)
from .cc_dt import format_datetime, get_datetime_from_string
from .cc_html import (
    get_html_sex_picker,
    get_html_which_idnum_picker,
    get_url_main_menu,
    get_yes_no_none,
)
from .cc_pyramid import CookieKey
from .cc_sqla_coltypes import (
    DateTimeAsIsoTextColType,
    FilterTextColType,
    IPAddressColType,
    PatientNameColType,
    SessionTokenColType,
    SexColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base
from .cc_task import get_task_filter_dropdown
from .cc_unittest import unit_test_ignore
from .cc_user import (
    get_user_filter_dropdown,
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest
    from .cc_tabletsession import TabletSession

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DEFAULT_NUMBER_OF_TASKS_TO_VIEW = 25


# =============================================================================
# Security for web sessions
# =============================================================================

def generate_token(num_bytes: int = 16) -> str:
    """
    Make a new session token that's not in use.
    It doesn't matter if it's already in use by a session with a different ID,
    because the ID/token pair is unique. (Removing that constraint gets rid of
    an in-principle-but-rare locking problem.)
    """
    # http://stackoverflow.com/questions/817882/unique-session-id-in-python
    return create_base64encoded_randomness(num_bytes)


# =============================================================================
# Session class
# =============================================================================

class CamcopsSession(Base):
    """
    Class representing an HTTPS session.
    """
    __tablename__ = "_security_webviewer_sessions"

    # no TEXT fields here; this is a performance-critical table
    id = Column(
        "id", Integer,
        primary_key=True, autoincrement=True, index=True,
        comment="Session ID (internal number for insertion speed)"
    )
    token = Column(
        "token", SessionTokenColType,
        comment="Token (base 64 encoded random number)"
    )
    ip_address = Column(
        "ip_address", IPAddressColType,
        comment="IP address of user"
    )
    user_id = Column(
        "user_id", Integer,
        ForeignKey("_security_users.id"),
        comment="User ID"
    )
    user = relationship("User", lazy="joined")
    last_activity_utc = Column(
        "last_activity_utc", DateTime,
        comment="Date/time of last activity (UTC)"
    )
    filter_surname = Column(
        "filter_surname", PatientNameColType,
        comment="Task filter in use: surname"
    )
    filter_forename = Column(
        "filter_forename", PatientNameColType,
        comment="Task filter in use: forename"
    )
    filter_dob_iso8601 = Column(
        "filter_dob_iso8601", DateTimeAsIsoTextColType,
        comment="Task filter in use: DOB"
        # *** Suboptimal: using a lengthy ISO field for a date only.
        # Could be just a Date?
    )
    filter_sex = Column(
        "filter_sex", SexColType,
        comment="Task filter in use: sex"
    )
    filter_task = Column(
        "filter_task", TableNameColType,
        comment="Task filter in use: task type"
    )
    filter_complete = Column(
        "filter_complete", Boolean,
        comment="Task filter in use: task complete?"
    )
    filter_include_old_versions = Column(
        "filter_include_old_versions", Boolean,
        comment="Task filter in use: allow old versions?"
    )
    filter_device_id = Column(
        "filter_device_id", Integer,
        comment="Task filter in use: source device ID"
    )
    filter_user_id = Column(
        "filter_user_id", Integer,
        comment="Task filter in use: adding user ID"
    )
    filter_start_datetime_iso8601 = Column(
        "filter_start_datetime_iso8601", DateTimeAsIsoTextColType,
        comment="Task filter in use: start date/time (UTC as ISO8601)"
    )
    filter_end_datetime_iso8601 = Column(
        "filter_end_datetime_iso8601", DateTimeAsIsoTextColType,
        comment="Task filter in use: end date/time (UTC as ISO8601)"
    )
    filter_text = Column(
        "filter_text", FilterTextColType,
        comment="Task filter in use: filter text fields"
    )
    number_to_view = Column(
        "number_to_view", Integer,
        comment="Number of records to view"
    )
    first_task_to_view = Column(
        "first_task_to_view", Integer,
        comment="First record number to view"
    )
    # filter_idnums_json = Column(  # new in v2.0.1
    #     "filter_idnums_json", Text,  # *** suboptimal! Text in high-speed table
    #     comment="ID filters as JSON"
    # )

    # *** DEFUNCT as of v2.0.1; NEED DELETING ONCE ALEMBIC RUNNING:
    filter_idnum1 = Column("filter_idnum1", Integer)
    filter_idnum2 = Column("filter_idnum2", Integer)
    filter_idnum3 = Column("filter_idnum3", Integer)
    filter_idnum4 = Column("filter_idnum4", Integer)
    filter_idnum5 = Column("filter_idnum5", Integer)
    filter_idnum6 = Column("filter_idnum6", Integer)
    filter_idnum7 = Column("filter_idnum7", Integer)
    filter_idnum8 = Column("filter_idnum8", Integer)

    def __repr__(self) -> str:
        return simple_repr(
            self,
            ["id", "token", "ip_address", "user_id", "last_activity_utc_iso"],
            with_addr=True
        )

    @property
    def last_activity_utc_iso(self) -> str:
        return format_datetime(self.last_activity_utc, DATEFORMAT.ISO8601)

    @classmethod
    def get_session_using_cookies(cls,
                                  req: "CamcopsRequest") -> "CamcopsSession":
        """
        Makes, or retrieves, a new CamcopsSession for this Pyramid Request.
        """
        pyramid_session = req.session  # type: ISession
        # noinspection PyArgumentList
        session_id_str = pyramid_session.get(CookieKey.SESSION_ID, '')
        # noinspection PyArgumentList
        session_token = pyramid_session.get(CookieKey.SESSION_TOKEN, '')
        return cls.get_session(req, session_id_str, session_token)

    @classmethod
    def get_session_for_tablet(cls, ts: "TabletSession") -> "CamcopsSession":
        session = cls.get_session(req=ts.req,
                                  session_id_str=ts.session_id,
                                  session_token=ts.session_token)
        if session.user and session.user.username != ts.username:
            # We found a session, and it's associated with a user, but with
            # the wrong user. This is unlikely to happen!
            # Wipe the old one:
            session.logout()
            # Create a fresh session.
            session = cls.get_session(req=ts.req, session_id_str=None,
                                      session_token=None)
            if ts.username:
                user = User.get_user_from_username_password(
                    ts.req, ts.username, ts.password)
                if user and user.may_login_as_tablet:
                    # Successful login.
                    session.login(user)

        return session

    @classmethod
    def get_session(cls,
                    req: "CamcopsRequest",
                    session_id_str: str,
                    session_token: str) -> 'CamcopsSession':
        """
        Retrieves, or makes, a new CamcopsSession for this Pyramid Request,
        for a specific session_id and session_token.
        """
        # ---------------------------------------------------------------------
        # Starting variables
        # ---------------------------------------------------------------------
        try:
            session_id = int(session_id_str)
        except (TypeError, ValueError):
            session_id = None
        dbsession = req.dbsession
        ip_addr = req.remote_addr
        now = req.now_utc_datetime

        # ---------------------------------------------------------------------
        # Fetch or create
        # ---------------------------------------------------------------------
        if session_id and session_token:
            oldest_last_activity_allowed = \
                cls.get_oldest_last_activity_allowed(req)
            candidate = dbsession.query(cls).\
                filter(cls.id == session_id).\
                filter(cls.token == session_token).\
                filter(cls.ip_address == ip_addr).\
                filter(cls.last_activity_utc >= oldest_last_activity_allowed).\
                first()  # type: Optional[CamcopsSession]
            if candidate is None:
                log.debug("Session not found in database")
        else:
            log.debug("Session ID and/or session token is missing.")
            candidate = None
        found = candidate is not None
        if found:
            candidate.last_activity_utc = now
            ccsession = candidate
        else:
            log.debug("Creating new CamcopsSession")
            new_http_session = cls(ip_addr=ip_addr, last_activity_utc=now)
            dbsession.add(new_http_session)
            # But we DO NOT FLUSH and we DO NOT SET THE COOKIES YET, because
            # we might hot-swap the session.
            # See complete_request_add_cookies().
            ccsession = new_http_session
        return ccsession

    @classmethod
    def get_oldest_last_activity_allowed(
            cls, req: "CamcopsRequest") -> datetime.datetime:
        cfg = req.config
        now = req.now_utc_datetime
        oldest_last_activity_allowed = now - cfg.SESSION_TIMEOUT
        return oldest_last_activity_allowed

    @classmethod
    def delete_old_sessions(cls, req: "CamcopsRequest") -> None:
        """Delete all expired sessions."""
        oldest_last_activity_allowed = \
            cls.get_oldest_last_activity_allowed(req)
        dbsession = req.dbsession
        log.info("Deleting expired sessions")
        dbsession.query(cls)\
            .filter(cls.last_activity_utc < oldest_last_activity_allowed)\
            .delete(synchronize_session=False)

    def __init__(self,
                 ip_addr: str = None,
                 last_activity_utc: datetime.datetime = None):
        self.token = generate_token()
        self.ip_address = ip_addr
        self.last_activity_utc = last_activity_utc

    @property
    def username(self) -> Optional[str]:
        if self.user:
            return self.user.username
        return None

    def __set_defaults(self) -> None:
        """
        Set some sensible default values.
        """
        self.number_to_view = DEFAULT_NUMBER_OF_TASKS_TO_VIEW
        self.first_task_to_view = 0

    def logout(self, req: "CamcopsRequest") -> None:
        """
        Log out, wiping session details. Also, perform periodic
        maintenance for the server, as this is a good time.
        """
        # First, the logout process.
        self.user_id = None
        self.token = ''  # so there's no way this token can be re-used

        # Secondly, some other things unrelated to logging out. Users will not
        # always log out manually. But sometimes they will. So we may as well
        # do some slow non-critical things:
        self.delete_old_sessions(req)
        SecurityAccountLockout.delete_old_account_lockouts(req)
        SecurityLoginFailure.clear_dummy_login_failures_if_necessary(req)
        send_analytics_if_necessary(req)

    def login(self, user: User) -> None:
        """Log in. Associates the user with the session and makes a new
        token."""
        log.debug("login: username = {}", user.username)
        self.user = user  # will set our user_id FK
        self.token = generate_token()
        # fresh token: https://www.owasp.org/index.php/Session_fixation

    def authorized_as_viewer(self) -> bool:
        """Is the user authorized as a viewer?"""
        if self.user is None:
            log.debug("not authorized as viewer: user is None")
            return False
        return self.user.may_use_webviewer or self.user.superuser

    def authorized_to_add_special_note(self) -> bool:
        """Is the user authorized to add special notes?"""
        if self.user is None:
            return False
        return self.user.may_add_notes or self.user.superuser

    def authorized_to_upload(self) -> bool:
        """Is the user authorized to upload from tablet devices?"""
        if self.user is None:
            return False
        return self.user.may_upload or self.user.superuser

    def authorized_for_webstorage(self) -> bool:
        """Is the user authorized to upload for web storage?"""
        if self.user is None:
            return False
        return self.user.may_use_webstorage or self.user.superuser

    def authorized_for_registration(self) -> bool:
        """Is the user authorized to register tablet devices??"""
        if self.user is None:
            return False
        return self.user.may_register_devices or self.user.superuser

    def user_must_change_password(self) -> bool:
        """Must the user change their password now?"""
        if self.user is None:
            return False
        return self.user.must_change_password

    def user_must_agree_terms(self) -> bool:
        """Must the user agree to the terms/conditions now?"""
        if self.user is None:
            return False
        return self.user.must_agree_terms()

    def agree_terms(self, req: "CamcopsRequest") -> None:
        """Marks the user as having agreed to the terms/conditions now."""
        if self.user is None:
            return
        self.user.agree_terms(req)

    def authorized_as_superuser(self) -> bool:
        """Is the user authorized as a superuser?"""
        if self.user is None:
            return False
        return self.user.superuser

    def authorized_to_dump(self) -> bool:
        """Is the user authorized to dump data?"""
        if self.user is None:
            return False
        return self.user.may_dump_data or self.user.superuser

    def authorized_for_reports(self) -> bool:
        """Is the user authorized to run reports?"""
        if self.user is None:
            return False
        return self.user.may_run_reports or self.user.superuser

    def restricted_to_viewing_user(self) -> Optional[str]:
        """If the user is restricted to viewing only their own records, returns
        the name of the user to which they're restricted. Otherwise, returns
        None."""
        if self.user is None:
            return None
        if self.user.may_view_other_users_records:
            return None
        if self.user.superuser:
            return None
        return self.user.id  # *** type bug?

    def user_may_view_all_patients_when_unfiltered(self) -> bool:
        """May the user view all patients when no filters are applied?"""
        if self.user is None:
            return False
        return self.user.view_all_patients_when_unfiltered
        # For superusers, this is a preference.

    def get_current_user_html(self,
                              req: "CamcopsRequest",
                              offer_main_menu: bool = True) -> str:
        """HTML showing current database/user, +/- link to main menu."""
        if self.username:
            user = "Logged in as <b>{}</b>.".format(ws.webify(self.username))
        else:
            user = ""
        cfg = req.config
        database = cfg.get_database_title_html()
        if offer_main_menu:
            menu = """ <a href="{}">Return to main menu</a>.""".format(
                get_url_main_menu(req))
        else:
            menu = ""
        if not user and not database and not menu:
            return ""
        return "<div>{} {}{}</div>".format(database, user, menu)

    # -------------------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------------------

    def get_idnum_filters(self) -> List[Tuple[int, int]]:  # which_idnum, idnum_value  # noqa
        if (not self.filter_idnums_json or
                not isinstance(self.filter_idnums_json, str)):
            # json.loads() requires a string
            return []
        restored = json.loads(self.filter_idnums_json)
        if not isinstance(restored, list):
            # garbage!
            return []
        final = []  # type: List[Tuple[int, int]]
        for pair in restored:
            if not isinstance(pair, list) or len(pair) != 2:
                # json.loads() will restore a tuple as a list of length 2
                return []
            final.append((pair[0], pair[1]))
        return final

    def set_idnum_filters(self, idnum_filter: List[Tuple[int, int]]) -> None:
        self.filter_idnums_json = json.dumps(idnum_filter)

    def any_patient_filtering(self) -> bool:
        """Is there some sort of patient filtering being applied?"""
        return (
            self.filter_surname is not None or
            self.filter_forename is not None or
            self.filter_dob_iso8601 is not None or
            self.filter_sex is not None or
            bool(self.get_idnum_filters())
        )

    def any_specific_patient_filtering(self) -> bool:
        """Are there filters that would restrict to one or a few patients?"""
        # differs from any_patient_filtering w.r.t. sex
        return (
            self.filter_surname is not None or
            self.filter_forename is not None or
            self.filter_dob_iso8601 is not None or
            bool(self.get_idnum_filters())
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

        id_filter_value = None
        id_filter_name = "ID number"
        for which_idnum, idnum_value in self.get_idnum_filters():
            if (idnum_value is not None and
                    which_idnum in pls.get_which_idnums()):
                id_filter_value = idnum_value
                id_filter_name = pls.get_id_desc(which_idnum)
        which_idnum_temp = """
                {picker}
                <input type="number" name="{PARAM.IDNUM_VALUE}">
        """.format(
            picker=get_html_which_idnum_picker(PARAM.WHICH_IDNUM),
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
            format_datetime(self.get_filter_dob(), DATEFORMAT.LONG_DATE),
            ACTION.CLEAR_FILTER_DOB,
            """<input type="date" name="{}">""".format(PARAM.DOB),
            ACTION.APPLY_FILTER_DOB,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Sex",
            self.filter_sex,
            ACTION.CLEAR_FILTER_SEX,
            get_html_sex_picker(param=PARAM.SEX,
                                selected=self.filter_sex,
                                offer_all=True),
            ACTION.APPLY_FILTER_SEX,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Task type",
            self.filter_task,
            ACTION.CLEAR_FILTER_TASK,
            get_task_filter_dropdown(self.filter_task),
            ACTION.APPLY_FILTER_TASK,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Task completed",
            get_yes_no_none(self.filter_complete),
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
            get_yes_no_none(self.filter_include_old_versions),
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
            get_username_from_id(self.filter_user_id),
            ACTION.CLEAR_FILTER_USER,
            get_user_filter_dropdown(self.filter_user_id),
            ACTION.APPLY_FILTER_USER,
            filters
        ) or found_one
        found_one = get_filter_html(
            "Start date (UTC)",
            format_datetime(self.get_filter_start_datetime(),
                            DATEFORMAT.LONG_DATE),
            ACTION.CLEAR_FILTER_START_DATETIME,
            """<input type="date" name="{}">""".format(PARAM.START_DATETIME),
            ACTION.APPLY_FILTER_START_DATETIME,
            filters
        ) or found_one
        found_one = get_filter_html(
            "End date (UTC)",
            format_datetime(self.get_filter_end_datetime(),
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
            self.filter_dob_iso8601 = format_datetime(
                dt, DATEFORMAT.ISO8601_DATE_ONLY)  # NB date only
        filter_sex = ws.get_cgi_parameter_str_or_none(form, PARAM.SEX)
        if filter_sex:
            self.filter_sex = filter_sex.upper()
        which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
        idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
        if (which_idnum and
                idnum_value is not None and
                which_idnum in pls.get_which_idnums()):
            self.set_idnum_filters([(which_idnum, idnum_value)])
            # Only filter on one ID at a time.
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
            self.filter_start_datetime_iso8601 = format_datetime(
                dt, DATEFORMAT.ISO8601)
        dt = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
        if dt:
            self.filter_end_datetime_iso8601 = format_datetime(
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
        self.filter_dob_iso8601 = format_datetime(
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
        which_idnum = ws.get_cgi_parameter_int(form, PARAM.WHICH_IDNUM)
        idnum_value = ws.get_cgi_parameter_int(form, PARAM.IDNUM_VALUE)
        if which_idnum in pls.get_which_idnums():
            self.set_idnum_filters([(which_idnum, idnum_value)])
        else:
            self.clear_filter_idnums()
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
        self.filter_start_datetime_iso8601 = format_datetime(
            dt, DATEFORMAT.ISO8601)
        self.reset_pagination()

    def apply_filter_end_datetime(self, form: cgi.FieldStorage) -> None:
        """Apply the end date filter."""
        dt = ws.get_cgi_parameter_datetime(form, PARAM.END_DATETIME)
        self.filter_end_datetime_iso8601 = format_datetime(
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
        self.clear_filter_idnums(reset_pagination=False)
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

    def clear_filter_idnums(self, reset_pagination: bool = True) -> None:
        """Clear all ID number filters."""
        self.set_idnum_filters([])
        if reset_pagination:
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
        return get_datetime_from_string(self.filter_dob_iso8601)

    def get_filter_start_datetime(self) -> Optional[datetime.datetime]:
        """Get start date filter as a datetime."""
        return get_datetime_from_string(
            self.filter_start_datetime_iso8601)

    def get_filter_end_datetime(self) -> Optional[datetime.datetime]:
        """Get end date filter as a datetime."""
        return get_datetime_from_string(self.filter_end_datetime_iso8601)

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
        npages = math.ceil(ntasks / self.number_to_view)  # type: int
        return npages

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

def unit_tests_session(s: CamcopsSession) -> None:
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


def ccsession_unit_tests(request: "CamcopsRequest") -> None:
    """Unit tests for cc_session module."""
    unit_test_ignore("", CamcopsSession.delete_old_sessions, request)
    unit_test_ignore("", generate_token)
    # skip: establish_session

    ccsession = request.camcops_session
    unit_tests_session(ccsession)
