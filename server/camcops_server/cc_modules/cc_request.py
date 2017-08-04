#!/usr/bin/env python
# camcops_server/cc_modules/cc_request.py

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

import logging
from typing import TYPE_CHECKING

import arrow
from arrow import Arrow
import datetime
from pyramid.decorator import reify
from pyramid.request import Request
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession

from .cc_config import CamcopsConfig, get_config, get_config_filename
from .cc_constants import (
    CAMCOPS_LOGO_FILE_WEBREF,
    DATEFORMAT,
    LOCAL_LOGO_FILE_WEBREF,
    WEB_HEAD,
)
from .cc_dt import format_datetime
from .cc_logger import BraceStyleAdapter

if TYPE_CHECKING:
    from .cc_session import CamcopsSession

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Modified Request interface, for type checking
# =============================================================================
# https://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/auth/user_object.html
# https://rollbar.com/blog/using-pyramid-request-factory-to-write-less-code/
#
# ... everything with reify=True is cached, so if we ask for something
#     more than once, we keep getting the same thing
# ... https://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html#pyramid.request.Request.set_property  # noqa


class CamcopsRequest(Request):
    @reify
    def config(self) -> CamcopsConfig:
        """
        Return an instance of CamcopsConfig for the request.
        Access it as request.config, with no brackets.
        """
        config_filename = get_config_filename(environ=self.environ)
        config = get_config(config_filename=config_filename)
        return config

    @reify
    def dbsession(self) -> SqlASession:
        """
        Return an SQLAlchemy session for the relevant request.
        The use of @reify makes this elegant. If and only if a view wants a
        database, it can say
            dbsession = request.dbsession
        and if it requests that, the cleanup callbacks get installed.
        """
        log.info("Making SQLAlchemy session")
        cfg = self.config
        engine = cfg.create_engine()
        maker = sessionmaker(bind=engine)
        session = maker()  # type: SqlASession

        def end_sqlalchemy_session(req: Request) -> None:
            if req.exception is not None:
                session.rollback()
            else:
                session.commit()
            log.info("Closing SQLAlchemy session")
            session.close()

        self.add_finished_callback(end_sqlalchemy_session)

        return session

    @reify
    def now_arrow(self) -> Arrow:
        """
        Returns the time of the request as an Arrow object.
        (Reified, so a request only ever has one time.)
        Exposed as the property: request.now_arrow
        """
        return arrow.now()

    @reify
    def now_utc_datetime(self) -> datetime.datetime:
        """
        Returns the time of the request as a UTC datetime.
        Exposed as the property: request.now_utc_datetime
        """
        a = self.now_arrow  # type: Arrow
        return a.to('utc').datetime

    @reify
    def now_iso8601_era_format(self) -> str:
        return format_datetime(self.now_arrow, DATEFORMAT.ISO8601)

    @reify
    def web_logo_html(self) -> str:
        """
        Returns the time of the request as a UTC datetime.
        Exposed as the property: request.web_logo_html
        """
        # Note: HTML4 uses <img ...>; XHTML uses <img ... />;
        # HTML5 is happy with <img ... />

        # IE float-right problems: http://stackoverflow.com/questions/1820007
        # Tables are a nightmare in IE (table max-width not working unless you
        # also specify it for image size, etc.)
        cfg = self.config
        return """
            <div class="web_logo_header">
                <a href="{}"><img class="logo_left" src="{}" alt="" /></a>
                <a href="{}"><img class="logo_right" src="{}" alt="" /></a>
            </div>
        """.format(
            self.script_name, CAMCOPS_LOGO_FILE_WEBREF,
            cfg.LOCAL_INSTITUTION_URL, LOCAL_LOGO_FILE_WEBREF
        )

    @reify
    def webstart_html(self) -> str:
        """
        Returns the time of the request as a UTC datetime.
        Exposed as the property: request.webstart_html
        """
        return WEB_HEAD + self.web_logo_html

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camcops_session = CamcopsSession.get_http_session(self)
