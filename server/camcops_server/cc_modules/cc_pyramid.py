#!/usr/bin/env python
# camcops_server/cc_modules/cc_pyramid.py

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

import enum
import logging
import os
import pprint
import re
import sys
from typing import (Any, Callable, Dict, List, Optional, Tuple, Type,
                    TYPE_CHECKING)
from urllib.parse import urlencode

from cardinal_pythonlib.logs import BraceStyleAdapter
from mako.lookup import TemplateLookup
from paginate import Page
from pyramid.authentication import IAuthenticationPolicy
from pyramid.authorization import IAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.interfaces import ILocation, ISession
from pyramid.response import Response
from pyramid.security import (
    Allowed,
    Denied,
    Authenticated,
    Everyone,
    PermitsResult,
)
from pyramid.session import SignedCookieSessionFactory
from pyramid_mako import (
    MakoLookupTemplateRenderer,
    MakoRendererFactory,
    MakoRenderingException,
    reraise,
    text_error_template,
)
from sqlalchemy.orm import Query
from zope.interface import implementer

from .cc_baseconstants import TEMPLATE_DIR
from .cc_cache import cache_region_static

if TYPE_CHECKING:
    from pyramid.request import Request
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))

DEBUG_EFFECTIVE_PRINCIPALS = False
DEBUG_TEMPLATES = False
# ... logs more information about template creation, but also writes the
# templates in their compiled-to-Python version to a debugging directory (see
# below), which is very informative.
DEBUGGING_MAKO_DIR = os.path.expanduser("~/tmp/mako_template_source")


# =============================================================================
# Constants
# =============================================================================

COOKIE_NAME = 'camcops'
SUBMIT = 'submit'


class CookieKey:
    SESSION_ID = 'session_id'
    SESSION_TOKEN = 'session_token'


class HttpMethod:
    GET = "GET"
    POST = "POST"


class ViewParam(object):
    """
    Used in the following situations:

    - as parameter names for parameterized URLs, via RoutePath to Pyramid's
      route configuration, then fetched from the matchdict.

    - as form parameter names (often with some duplication as the attribute
      names of deform Form objects, because to avoid duplication would involve
      metaclass mess);
    """
    # PK = "pk"
    # PATIENT_ID = "pid"
    # QUERY = "_query"  # built in to Pyramid
    # AGREE = "agree"
    END_DATETIME = "end_datetime"
    FILENAME = "filename"
    MUST_CHANGE_PASSWORD = "must_change_password"
    NEW_PASSWORD = "new_password"
    ROWS_PER_PAGE = "rows_per_page"
    OLD_PASSWORD = "old_password"
    PAGE = "page"
    PASSWORD = "password"
    REDIRECT_URL = "redirect_url"
    REMOTE_IP_ADDR = "remote_ip_addr"
    SERVER_PK = "server_pk"
    SOURCE = "source"
    START_DATETIME = "start_datetime"
    TABLENAME = "table_name"
    TRUNCATE = "truncate"
    USER_ID = "user_id"
    USERNAME = "username"


# =============================================================================
# Templates
# =============================================================================
# Adaptation of a small part of pyramid_mako, so we can use our own Mako
# TemplateLookup, and thus dogpile.cache. See
# https://github.com/Pylons/pyramid_mako/blob/master/pyramid_mako/__init__.py

MAKO_LOOKUP = TemplateLookup(
    directories=[
        os.path.join(TEMPLATE_DIR, "base"),
        os.path.join(TEMPLATE_DIR, "css"),
        os.path.join(TEMPLATE_DIR, "menu"),
        os.path.join(TEMPLATE_DIR, "snippets"),
        os.path.join(TEMPLATE_DIR, "taskcommon"),
        os.path.join(TEMPLATE_DIR, "tasks"),
    ],
    cache_impl="dogpile.cache",
    cache_args={
        "regions": {"local": cache_region_static},
    },
    # Now, in Mako templates, use:
    #   cached="True" cache_region="local"
    input_encoding="utf-8",
    output_encoding="utf-8",
    module_directory=DEBUGGING_MAKO_DIR if DEBUG_TEMPLATES else None,
)


class CamcopsMakoLookupTemplateRenderer(MakoLookupTemplateRenderer):
    def __call__(self, value: Dict[str, Any], system: Dict[str, Any]) -> str:
        if DEBUG_TEMPLATES:
            log.debug("value: {}", pprint.pformat(value))
            log.debug("system: {}", pprint.pformat(system))
        # RNC extra values:
        system['Routes'] = Routes
        # Update the system dictionary with the values from the user
        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('renderer was passed non-dictionary as value')

        # Check if 'context' in the dictionary
        context = system.pop('context', None)

        # Rename 'context' to '_context' because Mako internally already has a
        # variable named 'context'
        if context is not None:
            system['_context'] = context

        template = self.template
        if self.defname is not None:
            template = template.get_def(self.defname)
        # noinspection PyBroadException
        try:
            if DEBUG_TEMPLATES:
                log.debug("final dict to template: {}", pprint.pformat(system))
            result = template.render_unicode(**system)
        except:
            try:
                exc_info = sys.exc_info()
                errtext = text_error_template().render(
                    error=exc_info[1],
                    traceback=exc_info[2]
                    )
                reraise(MakoRenderingException(errtext), None, exc_info[2])
            finally:
                # noinspection PyUnboundLocalVariable
                del exc_info

        # noinspection PyUnboundLocalVariable
        return result


class CamcopsMakoRendererFactory(MakoRendererFactory):
    # noinspection PyTypeChecker
    renderer_factory = staticmethod(CamcopsMakoLookupTemplateRenderer)


def camcops_add_mako_renderer(config: Configurator, extension):
    """
    Replacement for add_mako_renderer from pyramid_mako, so we can use our own
    lookup.
    """
    renderer_factory = CamcopsMakoRendererFactory()
    renderer_factory.lookup = MAKO_LOOKUP
    config.add_renderer(extension, renderer_factory)


# =============================================================================
# URL/route helpers
# =============================================================================

RE_VALID_REPLACEMENT_MARKER = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
# All characters must be a-z, A-Z, _, or 0-9.
# First character must not be a digit.
# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#route-pattern-syntax  # noqa


def valid_replacement_marker(marker: str) -> bool:
    return RE_VALID_REPLACEMENT_MARKER.match(marker) is not None


class UrlParamType(enum.Enum):
    STRING = 1
    POSITIVE_INTEGER = 2
    PLAIN_STRING = 3


class UrlParam(object):
    def __init__(self, name: str,
                 paramtype: UrlParamType == UrlParamType.PLAIN_STRING) -> None:
        self.name = name
        self.paramtype = paramtype
        assert valid_replacement_marker(name), (
            "UrlParam: invalid replacement marker: " + repr(name)
        )

    def regex(self) -> str:
        if self.paramtype == UrlParamType.STRING:
            return ''
        elif self.paramtype == UrlParamType.POSITIVE_INTEGER:
            return r'\d+'  # digits
        elif self.paramtype == UrlParamType.PLAIN_STRING:
            return r'[a-zA-Z0-9_]+'
        else:
            raise RuntimeError("Bug in UrlParam")

    def markerdef(self) -> str:
        marker = self.name
        r = self.regex()
        if r:
            marker += ':' + r
        return '{' + marker + '}'


def make_url_path(base: str, *args: UrlParam) -> str:
    parts = []  # type: List[str]
    if not base.startswith("/"):
        parts.append("/")
    parts += [base] + [arg.markerdef() for arg in args]
    return "/".join(parts)


# =============================================================================
# Routes
# =============================================================================

# Class to collect constants together
# See also http://xion.io/post/code/python-enums-are-ok.html
class Routes(object):
    """
    Names of Pyramid routes.
    - Used by the @view_config(route_name=...) decorator.
    - Configured via RouteCollection / RoutePath to the Pyramid route
      configurator.
    """
    # Hard-coded special paths
    STATIC = "static"

    # Implemented
    CHANGE_OWN_PASSWORD = "change_own_password"
    CHANGE_OTHER_PASSWORD = "change_other_password"
    CHOOSE_CLINICALTEXTVIEW = "choose_clinicaltextview"
    CHOOSE_TRACKER = "choose_tracker"
    DATABASE_API = "database"
    DELETE_PATIENT = "delete_patient"
    FORCIBLY_FINALIZE = "forcibly_finalize"
    HOME = "home"
    INSPECT_TABLE_DEFS = "view_table_definitions"
    INSPECT_TABLE_VIEW_DEFS = "view_table_and_view_definitions"
    INTROSPECT = "introspect"
    LOGOUT = "logout"
    MANAGE_USERS = "manage_users"
    OFFER_AUDIT_TRAIL = "offer_audit_trail"
    OFFER_BASIC_DUMP = "offer_basic_dump"
    OFFER_HL7_LOG_OPTIONS = "offer_hl7_log"
    OFFER_HL7_RUN_OPTIONS = "offer_hl7_run"
    OFFER_INTROSPECTION = "offer_introspect"
    OFFER_REGENERATE_SUMMARIES = "offer_regenerate_summary_tables"
    OFFER_TABLE_DUMP = "offer_table_dump"
    OFFER_TERMS = "offer_terms"
    TESTPAGE_PRIVATE_1 = "testpage_private_1"
    TESTPAGE_PUBLIC_1 = "testpage_public_1"
    TESTPAGE_PUBLIC_2 = "testpage_public_2"
    VIEW_AUDIT_TRAIL = "view_audit_trail"
    VIEW_POLICIES = "view_policies"
    VIEW_TASKS = "view_tasks"

    # To implement ***
    ADD_SPECIAL_NOTE = "add_special_note"
    ADD_USER = "add_user"
    APPLY_FILTER_COMPLETE = "apply_filter_complete"
    APPLY_FILTER_DEVICE = "apply_filter_device"
    APPLY_FILTER_DOB = "apply_filter_dob"
    APPLY_FILTER_END_DATETIME = "apply_filter_end_datetime"
    APPLY_FILTER_FORENAME = "apply_filter_forename"
    APPLY_FILTER_IDNUMS = "apply_filter_idnums"
    APPLY_FILTER_INCLUDE_OLD_VERSIONS = "apply_filter_include_old_versions"
    APPLY_FILTERS = "apply_filters"
    APPLY_FILTER_SEX = "apply_filter_sex"
    APPLY_FILTER_START_DATETIME = "apply_filter_start_datetime"
    APPLY_FILTER_SURNAME = "apply_filter_surname"
    APPLY_FILTER_TASK = "apply_filter_task"
    APPLY_FILTER_TEXT = "apply_filter_text"
    APPLY_FILTER_USER = "apply_filter_user"
    ASK_DELETE_USER = "ask_delete_user"
    ASK_TO_ADD_USER = "ask_to_add_user"
    BASIC_DUMP = "basic_dump"
    CHANGE_NUMBER_TO_VIEW = "change_number_to_view"
    CHANGE_USER = "change_user"
    CLEAR_FILTER_COMPLETE = "clear_filter_complete"
    CLEAR_FILTER_DEVICE = "clear_filter_device"
    CLEAR_FILTER_DOB = "clear_filter_dob"
    CLEAR_FILTER_END_DATETIME = "clear_filter_end_datetime"
    CLEAR_FILTER_FORENAME = "clear_filter_forename"
    CLEAR_FILTER_IDNUMS = "clear_filter_idnums"
    CLEAR_FILTER_INCLUDE_OLD_VERSIONS = "clear_filter_include_old_versions"
    CLEAR_FILTERS = "clear_filters"
    CLEAR_FILTER_SEX = "clear_filter_sex"
    CLEAR_FILTER_START_DATETIME = "clear_filter_start_datetime"
    CLEAR_FILTER_SURNAME = "clear_filter_surname"
    CLEAR_FILTER_TASK = "clear_filter_task"
    CLEAR_FILTER_TEXT = "clear_filter_text"
    CLEAR_FILTER_USER = "clear_filter_user"
    CLINICALTEXTVIEW = "clinicaltextview"
    CRASH = "crash"
    DELETE_USER = "delete_user"
    EDIT_PATIENT = "edit_patient"
    EDIT_USER = "edit_user"
    ENABLE_USER = "enable_user"
    ENTER_NEW_PASSWORD = "enter_new_password"
    ERASE_TASK = "erase_task"
    FILTER = "filter"
    FIRST_PAGE = "first_page"
    LAST_PAGE = "last_page"
    LOGIN = "login"
    MAIN_MENU = "main_menu"
    NEXT_PAGE = "next_page"
    OFFER_REPORT = "offer_report"
    PREVIOUS_PAGE = "previous_page"
    PROVIDE_REPORT = "report"
    REGENERATE_SUMMARIES = "regenerate_summary_tables"
    REPORTS_MENU = "reports_menu"
    TABLE_DUMP = "table_dump"
    TASK = "task"
    TRACKER = "tracker"
    VIEW_HL7_LOG = "view_hl7_log"
    VIEW_HL7_RUN = "view_hl7_run"


class RoutePath(object):
    """
    Class to hold a route/path pair.
    - Pyramid route names are just strings used internally for convenience.
    - Pyramid URL paths are URL fragments, like '/thing', and can contain
      placeholders, like '/thing/{bork_id}', which will result in the
      request.matchdict object containing a 'bork_id' key. Those can be
      further constrained by regular expressions, like '/thing/{bork_id:\d+}'
      to restrict to digits.
    """
    def __init__(self, route: str, path: str,
                 ignore_in_all_routes: bool = False) -> None:
        self.route = route
        self.path = path
        self.ignore_in_all_routes = ignore_in_all_routes


class RouteCollection(object):
    """
    All routes, with their paths, for CamCOPS.
    They will be auto-read by all_routes().

    To make a URL on the fly, use Request.route_url() or
    CamcopsRequest.route_url_params().

    To associate a view with a route, use the Pyramid @view_config decorator.
    """
    # Hard-coded special paths
    DEBUG_TOOLBAR = RoutePath('debug_toolbar', '/_debug_toolbar/',
                              ignore_in_all_routes=True)  # hard-coded path
    STATIC = RoutePath(Routes.STATIC, "",  # path is ignored
                       ignore_in_all_routes=True)

    # Implemented
    CHANGE_OWN_PASSWORD = RoutePath(Routes.CHANGE_OWN_PASSWORD, '/change_pw')
    CHANGE_OTHER_PASSWORD = RoutePath(
        Routes.CHANGE_OTHER_PASSWORD,
        make_url_path(
            "/change_other_password",
            UrlParam(ViewParam.USER_ID, UrlParamType.POSITIVE_INTEGER)
        )
    )
    DATABASE_API = RoutePath(Routes.DATABASE_API, '/database')
    HOME = RoutePath(Routes.HOME, '/webview')
    INTROSPECT = RoutePath(Routes.INTROSPECT, '/introspect')
    # ... filename via query param (sorts out escaping)
    LOGIN = RoutePath(Routes.LOGIN, "/login")
    LOGOUT = RoutePath(Routes.LOGOUT, "/logout")
    OFFER_AUDIT_TRAIL = RoutePath(Routes.OFFER_AUDIT_TRAIL,
                                  "/offer_audit_trail")
    OFFER_INTROSPECTION = RoutePath(
        Routes.OFFER_INTROSPECTION, "/offer_introspect"
    )
    OFFER_TERMS = RoutePath(Routes.OFFER_TERMS, '/offer_terms')
    TESTPAGE_PRIVATE_1 = RoutePath(Routes.TESTPAGE_PRIVATE_1, '/testpriv1')
    TESTPAGE_PUBLIC_1 = RoutePath(Routes.TESTPAGE_PUBLIC_1, '/test1')
    TESTPAGE_PUBLIC_2 = RoutePath(Routes.TESTPAGE_PUBLIC_2, '/test2')
    VIEW_AUDIT_TRAIL = RoutePath(Routes.VIEW_AUDIT_TRAIL, "/view_audit_trail")
    VIEW_POLICIES = RoutePath(Routes.VIEW_POLICIES, "/view_policies")

    # To implement ***
    ADD_SPECIAL_NOTE = RoutePath(Routes.ADD_SPECIAL_NOTE, "/add_special_note")
    ADD_USER = RoutePath(Routes.ADD_USER, "/add_user")
    APPLY_FILTER_COMPLETE = RoutePath(
        Routes.APPLY_FILTER_COMPLETE, "/apply_filter_complete"
    )
    APPLY_FILTER_DEVICE = RoutePath(
        Routes.APPLY_FILTER_DEVICE, "/apply_filter_device"
    )
    APPLY_FILTER_DOB = RoutePath(Routes.APPLY_FILTER_DOB, "/apply_filter_dob")
    APPLY_FILTER_END_DATETIME = RoutePath(
        Routes.APPLY_FILTER_END_DATETIME, "/apply_filter_end_datetime"
    )
    APPLY_FILTER_FORENAME = RoutePath(
        Routes.APPLY_FILTER_FORENAME, "/apply_filter_forename"
    )
    APPLY_FILTER_IDNUMS = RoutePath(
        Routes.APPLY_FILTER_IDNUMS, "/apply_filter_idnums"
    )
    APPLY_FILTER_INCLUDE_OLD_VERSIONS = RoutePath(
        Routes.APPLY_FILTER_INCLUDE_OLD_VERSIONS,
        "/apply_filter_include_old_versions"
    )
    APPLY_FILTERS = RoutePath(Routes.APPLY_FILTERS, "/apply_filters")
    APPLY_FILTER_SEX = RoutePath(Routes.APPLY_FILTER_SEX, "/apply_filter_sex")
    APPLY_FILTER_START_DATETIME = RoutePath(
        Routes.APPLY_FILTER_START_DATETIME, "/apply_filter_start_datetime"
    )
    APPLY_FILTER_SURNAME = RoutePath(
        Routes.APPLY_FILTER_SURNAME,
        "/apply_filter_surname"
    )
    APPLY_FILTER_TASK = RoutePath(
        Routes.APPLY_FILTER_TASK, "/apply_filter_task"
    )
    APPLY_FILTER_TEXT = RoutePath(
        Routes.APPLY_FILTER_TEXT, "/apply_filter_text"
    )
    APPLY_FILTER_USER = RoutePath(
        Routes.APPLY_FILTER_USER, "/apply_filter_user"
    )
    ASK_DELETE_USER = RoutePath(Routes.ASK_DELETE_USER, "/ask_delete_user")
    ASK_TO_ADD_USER = RoutePath(Routes.ASK_TO_ADD_USER, "/ask_to_add_user")
    BASIC_DUMP = RoutePath(Routes.BASIC_DUMP, "/basic_dump")
    CHANGE_NUMBER_TO_VIEW = RoutePath(
        Routes.CHANGE_NUMBER_TO_VIEW, "/change_number_to_view"
    )
    CHANGE_USER = RoutePath(Routes.CHANGE_USER, "/change_user")
    CHOOSE_CLINICALTEXTVIEW = RoutePath(
        Routes.CHOOSE_CLINICALTEXTVIEW, "/choose_clinicaltextview"
    )
    CHOOSE_TRACKER = RoutePath(Routes.CHOOSE_TRACKER, "/choose_tracker")
    CLEAR_FILTER_COMPLETE = RoutePath(
        Routes.CLEAR_FILTER_COMPLETE, "/clear_filter_complete"
    )
    CLEAR_FILTER_DEVICE = RoutePath(
        Routes.CLEAR_FILTER_DEVICE, "/clear_filter_device"
    )
    CLEAR_FILTER_DOB = RoutePath(Routes.CLEAR_FILTER_DOB, "/clear_filter_dob")
    CLEAR_FILTER_END_DATETIME = RoutePath(
        Routes.CLEAR_FILTER_END_DATETIME, "/clear_filter_end_datetime"
    )
    CLEAR_FILTER_FORENAME = RoutePath(
        Routes.CLEAR_FILTER_FORENAME, "/clear_filter_forename"
    )
    CLEAR_FILTER_IDNUMS = RoutePath(
        Routes.CLEAR_FILTER_IDNUMS, "/clear_filter_idnums"
    )
    CLEAR_FILTER_INCLUDE_OLD_VERSIONS = RoutePath(
        Routes.CLEAR_FILTER_INCLUDE_OLD_VERSIONS,
        "/clear_filter_include_old_versions"
    )
    CLEAR_FILTERS = RoutePath(Routes.CLEAR_FILTERS, "/clear_filters")
    CLEAR_FILTER_SEX = RoutePath(Routes.CLEAR_FILTER_SEX, "/clear_filter_sex")
    CLEAR_FILTER_START_DATETIME = RoutePath(
        Routes.CLEAR_FILTER_START_DATETIME, "/clear_filter_start_datetime"
    )
    CLEAR_FILTER_SURNAME = RoutePath(
        Routes.CLEAR_FILTER_SURNAME, "/clear_filter_surname"
    )
    CLEAR_FILTER_TASK = RoutePath(
        Routes.CLEAR_FILTER_TASK, "/clear_filter_task"
    )
    CLEAR_FILTER_TEXT = RoutePath(
        Routes.CLEAR_FILTER_TEXT, "/clear_filter_text"
    )
    CLEAR_FILTER_USER = RoutePath(
        Routes.CLEAR_FILTER_USER, "/clear_filter_user"
    )
    CLINICALTEXTVIEW = RoutePath(Routes.CLINICALTEXTVIEW, "/clinicaltextview")
    CRASH = RoutePath(Routes.CRASH, "/crash")
    DELETE_PATIENT = RoutePath(Routes.DELETE_PATIENT, "/delete_patient")
    DELETE_USER = RoutePath(Routes.DELETE_USER, "/delete_user")
    EDIT_PATIENT = RoutePath(Routes.EDIT_PATIENT, "/edit_patient")
    EDIT_USER = RoutePath(Routes.EDIT_USER, "/edit_user")
    ENABLE_USER = RoutePath(Routes.ENABLE_USER, "/enable_user")
    ENTER_NEW_PASSWORD = RoutePath(
        Routes.ENTER_NEW_PASSWORD, "/enter_new_password"
    )
    ERASE_TASK = RoutePath(Routes.ERASE_TASK, "/erase_task")
    FILTER = RoutePath(Routes.FILTER, "/filter")
    FIRST_PAGE = RoutePath(Routes.FIRST_PAGE, "/first_page")
    FORCIBLY_FINALIZE = RoutePath(
        Routes.FORCIBLY_FINALIZE, "/forcibly_finalize"
    )
    INSPECT_TABLE_DEFS = RoutePath(
        Routes.INSPECT_TABLE_DEFS, "/view_table_definitions"
    )
    INSPECT_TABLE_VIEW_DEFS = RoutePath(
        Routes.INSPECT_TABLE_VIEW_DEFS, "/view_table_and_view_definitions"
    )
    LAST_PAGE = RoutePath(Routes.LAST_PAGE, "/last_page")
    # now HOME # MAIN_MENU = "main_menu"
    MANAGE_USERS = RoutePath(Routes.MANAGE_USERS, "/manage_users")
    NEXT_PAGE = RoutePath(Routes.NEXT_PAGE, "/next_page")
    OFFER_BASIC_DUMP = RoutePath(Routes.OFFER_BASIC_DUMP, "/offer_basic_dump")
    OFFER_HL7_LOG_OPTIONS = RoutePath(
        Routes.OFFER_HL7_LOG_OPTIONS, "/offer_hl7_log"
    )
    OFFER_HL7_RUN_OPTIONS = RoutePath(
        Routes.OFFER_HL7_RUN_OPTIONS, "/offer_hl7_run"
    )
    OFFER_REGENERATE_SUMMARIES = RoutePath(
        Routes.OFFER_REGENERATE_SUMMARIES, "/offer_regenerate_summary_tables"
    )
    OFFER_REPORT = RoutePath(Routes.OFFER_REPORT, "/offer_report")
    OFFER_TABLE_DUMP = RoutePath(Routes.OFFER_TABLE_DUMP, "/offer_table_dump")
    PREVIOUS_PAGE = RoutePath(Routes.PREVIOUS_PAGE, "/previous_page")
    PROVIDE_REPORT = RoutePath(Routes.PROVIDE_REPORT, "/report")
    REGENERATE_SUMMARIES = RoutePath(
        Routes.REGENERATE_SUMMARIES, "/regenerate_summary_tables"
    )
    REPORTS_MENU = RoutePath(Routes.REPORTS_MENU, "/reports_menu")
    TABLE_DUMP = RoutePath(Routes.TABLE_DUMP, "table_dump")
    TASK = RoutePath(Routes.TASK, "/task")
    TRACKER = RoutePath(Routes.TRACKER, "/tracker")
    VIEW_HL7_LOG = RoutePath(Routes.VIEW_HL7_LOG, "/view_hl7_log")
    VIEW_HL7_RUN = RoutePath(Routes.VIEW_HL7_RUN, "/view_hl7_run")
    VIEW_TASKS = RoutePath(Routes.VIEW_TASKS, "/view_tasks")

    @classmethod
    def all_routes(cls) -> List[RoutePath]:
        """
        Fetch all routes.
        """
        return [v for k, v in cls.__dict__.items()
                if not (k.startswith('_') or  # class hidden things
                        k == 'all_routes' or  # this function
                        v.ignore_in_all_routes)  # explicitly ignored
                ]


# =============================================================================
# Pyramid HTTP session handling
# =============================================================================

def get_session_factory() -> SignedCookieSessionFactory:
    """
    We have to give a Pyramid request a way of making an HTTP session.
    We must return a session factory.
    - An example is an instance of SignedCookieSessionFactory().
    - A session factory has the signature [1]:
            sessionfactory(req: CamcopsRequest) -> session_object
      ... where session "is a namespace" [2]
      ... but more concretely implementis the pyramid.interfaces.ISession 
          interface
      [1] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session-factory
      [2] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session
    - We want to be able to make the session by reading the CamcopsConfig from
      the request.
    """  # noqa
    def factory(req: "CamcopsRequest") -> ISession:
        """
        How does the session write the cookies to the response?

            SignedCookieSessionFactory
                BaseCookieSessionFactory  # pyramid/session.py
                    CookieSession
                        def changed():
                            if not self._dirty:
                                self._dirty = True
                                def set_cookie_callback(request, response):
                                    self._set_cookie(response)
                                    # ...
                                self.request.add_response_callback(set_cookie_callback)  # noqa

                        def _set_cookie(self, response):
                            # ...
                            response.set_cookie(...)

        """
        cfg = req.config
        secure_cookies = not cfg.ALLOW_INSECURE_COOKIES
        pyramid_factory = SignedCookieSessionFactory(
            secret=cfg.session_cookie_secret,
            hashalg='sha512',  # the default
            salt='camcops_pyramid_session.',
            cookie_name=COOKIE_NAME,
            max_age=None,  # browser scope; session cookie
            path='/',  # the default
            domain=None,  # the default
            secure=secure_cookies,
            httponly=secure_cookies,
            timeout=None,  # we handle timeouts at the database level instead
            reissue_time=0,  # default; reissue cookie at every request
            set_on_exception=True,  # (default) cookie even if exception raised
            serializer=None,  # (default) use pyramid.session.PickleSerializer
            # As max_age and expires are left at their default of None, these
            # are session cookies.
        )
        return pyramid_factory(req)

    return factory


# =============================================================================
# Authentication; authorization (permissions)
# =============================================================================

class Permission(object):
    # Permissions are strings.
    # For "logged in", use pyramid.security.Authenticated
    HAPPY = "happy"  # logged in + no need to change p/w + agreed to terms
    SUPERUSER = "superuser"


@implementer(IAuthenticationPolicy)
class CamcopsAuthenticationPolicy(object):
    # - https://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/wiki2/authorization.html  # noqa
    # - https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/auth/custom.html  # noqa
    # - Don't actually inherit from IAuthenticationPolicy; it ends up in the
    #   zope.interface.interface.InterfaceClass metaclass and then breaks with
    #   "zope.interface.exceptions.InvalidInterface: Concrete attribute, ..."
    # - But @implementer does the trick.

    @staticmethod
    def authenticated_userid(request: "CamcopsRequest") -> Optional[int]:
        return request.user_id

    # noinspection PyUnusedLocal
    @staticmethod
    def unauthenticated_userid(request: "CamcopsRequest") -> Optional[int]:
        return None

    @staticmethod
    def effective_principals(request: "CamcopsRequest") -> List[str]:
        principals = [Everyone]
        user = request.user
        if user is not None:
            principals += [Authenticated, 'u:%s' % user.id]
            if not (user.must_change_password or user.must_agree_terms()):
                principals.append(Permission.HAPPY)
            if user.superuser:
                principals.append(Permission.SUPERUSER)
            # principals.extend(('g:%s' % g.name for g in user.groups))
        if DEBUG_EFFECTIVE_PRINCIPALS:
            log.debug("effective_principals: {!r}", principals)
        return principals

    # noinspection PyUnusedLocal
    @staticmethod
    def remember(request: "CamcopsRequest",
                 userid: int,
                 **kw) -> List[Tuple[str, str]]:
        return []

    # noinspection PyUnusedLocal
    @staticmethod
    def forget(request: "CamcopsRequest") -> List[Tuple[str, str]]:
        return []


@implementer(IAuthorizationPolicy)
class CamcopsAuthorizationPolicy(object):
    # noinspection PyUnusedLocal
    @staticmethod
    def permits(context: ILocation, principals: List[str], permission: str) \
            -> PermitsResult:
        if permission in principals:
            return Allowed("ALLOWED: permission {} present in principals "
                           "{}".format(permission, principals))

        return Denied("DENIED: permission {} not in principals "
                      "{}".format(permission, principals))

    @staticmethod
    def principals_allowed_by_permission(context: ILocation,
                                         permission: str) -> List[str]:
        raise NotImplementedError()


# =============================================================================
# Responses
# =============================================================================

class PdfResponse(Response):
    def __init__(self, content: bytes, filename: str,
                 as_inline: bool = True) -> None:
        # Inline: display within browser, if possible.
        # Attachment: download.
        disp = "inline" if as_inline else "attachment"
        super().__init__(
            content_type="application/pdf",
            content_disposition="{}; filename={}".format(disp, filename),
            content_encoding="binary",
            content_length=len(content),
            body=content,
        )


class TextResponse(Response):
    def __init__(self, content: str) -> None:
        super().__init__(
            content_type="text/plain",
            body=content,
        )


class TsvResponse(Response):
    def __init__(self, content: bytes, filename: str) -> None:
        super().__init__(
            content_type="text/tab-separated-values",
            content_disposition="attachment; filename={}".format(filename),
            body=content,
        )


class XmlResponse(Response):
    def __init__(self, content: str) -> None:
        # application/xml versus text/xml:
        # https://stackoverflow.com/questions/4832357
        super().__init__(
            content_type="text/xml",
            body=content,
        )


class ZipResponse(Response):
    def __init__(self, content: bytes, filename: str) -> None:
        # For ZIP, "inline" and "attachment" dispositions are equivalent, since
        # browsers don't display ZIP files inline.
        # https://stackoverflow.com/questions/1395151
        super().__init__(
            content_type="application/zip",
            content_disposition="attachment; filename={}".format(filename),
            content_encoding="binary",
            body=content,
        )


# =============================================================================
# Pagination
# =============================================================================
# WebHelpers 1.3 doesn't support Python 3.5.
# The successor to webhelpers.paginate appears to be paginate.

class SqlalchemyOrmQueryWrapper(object):
    """
    Wrapper class to access elements of an SQLAlchemy ORM query.

    See:
    - https://docs.pylonsproject.org/projects/pylons-webframework/en/latest/helpers.html  # noqa
    - https://docs.pylonsproject.org/projects/webhelpers/en/latest/modules/paginate.html  # noqa
    - https://github.com/Pylons/paginate
    """
    def __init__(self, query: Query) -> None:
        self.query = query

    def __getitem__(self, cut: slice) -> List[Any]:
        # Return a range of objects of an sqlalchemy.orm.query.Query object
        return self.query[cut]
        # ... will apply LIMIT/OFFSET to fetch only what we need

    def __len__(self) -> int:
        # Count the number of objects in an sqlalchemy.orm.query.Query object
        return self.query.count()


PAGER_PATTERN = (
    '(Page $page of $page_count; total $item_count records) '
    '[$link_first $link_previous ~3~ $link_next $link_last]'
)


class SqlalchemyOrmPage(Page):
    """A pagination page that deals with SQLAlchemy ORM objects."""
    def __init__(self,
                 collection: Query,
                 page: int = 1,
                 items_per_page: int = 20,
                 item_count: int = None,
                 url_maker: Callable[[int], str] = None,
                 **kwargs) -> None:
        # Since views may accidentally throw strings our way:
        assert isinstance(page, int)
        assert isinstance(items_per_page, int)
        assert isinstance(item_count, int) or item_count is None
        super().__init__(
            collection=collection,
            page=page,
            items_per_page=items_per_page,
            item_count=item_count,
            wrapper_class=SqlalchemyOrmQueryWrapper,
            url_maker=url_maker,
            **kwargs
        )

    # noinspection PyShadowingBuiltins
    def pager(self,
              format: str = PAGER_PATTERN,
              url: str = None,
              show_if_single_page: bool = False,
              separator: str = ' ',
              symbol_first: str = '&lt;&lt;',
              symbol_last: str = '&gt;&gt;',
              symbol_previous: str = '&lt;',
              symbol_next: str = '&gt;',
              link_attr: Dict[str, str] = None,
              curpage_attr: Dict[str, str] = None,
              dotdot_attr: Dict[str, str] = None,
              link_tag: Callable[[Dict[str, str]], str] = None):
        link_attr = link_attr or {}  # type: Dict[str, str]
        curpage_attr = curpage_attr or {}  # type: Dict[str, str]
        # dotdot_attr = dotdot_attr or {}  # type: Dict[str, str]
        dotdot_attr = dotdot_attr or {'class':'pager_dotdot'}  # our default!
        return super().pager(
            format=format,
            url=url,
            show_if_single_page=show_if_single_page,
            separator=separator,
            symbol_first=symbol_first,
            symbol_last=symbol_last,
            symbol_previous=symbol_previous,
            symbol_next=symbol_next,
            link_attr=link_attr,
            curpage_attr=curpage_attr,
            dotdot_attr=dotdot_attr,
            link_tag=link_tag,
        )


# From webhelpers.paginate (which is broken on Python 3.5, but good),
# modified a bit:

def make_page_url(path: str, params: Dict[str, str], page: int,
                  partial: bool = False, sort: bool = True) -> str:
    """A helper function for URL generators.

    I assemble a URL from its parts. I assume that a link to a certain page is
    done by overriding the 'page' query parameter.

    ``path`` is the current URL path, with or without a "scheme://host" prefix.

    ``params`` is the current query parameters as a dict or dict-like object.

    ``page`` is the target page number.

    If ``partial`` is true, set query param 'partial=1'. This is to for AJAX
    calls requesting a partial page.

    If ``sort`` is true (default), the parameters will be sorted. Otherwise
    they'll be in whatever order the dict iterates them.
    """
    params = params.copy()
    params["page"] = page
    if partial:
        params["partial"] = "1"
    if sort:
        params = sorted(params.items())
    qs = urlencode(params, True)  # was urllib.urlencode, but changed in Py3.5
    return "%s?%s" % (path, qs)


class PageUrl(object):
    """A page URL generator for WebOb-compatible Request objects.

    I derive new URLs based on the current URL but overriding the 'page'
    query parameter.

    I'm suitable for Pyramid, Pylons, and TurboGears, as well as any other
    framework whose Request object has 'application_url', 'path', and 'GET'
    attributes that behave the same way as ``webob.Request``'s.
    """

    def __init__(self, request: "Request", qualified: bool = False):
        """
        ``request`` is a WebOb-compatible ``Request`` object.

        If ``qualified`` is false (default), generated URLs will have just the
        path and query string. If true, the "scheme://host" prefix will be
        included. The default is false to match traditional usage, and to avoid
        generating unuseable URLs behind reverse proxies (e.g., Apache's
        mod_proxy).
        """
        self.request = request
        self.qualified = qualified

    def __call__(self, page: int, partial: bool = False) -> str:
        """Generate a URL for the specified page."""
        if self.qualified:
            path = self.request.application_url
        else:
            path = self.request.path
        return make_page_url(path, self.request.GET, page, partial)
