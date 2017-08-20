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
import re
from typing import List


# =============================================================================
# Constants
# =============================================================================

COOKIE_NAME = 'camcops'


class CookieKeys:
    SESSION_ID = 'session_id'
    SESSION_TOKEN = 'session_token'


# =============================================================================
# Helpers
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
        assert valid_replacement_marker(name)

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
    assert valid_replacement_marker(base)
    parts = [base] + [arg.markerdef() for arg in args]
    return "/" + "/".join(parts)


# =============================================================================
# Routes
# =============================================================================

# Class to collect constants together
# See also http://xion.io/post/code/python-enums-are-ok.html
class Routes(object):
    HOME = "home"


class ViewParams(object):
    """
    Used as parameter placeholders in URLs, and fetched from the matchdict.
    """
    PK = 'pk'
    PATIENT_ID = 'pid'
    QUERY = '_query'  # built in to Pyramid


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
    def __init__(self, route: str, path: str) -> None:
        self.route = route
        self.path = path


class RouteCollection(object):
    """
    All routes, with their paths, for CamCOPS.

    To make a URL on the fly, use Request.route_url() or
    CamcopsRequest.route_url_params().

    To associate a view with a route, use the Pyramid @view_config decorator.
    """
    DEBUG_TOOLBAR = RoutePath('debug_toolbar', '/_debug_toolbar/')  # hard-coded path  # noqa

    HOME = RoutePath(Routes.HOME, '/')
    OTHER = RoutePath('other', '/other')
    VIEW_WITH_PARAMS = RoutePath(
        'vwp',
        make_url_path(
            'vwp',
            UrlParam(ViewParams.PATIENT_ID, UrlParamType.POSITIVE_INTEGER),
            UrlParam(ViewParams.PK, UrlParamType.POSITIVE_INTEGER)
        )
    )

    @classmethod
    def all_routes(cls) -> List[RoutePath]:
        """
        Fetch all routes.
        """
        return [v for k, v in cls.__dict__.items()
                if not (k.startswith('_') or  # class hidden things
                        k == 'all_routes' or  # this function
                        k == 'DEBUG_TOOLBAR')]  # hard-coded/invisible
