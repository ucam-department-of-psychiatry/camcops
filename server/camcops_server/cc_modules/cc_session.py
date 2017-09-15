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

import datetime
import logging
from typing import Any, List, Optional, TYPE_CHECKING

from cardinal_pythonlib.reprfunc import simple_repr
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.randomness import create_base64encoded_randomness
from pendulum import Pendulum
from pyramid.interfaces import ISession
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Integer

# from .cc_analytics import send_analytics_if_necessary
from .cc_constants import DateFormat
from .cc_dt import format_datetime
from .cc_pyramid import CookieKey
from .cc_simpleobjects import IdNumDefinition
from .cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    FilterTextColType,
    IdNumDefinitionListColType,
    IPAddressColType,
    PatientNameColType,
    SessionTokenColType,
    SexColType,
    TableNameColType,
)
from .cc_sqlalchemy import Base
from .cc_unittest import unit_test_ignore
from .cc_user import (
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
    filter_dob = Column(
        "filter_dob", Date,
        comment="Task filter in use: DOB"
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
    filter_include_old_versions = Column(  # DEPRECATED
        "filter_include_old_versions", Boolean,
        comment="Task filter in use: allow old versions?"
    )
    filter_device_id = Column(
        "filter_device_id", Integer, ForeignKey("_security_devices.id"),
        comment="Task filter in use: source device ID"
    )
    filter_user_id = Column(
        "filter_user_id", Integer, ForeignKey("_security_users.id"),
        comment="Task filter in use: adding user ID"
    )
    filter_start_datetime = Column(
        "filter_start_datetime_iso8601", PendulumDateTimeAsIsoTextColType,
        comment="Task filter in use: start date/time (UTC as ISO8601)"
    )
    filter_end_datetime = Column(
        "filter_end_datetime_iso8601", PendulumDateTimeAsIsoTextColType,
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
    filter_idnums = Column(  # new in v2.0.1
        "filter_idnums", IdNumDefinitionListColType,
        comment="ID filters as JSON"
    )

    user = relationship("User", lazy="joined", foreign_keys=[user_id])
    filter_user = relationship("User", foreign_keys=[filter_user_id])
    filter_device = relationship("Device")

    def __repr__(self) -> str:
        return simple_repr(
            self,
            ["id", "token", "ip_address", "user_id", "last_activity_utc_iso"],
            with_addr=True
        )

    @property
    def last_activity_utc_iso(self) -> str:
        return format_datetime(self.last_activity_utc, DateFormat.ISO8601)

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
            req = ts.req
            session.logout(req)
            # Create a fresh session.
            session = cls.get_session(req=req, session_id_str=None,
                                      session_token=None)
            if ts.username:
                user = User.get_user_from_username_password(
                    req, ts.username, ts.password)
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
        now = req.now_utc

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
            cls, req: "CamcopsRequest") -> Pendulum:
        cfg = req.config
        now = req.now_utc
        oldest_last_activity_allowed = now - cfg.session_timeout
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
                 last_activity_utc: Pendulum = None):
        self.token = generate_token()
        self.ip_address = ip_addr
        self.last_activity_utc = last_activity_utc

    @property
    def username(self) -> Optional[str]:
        if self.user:
            return self.user.username
        return None

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
        # send_analytics_if_necessary(req)

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

    def user_may_view_all_patients_when_unfiltered(self) -> bool:
        """May the user view all patients when no filters are applied?"""
        if self.user is None:
            return False
        return self.user.view_all_patients_when_unfiltered
        # For superusers, this is a preference.

    # -------------------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------------------

    def get_idnum_filters(self) -> List[IdNumDefinition]:
        return self.filter_idnums or []

    def set_idnum_filters(self, idnum_filter: List[IdNumDefinition]) -> None:
        self.filter_idnums = idnum_filter

    # -------------------------------------------------------------------------
    # Clear filters
    # -------------------------------------------------------------------------

    def clear_filters(self) -> None:
        """Clear all filters."""
        self.filter_surname = None
        self.filter_forename = None
        self.filter_dob = None
        self.filter_sex = None
        self.filter_idnums = []  # type: List[IdNumDefinition]
        self.filter_task = None
        self.filter_complete = None
        self.filter_include_old_versions = None  # DEPRECATED
        self.filter_device_id = None
        self.filter_user_id = None
        self.filter_start_datetime = None
        self.filter_end_datetime = None
        self.filter_text = None


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests_session(s: CamcopsSession) -> None:
    """Unit tests for Session class."""
    ntasks = 75

    # skip: make_tables
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
