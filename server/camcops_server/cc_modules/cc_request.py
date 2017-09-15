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
import os
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.plot import (
    png_img_html_from_pyplot_figure,
    svg_html_from_pyplot_figure,
)
import cardinal_pythonlib.rnc_web as ws
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
import pendulum
from pendulum import Date, Pendulum
from pendulum.parsing.exceptions import ParserError
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPException
from pyramid.interfaces import ISession
from pyramid.registry import Registry
from pyramid.request import Request
from pyramid.response import Response
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession

# Note: everything uder the sun imports this file, so keep the intra-package
# imports as minimal as possible.
from .cc_alembic import assert_database_is_at_head
from .cc_baseconstants import ENVVAR_CONFIG_FILE
from .cc_config import CamcopsConfig, get_config, get_config_filename
from .cc_constants import (
    CAMCOPS_LOGO_FILE_WEBREF,
    CSS_PAGED_MEDIA,
    DateFormat,
    DEFAULT_PLOT_DPI,
    LOCAL_LOGO_FILE_WEBREF,
    STATIC_URL_PREFIX,
    USE_SVG_IN_HTML,
)
from .cc_dt import (
    coerce_to_date,
    coerce_to_pendulum,
    convert_datetime_to_utc,
    format_datetime,
)
from .cc_plot import ccplot_no_op
from .cc_pyramid import CookieKey, get_session_factory
from .cc_string import all_extra_strings_as_dicts, APPSTRING_TASKNAME
from .cc_tabletsession import TabletSession

if TYPE_CHECKING:
    from matplotlib.axis import Axis
    from matplotlib.axes import Axes
    # from matplotlib.figure import SubplotBase
    from matplotlib.text import Text
    from .cc_session import CamcopsSession
    from .cc_user import User

log = BraceStyleAdapter(logging.getLogger(__name__))
ccplot_no_op()

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_CAMCOPS_SESSION = False
DEBUG_DBSESSION_MANAGEMENT = False

if DEBUG_CAMCOPS_SESSION or DEBUG_DBSESSION_MANAGEMENT:
    log.warning("Debugging options enabled!")


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
    def __init__(self, *args, **kwargs):
        """
        This is called as the Pyramid request factory; see
            config.set_request_factory(CamcopsRequest)

        What's the best way of handling the database client?
        - With Titanium, we were constrained not to use cookies. With Qt, we
          have the option.
        - But are cookies a good idea?
          Probably not; they are somewhat overcomplicated for this.
          See also
          https://softwareengineering.stackexchange.com/questions/141019/
          https://stackoverflow.com/questions/6068113/do-sessions-really-violate-restfulness  # noqa
        - Let's continue to avoid cookies.
        - We don't have to cache any information (we still send username/
          password details with each request, and that is RESTful) but it
          does save authentication time to do so on calls after the first.
        - What we could try to do is:
          - look up a session here, at Request creation time;
          - add a new session if there wasn't one;
          - but allow the database API code to replace that session (BEFORE
            it's saved to the database and gains its PK) with another,
            determined by the content.
          - This gives one more database hit, but avoids the bcrypt time.

        """
        super().__init__(*args, **kwargs)
        self.use_svg = False
        self.add_response_callback(complete_request_add_cookies)
        self._camcops_session = None
        # Don't make the _camcops_session yet; it will want a Registry, and
        # we may not have one yet; see command_line_request().

    # -------------------------------------------------------------------------
    # CamcopsSession
    # -------------------------------------------------------------------------

    @property
    def camcops_session(self) -> "CamcopsSession":
        # Contrast:
        # ccsession = request.camcops_session  # type: CamcopsSession
        # pyramid_session = request.session  # type: ISession
        if self._camcops_session is None:
            from .cc_session import CamcopsSession  # delayed import
            self._camcops_session = CamcopsSession.get_session_using_cookies(
                self)
            if DEBUG_CAMCOPS_SESSION:
                log.debug("{!r}", self._camcops_session)
        return self._camcops_session

    def replace_camcops_session(self, ccsession: "CamcopsSession") -> None:
        # We may have created a new HTTP session because the request had no
        # cookies (added to the DB session but not yet saved), but we might
        # then enter the database/tablet upload API and find session details,
        # not from the cookies, but from the POST data. At that point, we
        # want to replace the session in the Request, without committing the
        # first one to disk.
        self.dbsession.expunge(self.camcops_session)
        self._camcops_session = ccsession

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------

    @reify
    def config_filename(self) -> str:
        """
        Gets the config filename in use.
        """
        return get_config_filename(environ=self.environ)

    @reify
    def config(self) -> CamcopsConfig:
        """
        Return an instance of CamcopsConfig for the request.
        Access it as request.config, with no brackets.
        """
        config = get_config(config_filename=self.config_filename)
        return config

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------

    @reify
    def engine(self) -> Engine:
        cfg = self.config
        return cfg.create_engine()

    @reify
    def dbsession(self) -> SqlASession:
        """
        Return an SQLAlchemy session for the relevant request.
        The use of @reify makes this elegant. If and only if a view wants a
        database, it can say
            dbsession = request.dbsession
        and if it requests that, the cleanup callbacks get installed.
        """
        if DEBUG_DBSESSION_MANAGEMENT:
            log.debug("Making SQLAlchemy session")
        engine = self.engine
        maker = sessionmaker(bind=engine)
        session = maker()  # type: SqlASession

        def end_sqlalchemy_session(req: Request) -> None:
            # Do NOT roll back "if req.exception is not None"; that includes
            # all sorts of exceptions like HTTPFound, HTTPForbidden, etc.
            # See also
            # - https://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/pylons/exceptions.html  # noqa
            # But they are neatly subclasses of HTTPException, and isinstance()
            # deals with None, so:
            if (req.exception is not None and
                    not isinstance(req.exception, HTTPException)):
                log.critical(
                    "Request raised exception that wasn't an HTTPException; "
                    "rolling back; exception was: {!r}", req.exception)
                session.rollback()
            else:
                if DEBUG_DBSESSION_MANAGEMENT:
                    log.debug("Committing to database")
                session.commit()
            if DEBUG_DBSESSION_MANAGEMENT:
                log.debug("Closing SQLAlchemy session")
            session.close()

        self.add_finished_callback(end_sqlalchemy_session)

        return session

    # -------------------------------------------------------------------------
    # TabletSession
    # -------------------------------------------------------------------------

    @reify
    def tabletsession(self) -> TabletSession:
        """
        Request a TabletSession, which is an information structure geared to
        client (tablet) database accesses.
        If we're using this interface, we also want to ensure we're using
        the CamcopsSession for the information provided by the tablet in the
        POST request, not anything already loaded/reset via cookies.
        """
        from .cc_session import CamcopsSession  # delayed import
        ts = TabletSession(self)
        new_cc_session = CamcopsSession.get_session_for_tablet(ts)
        self.replace_camcops_session(new_cc_session)
        return ts

    # -------------------------------------------------------------------------
    # Date/time
    # -------------------------------------------------------------------------

    @reify
    def now(self) -> Pendulum:
        """
        Returns the time of the request as an Pendulum object.
        (Reified, so a request only ever has one time.)
        Exposed as a property.
        """
        return pendulum.now()

    @reify
    def now_utc(self) -> Pendulum:
        """
        Returns the time of the request as a UTC Pendulum.
        """
        p = self.now  # type: Pendulum
        return convert_datetime_to_utc(p)

    @reify
    def now_iso8601_era_format(self) -> str:
        return format_datetime(self.now, DateFormat.ISO8601)

    # -------------------------------------------------------------------------
    # Logos, static files, and other institution-specific stuff
    # -------------------------------------------------------------------------

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

    @property
    def url_local_institution(self) -> str:
        return self.config.LOCAL_INSTITUTION_URL

    @property
    def url_camcops_favicon(self) -> str:
        # *** check/revise ***
        return STATIC_URL_PREFIX + "favicon_camcops.png"

    @property
    def url_camcops_logo(self) -> str:
        # *** check/revise ***
        return STATIC_URL_PREFIX + "logo_camcops.png"

    @property
    def url_local_logo(self) -> str:
        # *** check/revise ***
        return STATIC_URL_PREFIX + "logo_local.png"

    # -------------------------------------------------------------------------
    # Low-level HTTP information
    # -------------------------------------------------------------------------

    @reify
    def remote_port(self) -> Optional[int]:
        """
        The remote_port variable is an optional WSGI extra provided by some
        frameworks, such as mod_wsgi.

        The WSGI spec:
        - https://www.python.org/dev/peps/pep-0333/

        The CGI spec:
        - https://en.wikipedia.org/wiki/Common_Gateway_Interface

        The Pyramid Request object:
        - https://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html#pyramid.request.Request  # noqa
        - ... note: that includes remote_addr, but not remote_port.
        """
        try:
            return int(self.environ.get("REMOTE_PORT", ""))
        except (TypeError, ValueError):
            return None

    # -------------------------------------------------------------------------
    # HTTP request convenience functions
    # -------------------------------------------------------------------------

    def get_str_param(self,
                      key: str,
                      default: str = None,
                      lower: bool = False,
                      upper: bool = False) -> Optional[str]:
        # HTTP parameters are always strings at heart
        value = self.params.get(key, default)
        if value is None:
            return value
        if lower:
            return value.lower()
        if upper:
            return value.upper()
        return value

    def get_str_list_param(self,
                           key: str,
                           lower: bool = False,
                           upper: bool = False) -> List[str]:
        values = self.params.getall(key)
        if lower:
            return [x.lower() for x in values]
        if upper:
            return [x.upper() for x in values]
        return values

    def get_int_param(self, key: str, default: int = None) -> Optional[int]:
        try:
            return int(self.params[key])
        except (KeyError, TypeError, ValueError):
            return default

    def get_bool_param(self, key: str, default: bool) -> bool:
        try:
            param_str = self.params[key].lower()
            if param_str in ["true", "t", "1", "yes", "y"]:
                return True
            elif param_str in ["false", "f", "0", "no", "n"]:
                return False
            else:
                return default
        except (AttributeError, KeyError, TypeError, ValueError):
            return default

    def get_date_param(self, key: str) -> Optional[Date]:
        try:
            return coerce_to_date(self.params[key])
        except (KeyError, ParserError, TypeError, ValueError):
            return None

    def get_datetime_param(self, key: str) -> Optional[Pendulum]:
        try:
            return coerce_to_pendulum(self.params[key])
        except (KeyError, ParserError, TypeError, ValueError):
            return None

    # -------------------------------------------------------------------------
    # Routing
    # -------------------------------------------------------------------------

    def route_url_params(self, route_name: str,
                         paramdict: Dict[str, Any]) -> str:
        """
        Provides a simplified interface to Request.route_url when you have
        parameters to pass.

        It does two things:
            (1) convert all params to their str() form;
            (2) allow you to pass parameters more easily using a string
                parameter name.

        The normal Pyramid Request use is:
            Request.route_url(route_name, param1=value1, param2=value2)

        where "param1" is the literal name of the parameter, but here we can do

            CamcopsRequest.route_url_params(route_name, {
                PARAM1_NAME: value1_not_necessarily_str,
                PARAM2_NAME: value2
            })
        """
        strparamdict = {k: str(v) for k, v in paramdict.items()}
        return self.route_url(route_name, **strparamdict)

    # -------------------------------------------------------------------------
    # Strings
    # -------------------------------------------------------------------------

    @reify
    def _all_extra_strings(self) -> Dict[str, Dict[str, str]]:
        return all_extra_strings_as_dicts(self.config_filename)

    def xstring(self,
                taskname: str,
                stringname: str,
                default: str = None,
                provide_default_if_none: bool = True) -> Optional[str]:
        """
        Looks up a string from one of the optional extra XML string files.
        """
        # For speed, calculate default only if needed:
        allstrings = self._all_extra_strings
        if taskname in allstrings:
            if stringname in allstrings[taskname]:
                return allstrings[taskname].get(stringname)
        if default is None and provide_default_if_none:
            default = "EXTRA_STRING_NOT_FOUND({}.{})".format(taskname,
                                                             stringname)
        return default

    def wxstring(self,
                 taskname: str,
                 stringname: str,
                 default: str = None,
                 provide_default_if_none: bool = True) -> Optional[str]:
        """Returns a web-safe version of an xstring (see above)."""
        value = self.xstring(taskname, stringname, default,
                             provide_default_if_none=provide_default_if_none)
        if value is None and not provide_default_if_none:
            return None
        return ws.webify(value)

    def wappstring(self,
                   stringname: str,
                   default: str = None,
                   provide_default_if_none: bool = True) -> Optional[str]:
        """
        Returns a web-safe version of an appstring (an app-wide extra string.
        """
        value = self.xstring(APPSTRING_TASKNAME, stringname, default,
                             provide_default_if_none=provide_default_if_none)
        if value is None and not provide_default_if_none:
            return None
        return ws.webify(value)

    def get_all_extra_strings(self) -> List[Tuple[str, str, str]]:
        """
        Returns all extra strings, as a list of (task, name, value) tuples.
        """
        allstrings = self._all_extra_strings
        rows = []
        for task, subdict in allstrings.items():
            for name, value in subdict.items():
                rows.append((task, name, value))
        return rows

    def task_extrastrings_exist(self, taskname: str) -> bool:
        """
        Has the server been supplied with extra strings for a specific task?
        """
        allstrings = self._all_extra_strings
        return taskname in allstrings

    # -------------------------------------------------------------------------
    # PNG versus SVG output, so tasks don't have to care (for e.g. PDF/web)
    # -------------------------------------------------------------------------

    def prepare_for_pdf_figures(self) -> None:
        if CSS_PAGED_MEDIA:
            # unlikely -- we use wkhtmltopdf instead now
            self.switch_output_to_png()
            # ... even weasyprint's SVG handling is inadequate
        else:
            # This is the main method -- we use wkhtmltopdf these days
            self.switch_output_to_svg()  # wkhtmltopdf can cope

    def prepare_for_html_figures(self) -> None:
        self.switch_output_to_svg()

    def switch_output_to_png(self) -> None:
        """Switch server to producing figures in PNG."""
        self.use_svg = False

    def switch_output_to_svg(self) -> None:
        """Switch server to producing figures in SVG."""
        self.use_svg = True

    @staticmethod
    def create_figure(**kwargs) -> "Figure":
        fig = Figure(**kwargs)
        # noinspection PyUnusedLocal
        canvas = FigureCanvas(fig)
        # The canvas will be now available as fig.canvas, since
        # FigureCanvasBase.__init__ calls fig.set_canvas(self); similarly, the
        # figure is available from the canvas as canvas.figure

        # How do we set the font, so the caller doesn't have to?
        # The "nasty global" way is:
        #       matplotlib.rc('font', **fontdict)
        #       matplotlib.rc('legend', **fontdict)
        # or similar. Then matplotlib often works its way round to using its
        # global rcParams object, which is Not OK in a multithreaded context.
        #
        # https://github.com/matplotlib/matplotlib/issues/6514
        # https://github.com/matplotlib/matplotlib/issues/6518
        #
        # The other way is to specify a fontdict with each call, e.g.
        #       ax.set_xlabel("some label", **fontdict)
        # https://stackoverflow.com/questions/21321670/how-to-change-fonts-in-matplotlib-python  # noqa
        # Relevant calls with explicit "fontdict: Dict" parameters:
        #       ax.set_xlabel(..., fontdict=XXX, ...)
        #       ax.set_ylabel(..., fontdict=XXX, ...)
        #       ax.set_xticklabels(..., fontdict=XXX, ...)
        #       ax.set_yticklabels(..., fontdict=XXX, ...)
        #       ax.text(..., fontdict=XXX, ...)
        #       ax.set_label_text(..., fontdict=XXX, ...)
        #       ax.set_title(..., fontdict=XXX, ...)
        #
        # And with "fontproperties: FontProperties"
        #       sig.suptitle(..., fontproperties=XXX, ...)
        #
        # And with "prop: FontProperties":
        #       ax.legend(..., prop=XXX, ...)
        #
        # Then, some things are automatically plotted...

        return fig

    @reify
    def fontdict(self) -> Dict[str, Any]:
        fontsize = self.config.PLOT_FONTSIZE
        return dict(
            # http://stackoverflow.com/questions/3899980
            # http://matplotlib.org/users/customizing.html
            family='sans-serif',
            # ... serif, sans-serif, cursive, fantasy, monospace
            style='normal',  # normal (roman), italic, oblique
            variant='normal',  # normal, small-caps
            weight='normal',
            # ... normal [=400], bold [=700], bolder [relative to current],
            # lighter [relative], 100, 200, 300, ..., 900
            size=fontsize  # in pt (default 12)
        )

    @reify
    def fontprops(self) -> FontProperties:
        return FontProperties(self.fontdict)

    def set_figure_font_sizes(self,
                              ax: "Axes",  # "SubplotBase",
                              fontdict: Dict[str, Any] = None,
                              x_ticklabels: bool = True,
                              y_ticklabels: bool = True) -> None:
        final_fontdict = self.fontdict.copy()
        if fontdict:
            final_fontdict.update(fontdict)
        fp = FontProperties(**final_fontdict)

        axes = []  # type: List[Axis]
        if x_ticklabels:  # and hasattr(ax, "xaxis"):
            axes.append(ax.xaxis)
        if y_ticklabels:  # and hasattr(ax, "yaxis"):
            axes.append(ax.yaxis)
        for axis in axes:
            for ticklabel in axis.get_ticklabels(which='both'):  # type: Text  # I think!  # noqa
                ticklabel.set_fontproperties(fp)

    def get_html_from_pyplot_figure(self, fig: "Figure") -> str:
        """Make HTML (as PNG or SVG) from pyplot figure."""
        if USE_SVG_IN_HTML and self.use_svg:
            return (
                svg_html_from_pyplot_figure(fig) +
                png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI,
                                                "pngfallback")
            )
            # return both an SVG and a PNG image, for browsers that can't deal
            # with SVG; the Javascript header will sort this out
            # http://www.voormedia.nl/blog/2012/10/displaying-and-detecting-support-for-svg-images  # noqa
        else:
            return png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI)

    # -------------------------------------------------------------------------
    # Convenience functions for user information
    # -------------------------------------------------------------------------

    @property
    def user(self) -> Optional["User"]:
        return self.camcops_session.user

    @property
    def user_id(self) -> Optional[int]:
        return self.camcops_session.user_id


# noinspection PyUnusedLocal
def complete_request_add_cookies(req: CamcopsRequest, response: Response):
    """
    Finializes the response by adding session cookies.
    We do this late so that we can hot-swap the session if we're using the
    database/tablet API rather than a human web browser.

    Response callbacks are called in the order first-to-most-recently-added.
    See pyramid.request.CallbackMethodsMixin.

    That looks like we can add a callback in the process of running a callback.
    And when we add a cookie to a Pyramid session, that sets a callback.
    Let's give it a go...
    """
    dbsession = req.dbsession
    dbsession.flush()  # sets the PK for ccsession, if it wasn't set
    # Write the details back to the Pyramid session (will be persisted
    # via the Response automatically):
    pyramid_session = req.session  # type: ISession
    ccsession = req.camcops_session
    pyramid_session[CookieKey.SESSION_ID] = str(ccsession.id)
    pyramid_session[CookieKey.SESSION_TOKEN] = ccsession.token
    # ... should cause the ISession to add a callback to add cookies,
    # which will be called immediately after this one.


def command_line_request() -> CamcopsRequest:
    """
    Creates a dummy CamcopsRequest for use on the command line.
    Presupposes that os.environ[ENVVAR_CONFIG_FILE] has been set, as it is
    in camcops.main().
    """
    os_env_dict = {
        ENVVAR_CONFIG_FILE: os.environ[ENVVAR_CONFIG_FILE],
    }
    registry = Registry()
    req = CamcopsRequest(environ=os_env_dict)
    # ... must pass an actual dict; os.environ itself isn't OK ("TypeError:
    # WSGI environ must be a dict; you passed environ({'key1': 'value1', ...})
    session_factory = get_session_factory()
    req.session = session_factory(req) # *** wrong! fix this
    req.registry = registry

    # If we proceed with an out-of-date database, we will have problems, and
    # those problems may not be immediately apparent, which is bad. So:
    assert_database_is_at_head(req.config)

    return req
