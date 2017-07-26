#!/usr/bin/env python
# database.py

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

# =============================================================================
# Imports
# =============================================================================

import cgi
import datetime
import logging
import re
import time
from typing import (Any, Callable, Dict, Iterable, List,
                    Optional, Sequence, Tuple, Type)

import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.rnc_web import HEADERS_TYPE

from .cc_modules.cc_dt import format_datetime
from .cc_modules import cc_audit
from .cc_modules.cc_session import establish_session_for_tablet
from .cc_modules.cc_string import get_all_extra_strings
from .cc_modules.cc_version import (
    CAMCOPS_SERVER_VERSION,
    FIRST_TABLET_VER_WITH_SEPARATE_IDNUM_TABLE,
    FIRST_TABLET_VER_WITHOUT_IDDESC_IN_PT_TABLE,
    MINIMUM_TABLET_VERSION,
)
from .cc_modules.cc_audit import SECURITY_AUDIT_TABLENAME
from .cc_modules.cc_constants import (
    CLIENT_DATE_FIELD,
    DATEFORMAT,
    ERA_NOW,
    FP_ID_NUM,
    FP_ID_DESC,
    FP_ID_SHORT_DESC,
    HL7MESSAGE_TABLENAME,
    MOVE_OFF_TABLET_FIELD,
    NUMBER_OF_IDNUMS_DEFUNCT,  # allowed; for old tablet versions
    STANDARD_GENERIC_FIELDSPECS
)
from .cc_modules.cc_convert import (
    decode_values,
    delimit,
    encode_single_value,
    escape_newlines,
    special_base64_encode,
    special_hex_encode,
    unescape_newlines,
)
from .cc_modules.cc_device import Device, get_device_by_name
from .cc_modules.cc_hl7 import HL7Run
from .cc_modules.cc_patient import Patient
from .cc_modules.cc_patientidnum import PatientIdNum
from .cc_modules.cc_pls import pls
from .cc_modules.cc_session import Session
from .cc_modules.cc_specialnote import SpecialNote
from .cc_modules.cc_storedvar import ServerStoredVar
from .cc_modules.cc_unittest import (
    unit_test_ignore,
    unit_test_must_raise,
    unit_test_verify
)
from .cc_modules.cc_user import (
    get_user_by_name,
    SECURITY_ACCOUNT_LOCKOUT_TABLENAME,
    SECURITY_LOGIN_FAILURE_TABLENAME,
    User,
)
from .cc_modules.cc_version import make_version

log = logging.getLogger(__name__)

# =============================================================================
# Debugging options
# =============================================================================

# Report profiling information to the HTTPD log? (Adds overhead; do not enable
# for production systems.)
PROFILE = False

# =============================================================================
# Constants
# =============================================================================

COPE_WITH_DELETED_PATIENT_DESCRIPTIONS = True
# ... as of client 2.0.0, ID descriptions are no longer duplicated.
# As of server 2.0.0, the fields still exist in the database, but the reporting
# and consistency check has been removed. In the next version of the server,
# the fields will be removed, and then the server should cope with old clients,
# at least for a while.

CONTENTTYPE = 'text/plain; charset=utf-8'
DUPLICATE_FAILED = "Failed to duplicate record"
INSERT_FAILED = "Failed to insert record"
INVALID_USERNAME_PASSWORD = "Invalid username/password"
REGEX_INVALID_TABLE_FIELD_CHARS = re.compile("[^a-zA-Z0-9_]")
# ... the ^ within the [] means the expression will match any character NOT in
# the specified range

# System tables without a class representation:
DIRTY_TABLES_TABLENAME = "_dirty_tables"
DIRTY_TABLES_FIELDSPECS = [
    dict(name="device_id", cctype="DEVICE",
         comment="Source tablet device ID"),
    dict(name="tablename", cctype="TABLENAME",
         comment="Table in the process of being preserved"),
]

RESERVED_TABLES = [
    DIRTY_TABLES_TABLENAME,
    HL7MESSAGE_TABLENAME,
    HL7Run.TABLENAME,
    SECURITY_ACCOUNT_LOCKOUT_TABLENAME,
    SECURITY_AUDIT_TABLENAME,
    Device.TABLENAME,
    SECURITY_LOGIN_FAILURE_TABLENAME,
    User.TABLENAME,
    Session.TABLENAME,
    ServerStoredVar.TABLENAME,
    SpecialNote.TABLENAME,
]
RESERVED_FIELDS = [
    x["name"] for x in STANDARD_GENERIC_FIELDSPECS
    if x["name"] not in [MOVE_OFF_TABLET_FIELD, CLIENT_DATE_FIELD]
]


class PARAM(object):
    CAMCOPS_VERSION = "camcops_version" 
    DATEVALUES = "datevalues" 
    DEVICE = "device" 
    FIELDS = "fields" 
    NRECORDS = "nrecords" 
    OPERATION = "operation" 
    PASSWORD = "password" 
    PKNAME = "pkname" 
    PKVALUES = "pkvalues" 
    RESULT = "result"   # server to tablet
    SESSION_ID = "session_id"   # bidirectional
    SESSION_TOKEN = "session_token"   # bidirectional
    SUCCESS = "success"   # server to tablet
    ERROR = "error"   # server to tablet
    TABLE = "table" 
    TABLES = "tables" 
    USER = "user" 
    WHEREFIELDS = "wherefields" 
    WHERENOTFIELDS = "wherenotfields" 
    WHERENOTVALUES = "wherenotvalues" 
    WHEREVALUES = "wherevalues" 
    VALUES = "values" 


# =============================================================================
# Return message functions/exceptions
# =============================================================================

class UserErrorException(Exception):
    """Exception class for when the input from the tablet is dodgy."""
    pass


class ServerErrorException(Exception):
    """Exception class for when something's broken on the server side."""
    pass


def exception_description(e: Exception) -> str:
    return "{t}: {m}".format(t=type(e).__name__, m=str(e))


def succeed_generic(operation: str) -> str:
    """Generic success message to tablet."""
    return "CamCOPS: {}".format(operation)


def fail_user_error(msg: str) -> None:
    """Function to abort the script when the input is dodgy."""
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
    """Function to abort the script when something's broken server-side."""
    raise ServerErrorException(msg)


def fail_server_error_from_exception(e: Exception) -> None:
    fail_server_error(exception_description(e))


def fail_unsupported_operation(operation: str) -> None:
    """Abort the script when the operation is invalid."""
    fail_user_error("operation={}: not supported".format(operation))


# =============================================================================
# CGI handling
# =============================================================================

class SessionManager(object):
    def __init__(self, form: cgi.FieldStorage) -> None:
        # Read key things
        self.form = form
        self.operation = ws.get_cgi_parameter_str(form, PARAM.OPERATION)
        self.device_name = ws.get_cgi_parameter_str(form, PARAM.DEVICE)
        self.username = ws.get_cgi_parameter_str(form, PARAM.USER)
        self.password = ws.get_cgi_parameter_str(form, PARAM.PASSWORD)
        self.session_id = ws.get_cgi_parameter_int(form, PARAM.SESSION_ID)
        self.session_token = ws.get_cgi_parameter_str(form,
                                                      PARAM.SESSION_TOKEN)
        self.tablet_version_str = ws.get_cgi_parameter_str(
            form, PARAM.CAMCOPS_VERSION)
        self.tablet_version_ver = make_version(self.tablet_version_str)
        # Look up device and user
        self._device_obj = get_device_by_name(self.device_name)
        self._user_obj = get_user_by_name(self.username)

        # Ensure table version is OK
        if self.tablet_version_ver < MINIMUM_TABLET_VERSION:  # noqa
            fail_user_error(
                "Tablet CamCOPS version too old: is {v}, need {r}".format(
                    v=self.tablet_version_str,
                    r=MINIMUM_TABLET_VERSION))
        # Other version things
        self.cope_with_deleted_patient_descriptors = (
            self.tablet_version_ver <
            FIRST_TABLET_VER_WITHOUT_IDDESC_IN_PT_TABLE)
        self.cope_with_old_idnums = (
            self.tablet_version_ver <
            FIRST_TABLET_VER_WITH_SEPARATE_IDNUM_TABLE)

        # Establish session
        establish_session_for_tablet(self.session_id, self.session_token,
                                     pls.remote_addr,
                                     self.username, self.password)
        # Report
        log.info(
            "Incoming connection from IP={i}, port={p}, device_name={dn}, "
            "device_id={di}, user={u}, operation={o}".format(
                i=pls.remote_addr,
                p=pls.remote_port,
                dn=self.device_name,
                di=self.device_id,
                u=self.username,
                o=self.operation,
            )
        )

    @property
    def device_id(self) -> Optional[int]:
        if not self._device_obj:
            return None
        return self._device_obj.get_id()

    @property
    def user_id(self) -> Optional[int]:
        if self._user_obj is None:
            return None
        return self._user_obj.get_id()

    def is_device_registered(self) -> bool:
        return self._device_obj is not None

    def reload_device(self):
        self._device_obj = get_device_by_name(self.device_name)

    def ensure_device_registered(self) -> None:
        """
        Ensure the device is registered. Raises UserErrorException on failure.
        """
        if not self.is_device_registered():
            fail_user_error("Unregistered device")

    def ensure_valid_device_and_user_for_uploading(self) -> None:
        """
        Ensure the device/username/password combination is valid for uploading.
        Raises UserErrorException on failure.
        """
        if not pls.session.authorized_to_upload():
            fail_user_error(INVALID_USERNAME_PASSWORD)
        # Username/password combination found and is valid. Now check device.
        self.ensure_device_registered()

    def ensure_valid_user_for_webstorage(self) -> None:
        """
        Ensure the username/password combination is valid for mobileweb storage
        access. Raises UserErrorException on failure.
        """
        # mobileweb storage is per-user; the device is "mobileweb_USERNAME".
        if self.device_name != "mobileweb_" + self.username:
            fail_user_error("Mobileweb device doesn't match username")
        if not pls.session.authorized_for_webstorage():
            fail_user_error(INVALID_USERNAME_PASSWORD)
        # otherwise, happy

    @staticmethod
    def ensure_valid_user_for_device_registration() -> None:
        """
        Ensure the username/password combination is valid for device
        registration. Raises UserErrorException on failure.
        """
        if not pls.session.authorized_for_registration():
            fail_user_error(INVALID_USERNAME_PASSWORD)


def get_post_var(form: cgi.FieldStorage,
                 var: str,
                 mandatory: bool = True,
                 valtype: Type[Any] = None) -> Any:
    """Retrieves a variable from a CGI form.

    Args:
        form: CGI form
        var: variable to retrieve
        mandatory: if True, script aborts if variable missing
        valtype: if not None, valtype() is performed on the result -- for
            example, valtype=int will perform conversion to int.
    Returns:
        value
    """
    val = ws.get_cgi_parameter_str_or_none(form, var)
    if mandatory and val is None:
        fail_user_error("Must provide the variable: {}".format(var))
    if valtype is not None:
        try:
            val = valtype(val)
        except (TypeError, ValueError):
            fail_user_error("Variable {} is of invalid type".format(var))
    return val


def get_table_from_post_var(form: cgi.FieldStorage, var: str) -> str:
    """Retrieves a table name from a CGI form and checks it's a valid
    table."""
    table = get_post_var(form, var, mandatory=True)
    ensure_valid_table_name(table)
    return table


def get_single_field_from_post_var(form: cgi.FieldStorage,
                                   var: str,
                                   mandatory: bool = True) -> str:
    """Retrieves a field name from a CGI form and checks it's not a bad
    fieldname."""
    field = get_post_var(form, var, mandatory=mandatory)
    ensure_valid_field_name(field)
    return field


def get_fields_from_post_var(form: cgi.FieldStorage,
                             var: str,
                             mandatory: bool = True) -> List[str]:
    """Get a comma-separated list of field names from a CGI and checks that
    all are acceptable. Returns a list of fieldnames."""
    csfields = get_post_var(form, var, mandatory=mandatory)
    if not csfields:
        return []
    # can't have any commas in fields, so it's OK to use a simple
    # split() command
    fields = [x.strip() for x in csfields.split(",")]
    for f in fields:
        ensure_valid_field_name(f)
    # log.debug("get_fields_from_post_var: fields={}".format(fields))
    return fields


def get_values_from_post_var(form: cgi.FieldStorage,
                             var: str,
                             mandatory: bool = True) -> List[Any]:
    """Retrieves a list of values from a CSV-separated list of SQL values
    stored in a CGI form (including e.g. NULL, numbers, quoted strings, and
    special handling for base-64/hex-encoded BLOBs.)"""
    csvalues = get_post_var(form, var, mandatory=mandatory)
    if not csvalues:
        return []
    return decode_values(csvalues)


def get_fields_and_values(form: cgi.FieldStorage,
                          fields_var: str,
                          values_var: str,
                          mandatory: bool = True) -> Dict[str, Any]:
    """Gets fieldnames and matching values from two variables in a CGI form."""
    fields = get_fields_from_post_var(form, fields_var, mandatory=mandatory)
    values = get_values_from_post_var(form, values_var, mandatory=mandatory)
    if len(fields) != len(values):
        fail_user_error(
            "Number of fields ({f}) doesn't match number of values "
            "({v})".format(
                f=len(fields),
                v=len(values),
            )
        )
    return dict(list(zip(fields, values)))


def get_tables_from_post_var(form: cgi.FieldStorage,
                             var: str,
                             mandatory: bool = True) -> List[str]:
    """Gets a list of tables from a CGI form variable, and ensures all are
    valid."""
    cstables = get_post_var(form, var, mandatory=mandatory)
    if not cstables:
        return []
    # can't have any commas in table names, so it's OK to use a simple
    # split() command
    tables = [x.strip() for x in cstables.split(",")]
    for t in tables:
        ensure_valid_table_name(t)
    return tables


# =============================================================================
# Validators
# =============================================================================

def ensure_valid_table_name(t: str) -> None:
    """Ensures a table name doesn't contain bad characters, isn't a reserved
    table that the user is prohibited from accessing, and is a valid table name
    that's in the database. Raises UserErrorException upon failure."""
    if bool(REGEX_INVALID_TABLE_FIELD_CHARS.search(t)):
        fail_user_error("Table name contains invalid characters: {}".format(t))
    if t in RESERVED_TABLES:
        fail_user_error(
            "Invalid attempt to write to a reserved table: {}".format(t))
    if t not in pls.VALID_TABLE_NAMES:
        fail_user_error("Table doesn't exist on the server: {}".format(t))


def ensure_valid_field_name(f: str) -> None:
    """Ensures a field name contains only valid characters, and isn't a
    reserved fieldname that the user isn't allowed to access.
    Raises UserErrorException upon failure."""
    if bool(REGEX_INVALID_TABLE_FIELD_CHARS.search(f)):
        fail_user_error("Field name contains invalid characters: {}".format(f))
    if f in RESERVED_FIELDS:
        fail_user_error(
            "Invalid attempt to access a reserved field name: {}".format(f))


# =============================================================================
# Sending stuff to the client
# =============================================================================

def nvp(name: str, value: Any) -> str:
    """Returns name/value pair in 'name:value\n' format."""
    return "{}:{}\n".format(name, value)


def get_server_id_info() -> Dict:
    """Returns a reply for the tablet giving details of the server."""
    reply = {
        "databaseTitle": pls.DATABASE_TITLE,
        "idPolicyUpload": pls.ID_POLICY_UPLOAD_STRING,
        "idPolicyFinalize": pls.ID_POLICY_FINALIZE_STRING,
        "serverCamcopsVersion": CAMCOPS_SERVER_VERSION,
    }
    for n in pls.get_which_idnums():
        nstr = str(n)
        reply["idDescription" + nstr] = pls.get_id_desc(n, "")
        reply["idShortDescription" + nstr] = pls.get_id_shortdesc(n, "")
    return reply


def get_select_reply(fields: Sequence[str],
                     rows: Sequence[Sequence[Any]]) -> Dict:
    """Return format:
        nfields:X
        fields:X
        nrecords:X
        record0:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
            ...
        record{n}:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
    """
    nrecords = len(rows)
    reply = {
        "nfields": len(fields),
        "fields": ",".join(fields),
        "nrecords": nrecords,
    }
    for r in range(nrecords):
        row = rows[r]
        encodedvalues = []
        for val in row:
            encodedvalues.append(encode_single_value(val))
        reply["record" + str(r)] = ",".join(encodedvalues)
    return reply


# =============================================================================
# CamCOPS table functions
# =============================================================================

def get_server_pks_of_active_records(sm: SessionManager,
                                     table: str) -> List[int]:
    """Gets server PKs of active records (_current and in the 'NOW' era) for
    the specified device/table."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    return pls.db.fetchallfirstvalues(query, *args)


def record_exists(sm: SessionManager,
                  table: str,
                  clientpk_name: str,
                  clientpk_value: Any) -> Tuple[bool, Optional[int]]:
    """Checks if a record exists, using the device's perspective of a
    table/client PK combination.
    Returns (exists, serverpk), where exists is Boolean.
    If exists is False, serverpk will be None."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}' AND {cpk}=?
    """.format(
        table=table,
        now=ERA_NOW,
        cpk=delimit(clientpk_name),
    )
    args = [sm.device_id, clientpk_value]
    pklist = pls.db.fetchallfirstvalues(query, *args)
    exists = bool(len(pklist) >= 1)
    serverpk = pklist[0] if exists else None
    return exists, serverpk
    # Consider a warning/failure if we have >1 row meeting these criteria.
    # Not currently checked for.


def get_server_pks_of_specified_records(sm: SessionManager,
                                        table: str,
                                        wheredict: Dict) -> List[int]:
    """Retrieves server PKs for a table, for a given device, given a set of
    'where' conditions specified in wheredict (as field/value combinations,
    joined with AND)."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    query = append_where_sql_and_values(query, args, wheredict=wheredict)
    return pls.db.fetchallfirstvalues(query, *args)


def append_where_sql_and_values(query: str,
                                args: List[Any],
                                wheredict: Dict = None,
                                wherenotdict: Dict = None) -> str:
    """Appends a set of conditions, joined with AND, to the WHERE clause of
    an SQL query. Note that there WHERE clause must already have been started.
    Allows WHERE and WHERE NOT clauses.

    MODIFIES the args argument in place, and returns an extended query."""
    wheredict = wheredict or []
    wherenotdict = wherenotdict or []
    if wheredict:
        for wherefield, wherevalue in wheredict.items():
            if wherevalue is None:
                query += " AND {} IS NULL".format(delimit(wherefield))
            else:
                query += " AND {} = ?".format(delimit(wherefield))
                args.append(wherevalue)
    if wherenotdict:
        for wnfield, wnvalue in wherenotdict.items():
            if wnvalue is None:
                query += " AND {} IS NOT NULL".format(delimit(wnfield))
            else:
                query += " AND {} <> ?".format(delimit(wnfield))
                args.append(wnvalue)
    return query


def count_records(sm: SessionManager,
                  table: str,
                  wheredict: Dict,
                  wherenotdict: Dict) -> int:
    """Returns a count of records for a device/table combination, subject to
    WHERE and WHERE NOT fields (combined with AND)."""
    query = """
        SELECT COUNT(*) FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    query = append_where_sql_and_values(query, args, wheredict=wheredict,
                                        wherenotdict=wherenotdict)
    return pls.db.fetchvalue(query, *args)


def select_records_with_specified_fields(
        sm: SessionManager,
        table: str,
        wheredict: Dict,
        wherenotdict: Dict,
        fields: List[str]) -> Sequence[Sequence[Any]]:
    """Returns a list of rows, for specified fields in a device/table
    combination, subject to WHERE and WHERE NOT conditions (joined by AND)."""
    fieldlist = ",".join([delimit(x) for x in fields])
    query = """
        SELECT {fieldlist} FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        fieldlist=fieldlist,
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    query = append_where_sql_and_values(query, args, wheredict=wheredict,
                                        wherenotdict=wherenotdict)
    return pls.db.fetchall(query, *args)


def get_max_client_pk(sm: SessionManager,
                      table: str,
                      clientpk_name: str) -> Optional[int]:
    """Retrieves the maximum current client PK in a given device/table
    combination, or None."""
    query = """
        SELECT MAX({cpk}) FROM {table}
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        cpk=delimit(clientpk_name),
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    return pls.db.fetchvalue(query, *args)


def webclient_delete_records(sm: SessionManager,
                             table: str,
                             wheredict: Dict) -> None:
    """Deletes records from a table, from a mobileweb client's perspective,
    where a 'device' is 'mobileweb_{username}'."""
    query = """
        UPDATE {table}
        SET
            _successor_pk=NULL,
            _current=0,
            _removal_pending=0,
            _removing_user_id=?,
            _when_removed_exact=?,
            _when_removed_batch_utc=?
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [
        sm.user_id,
        pls.NOW_LOCAL_TZ_ISO8601,
        pls.NOW_UTC_NO_TZ,
        sm.device_id,
    ]
    query = append_where_sql_and_values(query, args, wheredict=wheredict)
    pls.db.db_exec(query, *args)


def record_identical_full(table: str,
                          serverpk: int,
                          wheredict: Dict) -> bool:
    """If a record with the specified server PK exists in the specified table
    having all its values matching the field/value combinations in wheredict
    (joined with AND), returns True. Otherwise, returns False.
    Used to detect if an incoming record matches the database record.
    Copes with NULLs (see append_where_sql_and_values)."""
    query = """
        SELECT COUNT(*) FROM {table}
        WHERE _pk=?
    """.format(
        table=table,
    )
    args = [serverpk]
    query = append_where_sql_and_values(query, args, wheredict=wheredict)
    count = pls.db.fetchvalue(query, *args)
    return count > 0


def record_identical_by_date(table: str,
                             serverpk: int,
                             client_date_value: str) -> bool:
    """Shortcut to detecting a record being identical. Returns true if the
    record (defined by its table/server PK) has a CLIENT_DATE_FIELD field
    that matches that of the incoming record. As long as the tablet always
    updates the CLIENT_DATE_FIELD when it saves a record, and the clock on the
    device doesn't go backwards by a certain exact millisecond-precision value,
    this is a valid method."""
    query = """
        SELECT COUNT(*) from {table}
        WHERE _pk=? AND {cdf}=?
    """.format(
        table=table,
        cdf=CLIENT_DATE_FIELD,
    )
    args = [serverpk, client_date_value]
    count = pls.db.fetchvalue(query, *args)
    return count > 0


def upload_record_core(sm: SessionManager,
                       table: str,
                       clientpk_name: str,
                       valuedict: Dict,
                       recordnum: int) -> Tuple[int, int]:
    """Uploads a record. Deals with IDENTICAL, NEW, and MODIFIED records."""
    require_keys(valuedict, [clientpk_name, CLIENT_DATE_FIELD,
                             MOVE_OFF_TABLET_FIELD])
    clientpk_value = valuedict[clientpk_name]
    found, oldserverpk = record_exists(sm, table, clientpk_name,
                                       clientpk_value)
    newserverpk = None
    if found:
        client_date_value = valuedict[CLIENT_DATE_FIELD]
        if record_identical_by_date(table, oldserverpk, client_date_value):
            # IDENTICAL. No action needed...
            # UNLESS MOVE_OFF_TABLET_FIELDNAME is set
            if valuedict[MOVE_OFF_TABLET_FIELD]:
                flag_record_for_preservation(table, oldserverpk)
                log.debug(
                    "Table {table}, uploaded record {recordnum}: identical "
                    "but moving off tablet".format(
                        table=table,
                        recordnum=recordnum,
                    )
                )
            else:
                log.debug(
                    "Table {table}, uploaded record {recordnum}: "
                    "identical".format(
                        table=table,
                        recordnum=recordnum,
                    )
                )
        else:
            # MODIFIED
            if table == Patient.TABLENAME:
                if sm.cope_with_deleted_patient_descriptors:
                    # Old tablets (pre-2.0.0) will upload copies of the ID
                    # descriptions with the patient. To cope with that, we
                    # remove those here:
                    for n in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
                        nstr = str(n)
                        fn_desc = FP_ID_DESC + nstr
                        fn_shortdesc = FP_ID_SHORT_DESC + nstr
                        valuedict.pop(fn_desc, None)  # remove item, if exists
                        valuedict.pop(fn_shortdesc, None)
                if sm.cope_with_old_idnums:
                    # Insert records into the new ID number table from the old
                    # patient table:
                    for which_idnum in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
                        nstr = str(which_idnum)
                        fn_idnum = FP_ID_NUM + nstr
                        idnum_value = valuedict.get(fn_idnum, None)
                        patient_id = valuedict.get("id", None)
                        if idnum_value is None or patient_id is None:
                            continue
                        mark_table_dirty(sm, PatientIdNum.tablename)
                        _, _ = upload_record_core(
                            sm=sm,
                            table=PatientIdNum.tablename,
                            clientpk_name='id',
                            valuedict={
                                'id': patient_id * NUMBER_OF_IDNUMS_DEFUNCT,  # !  # noqa
                                # ... guarantees a pseudo client PK
                                'patient_id': patient_id,
                                'which_idnum': which_idnum,
                                'idnum_value': idnum_value,
                                CLIENT_DATE_FIELD: client_date_value,
                                MOVE_OFF_TABLET_FIELD: valuedict[MOVE_OFF_TABLET_FIELD],  # noqa
                            },
                            recordnum=recordnum
                        )
                    # Now, how to deal with deletion, i.e. records missing
                    # from the tablet?
                    # See our caller, upload_table().

            newserverpk = insert_record(sm, table, valuedict, oldserverpk)
            flag_modified(sm, table, oldserverpk, newserverpk)
            log.debug("Table {table}, record {recordnum}: modified".format(
                table=table,
                recordnum=recordnum,
            ))
    else:
        # NEW
        newserverpk = insert_record(sm, table, valuedict, None)
    return oldserverpk, newserverpk


def insert_record(sm: SessionManager,
                  table: str,
                  valuedict: Dict,
                  predecessor_pk: Optional[int]) -> int:
    """Inserts a record, or raises an exception if that fails."""
    mark_table_dirty(sm, table)
    valuedict.update({
        "_device_id": sm.device_id,
        "_era": ERA_NOW,
        "_current": 0,
        "_addition_pending": 1,
        "_removal_pending": 0,
        "_predecessor_pk": predecessor_pk,
        "_camcops_version": sm.tablet_version_str,
    })
    return pls.db.insert_record_by_dict(table, valuedict)


def duplicate_record(sm: SessionManager, table: str, serverpk: int) -> int:
    """Duplicates the record defined by the table/serverpk combination.
    Will raise an exception if the insert fails. Otherwise...
    The old record then NEEDS MODIFICATION by flag_modified().
    The new record NEEDS MODIFICATION by update_new_copy_of_record().
    """
    mark_table_dirty(sm, table)
    # Fetch the existing record.
    query = "SELECT * from {table} WHERE _pk=?".format(table=table)
    args = [serverpk]
    dictlist = pls.db.fetchall_as_dictlist(query, *args)
    if not dictlist:
        raise ServerErrorException(
            "Tried to fetch nonexistent record: table {t}, PK {pk}".format(
                t=table, pk=serverpk))
    d = dictlist[0]
    # Remove the PK from what we insert back (that will be autogenerated)
    d.pop("_pk", None)
    # ... or del d["_pk"]; http://stackoverflow.com/questions/5447494
    # Perform the insert
    return pls.db.insert_record_by_dict(table, d)


def update_new_copy_of_record(sm: SessionManager,
                              table: str,
                              serverpk: int,
                              valuedict: Dict,
                              predecessor_pk: int) -> None:
    """Following duplicate_record(), use this to modify the new copy (defined
    by the table/serverpk combination)."""
    query = """
        UPDATE {table}
        SET
            _current=0,
            _addition_pending=1,
            _predecessor_pk=?,
            _camcops_version=?
    """.format(
        table=table,
    )
    args = [predecessor_pk, sm.tablet_version_str]
    for f, v in valuedict.items():
        query += ", {}=?".format(delimit(f))
        args.append(v)
    query += " WHERE _pk=?"
    args.append(serverpk)
    pls.db.db_exec(query, *args)


# =============================================================================
# Batch (atomic) upload and preserving
# =============================================================================

def get_batch_details_start_if_needed(sm: SessionManager) \
        -> Tuple[Optional[datetime.datetime], Optional[bool]]:
    """Gets a (upload_batch_utc, currently_preserving) tuple.

    upload_batch_utc: the batchtime; UTC date/time of the current upload batch.
    currently_preserving: Boolean; whether preservation (shifting to an older
        era) is currently taking place.

    SIDE EFFECT: if the username is different from the username that started
    a previous upload batch for this device, we restart the upload batch (thus
    rolling back previous pending changes).
    """
    query = """
        SELECT ongoing_upload_batch_utc,
            uploading_user_id,
            currently_preserving
        FROM {table}
        WHERE id=?
    """.format(table=Device.TABLENAME)
    args = [sm.device_id]
    row = pls.db.fetchone(query, *args)
    if not row:
        return None, None
    upload_batch_utc, uploading_user_id, currently_preserving = row
    if not upload_batch_utc or uploading_user_id != sm.user_id:
        # SIDE EFFECT: if the username changes, we restart (and thus roll back
        # previous pending changes)
        start_device_upload_batch(sm)
        return pls.NOW_UTC_NO_TZ, False
    log.debug("get_batch_details_start_if_needed: upload_batch_utc "
              "= {}".format(repr(upload_batch_utc)))
    return upload_batch_utc, currently_preserving


def start_device_upload_batch(sm: SessionManager) -> None:
    """Starts an upload batch for a device."""
    rollback_all(sm)
    query = """
        UPDATE {table}
        SET
             last_upload_batch_utc=?,
             ongoing_upload_batch_utc=?,
             uploading_user_id=?
         WHERE id=?
    """.format(table=Device.TABLENAME)
    pls.db.db_exec(query,
                   pls.NOW_UTC_NO_TZ,
                   pls.NOW_UTC_NO_TZ,
                   sm.user_id,
                   sm.device_id)


def end_device_upload_batch(sm: SessionManager,
                            batchtime: datetime.datetime,
                            preserving: bool) -> None:
    """Ends an upload batch, committing all changes made thus far."""
    commit_all(sm, batchtime, preserving)
    pls.db.db_exec("""
        UPDATE {table}
        SET
            ongoing_upload_batch_utc=NULL,
            uploading_user_id=NULL,
            currently_preserving=0
        WHERE id=?
    """.format(table=Device.TABLENAME), sm.device_id)


def start_preserving(sm: SessionManager) -> None:
    """Starts preservation (the process of moving records from the NOW era to
    an older era, so they can be removed safely from the tablet)."""
    pls.db.db_exec("""
        UPDATE {table}
        SET currently_preserving=1
        WHERE id=?
    """.format(table=Device.TABLENAME), sm.device_id)


def mark_table_dirty(sm: SessionManager, table: str) -> None:
    """Marks a table as having been modified during the current upload."""
    pls.db.db_exec("""
        REPLACE INTO {table}
            (device_id, tablename)
        VALUES (?,?)
    """.format(table=DIRTY_TABLES_TABLENAME), sm.device_id, table)
    # http://dev.mysql.com/doc/refman/5.0/en/replace.html


def get_dirty_tables(sm: SessionManager) -> Sequence[str]:
    """Returns tables marked as dirty for this device."""
    return pls.db.fetchallfirstvalues(
        "SELECT tablename FROM {table} WHERE device_id=?".format(
            table=DIRTY_TABLES_TABLENAME),
        sm.device_id)


def flag_deleted(sm: SessionManager, table: str, pklist: Iterable[int]) -> None:
    """Marks record(s) as deleted, specified by a list of server PKs."""
    mark_table_dirty(sm, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _pk=?
    """.format(table=table)
    for pk in pklist:
        pls.db.db_exec(query, pk)


def flag_all_records_deleted(sm: SessionManager, table: str) -> None:
    """Marks all records in a table as deleted (that are current and in the
    current era)."""
    mark_table_dirty(sm, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    pls.db.db_exec(query, sm.device_id)


def flag_deleted_where_clientpk_not(sm: SessionManager,
                                    table: str,
                                    clientpk_name: str,
                                    clientpk_values: Sequence[Any]) -> None:
    """Marks for deletion all current/current-era records for a device, defined
    by a list of client-side PK values."""
    mark_table_dirty(sm, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _device_id=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [sm.device_id]
    wherelist = []
    for cpk in clientpk_values:
        wherelist.append("{}=?".format(delimit(clientpk_name)))
        args.append(cpk)
    if wherelist:
        query += " AND NOT ({nots})".format(nots=" OR ".join(wherelist))
    pls.db.db_exec(query, *args)


def flag_modified(sm: SessionManager,
                  table: str,
                  pk: int,
                  successor_pk: int) -> None:
    """Marks a record as old, storing its successor's details."""
    mark_table_dirty(sm, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=?
        WHERE _pk=?
    """.format(
        table=table,
    )
    pls.db.db_exec(query, successor_pk, pk)


def flag_record_for_preservation(table: str, pk: int) -> None:
    """Marks a record for preservation (moving off the tablet, changing its
    era details)."""
    query = """
        UPDATE {table}
        SET {MOVE_OFF_TABLET_FIELD}=1
        WHERE _pk=?
    """.format(
        table=table,
        MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD
    )
    pls.db.db_exec(query, pk)


def commit_all(sm: SessionManager,
               batchtime: datetime.datetime,
               preserving: bool) -> None:
    """Commits additions, removals, and preservations for all tables."""
    tables = get_dirty_tables(sm)
    auditsegments = []
    for table in tables:
        n_added, n_removed, n_preserved = commit_table(
            sm, batchtime, preserving, table, clear_dirty=False)
        auditsegments.append(
            "{table} ({n_added},{n_removed},{n_preserved})".format(
                table=table,
                n_added=n_added,
                n_removed=n_removed,
                n_preserved=n_preserved,
            )
        )
    clear_dirty_tables(sm)
    details = "Upload [table (n_added,n_removed,n_preserved)]: {}".format(
        ", ".join(auditsegments)
    )
    audit(sm, details)


def commit_table(sm: SessionManager,
                 batchtime: datetime.datetime,
                 preserving: bool,
                 table: str,
                 clear_dirty: bool = True) -> Tuple[int, int, int]:
    """Commits additions, removals, and preservations for one table."""
    exacttime = pls.NOW_LOCAL_TZ_ISO8601
    # Additions
    query = """
        UPDATE {table}
        SET
            _current=1,
            _addition_pending=0,
            _adding_user_id=?,
            _when_added_exact=?,
            _when_added_batch_utc=?
        WHERE _device_id=? AND _addition_pending
    """.format(table=table)
    n_added = pls.db.db_exec(query,
                             sm.user_id,
                             exacttime,
                             batchtime,
                             sm.device_id)
    # Removals
    query = """
        UPDATE {table}
        SET
            _current=0,
            _removal_pending=0,
            _removing_user_id=?,
            _when_removed_exact=?,
            _when_removed_batch_utc=?
        WHERE _device_id=? AND _removal_pending
    """.format(table=table)
    n_removed = pls.db.db_exec(query,
                               sm.user_id,
                               exacttime,
                               batchtime,
                               sm.device_id)
    # Preservation
    new_era = format_datetime(batchtime, DATEFORMAT.ERA)
    if preserving:
        # Preserve all relevant records
        query = """
            UPDATE {table}
            SET
                _era=?,
                _preserving_user_id=?,
                {MOVE_OFF_TABLET_FIELD}=0
            WHERE _device_id=? AND _era='{now}'
        """.format(
            table=table,
            MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
            now=ERA_NOW,
        )
        n_preserved = pls.db.db_exec(query, new_era, sm.user_id, sm.device_id)
        # Also preserve/finalize any corresponding special notes (2015-02-01)
        # NOTE DIFFERENT FIELDNAMES.
        query = """
            UPDATE  {table}
            SET     era=?
            WHERE   basetable=?
            AND     device_id=?
            AND     era='{now}'
        """.format(table=SpecialNote.TABLENAME, now=ERA_NOW)
        pls.db.db_exec(query, new_era, table, sm.device_id)
    else:
        # Preserve any individual records
        query = """
            UPDATE {table}
            SET
                _era=?,
                _preserving_user_id=?,
                {MOVE_OFF_TABLET_FIELD}=0
            WHERE _device_id=? AND {MOVE_OFF_TABLET_FIELD}
        """.format(
            table=table,
            MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
        )
        n_preserved = pls.db.db_exec(query, new_era, sm.user_id, sm.device_id)
        # Also preserve/finalize any corresponding special notes (2015-02-01)
        # NOTE DIFFERENT FIELDNAMES.
        query = """
            UPDATE  {st} s
            SET     s.era=?
            WHERE   s.basetable=?
            AND     s.device_id=?
            AND     s.era='{now}'
            AND     EXISTS (
                SELECT  *
                FROM    {table} t
                WHERE   t.id = s.task_id
                AND     t._device_id = s.device_id
                AND     t._era = ?
            )
        """.format(st=SpecialNote.TABLENAME,
                   now=ERA_NOW,
                   table=table)
        pls.db.db_exec(query, new_era, table, sm.device_id, new_era)
    # Remove individually from list of dirty tables?
    if clear_dirty:
        query = ("DELETE FROM {table} WHERE device_id=? "
                 "AND tablename=?".format(table=DIRTY_TABLES_TABLENAME))
        pls.db.db_exec(query, sm.device_id, table)
        # ... otherwise a call to clear_dirty_tables() must be made.
    return n_added, n_removed, n_preserved


def rollback_all(sm: SessionManager) -> None:
    """Rolls back all pending changes for a device."""
    tables = get_dirty_tables(sm)
    for table in tables:
        rollback_table(sm, table)
    clear_dirty_tables(sm)


def rollback_table(sm: SessionManager, table: str) -> None:
    """Rolls back changes for an individual table for a device."""
    # Pending additions
    pls.db.db_exec(
        "DELETE FROM {table} WHERE _device_id=? AND _addition_pending".format(
            table=table
        ),
        sm.device_id
    )
    # Pending deletions
    query = """
        UPDATE {table}
        SET
            _removal_pending=0,
            _when_removed_exact=NULL,
            _when_removed_batch_utc=NULL,
            _removing_user_id=NULL,
            _successor_pk=NULL
        WHERE _device_id=? AND _removal_pending
    """.format(table=table)
    pls.db.db_exec(query, sm.device_id)
    # Record-specific preservation (set by flag_record_for_preservation())
    query = """
        UPDATE {table}
        SET
            {MOVE_OFF_TABLET_FIELD}=0
        WHERE _device_id=?
    """.format(
        table=table,
        MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
    )
    pls.db.db_exec(query, sm.device_id)


def clear_dirty_tables(sm: SessionManager) -> None:
    """Clears the dirty-table list for a device."""
    pls.db.db_exec("DELETE FROM _dirty_tables WHERE device_id=?", sm.device_id)


# =============================================================================
# Audit functions
# =============================================================================

def audit(sm: SessionManager,
          details: str,
          patient_server_pk: int = None,
          table: str = None,
          server_pk: int = None) -> None:
    """Audit something."""
    # Add parameters and pass on:
    cc_audit.audit(
        details=details,
        patient_server_pk=patient_server_pk,
        table=table,
        server_pk=server_pk,
        device_id=sm.device_id,  # added
        remote_addr=pls.remote_addr,  # added
        user_id=sm.user_id,  # added
        from_console=False,  # added
        from_dbclient=True  # added
    )


# =============================================================================
# Action processors: allowed to any user
# =============================================================================
# If they return None, the framework uses the operation name as the reply in
# the success message. Not returning anything is the same as returning None.
# Authentication is performed in advance of these.

def check_device_registered(sm: SessionManager) -> None:
    """Check that a device is registered, or raise UserErrorException."""
    sm.ensure_device_registered()


# =============================================================================
# Action processors that require REGISTRATION privilege
# =============================================================================

def register(sm: SessionManager) -> Dict:
    """Register a device with the server."""
    device_friendly_name = get_post_var(sm.form, "devicefriendlyname",
                                        mandatory=False)

    table = Device.TABLENAME
    count = pls.db.fetchvalue(
        "SELECT COUNT(*) FROM {table} WHERE name=?".format(table=table),
        sm.device_name)
    if count > 0:
        # device already registered, but accept re-registration
        query = """
            UPDATE {table}
            SET
                friendly_name=?,
                camcops_version=?,
                registered_by_user_id=?,
                when_registered_utc=?
            WHERE name=?
        """.format(table=table)
        pls.db.db_exec(query,
                       device_friendly_name,
                       sm.tablet_version_str,
                       sm.user_id,
                       pls.NOW_UTC_NO_TZ,
                       sm.device_name)
    else:
        # new registration
        valuedict = {
            "name": sm.device_name,
            "friendly_name": device_friendly_name,
            "camcops_version": sm.tablet_version_str,
            "registered_by_user_id": sm.user_id,
            "when_registered_utc": pls.NOW_UTC_NO_TZ,
        }
        newpk = pls.db.insert_record_by_dict(table, valuedict)
        if newpk is None:
            fail_user_error(INSERT_FAILED)

    sm.reload_device()
    audit(
        sm,
        "register, device_id={}, friendly_name={}".format(
            sm.device_id, device_friendly_name),
        table=table
    )
    return get_server_id_info()


def get_extra_strings(sm: SessionManager) -> Dict:
    """Fetch all local extra strings from the server."""
    fields = ["task", "name", "value"]
    rows = get_all_extra_strings()
    reply = get_select_reply(fields, rows)
    audit(sm, "get_extra_strings")
    return reply


# =============================================================================
# Action processors that require UPLOAD privilege
# =============================================================================

# noinspection PyUnusedLocal
def check_upload_user_and_device(sm: SessionManager) -> None:
    """Stub function for the operation to check that a user is valid."""
    pass  # don't need to do anything!


# noinspection PyUnusedLocal
def get_id_info(sm: SessionManager) -> Dict:
    """Fetch server ID information."""
    return get_server_id_info()


def start_upload(sm: SessionManager) -> None:
    """Begin an upload."""
    start_device_upload_batch(sm)


def end_upload(sm: SessionManager) -> None:
    """Ends an upload and commits changes."""
    batchtime, preserving = get_batch_details_start_if_needed(sm)
    # ensure it's the same user finishing as starting!
    end_device_upload_batch(sm, batchtime, preserving)


def upload_table(sm: SessionManager) -> str:
    """Upload a table. Incoming information in the CGI form includes a CSV list
    of fields, a count of the number of records being provided, and a set of
    CGI variables named record0 ... record{nrecords}, each containing a CSV
    list of SQL-encoded values. Typically used for smaller tables, i.e. most
    except for BLOBs."""
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    fields = get_fields_from_post_var(sm.form, PARAM.FIELDS)
    nrecords = get_post_var(sm.form, PARAM.NRECORDS, valtype=int)

    nfields = len(fields)
    if nfields < 1:
        fail_user_error("nfields={}: can't be less than 1".format(nfields))
    if nrecords < 0:
        fail_user_error("nrecords={}: can't be less than 0".format(nrecords))

    _, _ = get_batch_details_start_if_needed(sm)
    clientpk_name = fields[0]
    server_uploaded_pks = []
    new_or_updated = 0
    server_active_record_pks = get_server_pks_of_active_records(sm, table)
    mark_table_dirty(sm, table)
    for r in range(nrecords):
        recname = "record{}".format(r)
        values = get_values_from_post_var(sm.form, recname)
        nvalues = len(values)
        if nvalues != nfields:
            errmsg = (
                "Number of fields in field list ({nfields}) doesn't match "
                "number of values in record {r} ({nvalues})".format(
                    nfields=nfields, r=r, nvalues=nvalues)
            )
            log.warning(errmsg)
            log.warning("fields: {}".format(repr(fields)))
            log.warning("values: {}".format(repr(values)))
            fail_user_error(errmsg)
        valuedict = dict(list(zip(fields, values)))
        # CORE: CALLS upload_record_core
        oldserverpk, newserverpk = upload_record_core(sm,
                                                      table,
                                                      clientpk_name,
                                                      valuedict,
                                                      r)
        new_or_updated += 1
        server_uploaded_pks.append(oldserverpk)

    # Now deal with any ABSENT (not in uploaded data set) conditions.
    server_pks_for_deletion = [x for x in server_active_record_pks
                               if x not in server_uploaded_pks]
    flag_deleted(sm, table, server_pks_for_deletion)

    # Special for old tablets:
    if sm.cope_with_old_idnums and table == Patient.TABLENAME:
        mark_table_dirty(sm, PatientIdNum.tablename)
        for delete_patient_pk in server_pks_for_deletion:
            pls.db.db_exec(
                """
                    UPDATE {idtable} AS i
                    INNER JOIN {patienttable} AS p
                    SET i._removal_pending = 1, i._successor_pk = NULL
                    WHERE i._device_id = p._device_id
                    AND i._era = '{now}'
                    AND i.patient_id = p.id
                    AND p._pk = ?
                """.format(
                    idtable=PatientIdNum.tablename,
                    patienttable=Patient.TABLENAME,
                    now=ERA_NOW,
                ),
                delete_patient_pk
            )

    # Success
    log.debug("server_active_record_pks: {}".format(
        server_active_record_pks))
    log.debug("server_uploaded_pks: {}".format(server_uploaded_pks))
    log.debug("server_pks_for_deletion: {}".format(
        server_pks_for_deletion))
    log.debug("Table {table}, number of missing records (deleted): "
              "{d}".format(table=table, d=len(server_pks_for_deletion)))
    # Auditing occurs at commit_all.
    log.info("Upload successful; {n} records uploaded to table {t}".format(
        n=nrecords, t=table))
    return "Table {} upload successful".format(table)


def upload_record(sm: SessionManager) -> str:
    """Upload an individual record. (Typically used for BLOBs.) Incoming
    CGI information includes a CSV list of fields and a CSV list of values."""
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, PARAM.PKNAME)
    valuedict = get_fields_and_values(sm.form, PARAM.FIELDS, PARAM.VALUES)
    require_keys(valuedict, [clientpk_name, CLIENT_DATE_FIELD])
    clientpk_value = valuedict[clientpk_name]
    wheredict = {clientpk_name: clientpk_value}

    serverpks = get_server_pks_of_specified_records(sm, table, wheredict)
    if not serverpks:
        # Insert
        insert_record(sm, table, valuedict, None)
        log.info("upload-insert")
        return "UPLOAD-INSERT"
    else:
        # Update
        oldserverpk = serverpks[0]
        client_date_value = valuedict[CLIENT_DATE_FIELD]
        exists = record_identical_by_date(table, oldserverpk,
                                          client_date_value)
        if exists:
            log.info("upload-update: skipping existing record")
        else:
            newserverpk = duplicate_record(sm, table, oldserverpk)
            flag_modified(sm, table, oldserverpk, newserverpk)
            update_new_copy_of_record(sm, table, newserverpk, valuedict,
                                      oldserverpk)
            log.info("upload-update")
        return "UPLOAD-UPDATE"
    # Auditing occurs at commit_all.


def upload_empty_tables(sm: SessionManager) -> str:
    """The tablet supplies a list of tables that are empty at its end, and we
    will 'wipe' all appropriate tables; this reduces the number of HTTP
    requests."""
    tables = get_tables_from_post_var(sm.form, PARAM.TABLES)

    _, _ = get_batch_details_start_if_needed(sm)
    for table in tables:
        flag_all_records_deleted(sm, table)
    log.info("upload_empty_tables")
    # Auditing occurs at commit_all.
    return "UPLOAD-EMPTY-TABLES"


def start_preservation(sm: SessionManager) -> str:
    """Marks this upload batch as one in which all records will be preserved
    (i.e. moved from NOW-era to an older era, so they can be deleted safely
    from the tablet).

    Without this, individual records can still be marked for preservation if
    their MOVE_OFF_TABLET_FIELD field (_move_off_tablet) is set; see
    upload_record and its functions."""
    _, _ = get_batch_details_start_if_needed(sm)
    start_preserving(sm)
    log.info("start_preservation successful")
    # Auditing occurs at commit_all.
    return "STARTPRESERVATION"


def delete_where_key_not(sm: SessionManager) -> str:
    """Marks records for deletion, for a device/table, where the client PK
    is not in a specified list."""
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, PARAM.PKNAME)
    clientpk_values = get_values_from_post_var(sm.form, PARAM.PKVALUES)

    _, _ = get_batch_details_start_if_needed(sm)
    flag_deleted_where_clientpk_not(sm, table, clientpk_name, clientpk_values)
    # Auditing occurs at commit_all.
    log.info("delete_where_key_not successful; table {} trimmed".format(
        table))
    return "Trimmed"


def which_keys_to_send(sm: SessionManager) -> str:
    """Intended use: "For my device, and a specified table, here are my client-
    side PKs (as a CSV list), and the modification dates for each corresponding
    record (as a CSV list). Please tell me which records have mismatching dates
    on the server, i.e. those that I need to re-upload."

    Used particularly for BLOBs, to reduce traffic, i.e. so we don't have to
    send a lot of BLOBs."""
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, PARAM.PKNAME)
    clientpk_values = get_values_from_post_var(sm.form, PARAM.PKVALUES,
                                               mandatory=False)
    client_dates = get_values_from_post_var(sm.form, PARAM.DATEVALUES,
                                            mandatory=False)

    npkvalues = len(clientpk_values)
    ndatevalues = len(client_dates)
    if npkvalues != ndatevalues:
        fail_user_error(
            "Number of PK values ({npk}) doesn't match number of dates "
            "({nd})".format(npk=npkvalues, nd=ndatevalues))

        _, _ = get_batch_details_start_if_needed(sm)

    # 1. The client sends us all its PKs. So "delete" anything not in that
    #    list.
    flag_deleted_where_clientpk_not(sm, table, clientpk_name, clientpk_values)

    # 2. See which ones are new or updates.
    pks_needed = []
    for i in range(npkvalues):
        clientpkval = clientpk_values[i]
        client_date_value = client_dates[i]
        found, serverpk = record_exists(sm, table, clientpk_name, clientpkval)
        if not found or not record_identical_by_date(table, serverpk,
                                                     client_date_value):
            pks_needed.append(clientpkval)

    # Success
    pk_csv_list = ",".join([str(x) for x in pks_needed if x is not None])
    log.info("which_keys_to_send successful: table {}".format(table))
    return pk_csv_list


# =============================================================================
# Action processors that require MOBILEWEB privilege
# =============================================================================

def mw_count(sm: SessionManager) -> int:
    """Count records in a table, given a set of WHERE/WHERE NOT conditions,
    joined by AND."""
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    wheredict = get_fields_and_values(sm.form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)
    wherenotdict = get_fields_and_values(sm.form, PARAM.WHERENOTFIELDS,
                                         PARAM.WHERENOTVALUES, mandatory=False)
    c = count_records(sm, table, wheredict, wherenotdict)
    auditstring = ("webclient SELECT COUNT(*) FROM {t} WHERE {w} AND WHERE "
                   "NOT {wn}".format(t=table, w=wheredict, wn=wherenotdict))
    log.debug(auditstring)
    audit(sm, auditstring, table=table)
    log.info("COUNT")
    return c


def mw_select(sm: SessionManager) -> Dict:
    """Select fields from a table, specified by WHERE/WHERE NOT criteria,
    joined by AND. Return format: see get_select_reply() help.
    """
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    fields = get_fields_from_post_var(sm.form, PARAM.FIELDS)
    wheredict = get_fields_and_values(sm.form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)
    wherenotdict = get_fields_and_values(sm.form, PARAM.WHERENOTFIELDS,
                                         PARAM.WHERENOTVALUES, mandatory=False)

    # Select records
    rows = select_records_with_specified_fields(sm, table, wheredict,
                                                wherenotdict, fields)

    # Send results back to user
    # .... even though this probably reinvents what the client sent us!
    reply = get_select_reply(fields, rows)

    auditstring = (
        "webclient SELECT {f} FROM {t} WHERE {w} AND WHERE NOT {wn}".format(
            f=",".join(fields),
            t=table,
            w=wheredict,
            wn=wherenotdict,
        )
    )
    log.debug(auditstring)
    audit(sm, auditstring, table=table)
    log.info("SELECT")
    return reply


def mw_insert(sm: SessionManager) -> int:
    """Mobileweb client non-transactional INSERT."""
    # Non-transactional
    #
    # Don't need to pay special attention to "id" (clientpk_name) field, to
    # ensure it remains unique per device/table for current records, because we
    # always create a new such value (clientpk_value below) and return it.
    # Potential for failure if two clients did this at the same time *for the
    # same device*, but that means the same user, so the advice is simply not
    # to do that.
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, PARAM.PKNAME)
    valuedict = get_fields_and_values(sm.form, PARAM.FIELDS, PARAM.VALUES)

    max_client_pk = get_max_client_pk(sm, table, clientpk_name)
    if max_client_pk is None:
        max_client_pk = 0
    clientpk_value = max_client_pk + 1
    valuedict[clientpk_name] = clientpk_value
    serverpk = insert_record(sm, table, valuedict, None)
    commit_table(sm, pls.NOW_UTC_NO_TZ, False, table)
    audit(sm, "webclient INSERT", table=table, server_pk=serverpk)
    log.info("INSERT")
    return clientpk_value


def mw_update(sm: SessionManager) -> str:
    """Mobileweb client non-transactional UPDATE."""
    # Non-transactional
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    valuedict = get_fields_and_values(sm.form, PARAM.FIELDS, PARAM.VALUES)
    wheredict = get_fields_and_values(sm.form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)

    serverpks = get_server_pks_of_specified_records(sm, table, wheredict)
    if len(serverpks) == 0:
        fail_user_error(
            "No records found to UPDATE (table={table}, where={where})".format(
                table=table,
                where=wheredict
            )
        )
    # The UPDATE information might not include the date; so we assume that a
    # real change is being made.
    for serverpk in serverpks:
        newserverpk = duplicate_record(sm, table, serverpk)
        flag_modified(sm, table, serverpk, newserverpk)
        update_new_copy_of_record(sm, table, newserverpk, valuedict, serverpk)
        audit(sm, "webclient UPDATE: old record deactivated",
              table=table, server_pk=serverpk)
        audit(sm, "webclient UPDATE: new record inserted",
              table=table, server_pk=newserverpk)
    commit_table(sm, pls.NOW_UTC_NO_TZ, False, table)
    log.info("UPDATE")
    return "Updated"


def mw_delete(sm: SessionManager) -> str:
    """Mobileweb client non-transactional DELETE."""
    # Non-transactional
    table = get_table_from_post_var(sm.form, PARAM.TABLE)
    wheredict = get_fields_and_values(sm.form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)

    webclient_delete_records(sm, table, wheredict)
    # ... doesn't need a separate commit_table
    audit(sm, "webclient DELETE WHERE {}".format(wheredict), table=table)
    log.info("DELETE")
    return "Deleted"


# =============================================================================
# Action maps
# =============================================================================

OPERATIONS_ANYONE = {
    "check_device_registered": check_device_registered,
}
OPERATIONS_REGISTRATION = {
    "register": register,
    "get_extra_strings": get_extra_strings,
}
OPERATIONS_UPLOAD = {
    "check_upload_user_and_device": check_upload_user_and_device,
    "get_id_info": get_id_info,
    "start_upload": start_upload,
    "end_upload": end_upload,
    "upload_table": upload_table,
    "upload_record": upload_record,
    "upload_empty_tables": upload_empty_tables,
    "start_preservation": start_preservation,
    "delete_where_key_not": delete_where_key_not,
    "which_keys_to_send": which_keys_to_send,
}
OPERATIONS_MOBILEWEB = {
    "count": mw_count,
    "select": mw_select,
    "insert": mw_insert,
    "update": mw_update,
    "delete": mw_delete,
}


# =============================================================================
# Main action processor
# =============================================================================

def main_http_processor(env: Dict[str, str]) -> Dict:
    """Main HTTP processor."""
    # For success, returns:
    #   text:   main text to send (will use status '200 OK')
    # For failure, raises an exception.

    log.info("CamCOPS database script starting at {}".format(
        format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.ISO8601)
    ))
    form = ws.get_cgi_fieldstorage_from_wsgi_env(env)

    if not ws.cgi_method_is_post(env):
        fail_user_error("Must use POST method")

    sm = SessionManager(form)

    fn = None

    if sm.operation in OPERATIONS_ANYONE:
        fn = OPERATIONS_ANYONE.get(sm.operation)

    if sm.operation in OPERATIONS_REGISTRATION:
        sm.ensure_valid_user_for_device_registration()
        fn = OPERATIONS_REGISTRATION.get(sm.operation)

    if sm.operation in OPERATIONS_UPLOAD:
        sm.ensure_valid_device_and_user_for_uploading()
        fn = OPERATIONS_UPLOAD.get(sm.operation)

    if pls.ALLOW_MOBILEWEB:
        if sm.operation in OPERATIONS_MOBILEWEB:
            sm.ensure_valid_user_for_webstorage()
            fn = OPERATIONS_MOBILEWEB.get(sm.operation)

    if not fn:
        fail_unsupported_operation(sm.operation)
    result = fn(sm)
    if result is None:
        result = {PARAM.RESULT: sm.operation}
    elif not isinstance(result, dict):
        result = {PARAM.RESULT: result}
    return result


# =============================================================================
# WSGI application
# =============================================================================

def database_application(environ: Dict[str, str],
                         start_response: Callable[[str, HEADERS_TYPE], None]) \
        -> Iterable[bytes]:
    """Main WSGI application handler. Very simple."""
    # Call main
    t0 = time.time()  # in seconds
    try:
        resultdict = main_http_processor(environ)
        resultdict[PARAM.SUCCESS] = 1
        status = '200 OK'
    except UserErrorException as e:
        log.warn("CLIENT-SIDE SCRIPT ERROR: " + str(e))
        resultdict = {
            PARAM.SUCCESS: 0,
            PARAM.ERROR: escape_newlines(str(e))
        }
        status = '200 OK'
    except ServerErrorException as e:
        log.error("SERVER-SIDE SCRIPT ERROR: " + str(e))
        pls.db.rollback()
        resultdict = {
            PARAM.SUCCESS: 0,
            PARAM.ERROR: escape_newlines(str(e))
        }
        status = "503 Database Unavailable: " + str(e)
    except Exception as e:
        # All other exceptions. May include database write failures.
        # Let's return with status '200 OK'; though this seems dumb, it means
        # the tablet user will at least see the message.
        log.exception("Unhandled exception")
        pls.db.rollback()
        resultdict = {
            PARAM.SUCCESS: 0,
            PARAM.ERROR: escape_newlines(exception_description(e))
        }
        status = '200 OK'
    # Add session token information
    if pls.session:
        resultdict[PARAM.SESSION_ID] = pls.session.id
        resultdict[PARAM.SESSION_TOKEN] = pls.session.token
    # Convert dictionary to text
    text = ""
    for k, v in resultdict.items():
        text += nvp(k, v)
    output = text.encode("utf-8")

    # Commit
    t1 = time.time()
    pls.db.commit()
    t2 = time.time()

    # log.debug("Reply: {}".format(repr(output)))
    # ... don't send Unicode to the log...
    log.info(
        "Total time (s): {t} (script {s}, commit {c})".format(
            t=t2 - t0,
            s=t1 - t0,
            c=t2 - t1
        )
    )

    # Return headers and output
    response_headers = [('Content-Type', CONTENTTYPE),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


# =============================================================================
# Unit tests
# =============================================================================

def database_unit_tests() -> None:
    """Unit tests for database script."""
    # a = (UserErrorException, ServerErrorException)
    u = UserErrorException
    s = ServerErrorException

    print("pls.VALID_TABLE_NAMES: {}".format(pls.VALID_TABLE_NAMES))

    unit_test_ignore("", succeed_generic, "testmsg")
    unit_test_must_raise("", fail_user_error, u, "testmsg")
    unit_test_must_raise("", fail_server_error, s, "testmsg")
    unit_test_must_raise("", fail_unsupported_operation, u, "duffop")
    unit_test_verify("", nvp, "n:v\n", "n", "v")

    # Encoding/decoding tests
    # data = bytearray("hello")
    data = b"hello"
    enc_b64data = special_base64_encode(data)
    enc_hexdata = special_hex_encode(data)
    not_enc_1 = "X'012345'"
    not_enc_2 = "64'aGVsbG8='"
    teststring = """one, two, 3, 4.5, NULL, 'hello "hi
        with linebreak"', 'NULL', 'quote''s here', {b}, {h}, {s1}, {s2}"""
    sql_csv_testdict = {
        teststring.format(
            b=enc_b64data,
            h=enc_hexdata,
            s1=rnc_db.sql_quote_string(not_enc_1),
            s2=rnc_db.sql_quote_string(not_enc_2),
        ): [
            "one",
            "two",
            3,
            4.5,
            None,
            'hello "hi\n        with linebreak"',
            "NULL",
            "quote's here",
            data,
            data,
            not_enc_1,
            not_enc_2,
        ],
        "": [],
    }
    for k, v in sql_csv_testdict.items():
        r = decode_values(k)
        if r != v:
            raise AssertionError(
                "Mismatch! Result: {}\nShould have been: {}\n".format(r, v))

    # Newline encoding/decodine
    ts2 = "slash \\ newline \n ctrl_r \r special \\n other special \\r " \
          "quote ' doublequote \" "
    if unescape_newlines(escape_newlines(ts2)) != ts2:
        raise AssertionError("Bug in escape_newlines() or unescape_newlines()")

    # more... ?
