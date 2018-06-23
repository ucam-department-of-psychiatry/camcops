#!/usr/bin/env python
# camcops_server/cc_modules/cc_client_api_core.py

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

from typing import Any, Dict, List


# =============================================================================
# Constants
# =============================================================================

class TabletParam(object):
    """
    Keys used by server or client (S server, C client, B bidirectional)
    """
    CAMCOPS_VERSION = "camcops_version"  # C->S
    DATABASE_TITLE = "databaseTitle"  # S->C
    DATEVALUES = "datevalues"  # C->S
    DEVICE = "device"  # C->S
    DEVICE_FRIENDLY_NAME = "devicefriendlyname"  # C->S
    ERROR = "error"   # S->C
    FIELDS = "fields"  # B
    ID_DESCRIPTION_PREFIX = "idDescription"  # S->C
    ID_POLICY_FINALIZE = "idPolicyFinalize"  # S->C
    ID_POLICY_UPLOAD = "idPolicyUpload"  # S->C
    ID_SHORT_DESCRIPTION_PREFIX = "idShortDescription"  # S->C
    NFIELDS = "nfields"  # B
    NRECORDS = "nrecords"  # B
    OPERATION = "operation"  # C->S
    PASSWORD = "password"  # C->S
    PKNAME = "pkname"  # C->S
    PKVALUES = "pkvalues"  # C->S
    RECORD_PREFIX = "record"  # B
    RESULT = "result"   # S->C
    SERVER_CAMCOPS_VERSION = "serverCamcopsVersion"  # S->C
    SESSION_ID = "session_id"   # B
    SESSION_TOKEN = "session_token"   # B
    SUCCESS = "success"   # S->C
    TABLE = "table"  # C->S
    TABLES = "tables"  # C->S
    USER = "user"  # C->S
    VALUES = "values"  # C->S
    # Retired (part of defunct mobileweb interface):
    # WHEREFIELDS = "wherefields"
    # WHERENOTFIELDS = "wherenotfields"
    # WHERENOTVALUES = "wherenotvalues"
    # WHEREVALUES = "wherevalues"


class ExtraStringFieldNames(object):
    """
    To match extrastring.cpp on the tablet.
    """
    TASK = "task"
    NAME = "name"
    VALUE = "value"


class AllowedTablesFieldNames(object):
    """
    To match allowedservertable.cpp on the tablet
    """
    TABLENAME = "tablename"
    MIN_CLIENT_VERSION = "min_client_version"


# =============================================================================
# Exceptions used by client API
# =============================================================================
# Note the following about exception strings:
#
# class Blah(Exception):
#     pass
#
# x = Blah("hello")
# str(x)  # 'hello'

class UserErrorException(Exception):
    """
    Exception class for when the input from the tablet is dodgy.
    """
    pass


class ServerErrorException(Exception):
    """
    Exception class for when something's broken on the server side.
    """
    pass


class IgnoringAntiqueTableException(Exception):
    """
    Special exception to return success when we're ignoring an old tablet's
    request to upload the "storedvars" table.
    """
    pass


# =============================================================================
# Return message functions
# =============================================================================

def exception_description(e: Exception) -> str:
    return "{t}: {m}".format(t=type(e).__name__, m=str(e))


# NO LONGER USED:
# def succeed_generic(operation: str) -> str:
#     """
#     Generic success message to tablet.
#     """
#     return "CamCOPS: {}".format(operation)


def fail_user_error(msg: str) -> None:
    """
    Function to abort the script when the input is dodgy.
    """
    # While Titanium-Android can extract error messages from e.g.
    # finish("400 Bad Request: @_"), Titanium-iOS can't, and we need the error
    # messages. Therefore, we will return an HTTP success code but "Success: 0"
    # in the reply details.
    raise UserErrorException(msg)


def require_keys(dictionary: Dict[Any, Any], keys: List[Any]) -> None:
    for k in keys:
        if k not in dictionary:
            fail_user_error("Field {} missing in client input".format(repr(k)))


def fail_user_error_from_exception(e: Exception) -> None:
    fail_user_error(exception_description(e))


def fail_server_error(msg: str) -> None:
    """
    Function to abort the script when something's broken server-side.
    """
    raise ServerErrorException(msg)


def fail_server_error_from_exception(e: Exception) -> None:
    fail_server_error(exception_description(e))


def fail_unsupported_operation(operation: str) -> None:
    """
    Abort the script when the operation is invalid.
    """
    fail_user_error("operation={}: not supported".format(operation))
