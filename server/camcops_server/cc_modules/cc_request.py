#!/usr/bin/env python
# camcops_server/cc_modules/cc_request.py

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

from contextlib import contextmanager
import logging
import os
from typing import Any, Dict, Generator, List, Optional, Tuple, TYPE_CHECKING
import urllib.parse

from cardinal_pythonlib.datetimefunc import (
    coerce_to_pendulum,
    coerce_to_pendulum_date,
    convert_datetime_to_utc,
    format_datetime,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.plot import (
    png_img_html_from_pyplot_figure,
    svg_html_from_pyplot_figure,
)
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.wsgi.constants import WsgiEnvVar
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from pendulum import Date, DateTime as Pendulum
from pendulum.parsing.exceptions import ParserError
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPException
from pyramid.interfaces import ISession
from pyramid.request import Request
from pyramid.response import Response
from pyramid.testing import DummyRequest
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqlASession
from webob.multidict import MultiDict

# Note: everything uder the sun imports this file, so keep the intra-package
# imports as minimal as possible.
from .cc_baseconstants import (
    ENVVAR_CONFIG_FILE,
    DOCUMENTATION_INDEX_FILENAME_STEM,
)
from .cc_config import (
    CamcopsConfig,
    get_config,
    get_config_filename_from_os_env,
)
from .cc_constants import (
    CSS_PAGED_MEDIA,
    DateFormat,
    DEFAULT_PLOT_DPI,
    USE_SVG_IN_HTML,
)
from .cc_idnumdef import get_idnum_definitions, IdNumDefinition
# noinspection PyUnresolvedReferences
import camcops_server.cc_modules.cc_plot  # import side effects (configure matplotlib)  # noqa
from .cc_pyramid import (
    camcops_add_mako_renderer,
    CamcopsAuthenticationPolicy,
    CamcopsAuthorizationPolicy,
    CookieKey,
    get_session_factory,
    Permission,
    RequestMethod,
    RouteCollection,
    STATIC_CAMCOPS_PACKAGE_PATH,
)
from .cc_serversettings import get_server_settings, ServerSettings
from .cc_string import all_extra_strings_as_dicts, APPSTRING_TASKNAME
from .cc_tabletsession import TabletSession
from .cc_user import User

if TYPE_CHECKING:
    from matplotlib.axis import Axis
    from matplotlib.axes import Axes
    # from matplotlib.figure import SubplotBase
    from matplotlib.text import Text
    from .cc_session import CamcopsSession

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_ADD_ROUTES = False
DEBUG_AUTHORIZATION = False
DEBUG_REQUEST_CREATION = False
DEBUG_CAMCOPS_SESSION = False
DEBUG_TABLET_SESSION = False
DEBUG_DBSESSION_MANAGEMENT = False

if any([DEBUG_ADD_ROUTES,
        DEBUG_AUTHORIZATION,
        DEBUG_REQUEST_CREATION,
        DEBUG_CAMCOPS_SESSION,
        DEBUG_TABLET_SESSION,
        DEBUG_DBSESSION_MANAGEMENT]):
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
        ``config.set_request_factory(CamcopsRequest)``

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
        self._debugging_db_session = None  # type: SqlASession  # for unit testing only  # noqa
        self._debugging_user = None  # type: User  # for unit testing only  # noqa
        # Don't make the _camcops_session yet; it will want a Registry, and
        # we may not have one yet; see command_line_request().
        if DEBUG_REQUEST_CREATION:
            log.debug("CamcopsRequest.__init__: args={!r}, kwargs={!r}",
                      args, kwargs)

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
        if self._camcops_session is not None:
            self.dbsession.expunge(self._camcops_session)
        self._camcops_session = ccsession

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------

    @reify
    def config_filename(self) -> str:
        """
        Gets the config filename in use.
        """
        return get_config_filename_from_os_env()

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
        return cfg.get_sqla_engine()

    @reify
    def dbsession(self) -> SqlASession:
        """
        Return an SQLAlchemy session for the relevant request.
        The use of @reify makes this elegant. If and only if a view wants a
        database, it can say

        .. code-block:: python

            dbsession = request.dbsession

        and if it requests that, the cleanup callbacks get installed.
        """
        session = self.get_bare_dbsession()

        def end_sqlalchemy_session(req: Request) -> None:
            # noinspection PyProtectedMember
            req._finish_dbsession()

        # - For command-line pseudo-requests, add_finished_callback is no use,
        #   because that's called by the Pyramid routing framework.
        # - So how do we autocommit a command-line session?
        # - Hooking into CamcopsRequest.__del__ did not work: called, yes, but
        #   object state (e.g. newly inserted User objects) went wrong (e.g.
        #   the objects had been blanked somehow, or that's what the INSERT
        #   statements looked like).
        # - Use a context manager instead; see below.
        self.add_finished_callback(end_sqlalchemy_session)

        return session

    def _finish_dbsession(self) -> None:
        # Do NOT roll back "if req.exception is not None"; that includes
        # all sorts of exceptions like HTTPFound, HTTPForbidden, etc.
        # See also
        # - https://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/pylons/exceptions.html  # noqa
        # But they are neatly subclasses of HTTPException, and isinstance()
        # deals with None, so:
        session = self.dbsession
        if (self.exception is not None and
                not isinstance(self.exception, HTTPException)):
            log.critical(
                "Request raised exception that wasn't an HTTPException; "
                "rolling back; exception was: {!r}", self.exception)
            session.rollback()
        else:
            if DEBUG_DBSESSION_MANAGEMENT:
                log.debug("Committing to database")
            session.commit()
        if DEBUG_DBSESSION_MANAGEMENT:
            log.debug("Closing SQLAlchemy session")
        session.close()

    def get_bare_dbsession(self) -> SqlASession:
        if self._debugging_db_session:
            log.debug("Request is using debugging SQLAlchemy session")
            return self._debugging_db_session
        if DEBUG_DBSESSION_MANAGEMENT:
            log.debug("Making SQLAlchemy session")
        engine = self.engine
        maker = sessionmaker(bind=engine)
        session = maker()  # type: SqlASession
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
        ts.set_session_id_token(new_cc_session.id, new_cc_session.token)
        if DEBUG_TABLET_SESSION:
            log.debug("CamcopsRequest: {!r}", self)
            log.debug("CamcopsRequest.tabletsession: {!r}", ts)
            log.debug("CamcopsRequest.camcops_session: {!r}",
                      self._camcops_session)
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
        return Pendulum.now()

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

    @property
    def today(self) -> Date:
        return self.now.date()

    # -------------------------------------------------------------------------
    # Logos, static files, and other institution-specific stuff
    # -------------------------------------------------------------------------

    @property
    def url_local_institution(self) -> str:
        return self.config.local_institution_url

    @property
    def url_camcops_favicon(self) -> str:
        # Cope with reverse proxies, etc.
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html#pyramid.request.Request.static_url  # noqa
        return self.static_url(STATIC_CAMCOPS_PACKAGE_PATH +
                               "favicon_camcops.png")

    @property
    def url_camcops_logo(self) -> str:
        return self.static_url(STATIC_CAMCOPS_PACKAGE_PATH +
                               "logo_camcops.png")

    @property
    def url_local_logo(self) -> str:
        return self.static_url(STATIC_CAMCOPS_PACKAGE_PATH + "logo_local.png")

    @property
    def url_camcops_manual_pdf(self) -> str:
        return self.static_url(STATIC_CAMCOPS_PACKAGE_PATH +
                               "documentation_copy/" +
                               DOCUMENTATION_INDEX_FILENAME_STEM)

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

    def get_int_list_param(self, key: str) -> List[int]:
        values = self.params.getall(key)
        try:
            return [int(x) for x in values]
        except (KeyError, TypeError, ValueError):
            return []

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
            return coerce_to_pendulum_date(self.params[key])
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

        .. code-block:: python

            Request.route_url(route_name, param1=value1, param2=value2)

        where "param1" is the literal name of the parameter, but here we can do

        .. code-block:: python

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

    def extrastring_families(self, sort: bool = True) -> List[str]:
        """
        Which sets of extra strings do we have?
        """
        families = list(self._all_extra_strings.keys())
        if sort:
            families.sort()
        return families

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
    def create_figure(**kwargs) -> Figure:
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
        fontsize = self.config.plot_fontsize
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

    def get_html_from_pyplot_figure(self, fig: Figure) -> str:
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
        return self._debugging_user or self.camcops_session.user

    @property
    def user_id(self) -> Optional[int]:
        if self._debugging_user:
            return self._debugging_user.user_id
        return self.camcops_session.user_id

    # -------------------------------------------------------------------------
    # ID number definitions
    # -------------------------------------------------------------------------

    @reify
    def idnum_definitions(self) -> List[IdNumDefinition]:
        return get_idnum_definitions(self.dbsession)  # no longer cached

    @reify
    def valid_which_idnums(self) -> List[int]:
        return [iddef.which_idnum for iddef in self.idnum_definitions]
        # ... pre-sorted

    def get_idnum_definition(self,
                             which_idnum: int) -> Optional[IdNumDefinition]:
        return next((iddef for iddef in self.idnum_definitions
                     if iddef.which_idnum == which_idnum), None)

    def get_id_desc(self, which_idnum: int,
                    default: str = None) -> Optional[str]:
        """Get server's ID description."""
        return next((iddef.description for iddef in self.idnum_definitions
                     if iddef.which_idnum == which_idnum),
                    default)

    def get_id_shortdesc(self, which_idnum: int,
                         default: str = None) -> Optional[str]:
        """Get server's short ID description."""
        return next((iddef.short_description
                     for iddef in self.idnum_definitions
                     if iddef.which_idnum == which_idnum),
                    default)

    # -------------------------------------------------------------------------
    # Server settings
    # -------------------------------------------------------------------------

    @reify
    def server_settings(self) -> ServerSettings:
        return get_server_settings(self)

    @reify
    def database_title(self) -> str:
        ss = self.server_settings
        return ss.database_title or ""

    def set_database_title(self, title: str) -> None:
        ss = self.server_settings
        ss.database_title = title


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


# =============================================================================
# Configurator
# =============================================================================

@contextmanager
def pyramid_configurator_context(debug_toolbar: bool = False) -> Configurator:
    # Note this includes settings that transcend the config file.
    #
    # Most things should be in the config file. This enables us to run multiple
    # configs (e.g. multiple CamCOPS databases) through the same process.
    # However, some things we need to know right now, to make the WSGI app.
    # Here, OS environment variables and command-line switches are appropriate.

    # -------------------------------------------------------------------------
    # 1. Base app
    # -------------------------------------------------------------------------
    settings = {  # Settings that can't be set directly?
        'debug_authorization': DEBUG_AUTHORIZATION,
        # ... see https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html#debugging-view-authorization-failures  # noqa
    }
    with Configurator(settings=settings) as config:
        # ---------------------------------------------------------------------
        # Authentication; authorizaion (permissions)
        # ---------------------------------------------------------------------
        authentication_policy = CamcopsAuthenticationPolicy()
        config.set_authentication_policy(authentication_policy)
        # Let's not use ACLAuthorizationPolicy, which checks an access control
        # list for a resource hierarchy of objects, but instead:
        authorization_policy = CamcopsAuthorizationPolicy()
        config.set_authorization_policy(authorization_policy)
        config.set_default_permission(Permission.HAPPY)
        # ... applies to all SUBSEQUENT view configuration registrations

        # ---------------------------------------------------------------------
        # Factories
        # ---------------------------------------------------------------------
        config.set_request_factory(CamcopsRequest)
        # ... for request attributes: config, database, etc.
        config.set_session_factory(get_session_factory())
        # ... for request.session

        camcops_add_mako_renderer(config, extension='.mako')

        # deform_bootstrap.includeme(config)

        # ---------------------------------------------------------------------
        # Routes and accompanying views
        # ---------------------------------------------------------------------

        # Add static views
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#serving-static-assets  # noqa
        # Hmm. We cannot fail to set up a static file route, because otherwise
        # we can't provide URLs to them.
        static_filepath = STATIC_CAMCOPS_PACKAGE_PATH
        static_name = RouteCollection.STATIC.route
        log.debug("... including static files from {!r} at Pyramid static "
                  "name {!r}", static_filepath, static_name)
        # ... does the name needs to start with "/" or the pattern "static/"
        # will override the later "deform_static"? Not sure.
        config.add_static_view(name=static_name, path=static_filepath)

        # Add all the routes:
        for pr in RouteCollection.all_routes():
            if DEBUG_ADD_ROUTES:
                log.info("{} -> {}", pr.route, pr.path)
            config.add_route(pr.route, pr.path)
        # See also:
        # https://stackoverflow.com/questions/19184612/how-to-ensure-urls-generated-by-pyramids-route-url-and-route-path-are-valid  # noqa

        # Routes added EARLIER have priority. So add this AFTER our custom
        # bugfix:
        config.add_static_view('/deform_static', 'deform:static/')

        # Most views are using @view_config() which calls add_view().
        # Scan for @view_config decorators, to map views to routes:
        # https://docs.pylonsproject.org/projects/venusian/en/latest/api.html
        config.scan("camcops_server.cc_modules")

        # ---------------------------------------------------------------------
        # Add tweens (inner to outer)
        # ---------------------------------------------------------------------
        # We will use implicit positioning:
        # - https://www.slideshare.net/aconrad/alex-conrad-pyramid-tweens-ploneconf-2011  # noqa

        # config.add_tween('camcops_server.camcops.http_session_tween_factory')

        # ---------------------------------------------------------------------
        # Debug toolbar
        # ---------------------------------------------------------------------
        if debug_toolbar:
            log.debug("Enabling Pyramid debug toolbar")
            config.include('pyramid_debugtoolbar')  # BEWARE! SIDE EFFECTS
            # ... Will trigger an import that hooks events into all
            # SQLAlchemy queries. There's a bug somewhere relating to that;
            # see notes below relating to the "mergedb" function.
            config.add_route(RouteCollection.DEBUG_TOOLBAR.route,
                             RouteCollection.DEBUG_TOOLBAR.path)

        yield config


# =============================================================================
# Debugging requests
# =============================================================================

def make_post_body_from_dict(d: Dict[str, str],
                             encoding: str = "utf8") -> bytes:
    # https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/testing/testing_post_curl.html  # noqa
    txt = urllib.parse.urlencode(query=d)
    # ... this encoding mimics how the tablet operates
    body = txt.encode(encoding)
    return body


class CamcopsDummyRequest(CamcopsRequest, DummyRequest):
    """
    Request class that allows manual manipulation of GET/POST parameters
    for debugging.

    Notes:

    - The important base class is webob.request.BaseRequest.
    - self.params is a NestedMultiDict (see webob/multidict.py); these are
      intrinsically read-only.
    - self.params is also a read-only property. When read, it combines
      self.GET and self.POST.
    - What we do here is to manipulate the underlying GET/POST data.

    """
    _CACHE_KEY = "webob._parsed_query_vars"
    _QUERY_STRING_KEY = "QUERY_STRING"

    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     # Just a technique worth noting:
    #     #
    #     # self._original_params_property = CamcopsRequest.params  # type: property  # noqa
    #     # self._original_params = self._original_params_property.fget(self)  # type: NestedMultiDict  # noqa
    #     # self._fake_params = self._original_params.copy()  # type: MultiDict
    #     # if params:
    #     #     self._fake_params.update(params)
    #
    # @property
    # def params(self):
    #     log.critical(repr(self._fake_params))
    #     return self._fake_params
    #     # Returning the member object allows clients to call
    #     #       dummyreq.params.update(...)
    #
    # @params.setter
    # def params(self, value):
    #     self._fake_params = value

    def set_method_get(self) -> None:
        self.method = RequestMethod.GET

    def set_method_post(self) -> None:
        self.method = RequestMethod.POST

    def clear_get_params(self) -> None:
        env = self.environ
        if self._CACHE_KEY in env:
            del env[self._CACHE_KEY]
        env[self._QUERY_STRING_KEY] = ""

    def add_get_params(self, d: Dict[str, str],
                       set_method_get: bool = True) -> None:
        if not d:
            return
        # webob.request.BaseRequest.GET reads from self.environ['QUERY_STRING']
        paramdict = self.GET.copy()  # type: MultiDict
        paramdict.update(d)
        env = self.environ
        # Delete the cached version.
        if self._CACHE_KEY in env:
            del env[self._CACHE_KEY]
        # Write the new version
        env[self._QUERY_STRING_KEY] = urllib.parse.urlencode(query=paramdict)
        if set_method_get:
            self.set_method_get()

    def set_get_params(self, d: Dict[str, str],
                       set_method_get: bool = True) -> None:
        self.clear_get_params()
        self.add_get_params(d, set_method_get=set_method_get)

    def set_post_body(self, body: bytes,
                      set_method_post: bool = True) -> None:
        log.debug("Applying fake POST body: {!r}", body)
        self.body = body
        self.content_length = len(body)
        if set_method_post:
            self.set_method_post()

    def fake_request_post_from_dict(self,
                                    d: Dict[str, str],
                                    encoding: str = "utf8",
                                    set_method_post: bool = True) -> None:
        # webob.request.BaseRequest.POST reads from 'body' (indirectly).
        body = make_post_body_from_dict(d, encoding=encoding)
        self.set_post_body(body, set_method_post=set_method_post)


_ = """
# A demonstration of the manipulation of superclass properties:

class Test(object):
    def __init__(self):
        self.a = 3
        
    @property
    def b(self):
        return 4


class Derived(Test):
    def __init__(self):
        super().__init__()
        self._superclass_b = super().b
        self._b = 4
        
    @property
    def b(self):
        print("Superclass b: {}".format(self._superclass_b.fget(self)))
        print("Self _b: {}".format(self._b))
        return self._b
    @b.setter
    def b(self, value):
        self._b = value


x = Test()
x.a  # 3
x.a = 5
x.a  # 5
x.b  # 4
x.b = 6  # can't set attribute

y = Derived()
y.a  # 3
y.a = 5
y.a  # 5
y.b  # 4
y.b = 6
y.b  # 6

"""


def _get_core_debugging_request() -> CamcopsDummyRequest:
    with pyramid_configurator_context(debug_toolbar=False) as config:
        req = CamcopsDummyRequest(
            environ={
                ENVVAR_CONFIG_FILE: os.environ[ENVVAR_CONFIG_FILE],
                WsgiEnvVar.PATH_INFO: '/',
                WsgiEnvVar.SCRIPT_NAME: '',
                WsgiEnvVar.SERVER_NAME: '127.0.0.1',
                WsgiEnvVar.SERVER_PORT: '8000',
                WsgiEnvVar.WSGI_URL_SCHEME: 'http',
            }
        )
        # ... must pass an actual dict to the "environ" parameter; os.environ
        # itself isn't OK ("TypeError: WSGI environ must be a dict; you passed
        # environ({'key1': 'value1', ...})

        req.registry = config.registry
        config.begin(request=req)
        return req


def get_command_line_request() -> CamcopsRequest:
    """
    Creates a dummy CamcopsRequest for use on the command line.
    Presupposes that os.environ[ENVVAR_CONFIG_FILE] has been set, as it is
    in camcops.main().
    """
    log.debug("Creating command-line pseudo-request")
    req = _get_core_debugging_request()

    # If we proceed with an out-of-date database, we will have problems, and
    # those problems may not be immediately apparent, which is bad. So:
    req.config.assert_database_ok()

    return req


@contextmanager
def command_line_request_context() -> Generator[CamcopsRequest, None, None]:
    """
    Request objects are ubiquitous, and allow code to refer to the HTTP
    request, config, HTTP session, database session, and so on. Here we make
    a special sort of request for use from the command line, and provide it
    as a context manager that will COMMIT the database afterwards (because the
    normal method, via the Pyramid router, is unavailable).
    """
    req = get_command_line_request()
    yield req
    # noinspection PyProtectedMember
    req._finish_dbsession()


def get_unittest_request(dbsession: SqlASession,
                         params: Dict[str, Any] = None) -> CamcopsDummyRequest:
    """
    Creates a dummy CamcopsRequest for use by unit tests.
    Points to an existing database (e.g. SQLite in-memory database).
    Presupposes that os.environ[ENVVAR_CONFIG_FILE] has been set, as it is
    in camcops.main().
    """
    log.debug("Creating unit testing pseudo-request")
    req = _get_core_debugging_request()
    req.set_get_params(params)

    req._debugging_db_session = dbsession
    user = User()
    user.superuser = True
    req._debugging_user = user

    return req
