#!/usr/bin/env python
# camcops_server/cc_modules/cc_pyramid.py

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

from enum import Enum
import logging
import os
import pprint
import re
import sys
from typing import (Any, Callable, Dict, List, Optional, Sequence, Tuple,
                    Type, TYPE_CHECKING, Union)
from urllib.parse import urlencode

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.wsgi.constants import WsgiEnvVar
from mako.lookup import TemplateLookup
from paginate import Page
from pyramid.authentication import IAuthenticationPolicy
from pyramid.authorization import IAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import ILocation, ISession
from pyramid.request import Request
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
from sqlalchemy.sql.selectable import Select
from zope.interface import implementer

from .cc_baseconstants import TEMPLATE_DIR
from .cc_cache import cache_region_static
from .cc_constants import DEFAULT_ROWS_PER_PAGE

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_ADD_ROUTES = False
DEBUG_EFFECTIVE_PRINCIPALS = False
DEBUG_TEMPLATE_PARAMETERS = False
# ... logs more information about template creation
DEBUG_TEMPLATE_SOURCE = False
# ... writes the templates in their compiled-to-Python version to a debugging
#     directory (see below), which is very informative.
DEBUGGING_MAKO_DIR = os.path.expanduser("~/tmp/mako_template_source")

if any([DEBUG_ADD_ROUTES,
        DEBUG_EFFECTIVE_PRINCIPALS,
        DEBUG_TEMPLATE_PARAMETERS,
        DEBUG_TEMPLATE_SOURCE]):
    log.warning("Debugging options enabled!")


# =============================================================================
# Constants
# =============================================================================

COOKIE_NAME = 'camcops'


class CookieKey:
    SESSION_ID = 'session_id'
    SESSION_TOKEN = 'session_token'


class FormAction(object):
    CANCEL = 'cancel'
    CLEAR_FILTERS = 'clear_filters'
    DELETE = 'delete'
    FINALIZE = 'finalize'
    SET_FILTERS = 'set_filters'
    SUBMIT = 'submit'  # the default for many forms
    SUBMIT_TASKS_PER_PAGE = 'submit_tpp'
    REFRESH_TASKS = 'refresh_tasks'


class RequestMethod(object):
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
    # QUERY = "_query"  # built in to Pyramid
    ADDRESS = "address"
    ADD_SPECIAL_NOTE = "add_special_note"
    ADMIN = "admin"
    AGE_MINIMUM = "age_minimum"
    AGE_MAXIMUM = "age_maximum"
    ALL_TASKS = "all_tasks"
    ANONYMISE = "anonymise"
    CSRF_TOKEN = "csrf"
    DATABASE_TITLE = "database_title"
    DIALECT = "dialect"
    DIAGNOSES_INCLUSION = "diagnoses_inclusion"
    DIAGNOSES_EXCLUSION = "diagnoses_exclusion"
    DESCRIPTION = "description"
    DEVICE_ID = "device_id"
    DEVICE_IDS = "device_ids"
    DUMP_METHOD = "dump_method"
    DOB = "dob"
    EMAIL = "email"
    END_DATETIME = "end_datetime"
    FILENAME = "filename"
    FINALIZE_POLICY = "finalize_policy"
    FORENAME = "forename"
    FULLNAME = "fullname"
    GP = "gp"
    GROUPADMIN = "groupadmin"
    GROUP_ID = "group_id"
    GROUP_IDS = "group_ids"
    HL7_ID_TYPE = "hl7_id_type"
    HL7_ASSIGNING_AUTHORITY = "hl7_assigning_authority"
    HL7_MSG_ID = "hl7_msg_id"
    HL7_RUN_ID = "hl7_run_id"
    ID_DEFINITIONS = "id_definitions"
    ID_REFERENCES = "id_references"
    IDNUM_VALUE = "idnum_value"
    INCLUDE_BLOBS = "include_blobs"
    INCLUDE_CALCULATED = "include_calculated"
    INCLUDE_COMMENTS = "include_comments"
    INCLUDE_PATIENT = "include_patient"
    MANUAL = "manual"
    MAY_ADD_NOTES = "may_add_notes"
    MAY_DUMP_DATA = "may_dump_data"
    MAY_REGISTER_DEVICES = "may_register_devices"
    MAY_RUN_REPORTS = "may_run_reports"
    MAY_UPLOAD = "may_upload"
    MAY_USE_WEBVIEWER = "may_use_webviewer"
    MUST_CHANGE_PASSWORD = "must_change_password"
    NAME = "name"
    NOTE = "note"
    NEW_PASSWORD = "new_password"
    OLD_PASSWORD = "old_password"
    OTHER = "other"
    COMPLETE_ONLY = "complete_only"
    PAGE = "page"
    PASSWORD = "password"
    REDIRECT_URL = "redirect_url"
    REPORT_ID = "report_id"
    REMOTE_IP_ADDR = "remote_ip_addr"
    ROWS_PER_PAGE = "rows_per_page"
    SERVER_PK = "server_pk"
    SEX = "sex"
    SHORT_DESCRIPTION = "short_description"
    SORT = "sort"
    SOURCE = "source"
    SQLITE_METHOD = "sqlite_method"
    START_DATETIME = "start_datetime"
    SUPERUSER = "superuser"
    SURNAME = "surname"
    TABLE_NAME = "table_name"
    TASKS = "tasks"
    TEXT_CONTENTS = "text_contents"
    TRUNCATE = "truncate"
    UPLOAD_GROUP_ID = "upload_group_id"
    UPLOAD_POLICY = "upload_policy"
    USER_GROUP_MEMBERSHIP_ID = "user_group_membership_id"
    USER_ID = "user_id"
    USER_IDS = "user_ids"
    USERNAME = "username"
    VIEW_ALL_PATIENTS_WHEN_UNFILTERED = "view_all_patients_when_unfiltered"
    VIEWTYPE = "viewtype"
    WHICH_IDNUM = "which_idnum"
    WHAT = "what"
    WHEN = "when"
    WHO = "who"


class ViewArg(object):
    """
    String used as view arguments, e.g.
    """
    EVERYTHING = "everything"
    HTML = "html"
    PDF = "pdf"
    PDFHTML = "pdfhtml"
    SPECIFIC_TASKS_GROUPS = "specific_tasks_groups"
    SQL = "sql"
    SQLITE = "sqlite"
    TSV = "tsv"
    USE_SESSION_FILTER = "use_session_filter"
    XML = "xml"


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
        os.path.join(TEMPLATE_DIR, "test"),
    ],

    input_encoding="utf-8",
    output_encoding="utf-8",

    module_directory=DEBUGGING_MAKO_DIR if DEBUG_TEMPLATE_SOURCE else None,

    # -------------------------------------------------------------------------
    # TEMPLATE CACHING
    # -------------------------------------------------------------------------
    # http://dogpilecache.readthedocs.io/en/latest/api.html#module-dogpile.cache.plugins.mako_cache  # noqa
    # http://docs.makotemplates.org/en/latest/caching.html#cache-arguments

    cache_impl="dogpile.cache",
    cache_args={
        "regions": {"local": cache_region_static},
    },

    # Now, in Mako templates, use:
    #   cached="True" cache_region="local" cache_key="SOME_CACHE_KEY"
    # on <%page>, <%def>, and <%block> regions.
    # It is VITAL that you specify "name", and that it be appropriately
    # unique, or there'll be a cache conflict.
    # The easy way is:
    #   cached="True" cache_region="local" cache_key="${self.filename}"
    #                                                 ^^^^^^^^^^^^^^^^
    #                                                   No!
    # ... with ${self.filename} you can get an inheritance deadlock:
    # See https://bitbucket.org/zzzeek/mako/issues/269/inheritance-related-cache-deadlock-when  # noqa
    #
    # HOWEVER, note also: it is the CONTENT that is cached. You can cause some
    # right disasters with this. Only stuff producing entirely STATIC content
    # should be cached. "base.mako" isn't static - it calls back to its
    # children; and if you cache it, one request produces results for an
    # entirely different request. Similarly for lots of other things like
    # "task.mako".
    # SO, THERE IS NOT MUCH REASON HERE TO USE TEMPLATE CACHING.
)


class CamcopsMakoLookupTemplateRenderer(MakoLookupTemplateRenderer):
    """
    (a) load the Mako template
    (b) shove any other keys into its dictionary
    """
    def __call__(self, value: Dict[str, Any], system: Dict[str, Any]) -> str:
        if DEBUG_TEMPLATE_PARAMETERS:
            log.debug("spec: {!r}", self.spec)
            log.debug("value: {}", pprint.pformat(value))
            log.debug("system: {}", pprint.pformat(system))

        # ---------------------------------------------------------------------
        # RNC extra values:
        # ---------------------------------------------------------------------
        # Note that <%! ... %> Python blocks are not themselves inherited.
        # So putting "import" calls in base.mako doesn't deliver the following
        # as ever-present variable. Instead, plumb them in like this:
        #
        # system['Routes'] = Routes
        # system['ViewArg'] = ViewArg
        # system['ViewParam'] = ViewParam
        #
        # ... except that we're better off with an import in the template

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
            if DEBUG_TEMPLATE_PARAMETERS:
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


class UrlParamType(Enum):
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
    ADD_GROUP = "add_group"
    ADD_ID_DEFINITION = "add_id_definition"
    ADD_SPECIAL_NOTE = "add_special_note"
    ADD_USER = "add_user"
    BUGFIX_DEFORM_MISSING_GLYPHS = "bugfix_deform_missing_glyphs"
    # ... test by visiting the Task Filters page
    CHANGE_OWN_PASSWORD = "change_own_password"
    CHANGE_OTHER_PASSWORD = "change_other_password"
    CHOOSE_CTV = "choose_ctv"
    CHOOSE_TRACKER = "choose_tracker"
    CLIENT_API = "client_api"
    CRASH = "crash"
    CTV = "ctv"
    DELETE_GROUP = "delete_group"
    DELETE_ID_DEFINITION = "delete_id_definition"
    DELETE_PATIENT = "delete_patient"
    DELETE_USER = "delete_user"
    DEVELOPER = "developer"
    EDIT_GROUP = "edit_group"
    EDIT_ID_DEFINITION = "edit_id_definition"
    EDIT_PATIENT = "edit_patient"
    EDIT_SERVER_SETTINGS = "edit_server_settings"
    EDIT_USER = "edit_user"
    EDIT_USER_GROUP_MEMBERSHIP = "edit_user_group_membership"
    ERASE_TASK = "erase_task"
    FORCIBLY_FINALIZE = "forcibly_finalize"
    HOME = "home"
    INTROSPECT = "introspect"
    LOGIN = "login"
    LOGOUT = "logout"
    OFFER_AUDIT_TRAIL = "offer_audit_trail"
    OFFER_HL7_MESSAGE_LOG = "offer_hl7_message_log"
    OFFER_HL7_RUN_LOG = "offer_hl7_run_log"
    OFFER_INTROSPECTION = "offer_introspect"
    OFFER_REGENERATE_SUMMARIES = "offer_regenerate_summary_tables"
    OFFER_REPORT = "offer_report"
    OFFER_SQL_DUMP = "offer_sql_dump"
    OFFER_TERMS = "offer_terms"
    OFFER_TSV_DUMP = "offer_tsv_dump"
    REPORT = "report"
    REPORTS_MENU = "reports_menu"
    SET_FILTERS = "set_filters"
    SET_OWN_USER_UPLOAD_GROUP = "set_user_upload_group"
    SET_OTHER_USER_UPLOAD_GROUP = "set_other_user_upload_group"
    SQL_DUMP = "sql_dump"
    TASK = "task"
    TESTPAGE_PRIVATE_1 = "testpage_private_1"
    TESTPAGE_PRIVATE_2 = "testpage_private_2"
    TESTPAGE_PRIVATE_3 = "testpage_private_3"
    TESTPAGE_PUBLIC_1 = "testpage_public_1"
    TRACKER = "tracker"
    TSV_DUMP = "tsv_dump"
    UNLOCK_USER = "unlock_user"
    VIEW_OWN_USER_INFO = "view_own_user_info"
    VIEW_DDL = "inspect_ddl"
    VIEW_ALL_USERS = "view_all_users"
    VIEW_AUDIT_TRAIL = "view_audit_trail"
    VIEW_GROUPS = "view_groups"
    VIEW_HL7_MESSAGE = "view_hl7_message"
    VIEW_HL7_MESSAGE_LOG = "view_hl7_message_log"
    VIEW_HL7_RUN = "view_hl7_run"
    VIEW_HL7_RUN_LOG = "view_hl7_run_log"
    VIEW_ID_DEFINITIONS = "view_id_definitions"
    VIEW_USER = "view_user"
    VIEW_SERVER_INFO = "view_server_info"
    VIEW_TASKS = "view_tasks"


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


MASTER_ROUTE_WEBVIEW = "/"
MASTER_ROUTE_CLIENT_API = "/database"
STATIC_CAMCOPS_PACKAGE_PATH = "camcops_server.static:"
# ... the "static" package (directory with __init__.py) within the
# "camcops_server" owning package


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
    STATIC = RoutePath(Routes.STATIC, "",  # path ignored
                       ignore_in_all_routes=True)

    # Implemented
    ADD_GROUP = RoutePath(Routes.ADD_GROUP, "/add_group")
    ADD_ID_DEFINITION = RoutePath(Routes.ADD_ID_DEFINITION,
                                  "/add_id_definition")
    ADD_SPECIAL_NOTE = RoutePath(Routes.ADD_SPECIAL_NOTE, "/add_special_note")
    ADD_USER = RoutePath(Routes.ADD_USER, "/add_user")
    TSV_DUMP = RoutePath(Routes.TSV_DUMP, "/tsv_dump")
    BUGFIX_DEFORM_MISSING_GLYPHS = RoutePath(
        Routes.BUGFIX_DEFORM_MISSING_GLYPHS,
        "/deform_static/fonts/glyphicons-halflings-regular.woff2"
    )
    CHANGE_OWN_PASSWORD = RoutePath(Routes.CHANGE_OWN_PASSWORD,
                                    '/change_own_password')
    CHANGE_OTHER_PASSWORD = RoutePath(
        Routes.CHANGE_OTHER_PASSWORD,
        "/change_other_password"
        # make_url_path(
        #     "/change_other_password",
        #     UrlParam(ViewParam.USER_ID, UrlParamType.POSITIVE_INTEGER)
        # )
    )
    CHOOSE_CTV = RoutePath(Routes.CHOOSE_CTV, "/choose_clinicaltextview")
    CHOOSE_TRACKER = RoutePath(Routes.CHOOSE_TRACKER, "/choose_tracker")
    CRASH = RoutePath(Routes.CRASH, "/crash")
    CTV = RoutePath(Routes.CTV, "/ctv")
    CLIENT_API = RoutePath(Routes.CLIENT_API, MASTER_ROUTE_CLIENT_API)
    DELETE_GROUP = RoutePath(Routes.DELETE_GROUP, "/delete_group")
    DELETE_ID_DEFINITION = RoutePath(Routes.DELETE_ID_DEFINITION,
                                     "/delete_id_definition")
    DELETE_PATIENT = RoutePath(Routes.DELETE_PATIENT, "/delete_patient")
    DELETE_USER = RoutePath(Routes.DELETE_USER, "/delete_user")
    DEVELOPER = RoutePath(Routes.DEVELOPER, "/developer")
    EDIT_GROUP = RoutePath(Routes.EDIT_GROUP, "/edit_group")
    EDIT_ID_DEFINITION = RoutePath(Routes.EDIT_ID_DEFINITION,
                                   '/edit_id_definitions')
    EDIT_PATIENT = RoutePath(Routes.EDIT_PATIENT, '/edit_patient')
    EDIT_SERVER_SETTINGS = RoutePath(Routes.EDIT_SERVER_SETTINGS,
                                     '/edit_server_settings')
    EDIT_USER = RoutePath(Routes.EDIT_USER, "/edit_user")
    EDIT_USER_GROUP_MEMBERSHIP = RoutePath(Routes.EDIT_USER_GROUP_MEMBERSHIP,
                                           "/edit_user_group_membership")
    ERASE_TASK = RoutePath(Routes.ERASE_TASK, "/erase_task")
    FORCIBLY_FINALIZE = RoutePath(
        Routes.FORCIBLY_FINALIZE, "/forcibly_finalize"
    )
    HOME = RoutePath(Routes.HOME, MASTER_ROUTE_WEBVIEW)
    INTROSPECT = RoutePath(Routes.INTROSPECT, '/introspect')
    # ... filename via query param (sorts out escaping)
    LOGIN = RoutePath(Routes.LOGIN, "/login")
    LOGOUT = RoutePath(Routes.LOGOUT, "/logout")
    OFFER_AUDIT_TRAIL = RoutePath(Routes.OFFER_AUDIT_TRAIL,
                                  "/offer_audit_trail")
    OFFER_HL7_MESSAGE_LOG = RoutePath(Routes.OFFER_HL7_MESSAGE_LOG,
                                      "/offer_hl7_message_log")
    OFFER_HL7_RUN_LOG = RoutePath(Routes.OFFER_HL7_RUN_LOG,
                                  "/offer_hl7_run_log")
    OFFER_INTROSPECTION = RoutePath(Routes.OFFER_INTROSPECTION,
                                    "/offer_introspect")
    OFFER_REPORT = RoutePath(Routes.OFFER_REPORT, '/offer_report')
    OFFER_SQL_DUMP = RoutePath(Routes.OFFER_SQL_DUMP, "/offer_sql_dump")
    OFFER_TERMS = RoutePath(Routes.OFFER_TERMS, '/offer_terms')
    OFFER_TSV_DUMP = RoutePath(Routes.OFFER_TSV_DUMP, "/offer_tsv_dump")
    REPORT = RoutePath(Routes.REPORT, '/report')
    REPORTS_MENU = RoutePath(Routes.REPORTS_MENU, "/reports_menu")
    SET_FILTERS = RoutePath(Routes.SET_FILTERS, '/set_filters')
    SET_OWN_USER_UPLOAD_GROUP = RoutePath(Routes.SET_OWN_USER_UPLOAD_GROUP,
                                          '/set_user_upload_group')
    SET_OTHER_USER_UPLOAD_GROUP = RoutePath(Routes.SET_OTHER_USER_UPLOAD_GROUP,
                                            '/set_other_user_upload_group')
    SQL_DUMP = RoutePath(Routes.SQL_DUMP, '/sql_dump')
    TASK = RoutePath(Routes.TASK, "/task")
    TESTPAGE_PRIVATE_1 = RoutePath(Routes.TESTPAGE_PRIVATE_1, '/testpriv1')
    TESTPAGE_PRIVATE_2 = RoutePath(Routes.TESTPAGE_PRIVATE_2, '/testpriv2')
    TESTPAGE_PRIVATE_3 = RoutePath(Routes.TESTPAGE_PRIVATE_3, '/testpriv3')
    TESTPAGE_PUBLIC_1 = RoutePath(Routes.TESTPAGE_PUBLIC_1, '/test1')
    TRACKER = RoutePath(Routes.TRACKER, "/tracker")
    UNLOCK_USER = RoutePath(Routes.UNLOCK_USER, "/unlock_user")
    VIEW_ALL_USERS = RoutePath(Routes.VIEW_ALL_USERS, "/view_all_users")
    VIEW_AUDIT_TRAIL = RoutePath(Routes.VIEW_AUDIT_TRAIL, "/view_audit_trail")
    VIEW_DDL = RoutePath(Routes.VIEW_DDL, "/view_ddl")
    VIEW_GROUPS = RoutePath(Routes.VIEW_GROUPS, "/view_groups")
    VIEW_HL7_MESSAGE = RoutePath(Routes.VIEW_HL7_MESSAGE, "/view_hl7_message")
    VIEW_HL7_MESSAGE_LOG = RoutePath(Routes.VIEW_HL7_MESSAGE_LOG,
                                     "/view_hl7_message_log")
    VIEW_HL7_RUN = RoutePath(Routes.VIEW_HL7_RUN, "/view_hl7_run")
    VIEW_HL7_RUN_LOG = RoutePath(Routes.VIEW_HL7_RUN_LOG,
                                 "/view_hl7_run_log")
    VIEW_ID_DEFINITIONS = RoutePath(Routes.VIEW_ID_DEFINITIONS,
                                    "/view_id_definitions")
    VIEW_OWN_USER_INFO = RoutePath(Routes.VIEW_OWN_USER_INFO,
                                   "/view_own_user_info")
    VIEW_SERVER_INFO = RoutePath(Routes.VIEW_SERVER_INFO, "/view_server_info")
    VIEW_TASKS = RoutePath(Routes.VIEW_TASKS, "/view_tasks")
    VIEW_USER = RoutePath(Routes.VIEW_USER, "/view_user")

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
    
      .. code-block:: none
      
            sessionfactory(req: CamcopsRequest) -> session_object

      ... where session "is a namespace" [2]
      ... but more concretely, "implements the pyramid.interfaces.ISession 
      interface"

    - We want to be able to make the session by reading the CamcopsConfig from
      the request.

    [1] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session-factory
    
    [2] https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-session
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
        secure_cookies = not cfg.allow_insecure_cookies
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
    GROUPADMIN = "groupadmin"
    HAPPY = "happy"  # logged in, can use webview, no need to change p/w, agreed to terms  # noqa
    MUST_AGREE_TERMS = "must_agree_terms"
    MUST_CHANGE_PASSWORD = "must_change_password"
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
            if user.may_use_webviewer:
                if user.must_change_password:
                    principals.append(Permission.MUST_CHANGE_PASSWORD)
                elif user.must_agree_terms:
                    principals.append(Permission.MUST_AGREE_TERMS)
                else:
                    principals.append(Permission.HAPPY)
            if user.superuser:
                principals.append(Permission.SUPERUSER)
            if user.authorized_as_groupadmin:
                principals.append(Permission.GROUPADMIN)
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
    '[ $link_first $link_previous ~3~ $link_next $link_last ]'
)


class CamcopsPage(Page):
    # noinspection PyShadowingBuiltins
    def __init__(self,
                 collection: Union[Sequence[Any], Query, Select],
                 url_maker: Callable[[int], str],
                 page: int = 1,
                 items_per_page: int = 20,
                 item_count: int = None,
                 wrapper_class: Type[Any] = None,
                 ellipsis: str = "&hellip;",
                 **kwargs) -> None:
        # Bug in paginate: it slices its collection BEFORE it realizes that the
        # page number is out of range.
        # Also, it uses ".." for an ellipsis, which is just wrong.
        self.ellipsis = ellipsis
        page = max(1, page)
        if item_count is None:
            if wrapper_class:
                item_count = len(wrapper_class(collection))
            else:
                item_count = len(collection)
        n_pages = ((item_count - 1) // items_per_page) + 1
        page = min(page, n_pages)
        super().__init__(
            collection=collection,
            page=page,
            items_per_page=items_per_page,
            item_count=item_count,
            wrapper_class=wrapper_class,
            url_maker=url_maker,
            **kwargs
        )
        # Original defines attributes outside __init__, so:
        self.radius = 2
        self.curpage_attr = {}  # type: Dict[str, str]
        self.separator = ""
        self.link_attr = {}  # type: Dict[str, str]
        self.dotdot_attr = {}  # type: Dict[str, str]
        self.url = ""

    # noinspection PyShadowingBuiltins
    def pager(self,
              format: str = PAGER_PATTERN,
              url: str = None,
              show_if_single_page: bool = True,  # see below!
              separator: str = ' ',
              symbol_first: str = '&lt;&lt;',
              symbol_last: str = '&gt;&gt;',
              symbol_previous: str = '&lt;',
              symbol_next: str = '&gt;',
              link_attr: Dict[str, str] = None,
              curpage_attr: Dict[str, str] = None,
              dotdot_attr: Dict[str, str] = None,
              link_tag: Callable[[Dict[str, str]], str] = None):
        # The reason for the default for 'show_if_single_page' being True is
        # that it's possible otherwise to think you've lost your tasks. For
        # example: (1) have 99 tasks; (2) view 50/page; (3) go to page 2;
        # (4) set number per page to 100. Or simply use the URL to go beyond
        # the end.
        link_attr = link_attr or {}  # type: Dict[str, str]
        curpage_attr = curpage_attr or {}  # type: Dict[str, str]
        # dotdot_attr = dotdot_attr or {}  # type: Dict[str, str]
        # dotdot_attr = dotdot_attr or {'class': 'pager_dotdot'}  # our default!
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

    # noinspection PyShadowingBuiltins
    def link_map(self,
                 format: str = '~2~',
                 url: str = None,
                 show_if_single_page: bool = False,
                 separator: str = ' ',
                 symbol_first: str = '&lt;&lt;',
                 symbol_last: str ='&gt;&gt;',
                 symbol_previous: str = '&lt;',
                 symbol_next: str='&gt;',
                 link_attr: Dict[str, str] = None,
                 curpage_attr: Dict[str, str] = None,
                 dotdot_attr: Dict[str, str] = None):
        """
        Fixes bugs (e.g. mutable default arguments) and nasties (e.g.
        enforcing ".." for the ellipsis) in the original.
        """
        self.curpage_attr = curpage_attr or {}  # type: Dict[str, str]
        self.separator = separator
        self.link_attr = link_attr or {}  # type: Dict[str, str]
        self.dotdot_attr = dotdot_attr or {}  # type: Dict[str, str]
        self.url = url

        regex_res = re.search(r'~(\d+)~', format)
        if regex_res:
            radius = regex_res.group(1)
        else:
            radius = 2
        radius = int(radius)
        self.radius = radius

        # Compute the first and last page number within the radius
        # e.g. '1 .. 5 6 [7] 8 9 .. 12'
        # -> leftmost_page  = 5
        # -> rightmost_page = 9
        leftmost_page = (
            max(self.first_page, (self.page - radius))
            if self.first_page else None
        )
        rightmost_page = (
            min(self.last_page, (self.page+radius))
            if self.last_page else None
        )
        nav_items = {
            "first_page": None,
            "last_page": None,
            "previous_page": None,
            "next_page": None,
            "current_page": None,
            "radius": self.radius,
            "range_pages": []
        }  # type: Dict[str, Any]

        if leftmost_page is None or rightmost_page is None:
            return nav_items

        nav_items["first_page"] = {
            "type": "first_page",
            "value": symbol_first,
            "attrs": self.link_attr,
            "number": self.first_page,
            "href": self.url_maker(self.first_page)
        }

        # Insert dots if there are pages between the first page
        # and the currently displayed page range
        if leftmost_page - self.first_page > 1:
            # Wrap in a SPAN tag if dotdot_attr is set
            nav_items["range_pages"].append({
                "type": "span",
                "value": self.ellipsis,
                "attrs": self.dotdot_attr,
                "href": "",
                "number": None
            })

        for thispage in range(leftmost_page, rightmost_page + 1):
            # Highlight the current page number and do not use a link
            if thispage == self.page:
                # Wrap in a SPAN tag if curpage_attr is set
                nav_items["range_pages"].append({
                    "type": "current_page",
                    "value": str(thispage),
                    "number": thispage,
                    "attrs": self.curpage_attr,
                    "href": self.url_maker(thispage)
                })
                nav_items["current_page"] = {
                    "value": thispage,
                    "attrs": self.curpage_attr,
                    "type": "current_page",
                    "href": self.url_maker(thispage)
                }
            # Otherwise create just a link to that page
            else:
                nav_items["range_pages"].append({
                    "type": "page",
                    "value": str(thispage),
                    "number": thispage,
                    "attrs": self.link_attr,
                    "href": self.url_maker(thispage)
                })

        # Insert dots if there are pages between the displayed
        # page numbers and the end of the page range
        if self.last_page - rightmost_page > 1:
            # Wrap in a SPAN tag if dotdot_attr is set
            nav_items["range_pages"].append({
                "type": "span",
                "value": self.ellipsis,
                "attrs": self.dotdot_attr,
                "href": "",
                "number": None
            })

        # Create a link to the very last page (unless we are on the last
        # page or there would be no need to insert '..' spacers)
        nav_items["last_page"] = {
            "type": "last_page",
            "value": symbol_last,
            "attrs": self.link_attr,
            "href": self.url_maker(self.last_page),
            "number": self.last_page
        }
        nav_items["previous_page"] = {
            "type": "previous_page",
            "value": symbol_previous,
            "attrs": self.link_attr,
            "number": self.previous_page or self.first_page,
            "href": self.url_maker(self.previous_page or self.first_page)
        }
        nav_items["next_page"] = {
            "type": "next_page",
            "value": symbol_next,
            "attrs": self.link_attr,
            "number": self.next_page or self.last_page,
            "href": self.url_maker(self.next_page or self.last_page)
        }
        return nav_items


class SqlalchemyOrmPage(CamcopsPage):
    """A pagination page that deals with SQLAlchemy ORM objects."""
    def __init__(self,
                 query: Query,
                 url_maker: Callable[[int], str],
                 page: int = 1,
                 items_per_page: int = DEFAULT_ROWS_PER_PAGE,
                 item_count: int = None,
                 **kwargs) -> None:
        # Since views may accidentally throw strings our way:
        assert isinstance(page, int)
        assert isinstance(items_per_page, int)
        assert isinstance(item_count, int) or item_count is None
        super().__init__(
            collection=query,
            page=page,
            items_per_page=items_per_page,
            item_count=item_count,
            wrapper_class=SqlalchemyOrmQueryWrapper,
            url_maker=url_maker,
            **kwargs
        )


# From webhelpers.paginate (which is broken on Python 3.5, but good),
# modified a bit:

def make_page_url(path: str, params: Dict[str, str], page: int,
                  partial: bool = False, sort: bool = True) -> str:
    """
    A helper function for URL generators.

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
    """
    A page URL generator for WebOb-compatible Request objects.

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


# =============================================================================
# Debugging requests and responses
# =============================================================================

def get_body_from_request(req: Request) -> bytes:
    log.warning("Attempting to read body from request -- but a previous read "
                "may have left this empty. Consider using Wireshark!")
    wsgi_input = req.environ[WsgiEnvVar.WSGI_INPUT]
    # ... under gunicorn, is an instance of gunicorn.http.body.Body
    return wsgi_input.read()


class HTTPFoundDebugVersion(HTTPFound):
    """
    For debugging redirections.
    """
    def __init__(self, location: str = '', **kwargs) -> None:
        log.debug("Redirecting to {!r}", location)
        super().__init__(location, **kwargs)
