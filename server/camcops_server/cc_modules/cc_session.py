#!/usr/bin/env python
# camcops_server/cc_modules/cc_session.py

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
from typing import Optional, TYPE_CHECKING

from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.reprfunc import simple_repr
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.randomness import create_base64encoded_randomness
from pendulum import DateTime as Pendulum
from pyramid.interfaces import ISession
from sqlalchemy.orm import relationship, Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Integer

from .cc_constants import DateFormat
from .cc_pyramid import CookieKey
from .cc_sqla_coltypes import IPAddressColType, SessionTokenColType
from .cc_sqlalchemy import Base
from .cc_taskfilter import TaskFilter
from .cc_unittest import DemoDatabaseTestCase
from .cc_user import SecurityAccountLockout, SecurityLoginFailure, User

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest
    from .cc_tabletsession import TabletSession

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Debugging options
# =============================================================================

DEBUG_CAMCOPS_SESSION_CREATION = False

if DEBUG_CAMCOPS_SESSION_CREATION:
    log.warning("Debugging options enabled!")

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
        ForeignKey("_security_users.id", ondelete="CASCADE"),
        # http://docs.sqlalchemy.org/en/latest/core/constraints.html#on-update-and-on-delete  # noqa
        comment="User ID"
    )
    last_activity_utc = Column(
        "last_activity_utc", DateTime,
        comment="Date/time of last activity (UTC)"
    )
    number_to_view = Column(
        "number_to_view", Integer,
        comment="Number of records to view"
    )
    task_filter_id = Column(
        "task_filter_id", Integer,
        ForeignKey("_task_filters.id"),
        comment="Task filter ID"
    )

    user = relationship("User", lazy="joined", foreign_keys=[user_id])
    task_filter = relationship("TaskFilter", foreign_keys=[task_filter_id],
                               cascade="save-update, merge, delete")
    # ... "save-update, merge" is the default. We are adding "delete", which
    # means that when this CamcopsSession is deleted, the corresponding
    # TaskFilter will be deleted as well. See
    # http://docs.sqlalchemy.org/en/latest/orm/cascades.html#delete

    # -------------------------------------------------------------------------
    # Basic info
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return simple_repr(
            self,
            ["id", "token", "ip_address", "user_id", "last_activity_utc_iso",
             "user"],
            with_addr=True
        )

    @property
    def last_activity_utc_iso(self) -> str:
        return format_datetime(self.last_activity_utc, DateFormat.ISO8601)

    # -------------------------------------------------------------------------
    # Creating sessions
    # -------------------------------------------------------------------------

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

        def login_from_ts(cc: "CamcopsSession", ts_: "TabletSession") -> None:
            if DEBUG_CAMCOPS_SESSION_CREATION:
                log.debug("Considering login from tablet (with username: {!r}",
                          ts_.username)
            if ts_.username:
                user = User.get_user_from_username_password(
                    ts.req, ts.username, ts.password)
                if DEBUG_CAMCOPS_SESSION_CREATION:
                    log.debug("... looked up User: {!r}", user)
                if user:
                    # Successful login of sorts, ALTHOUGH the user may be
                    # severely restricted (if they can neither register nor
                    # upload). However, effecting a "login" here means that the
                    # error messages can become more helpful!
                    cc.login(user)
            if DEBUG_CAMCOPS_SESSION_CREATION:
                log.debug("... final session user: {!r}", cc.user)

        session = cls.get_session(req=ts.req,
                                  session_id_str=ts.session_id,
                                  session_token=ts.session_token)
        if not session.user:
            login_from_ts(session, ts)
        elif session.user and session.user.username != ts.username:
            # We found a session, and it's associated with a user, but with
            # the wrong user. This is unlikely to happen!
            # Wipe the old one:
            req = ts.req
            session.logout(req)
            # Create a fresh session.
            session = cls.get_session(req=req, session_id_str=None,
                                      session_token=None)
            login_from_ts(session, ts)
        return session

    @classmethod
    def get_session(cls,
                    req: "CamcopsRequest",
                    session_id_str: Optional[str],
                    session_token: Optional[str]) -> 'CamcopsSession':
        """
        Retrieves, or makes, a new CamcopsSession for this Pyramid Request,
        for a specific session_id and session_token.
        """
        if DEBUG_CAMCOPS_SESSION_CREATION:
            log.debug("CamcopsSession.get_session: session_id_str={!r}, "
                      "session_token={!r}", session_id_str, session_token)
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
            if DEBUG_CAMCOPS_SESSION_CREATION:
                if candidate is None:
                    log.debug("Session not found in database")
        else:
            if DEBUG_CAMCOPS_SESSION_CREATION:
                log.debug("Session ID and/or session token is missing.")
            candidate = None
        found = candidate is not None
        if found:
            candidate.last_activity_utc = now
            ccsession = candidate
        else:
            new_http_session = cls(ip_addr=ip_addr, last_activity_utc=now)
            dbsession.add(new_http_session)
            if DEBUG_CAMCOPS_SESSION_CREATION:
                log.debug("Creating new CamcopsSession: {!r}",
                          new_http_session)
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

    # -------------------------------------------------------------------------
    # User info and login/logout
    # -------------------------------------------------------------------------

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
        """
        Log in. Associates the user with the session and makes a new
        token.
        """
        if DEBUG_CAMCOPS_SESSION_CREATION:
            log.debug("Session {} login: username={!r}",
                      self.id, user.username)
        self.user = user  # will set our user_id FK
        self.token = generate_token()
        # fresh token: https://www.owasp.org/index.php/Session_fixation

    # -------------------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------------------

    def get_task_filter(self) -> TaskFilter:
        if not self.task_filter:
            dbsession = SqlASession.object_session(self)
            assert dbsession, (
                "CamcopsSession.get_task_filter() called on a CamcopsSession "
                "that's not yet in a session")
            self.task_filter = TaskFilter()
            dbsession.add(self.task_filter)
        return self.task_filter


# =============================================================================
# Unit tests
# =============================================================================

class SessionTests(DemoDatabaseTestCase):
    def test_sessions(self) -> None:
        self.announce("test_sessions")
        req = self.req
        dbsession = self.dbsession

        self.assertIsInstance(generate_token(), str)

        CamcopsSession.delete_old_sessions(req)
        self.assertIsInstance(
            CamcopsSession.get_oldest_last_activity_allowed(req), Pendulum)

        s = req.camcops_session
        u = self.dbsession.query(User).first()  # type: User
        assert u, "Missing user in demo database!"

        self.assertIsInstance(s.last_activity_utc_iso, str)
        self.assertIsInstanceOrNone(s.username, str)
        s.logout(req)
        s.login(u)
        self.assertIsInstance(s.get_task_filter(), TaskFilter)

        # Now test deletion cascade
        dbsession.commit()
        numfilters = dbsession.query(TaskFilter).count()
        assert numfilters == 1, "TaskFilter count should be 1"

        dbsession.delete(s)
        dbsession.commit()
        numfilters = dbsession.query(TaskFilter).count()
        assert numfilters == 0, (
            "TaskFilter count should be 0; cascade delete not working"
        )
