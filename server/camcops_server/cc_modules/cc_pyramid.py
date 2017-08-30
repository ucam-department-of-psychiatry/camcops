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
import re
import sys
from typing import Any, Dict, List

from mako.lookup import TemplateLookup
from pyramid.config import Configurator
from pyramid_mako import (
    MakoLookupTemplateRenderer,
    MakoRendererFactory,
    MakoRenderingException,
    reraise,
    text_error_template,
)

from .cc_baseconstants import TEMPLATE_DIR
from .cc_cache import cache_region_static

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

COOKIE_NAME = 'camcops'


class CookieKeys:
    SESSION_ID = 'session_id'
    SESSION_TOKEN = 'session_token'


class Methods:
    GET = "GET"
    POST = "POST"


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
)


class CamcopsMakoLookupTemplateRenderer(MakoLookupTemplateRenderer):
    def __call__(self, value: Dict[str, Any], system: Dict[str, Any]) -> str:
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
        try:
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
                del exc_info

        return result


class CamcopsMakoRendererFactory(MakoRendererFactory):
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
    parts = [base] + [arg.markerdef() for arg in args]
    return "/" + "/".join(parts)


# =============================================================================
# Routes
# =============================================================================

# Class to collect constants together
# See also http://xion.io/post/code/python-enums-are-ok.html
class Routes(object):
    # Hard-coded special paths
    STATIC = "static"

    # Implemented
    CHANGE_PASSWORD = "change_password"
    CHOOSE_CLINICALTEXTVIEW = "choose_clinicaltextview"
    CHOOSE_TRACKER = "choose_tracker"
    DATABASE_API = "database"
    DELETE_PATIENT = "delete_patient"
    FORCIBLY_FINALIZE = "forcibly_finalize"
    HOME = "home"
    INSPECT_TABLE_DEFS = "view_table_definitions"
    INSPECT_TABLE_VIEW_DEFS = "view_table_and_view_definitions"
    LOGOUT = "logout"
    MANAGE_USERS = "manage_users"
    OFFER_AUDIT_TRAIL_OPTIONS = "offer_audit_trail_options"
    OFFER_BASIC_DUMP = "offer_basic_dump"
    OFFER_HL7_LOG_OPTIONS = "offer_hl7_log"
    OFFER_HL7_RUN_OPTIONS = "offer_hl7_run"
    OFFER_INTROSPECTION = "offer_introspect"
    OFFER_REGENERATE_SUMMARIES = "offer_regenerate_summary_tables"
    OFFER_TABLE_DUMP = "offer_table_dump"
    OFFER_TERMS = "offer_terms"
    TESTPAGE = "testpage"
    VIEW_POLICIES = "view_policies"
    VIEW_TASKS = "view_tasks"

    # To implement ***
    ADD_SPECIAL_NOTE = "add_special_note"
    ADD_USER = "add_user"
    AGREE_TERMS = "agree_terms"
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
    INTROSPECT = "introspect"
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
    VIEW_AUDIT_TRAIL = "view_audit_trail"
    VIEW_HL7_LOG = "view_hl7_log"
    VIEW_HL7_RUN = "view_hl7_run"


class ViewParams(object):
    """
    Used as parameter placeholders in URLs, and fetched from the matchdict.
    """
    PK = 'pk'
    PATIENT_ID = 'pid'
    QUERY = '_query'  # built in to Pyramid
    USERNAME = 'username'


class QueryParams(object):
    """
    Parameters for the request.GET dictionary, and in URL as '...?key=value'
    """
    SORT = 'sort'


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
    CHANGE_PASSWORD = RoutePath(
        Routes.CHANGE_PASSWORD,
        make_url_path(
            "/change_password",
            UrlParam(ViewParams.USERNAME, UrlParamType.PLAIN_STRING)
        )
    )
    DATABASE_API = RoutePath(Routes.DATABASE_API, '/database')
    HOME = RoutePath(Routes.HOME, '/webview')
    OFFER_TERMS = RoutePath(Routes.OFFER_TERMS, '/offer_terms')
    TESTPAGE = RoutePath(Routes.TESTPAGE, '/testpage')

    # To implement ***
    ADD_SPECIAL_NOTE = RoutePath(Routes.ADD_SPECIAL_NOTE, "/add_special_note")
    ADD_USER = RoutePath(Routes.ADD_USER, "/add_user")
    AGREE_TERMS = RoutePath(Routes.AGREE_TERMS, "/agree_terms")
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
    INTROSPECT = RoutePath(Routes.INTROSPECT, "/introspect")
    LAST_PAGE = RoutePath(Routes.LAST_PAGE, "/last_page")
    LOGIN = RoutePath(Routes.LOGIN, "/login")
    LOGOUT = RoutePath(Routes.LOGOUT, "/logout")
    # now HOME # MAIN_MENU = "main_menu"
    MANAGE_USERS = RoutePath(Routes.MANAGE_USERS, "/manage_users")
    NEXT_PAGE = RoutePath(Routes.NEXT_PAGE, "/next_page")
    OFFER_AUDIT_TRAIL_OPTIONS = RoutePath(
        Routes.OFFER_AUDIT_TRAIL_OPTIONS, "/offer_audit_trail_options"
    )
    OFFER_BASIC_DUMP = RoutePath(Routes.OFFER_BASIC_DUMP, "/offer_basic_dump")
    OFFER_HL7_LOG_OPTIONS = RoutePath(
        Routes.OFFER_HL7_LOG_OPTIONS, "/offer_hl7_log"
    )
    OFFER_HL7_RUN_OPTIONS = RoutePath(
        Routes.OFFER_HL7_RUN_OPTIONS, "/offer_hl7_run"
    )
    OFFER_INTROSPECTION = RoutePath(
        Routes.OFFER_INTROSPECTION, "/offer_introspect"
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
    VIEW_AUDIT_TRAIL = RoutePath(Routes.VIEW_AUDIT_TRAIL, "/view_audit_trail")
    VIEW_HL7_LOG = RoutePath(Routes.VIEW_HL7_LOG, "/view_hl7_log")
    VIEW_HL7_RUN = RoutePath(Routes.VIEW_HL7_RUN, "/view_hl7_run")
    VIEW_POLICIES = RoutePath(Routes.VIEW_POLICIES, "/view_policies")
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
