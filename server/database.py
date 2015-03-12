#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from __future__ import print_function

# =============================================================================
# Debugging options
# =============================================================================

# Report profiling information to the HTTPD log? (Adds overhead; do not enable
# for production systems.)
PROFILE = False

# =============================================================================
# Imports
# =============================================================================

import base64
import ConfigParser
import re
import sys
import time

import rnc_db
import rnc_web as ws

import cc_audit
from cc_constants import (
    CAMCOPS_URL,
    CLIENT_DATE_FIELD,
    DATEFORMAT,
    ERA_NOW,
    MOVE_OFF_TABLET_FIELD,
    NUMBER_OF_IDNUMS,
    STANDARD_GENERIC_FIELDSPECS
)
import cc_dt
import cc_lang
from cc_logger import dblogger as logger
from cc_pls import pls
import cc_session
import cc_version

# Conditional imports
if PROFILE:
    import werkzeug.contrib.profiler

# =============================================================================
# Constants
# =============================================================================

CONTENTTYPE = 'text/plain; charset=utf-8'
DUPLICATE_FAILED = "Failed to duplicate record"
INSERT_FAILED = "Failed to insert record"
INVALID_USERNAME_PASSWORD = "Invalid username/password"
PARAM = cc_lang.AttrDict({
    "CAMCOPS_VERSION": "camcops_version",
    "DATEVALUES": "datevalues",
    "DEVICE": "device",
    "FIELDS": "fields",
    "NRECORDS": "nrecords",
    "OPERATION": "operation",
    "PASSWORD": "password",
    "PKNAME": "pkname",
    "PKVALUES": "pkvalues",
    "RESULT": "result",  # server to tablet
    "SESSION_ID": "session_id",  # bidirectional
    "SESSION_TOKEN": "session_token",  # bidirectional
    "SUCCESS": "success",  # server to tablet
    "ERROR": "error",  # server to tablet
    "TABLE": "table",
    "TABLES": "tables",
    "USER": "user",
    "WHEREFIELDS": "wherefields",
    "WHERENOTFIELDS": "wherenotfields",
    "WHERENOTVALUES": "wherenotvalues",
    "WHEREVALUES": "wherevalues",
    "VALUES": "values",
})
RESERVED_TABLES = [
    "_dirty_tables",
    "_hl7_message_log",
    "_hl7_run_log",
    "_security_account_lockouts",
    "_security_audit",
    "_security_devices",
    "_security_login_failures",
    "_security_users",
    "_security_webviewer_sessions",
    "_server_storedvars",
    "_special_notes",
]
RESERVED_FIELDS = [
    x["name"] for x in STANDARD_GENERIC_FIELDSPECS
    if x["name"] not in [MOVE_OFF_TABLET_FIELD, CLIENT_DATE_FIELD]
]
REGEX_WHITESPACE = re.compile("\s")
REGEX_BLOB_HEX = re.compile("""
    ^X'                             # begins with X'
    ([a-fA-F0-9][a-fA-F0-9])+       # one or more hex pairs
    '$                              # ends with '
    """, re.X)  # re.X allows whitespace/comments in regex
REGEX_BLOB_BASE64 = re.compile("""
    ^64'                                # begins with 64'
    (?: [A-Za-z0-9+/]{4} )*             # zero or more quads, followed by...
    (?:
        [A-Za-z0-9+/]{2} [AEIMQUYcgkosw048] =       # a triple then an =
     |                                              # or
        [A-Za-z0-9+/] [AQgw] ==                     # a pair then ==
    )?
    '$                                  # ends with '
    """, re.X)  # re.X allows whitespace/comments in regex
REGEX_INVALID_TABLE_FIELD_CHARS = re.compile("[^a-zA-Z0-9_]")
# ... the ^ within the [] means the expression will match any character NOT in
# the specified range
SQLSEP = ","
SQLQUOTE = "'"


# =============================================================================
# Return message functions/exceptions
# =============================================================================

class UserErrorException(Exception):
    """Exception class for when the input from the tablet is dodgy."""
    pass


class ServerErrorException(Exception):
    """Exception class for when something's broken on the server side."""
    pass


def exception_description(e):
    return "{t}: {m}".format(t=type(e).__name__, m=str(e))


def succeed_generic(operation):
    """Generic success message to tablet."""
    return "CamCOPS: {}".format(operation)


def fail_user_error(msg):
    """Function to abort the script when the input is dodgy."""
    # While Titanium-Android can extract error messages from e.g.
    # finish("400 Bad Request: @_"), Titanium-iOS can't, and we need the error
    # messages. Therefore, we will return an HTTP success code but "Success: 0"
    # in the reply details.
    raise UserErrorException(msg)


def fail_user_error_from_exception(e):
    fail_user_error(exception_description(e))


def fail_server_error(msg):
    """Function to abort the script when something's broken server-side."""
    raise ServerErrorException(msg)


def fail_server_error_from_exception(e):
    fail_server_error(exception_description(e))


def fail_unsupported_operation(operation):
    """Abort the script when the operation is invalid."""
    fail_user_error("operation={}: not supported".format(operation))


# =============================================================================
# CGI handling
# =============================================================================

def get_post_var(form, var, mandatory=True, valtype=None):
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


def get_table_from_post_var(form, var):
    """Retrieves a table name from a CGI form and checks it's a valid
    table."""
    table = get_post_var(form, var, mandatory=True)
    ensure_valid_table_name(table)
    return table


def get_single_field_from_post_var(form, var, mandatory=True):
    """Retrieves a field name from a CGI form and checks it's not a bad
    fieldname."""
    field = get_post_var(form, var, mandatory=mandatory)
    ensure_valid_field_name(field)
    return field


def get_fields_from_post_var(form, var, mandatory=True):
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
    # logger.debug("get_fields_from_post_var: fields={}".format(fields))
    return fields


def get_values_from_post_var(form, var, mandatory=True):
    """Retrieves a list of values from a CSV-separated list of SQL values
    stored in a CGI form (including e.g. NULL, numbers, quoted strings, and
    special handling for base-64/hex-encoded BLOBs.)"""
    csvalues = get_post_var(form, var, mandatory=mandatory)
    if not csvalues:
        return []
    return decode_values(csvalues)


def get_fields_and_values(form, fields_var, values_var, mandatory=True):
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
    return dict(zip(fields, values))


def get_tables_from_post_var(form, var, mandatory=True):
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

def ensure_valid_table_name(t):
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


def ensure_valid_field_name(f):
    """Ensures a field name contains only valid characters, and isn't a
    reserved fieldname that the user isn't allowed to access.
    Raises UserErrorException upon failure."""
    if bool(REGEX_INVALID_TABLE_FIELD_CHARS.search(f)):
        fail_user_error("Field name contains invalid characters: {}".format(f))
    if f in RESERVED_FIELDS:
        fail_user_error(
            "Invalid attempt to access a reserved field name: {}".format(f))


def ensure_valid_user_for_device_registration():
    """Ensure the username/password combination is valid for device
    registration. Raises UserErrorException on failure."""
    if not pls.session.authorized_for_registration():
        fail_user_error(INVALID_USERNAME_PASSWORD)


def ensure_valid_user_for_webstorage(username, device):
    """Ensure the username/password combination is valid for mobileweb storage
    access. Raises UserErrorException on failure."""
    # mobileweb storage is per-user; the device is "mobileweb_USERNAME".
    if device != "mobileweb_" + username:
        fail_user_error("Mobileweb device doesn't match username")
    if not pls.session.authorized_for_webstorage():
        fail_user_error(INVALID_USERNAME_PASSWORD)
    # otherwise, happy


def ensure_device_registered(device):
    """Ensure the device is registered. Raises UserErrorException on
    failure."""
    count = pls.db.fetchvalue(
        "SELECT COUNT(*) FROM _security_devices WHERE device=?",
        device)
    if count == 0:
        fail_user_error("Unregistered device")


def ensure_valid_device_and_user_for_uploading(device):
    """Ensure the device/username/password combination is valid for uploading.
    Raises UserErrorException on failure."""
    if not pls.session.authorized_to_upload():
        fail_user_error(INVALID_USERNAME_PASSWORD)
    # Username/password combination found and is valid. Now check device.
    ensure_device_registered(device)


# =============================================================================
# Conversion to/from quoted SQL values
# =============================================================================

def special_hex_encode(v):
    """Encode in X'{hex}' format."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    # as we never really use this!
    import binascii
    return "X'{}'".format(binascii.hexlify(v))


def special_hex_decode(s):
    """Reverse special_hex_encode()."""
    # SPECIAL HANDLING for BLOBs: a string like X'01FF' means a hex-
    # encoded BLOB. Titanium is rubbish at blobs, so we encode them as
    # special string literals.
    # Hex-encoded BLOB like X'CDE7A24B1A9DBA3148BCB7A0B9DA5BB6A424486C'
    # Strip off the start and end and convert it to a byte array:
    # http://stackoverflow.com/questions/5649407
    return bytearray.fromhex(s[2:-1])


def special_base64_encode(v):
    """Encode in 64'{base64encoded}' format."""
    return "64'{}'".format(base64.b64encode(v))


def special_base64_decode(s):
    """Reverse special_base64_encode()."""
    # OTHER WAY OF DOING BLOBS: base64 encoding
    # e.g. a string like 64'cGxlYXN1cmUu' is a base-64-encoded BLOB
    # (the 64'...' bit is my representation)
    # regex from http://stackoverflow.com/questions/475074
    # better one from http://www.perlmonks.org/?node_id=775820
    return bytearray(base64.b64decode(s[3:-1]))


def escape_newlines(s):
    """Escapes CR, LF, and backslashes.
    Tablet counterpart is unescape_newlines() in conversion.js."""
    # s.encode("string_escape") and s.encode("unicode_escape") are
    # alternatives, but they mess around with quotes, too (specifically,
    # backslash-escaping single quotes).
    if not s:
        return s
    s = s.replace("\\", r"\\")  # replace \ with \\
    s = s.replace("\n", r"\n")  # escape \n; note ord("\n") == 10
    s = s.replace("\r", r"\r")  # escape \r; note ord("\r") == 13
    return s


def unescape_newlines(s):
    """Reverses escape_newlines. Just for testing purposes."""
    # See also http://stackoverflow.com/questions/4020539
    if not s:
        return s
    d = ""  # the destination string
    in_escape = False
    for i in range(len(s)):
        c = s[i]  # the character being processed
        if in_escape:
            if c == "r":
                d += "\r"
            elif c == "n":
                d += "\n"
            else:
                d += c
            in_escape = False
        else:
            if c == "\\":
                in_escape = True
            else:
                d += c
    return d


def encode_single_value(v, is_blob=False):
    """Encodes a value for incorporation into an SQL CSV value string.

    Note that this also escapes newlines (not necessary when receiving data
    from tablets, because those data arrive in CGI forms, but necessary for
    the return journey to the tablet/webclient, because those data get sent in
    a one-record-one-line format.

    The client-side counterpart to this function is decode_single_sql_literal()
    in lib/conversion.js.
    """
    if v is None:
        return "NULL"
    if is_blob:
        return special_base64_encode(v)
    if isinstance(v, basestring):
        return escape_newlines(rnc_db.sql_quote_string(v))
    # for int, float, etc.:
    return str(v)


def gen_items_from_sql_csv(s):
    """Splits a comma-separated list of quoted SQL values, with ' as the quote
    character. Allows escaping of the quote character by doubling it. Returns
    the quotes (and escaped quotes) as part of the result. Allows newlines etc.
    within the string passed."""
    # csv.reader will not both process the quotes and return the quotes;
    # we need them to distinguish e.g. NULL from 'NULL'.
    if not s:
        return
    n = len(s)
    startpos = 0
    pos = 0
    in_quotes = False
    while pos < n:
        if not in_quotes:
            if s[pos] == SQLSEP:
                # end of chunk
                chunk = s[startpos:pos]  # does not include s[pos]
                yield chunk.strip()
                startpos = pos + 1
            elif s[pos] == SQLQUOTE:
                # start of quote
                in_quotes = True
        else:
            if pos < n - 1 and s[pos] == SQLQUOTE and s[pos + 1] == SQLQUOTE:
                # double quote, '', is an escaped quote, not end of quote
                pos += 1  # skip one more than we otherwise would
            elif s[pos] == SQLQUOTE:
                # end of quote
                in_quotes = False
        pos += 1
    # Last chunk
    yield s[startpos:].strip()


def decode_single_value(v):
    """Takes a string representing an SQL value. Returns the value. Value
    types/examples:

        int         35
                    -12
        float       7.23
        str         'hello, here''s an apostrophe'
            (starts and ends with a quote)
        NULL        NULL
            (case-insensitive)
        BLOB        X'4D7953514C'
            (hex-encoded; matches MySQL method;
            http://dev.mysql.com/doc/refman/5.0/en/hexadecimal-literals.html)
        BLOB        64'TXlTUUw='
            (base-64-encoded; this notation is my invention)

    But
        - we use ISO-8601 text for dates/times

    The client-side counterpart to this function is SQLite's QUOTE() function
    (see getRecordByPK_lowmem() in lib/dbsqlite.js), except in the case of
    BLOBs (when it's getEncodedBlob() in table/Blob.js); see lib/dbupload.js.
    """

    if not v:
        # shouldn't happen; treat it as a NULL
        return None
    if v.upper() == "NULL":
        return None

    # special BLOB encoding here
    t = REGEX_WHITESPACE.sub("", v)
    # t is a copy of v with all whitespace removed. We remove whitespace in
    # some cases because some base-64 encoders insert newline characters
    # (e.g. Titanium iOS).
    if REGEX_BLOB_HEX.match(t):
        # logger.debug("MATCHES HEX-ENCODED BLOB")
        return special_hex_decode(t)
    if REGEX_BLOB_BASE64.match(t):
        # logger.debug("MATCHES BASE64-ENCODED BLOB")
        return special_base64_decode(t)

    if len(v) >= 2 and v[0] == SQLQUOTE and v[-1] == SQLQUOTE:
        # v is a quoted string
        s = rnc_db.sql_dequote_string(v)
        # s is the underlying string that the source started with
        # logger.debug("UNDERLYING STRING: {}".format(s))
        return s

    # Not a quoted string.
    # int?
    try:
        return int(v)
    except:
        pass
    # float?
    try:
        return float(v)
    except:
        pass
    # Who knows; something odd. Allow it as a string. "Be conservative in what
    # you send, liberal in what you accept", and all that.
    return v


def decode_values(valuelist):
    """Takes a SQL CSV value list and returns the corresponding list of decoded
    values."""
    # logger.debug("decode_values: valuelist={}".format(valuelist))
    v = [decode_single_value(v) for v in gen_items_from_sql_csv(valuelist)]
    # logger.debug("decode_values: values={}".format(v))
    return v


def delimit(f):
    """Delimits a field for SQL queries."""
    return pls.db.delimit(f)


# =============================================================================
# Sending stuff to the client
# =============================================================================

def nvp(name, value):
    """Returns name/value pair in 'name:value\n' format."""
    return u"{}:{}\n".format(name, value)


def get_server_id_info():
    """Returns a reply for the tablet giving details of the server."""
    reply = {
        "databaseTitle": pls.DATABASE_TITLE,
        "idPolicyUpload": pls.ID_POLICY_UPLOAD_STRING,
        "idPolicyFinalize": pls.ID_POLICY_FINALIZE_STRING,
        "serverCamcopsVersion": cc_version.CAMCOPS_SERVER_VERSION,
    }
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        i = n - 1
        nstr = str(n)
        reply["idDescription" + nstr] = pls.IDDESC[i]
        reply["idShortDescription" + nstr] = pls.IDSHORTDESC[i]
    return reply


# =============================================================================
# CamCOPS table functions
# =============================================================================

def get_server_pks_of_active_records(device, table):
    """Gets server PKs of active records (_current and in the 'NOW' era) for
    the specified device/table."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    return pls.db.fetchallfirstvalues(query, *args)


def record_exists(device, table, clientpk_name, clientpk_value):
    """Checks if a record exists, using the device's perspective of a
    table/client PK combination.
    Returns (exists, serverpk), where exists is Boolean.
    If exists is False, serverpk will be None."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device=? AND _current AND _era='{now}' AND {cpk}=?
    """.format(
        table=table,
        now=ERA_NOW,
        cpk=delimit(clientpk_name),
    )
    args = [device, clientpk_value]
    pklist = pls.db.fetchallfirstvalues(query, *args)
    exists = bool(len(pklist) >= 1)
    serverpk = pklist[0] if exists else None
    return (exists, serverpk)
    # Consider a warning/failure if we have >1 row meeting these criteria.
    # Not currently checked for.


def get_server_pks_of_specified_records(device, table, wheredict):
    """Retrieves server PKs for a table, for a given device, given a set of
    'where' conditions specified in wheredict (as field/value combinations,
    joined with AND)."""
    query = """
        SELECT _pk FROM {table}
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    query = append_where_sql_and_values(query, args, wheredict=wheredict)
    return pls.db.fetchallfirstvalues(query, *args)


def append_where_sql_and_values(query, args, wheredict=[], wherenotdict=[]):
    """Appends a set of conditions, joined with AND, to the WHERE clause of
    an SQL query. Note that there WHERE clause must already have been started.
    Allows WHERE and WHERE NOT clauses.

    MODIFIES the args argument in place, and returns an extended query."""
    if wheredict:
        for wherefield, wherevalue in wheredict.iteritems():
            if wherevalue is None:
                query += " AND {} IS NULL".format(delimit(wherefield))
            else:
                query += " AND {} = ?".format(delimit(wherefield))
                args.append(wherevalue)
    if wherenotdict:
        for wnfield, wnvalue in wherenotdict.iteritems():
            if wnvalue is None:
                query += " AND {} IS NOT NULL".format(delimit(wnfield))
            else:
                query += " AND {} <> ?".format(delimit(wnfield))
                args.append(wnvalue)
    return query


def count_records(device, table, wheredict, wherenotdict):
    """Returns a count of records for a device/table combination, subject to
    WHERE and WHERE NOT fields (combined with AND)."""
    query = """
        SELECT COUNT(*) FROM {table}
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    query = append_where_sql_and_values(query, args, wheredict=wheredict,
                                        wherenotdict=wherenotdict)
    return pls.db.fetchvalue(query, *args)


def select_records_with_specified_fields(device, table, wheredict,
                                         wherenotdict, fields):
    """Returns a list of rows, for specified fields in a device/table
    combination, subject to WHERE and WHERE NOT conditions (joined by AND)."""
    fieldlist = ",".join([delimit(x) for x in fields])
    query = """
        SELECT {fieldlist} FROM {table}
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        fieldlist=fieldlist,
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    query = append_where_sql_and_values(query, args, wheredict=wheredict,
                                        wherenotdict=wherenotdict)
    return pls.db.fetchall(query, *args)


def get_max_client_pk(device, table, clientpk_name):
    """Retrieves the maximum current client PK in a given device/table
    combination, or None."""
    query = """
        SELECT MAX({cpk}) FROM {table}
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        cpk=delimit(clientpk_name),
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    return pls.db.fetchvalue(query, *args)


def webclient_delete_records(device, user, table, wheredict):
    """Deletes records from a table, from a mobileweb client's perspective,
    where a 'device' is 'mobileweb_{username}'."""
    query = """
        UPDATE {table}
        SET
            _successor_pk=NULL,
            _current=0,
            _removal_pending=0,
            _removing_user=?,
            _when_removed_exact=?,
            _when_removed_batch_utc=?
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [
        user,
        pls.NOW_LOCAL_TZ_ISO8601,
        pls.NOW_UTC_NO_TZ,
        device,
    ]
    query = append_where_sql_and_values(query, args, wheredict=wheredict)
    pls.db.db_exec(query, *args)


def record_identical_full(table, serverpk, wheredict):
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
    return (count > 0)


def record_identical_by_date(table, serverpk, client_date_value):
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
    return (count > 0)


def upload_record_core(device, table, clientpk_name, valuedict, recordnum,
                       tablet_camcops_version):
    """Uploads a record. Deals with IDENTICAL, NEW, and MODIFIED records."""
    clientpk_value = valuedict[clientpk_name]
    found, oldserverpk = record_exists(device, table, clientpk_name,
                                       clientpk_value)
    newserverpk = None
    if found:
        client_date_value = valuedict[CLIENT_DATE_FIELD]
        if record_identical_by_date(table, oldserverpk, client_date_value):
            # IDENTICAL. No action needed...
            # UNLESS MOVE_OFF_TABLET_FIELDNAME is set
            if valuedict[MOVE_OFF_TABLET_FIELD]:
                flag_record_for_preservation(table, oldserverpk)
                logger.debug(
                    "Table {table}, uploaded record {recordnum}: identical "
                    "but moving off tablet".format(
                        table=table,
                        recordnum=recordnum,
                    )
                )
            else:
                logger.debug(
                    "Table {table}, uploaded record {recordnum}: "
                    "identical".format(
                        table=table,
                        recordnum=recordnum,
                    )
                )
        else:
            # MODIFIED
            newserverpk = insert_record(device, table, valuedict, oldserverpk,
                                        tablet_camcops_version)
            flag_modified(device, table, oldserverpk, newserverpk)
            logger.debug("Table {table}, record {recordnum}: modified".format(
                table=table,
                recordnum=recordnum,
            ))
    else:
        # NEW
        newserverpk = insert_record(device, table, valuedict, None,
                                    tablet_camcops_version)
    return oldserverpk, newserverpk


def insert_record(device, table, valuedict, predecessor_pk,
                  tablet_camcops_version):
    """Inserts a record, or raises an exception if that fails."""
    mark_table_dirty(device, table)
    valuedict.update({
        "_device": device,
        "_era": ERA_NOW,
        "_current": 0,
        "_addition_pending": 1,
        "_removal_pending": 0,
        "_predecessor_pk": predecessor_pk,
        "_camcops_version": tablet_camcops_version,
    })
    return pls.db.insert_record_by_dict(table, valuedict)


def duplicate_record(device, table, serverpk):
    """Duplicates the record defined by the table/serverpk combination.
    Will raise an exception if the insert fails. Otherwise...
    The old record then NEEDS MODIFICATION by flag_modified().
    The new record NEEDS MODIFICATION by update_new_copy_of_record().
    """
    mark_table_dirty(device, table)
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


def update_new_copy_of_record(table, serverpk, valuedict, predecessor_pk,
                              tablet_camcops_version):
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
    args = [predecessor_pk, tablet_camcops_version]
    for f, v in valuedict.iteritems():
        query += ", {}=?".format(delimit(f))
        args.append(v)
    query += " WHERE _pk=?"
    args.append(serverpk)
    pls.db.db_exec(query, *args)


# =============================================================================
# Batch (atomic) upload and preserving
# =============================================================================

def get_device_upload_batch_details(device, user):
    """Gets a (upload_batch_utc, currently_preserving) tuple.

    upload_batch_utc: the batchtime; UTC date/time of the current upload batch.
    currently_preserving: Boolean; whether preservation (shifting to an older
        era) is currently taking place.

    SIDE EFFECT: if the username is different from the username that started
    a previous upload batch for this device, we restart the upload batch (thus
    rolling back previous pending changes).
    """
    query = """
        SELECT ongoing_upload_batch_utc, uploading_user, currently_preserving
        FROM _security_devices
        WHERE device=?
    """
    args = [device]
    row = pls.db.fetchone(query, *args)
    if not row:
        return None, None
    upload_batch_utc, uploading_user, currently_preserving = row
    if not upload_batch_utc or uploading_user != user:
        # SIDE EFFECT: if the username changes, we restart (and thus roll back
        # previous pending changes)
        start_device_upload_batch(device, user)
        return pls.NOW_UTC_NO_TZ
    logger.debug(
        "get_device_upload_batch_details: upload_batch_utc = {}".format(
            repr(upload_batch_utc)))
    return upload_batch_utc, currently_preserving


def start_device_upload_batch(device, user):
    """Starts an upload batch for a device."""
    rollback_all(device)
    pls.db.db_exec("""
        UPDATE _security_devices
        SET
            last_upload_batch_utc=?,
            ongoing_upload_batch_utc=?,
            uploading_user=?
        WHERE device=?
    """, pls.NOW_UTC_NO_TZ, pls.NOW_UTC_NO_TZ, user, device)


def end_device_upload_batch(device, user, batchtime, preserving):
    """Ends an upload batch, committing all changes made thus far."""
    commit_all(device, user, batchtime, preserving)
    pls.db.db_exec("""
        UPDATE _security_devices
        SET
            ongoing_upload_batch_utc=NULL,
            uploading_user=NULL,
            currently_preserving=0
        WHERE device=?
    """, device)


def start_preserving(device):
    """Starts preservation (the process of moving records from the NOW era to
    an older era, so they can be removed safely from the tablet)."""
    pls.db.db_exec("""
        UPDATE _security_devices
        SET currently_preserving=1
        WHERE device=?
    """, device)


def mark_table_dirty(device, table):
    """Marks a table as having been modified during the current upload."""
    pls.db.db_exec("""
        REPLACE INTO _dirty_tables
            (device, tablename)
        VALUES (?,?)
    """, device, table)
    # http://dev.mysql.com/doc/refman/5.0/en/replace.html


def get_dirty_tables(device):
    """Returns tables marked as dirty for this device."""
    return pls.db.fetchallfirstvalues(
        "SELECT tablename FROM _dirty_tables WHERE device=?",
        device)


def flag_deleted(device, table, pklist):
    """Marks record(s) as deleted, specified by a list of server PKs."""
    mark_table_dirty(device, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _pk=?
    """.format(table=table)
    for pk in pklist:
        pls.db.db_exec(query, pk)


def flag_all_records_deleted(device, table):
    """Marks all records in a table as deleted (that are current and in the
    current era)."""
    mark_table_dirty(device, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    pls.db.db_exec(query, device)


def flag_deleted_where_clientpk_not(device, table, clientpk_name,
                                    clientpk_values):
    """Marks for deletion all current/current-era records for a device, defined
    by a list of client-side PK values."""
    mark_table_dirty(device, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=NULL
        WHERE _device=? AND _current AND _era='{now}'
    """.format(
        table=table,
        now=ERA_NOW,
    )
    args = [device]
    wherelist = []
    for cpk in clientpk_values:
        wherelist.append("{}=?".format(delimit(clientpk_name)))
        args.append(cpk)
    if wherelist:
        query += " AND NOT ({nots})".format(nots=" OR ".join(wherelist))
    pls.db.db_exec(query, *args)


def flag_modified(device, table, pk, successor_pk):
    """Marks a record as old, storing its successor's details."""
    mark_table_dirty(device, table)
    query = """
        UPDATE {table}
        SET _removal_pending=1, _successor_pk=?
        WHERE _pk=?
    """.format(
        table=table,
    )
    pls.db.db_exec(query, successor_pk, pk)


def flag_record_for_preservation(table, pk):
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


def commit_all(device, user, batchtime, preserving):
    """Commits additions, removals, and preservations for all tables."""
    tables = get_dirty_tables(device)
    auditsegments = []
    for table in tables:
        n_added, n_removed, n_preserved = commit_table(
            device, user, batchtime, preserving, table, clear_dirty=False)
        auditsegments.append(
            "{table} ({n_added},{n_removed},{n_preserved})".format(
                table=table,
                n_added=n_added,
                n_removed=n_removed,
                n_preserved=n_preserved,
            )
        )
    clear_dirty_tables(device)
    details = "Upload [table (n_added,n_removed,n_preserved)]: {}".format(
        ", ".join(auditsegments)
    )
    audit(details, user=user, device=device)


def commit_table(device, user, batchtime, preserving, table,
                 clear_dirty=True):
    """Commits additions, removals, and preservations for one table."""
    exacttime = pls.NOW_LOCAL_TZ_ISO8601
    # Additions
    query = """
        UPDATE {table}
        SET
            _current=1,
            _addition_pending=0,
            _adding_user=?,
            _when_added_exact=?,
            _when_added_batch_utc=?
        WHERE _device=? AND _addition_pending
    """.format(table=table)
    n_added = pls.db.db_exec(query, user, exacttime, batchtime, device)
    # Removals
    query = """
        UPDATE {table}
        SET
            _current=0,
            _removal_pending=0,
            _removing_user=?,
            _when_removed_exact=?,
            _when_removed_batch_utc=?
        WHERE _device=? AND _removal_pending
    """.format(table=table)
    n_removed = pls.db.db_exec(query, user, exacttime, batchtime, device)
    # Preservation
    new_era = cc_dt.format_datetime(batchtime, DATEFORMAT.ERA)
    if preserving:
        # Preserve all relevant records
        query = """
            UPDATE {table}
            SET
                _era=?,
                _preserving_user=?,
                {MOVE_OFF_TABLET_FIELD}=0
            WHERE _device=? AND _era='{now}'
        """.format(
            table=table,
            MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
            now=ERA_NOW,
        )
        n_preserved = pls.db.db_exec(query, new_era, user, device)
        # Also preserve/finalize any corresponding special notes (2015-02-01)
        # NOTE DIFFERENT FIELDNAMES.
        query = """
            UPDATE  _special_notes
            SET     era=?
            WHERE   basetable=?
            AND     device=?
            AND     era='{now}'
        """.format(now=ERA_NOW)
        pls.db.db_exec(query, new_era, table, device)
    else:
        # Preserve any individual records
        query = """
            UPDATE {table}
            SET
                _era=?,
                _preserving_user=?,
                {MOVE_OFF_TABLET_FIELD}=0
            WHERE _device=? AND {MOVE_OFF_TABLET_FIELD}
        """.format(
            table=table,
            MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
        )
        n_preserved = pls.db.db_exec(query, new_era, user, device)
        # Also preserve/finalize any corresponding special notes (2015-02-01)
        # NOTE DIFFERENT FIELDNAMES.
        query = """
            UPDATE  _special_notes s
            SET     s.era=?
            WHERE   s.basetable=?
            AND     s.device=?
            AND     s.era='{now}'
            AND     EXISTS (
                SELECT  *
                FROM    {table} t
                WHERE   t.id = s.task_id
                AND     t._device = s.device
                AND     t._era = ?
            )
        """.format(now=ERA_NOW, table=table)
        pls.db.db_exec(query, new_era, table, device, new_era)
    # Remove individually from list of dirty tables?
    if clear_dirty:
        pls.db.db_exec(
            "DELETE FROM _dirty_tables WHERE device=? AND tablename=?",
            device,
            table
        )
        # ... otherwise a call to clear_dirty_tables() must be made.
    return n_added, n_removed, n_preserved


def rollback_all(device):
    """Rolls back all pending changes for a device."""
    tables = get_dirty_tables(device)
    for table in tables:
        rollback_table(device, table)
    clear_dirty_tables(device)


def rollback_table(device, table):
    """Rolls back changes for an individual table for a device."""
    # Pending additions
    pls.db.db_exec(
        "DELETE FROM {table} WHERE _device=? AND _addition_pending".format(
            table=table
        ),
        device
    )
    # Pending deletions
    query = """
        UPDATE {table}
        SET
            _removal_pending=0,
            _when_removed_exact=NULL,
            _when_removed_batch_utc=NULL,
            _removing_user=NULL,
            _successor_pk=NULL
        WHERE _device=? AND _removal_pending
    """.format(table=table)
    pls.db.db_exec(query, device)
    # Record-specific preservation (set by flag_record_for_preservation())
    query = """
        UPDATE {table}
        SET
            {MOVE_OFF_TABLET_FIELD}=0
        WHERE _device=?
    """.format(
        table=table,
        MOVE_OFF_TABLET_FIELD=MOVE_OFF_TABLET_FIELD,
    )
    pls.db.db_exec(query, device)


def clear_dirty_tables(device):
    """Clears the dirty-table list for a device."""
    pls.db.db_exec("DELETE FROM _dirty_tables WHERE device=?", device)


# =============================================================================
# Audit functions
# =============================================================================

def audit(*args, **kwargs):
    """Audit something."""
    # Add parameters and pass on:
    kwargs["from_dbclient"] = True
    kwargs["remote_addr"] = pls.remote_addr
    cc_audit.audit(*args, **kwargs)


# =============================================================================
# Actions
# =============================================================================

def register_device(device, user, device_friendly_name,
                    tablet_camcops_version):
    """Registers a device with the server."""
    table = "_security_devices"
    count = pls.db.fetchvalue(
        "SELECT COUNT(*) FROM {table} WHERE device=?".format(table=table),
        device)
    if count > 0:
        # device already registered, but accept re-registration
        query = """
            UPDATE {table}
            SET
                friendly_name=?,
                camcops_version=?,
                registered_by_user=?,
                when_registered_utc=?
            WHERE device=?
        """.format(table=table)
        pls.db.db_exec(query, device_friendly_name, tablet_camcops_version,
                       user, pls.NOW_UTC_NO_TZ, device)
    else:
        # new registration
        valuedict = {
            "device": device,
            "friendly_name": device_friendly_name,
            "camcops_version": tablet_camcops_version,
            "registered_by_user": user,
            "when_registered_utc": pls.NOW_UTC_NO_TZ,
        }
        newpk = pls.db.insert_record_by_dict(table, valuedict)
        if newpk is None:
            fail_user_error(INSERT_FAILED)
    audit("register, friendly_name={}".format(device_friendly_name),
          user=user, device=device, table=table)


# =============================================================================
# Action processors: allowed to any user
# =============================================================================
# If they return None, the framework uses the operation name as the reply in
# the success message. Not returning anything is the same as returning None.
# Authentication is performed in advance of these.

def check_device_registered(form):
    """Check that a device is registered, or raise UserErrorException."""
    device = get_post_var(form, PARAM.DEVICE)
    ensure_device_registered(device)


# =============================================================================
# Action processors that require REGISTRATION privilege
# =============================================================================

def register(form):
    """Register a device with the server."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    device_friendly_name = get_post_var(form, "devicefriendlyname",
                                        mandatory=False)
    camcops_version = get_post_var(form, PARAM.CAMCOPS_VERSION,
                                   mandatory=False)
    register_device(device, user, device_friendly_name, camcops_version)
    return get_server_id_info()


# =============================================================================
# Action processors that require UPLOAD privilege
# =============================================================================

def check_upload_user_and_device(form):
    """Stub function for the operation to check that a user is valid."""
    pass  # don't need to do anything!


def get_id_info(form):
    """Fetch server ID information."""
    return get_server_id_info()


def start_upload(form):
    """Begin an upload."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    start_device_upload_batch(device, user)


def end_upload(form):
    """Ends an upload and commits changes."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    batchtime, preserving = get_device_upload_batch_details(device, user)
    # ensure it's the same user finishing as starting!
    end_device_upload_batch(device, user, batchtime, preserving)


def upload_table(form):
    """Upload a table. Incoming information in the CGI form includes a CSV list
    of fields, a count of the number of records being provided, and a set of
    CGI variables named record0 ... record{nrecords}, each containing a CSV
    list of SQL-encoded values. Typically used for smaller tables, i.e. most
    except for BLOBs."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    camcops_version = get_post_var(form, PARAM.CAMCOPS_VERSION,
                                   mandatory=False)
    table = get_table_from_post_var(form, PARAM.TABLE)
    fields = get_fields_from_post_var(form, PARAM.FIELDS)
    nrecords = get_post_var(form, PARAM.NRECORDS, valtype=int)

    nfields = len(fields)
    if nfields < 1:
        fail_user_error("nfields={}: can't be less than 1".format(nfields))
    if nrecords < 0:
        fail_user_error("nrecords={}: can't be less than 0".format(nrecords))

    batchtime, preserving = get_device_upload_batch_details(device, user)
    clientpk_name = fields[0]
    server_uploaded_pks = []
    new_or_updated = 0
    server_active_record_pks = get_server_pks_of_active_records(device, table)
    mark_table_dirty(device, table)
    for r in range(nrecords):
        recname = "record{}".format(r)
        values = get_values_from_post_var(form, recname)
        nvalues = len(values)
        if nvalues != nfields:
            fail_user_error(
                "Number of fields in field list ({nfields}) doesn't match "
                "number of values in record {r} ({nvalues})".format(
                    nfields=nfields, r=r, nvalues=nvalues))
        valuedict = dict(zip(fields, values))
        # CORE: CALLS upload_record_core
        oldserverpk, newserverpk = upload_record_core(
            device, table, clientpk_name, valuedict, r, camcops_version)
        new_or_updated += 1
        server_uploaded_pks.append(oldserverpk)

    # Now deal with any ABSENT (not in uploaded data set) conditions.
    server_pks_for_deletion = [x for x in server_active_record_pks
                               if x not in server_uploaded_pks]
    flag_deleted(device, table, server_pks_for_deletion)

    # Success
    logger.debug("server_active_record_pks: {}".format(
        server_active_record_pks))
    logger.debug("server_uploaded_pks: {}".format(server_uploaded_pks))
    logger.debug("server_pks_for_deletion: {}".format(
        server_pks_for_deletion))
    logger.debug("Table {table}, number of missing records (deleted): "
                 "{d}".format(table=table, d=len(server_pks_for_deletion)))
    # Auditing occurs at commit_all.
    logger.info("Upload successful; {n} records uploaded to table {t}".format(
        n=nrecords, t=table))
    return "Table {} upload successful".format(table)


def upload_record(form):
    """Upload an individual record. (Typically used for BLOBs.) Incoming
    CGI information includes a CSV list of fields and a CSV list of values."""
    device = get_post_var(form, PARAM.DEVICE)
    # user = get_post_var(form, PARAM.USER)
    camcops_version = get_post_var(form, PARAM.CAMCOPS_VERSION,
                                   mandatory=False)
    table = get_table_from_post_var(form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(form, PARAM.PKNAME)
    valuedict = get_fields_and_values(form, PARAM.FIELDS, PARAM.VALUES)

    if clientpk_name not in valuedict:
        fail_user_error("PK ({}) not in field list".format(clientpk_name))
    clientpk_value = valuedict[clientpk_name]
    wheredict = {clientpk_name: clientpk_value}

    serverpks = get_server_pks_of_specified_records(device, table, wheredict)
    if not serverpks:
        # Insert
        insert_record(device, table, valuedict, None, camcops_version)
        logger.info("upload-insert")
        return "UPLOAD-INSERT"
    else:
        # Update
        oldserverpk = serverpks[0]
        newserverpk = duplicate_record(device, table, oldserverpk)
        flag_modified(device, table, oldserverpk, newserverpk)
        update_new_copy_of_record(table, newserverpk, valuedict, oldserverpk,
                                  camcops_version)
        logger.info("upload-update")
        return "UPLOAD-UPDATE"
    # Auditing occurs at commit_all.


def upload_empty_tables(form):
    """The tablet supplies a list of tables that are empty at its end, and we
    will 'wipe' all appropriate tables; this reduces the number of HTTP
    requests."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    tables = get_tables_from_post_var(form, PARAM.TABLES)

    batchtime, preserving = get_device_upload_batch_details(device, user)
    for table in tables:
        flag_all_records_deleted(device, table)
    logger.info("upload_empty_tables")
    # Auditing occurs at commit_all.
    return "UPLOAD-EMPTY-TABLES"


def start_preservation(form):
    """Marks this upload batch as one in which all records will be preserved
    (i.e. moved from NOW-era to an older era, so they can be deleted safely
    from the tablet).

    Without this, individual records can still be marked for preservation if
    their MOVE_OFF_TABLET_FIELD field (_move_off_tablet) is set; see
    upload_record and its functions."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)

    batchtime, preserving = get_device_upload_batch_details(device, user)
    start_preserving(device)
    logger.info("start_preservation successful")
    # Auditing occurs at commit_all.
    return "STARTPRESERVATION"


def delete_where_key_not(form):
    """Marks records for deletion, for a device/table, where the client PK
    is not in a specified list."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(form, PARAM.PKNAME)
    clientpk_values = get_values_from_post_var(form, PARAM.PKVALUES)

    batchtime, preserving = get_device_upload_batch_details(device, user)
    flag_deleted_where_clientpk_not(device, table, clientpk_name,
                                    clientpk_values)
    # Auditing occurs at commit_all.
    logger.info("delete_where_key_not successful; table {} trimmed".format(
        table))
    return "Trimmed"


def which_keys_to_send(form):
    """Intended use: "For my device, and a specified table, here are my client-
    side PKs (as a CSV list), and the modification dates for each corresponding
    record (as a CSV list). Please tell me which records have mismatching dates
    on the server, i.e. those that I need to re-upload."

    Used particularly for BLOBs, to reduce traffic, i.e. so we don't have to
    send a lot of BLOBs."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(form, PARAM.PKNAME)
    clientpk_values = get_values_from_post_var(form, PARAM.PKVALUES,
                                               mandatory=False)
    client_dates = get_values_from_post_var(form, PARAM.DATEVALUES,
                                            mandatory=False)

    npkvalues = len(clientpk_values)
    ndatevalues = len(client_dates)
    if npkvalues != ndatevalues:
        fail_user_error(
            "Number of PK values ({npk}) doesn't match number of dates "
            "({nd})".format(npk=npkvalues, nd=ndatevalues))

    batchtime, preserving = get_device_upload_batch_details(device, user)

    # 1. The client sends us all its PKs. So "delete" anything not in that
    #    list.
    flag_deleted_where_clientpk_not(device, table, clientpk_name,
                                    clientpk_values)

    # 2. See which ones are new or updates.
    pks_needed = []
    for i in range(npkvalues):
        clientpkval = clientpk_values[i]
        client_date_value = client_dates[i]
        found, serverpk = record_exists(device, table, clientpk_name,
                                        clientpkval)
        if not found or not record_identical_by_date(table, serverpk,
                                                     client_date_value):
            pks_needed.append(clientpkval)

    # Success
    pk_csv_list = ",".join([str(x) for x in pks_needed if x is not None])
    logger.info("which_keys_to_send successful: table {}".format(table))
    return pk_csv_list


# =============================================================================
# Action processors that require MOBILEWEB privilege
# =============================================================================

def count(form):
    """Count records in a table, given a set of WHERE/WHERE NOT conditions,
    joined by AND."""
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    wheredict = get_fields_and_values(form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)
    wherenotdict = get_fields_and_values(form, PARAM.WHERENOTFIELDS,
                                         PARAM.WHERENOTVALUES, mandatory=False)
    c = count_records(device, table, wheredict, wherenotdict)
    auditstring = ("webclient SELECT COUNT(*) FROM {t} WHERE {w} AND WHERE "
                   "NOT {wn}".format(t=table, w=wheredict, wn=wherenotdict))
    logger.debug(auditstring)
    audit(auditstring, user=user, device=device, table=table)
    logger.info("COUNT")
    return c


def select(form):
    """Select fields from a table, specified by WHERE/WHERE NOT criteria,
    joined by AND. Return format:
        nfields:X
        fields:X
        nrecords:X
        record0:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
            ...
        record{n}:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
    """
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    fields = get_fields_from_post_var(form, PARAM.FIELDS)
    wheredict = get_fields_and_values(form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)
    wherenotdict = get_fields_and_values(form, PARAM.WHERENOTFIELDS,
                                         PARAM.WHERENOTVALUES, mandatory=False)

    # Select records
    rows = select_records_with_specified_fields(device, table, wheredict,
                                                wherenotdict, fields)
    nrecords = len(rows)

    # Send results back to user
    # .... even though this probably reinvents what the client sent us!
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

    auditstring = (
        "webclient SELECT {f} FROM {t} WHERE {w} AND WHERE NOT {wn}".format(
            f=",".join(fields),
            t=table,
            w=wheredict,
            wn=wherenotdict,
        )
    )
    logger.debug(auditstring)
    audit(auditstring, user=user, device=device, table=table)
    logger.info("SELECT")
    return reply


def insert(form):
    """Mobileweb client non-transactional INSERT."""
    # Non-transactional
    #
    # Don't need to pay special attention to "id" (clientpk_name) field, to
    # ensure it remains unique per device/table for current records, because we
    # always create a new such value (clientpk_value below) and return it.
    # Potential for failure if two clients did this at the same time *for the
    # same device*, but that means the same user, so the advice is simply not
    # to do that.
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    clientpk_name = get_single_field_from_post_var(form, PARAM.PKNAME)
    valuedict = get_fields_and_values(form, PARAM.FIELDS, PARAM.VALUES)
    camcops_version = get_post_var(form, PARAM.CAMCOPS_VERSION,
                                   mandatory=False)

    max_client_pk = get_max_client_pk(device, table, clientpk_name)
    if max_client_pk is None:
        max_client_pk = 0
    clientpk_value = max_client_pk + 1
    valuedict[clientpk_name] = clientpk_value
    serverpk = insert_record(device, table, valuedict, None, camcops_version)
    commit_table(device, user, pls.NOW_UTC_NO_TZ, False, table)
    audit("webclient INSERT", user=user, device=device, table=table,
          server_pk=serverpk)
    logger.info("INSERT")
    return clientpk_value


def update(form):
    """Mobileweb client non-transactional UPDATE."""
    # Non-transactional
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    valuedict = get_fields_and_values(form, PARAM.FIELDS, PARAM.VALUES)
    wheredict = get_fields_and_values(form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)
    camcops_version = get_post_var(form, PARAM.CAMCOPS_VERSION,
                                   mandatory=False)

    serverpks = get_server_pks_of_specified_records(device, table, wheredict)
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
        newserverpk = duplicate_record(device, table, serverpk)
        flag_modified(device, table, serverpk, newserverpk)
        update_new_copy_of_record(table, newserverpk, valuedict, serverpk,
                                  camcops_version)
        audit("webclient UPDATE: old record deactivated",
              user=user, device=device, table=table, server_pk=serverpk)
        audit("webclient UPDATE: new record inserted",
              user=user, device=device, table=table, server_pk=newserverpk)
    commit_table(device, user, pls.NOW_UTC_NO_TZ, False, table)
    logger.info("UPDATE")
    return "Updated"


def delete(form):
    """Mobileweb client non-transactional DELETE."""
    # Non-transactional
    device = get_post_var(form, PARAM.DEVICE)
    user = get_post_var(form, PARAM.USER)
    table = get_table_from_post_var(form, PARAM.TABLE)
    wheredict = get_fields_and_values(form, PARAM.WHEREFIELDS,
                                      PARAM.WHEREVALUES, mandatory=False)

    webclient_delete_records(device, user, table, wheredict)
    # ... doesn't need a separate commit_table
    audit("webclient DELETE WHERE {}".format(wheredict),
          user=user, device=device, table=table)
    logger.info("DELETE")
    return "Deleted"


# =============================================================================
# Action maps
# =============================================================================

OPERATIONS_ANYONE = {
    "check_device_registered": check_device_registered,
}
OPERATIONS_REGISTRATION = {
    "register": register,
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
    "count": count,
    "select": select,
    "insert": insert,
    "update": update,
    "delete": delete,
}


# =============================================================================
# Main action processor
# =============================================================================

def main_http_processor(env):
    """Main HTTP processor."""
    # For success, returns:
    #   text:   main text to send (will use status '200 OK')
    # For failure, raises an exception.

    logger.info("CamCOPS database script starting at {}".format(
        cc_dt.format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.ISO8601)
    ))
    form = ws.get_cgi_fieldstorage_from_wsgi_env(env)

    # if pls.DBCLIENT_LOGLEVEL <= logging.DEBUG:
    #    # Raw environment will not include database password (that's in the
    #    # config file). However, the raw CGI form will include the client's
    #    # cleartext password.

    #    # logger.debug("Environment: {}".format(env))
    #    cleanform = dict([
    #        (k, form.getvalue(k) if k != PARAM.PASSWORD else "*"*8)
    #        for k in form.keys()
    #    ])
    #    logger.debug("CGI form: {}".format(cleanform))

    if not ws.cgi_method_is_post(env):
        fail_user_error("Must use POST method")

    operation = ws.get_cgi_parameter_str(form, PARAM.OPERATION)
    device = ws.get_cgi_parameter_str(form, PARAM.DEVICE)
    username = ws.get_cgi_parameter_str(form, PARAM.USER)
    password = ws.get_cgi_parameter_str(form, PARAM.PASSWORD)
    session_id = ws.get_cgi_parameter_str(form, PARAM.SESSION_ID)
    session_token = ws.get_cgi_parameter_str(form, PARAM.SESSION_TOKEN)
    tablet_version = ws.get_cgi_parameter_float(form, PARAM.CAMCOPS_VERSION)

    if (tablet_version is None
            or tablet_version < cc_version.MINIMUM_TABLET_VERSION):
        fail_user_error(
            "Tablet CamCOPS version too old: is {v}, need {r}".format(
                v=tablet_version,
                r=cc_version.MINIMUM_TABLET_VERSION))

    cc_session.establish_session_for_tablet(
        session_id, session_token, pls.remote_addr, username, password)

    logger.info(
        "Incoming connection from IP={i}, port={p}, device={d}, user={u}, "
        "operation={o}".format(
            i=pls.remote_addr,
            p=pls.remote_port,
            d=device,
            u=username,
            o=operation,
        )
    )

    fn = None

    if operation in OPERATIONS_ANYONE.keys():
        fn = OPERATIONS_ANYONE.get(operation)

    if operation in OPERATIONS_REGISTRATION.keys():
        ensure_valid_user_for_device_registration()
        fn = OPERATIONS_REGISTRATION.get(operation)

    if operation in OPERATIONS_UPLOAD.keys():
        ensure_valid_device_and_user_for_uploading(device)
        fn = OPERATIONS_UPLOAD.get(operation)

    if pls.ALLOW_MOBILEWEB:
        if operation in OPERATIONS_MOBILEWEB.keys():
            ensure_valid_user_for_webstorage(username, device)
            fn = OPERATIONS_MOBILEWEB.get(operation)

    if not fn:
        fail_unsupported_operation(operation)
    result = fn(form)
    if result is None:
        result = {PARAM.RESULT: operation}
    elif not isinstance(result, dict):
        result = {PARAM.RESULT: result}
    return result


# =============================================================================
# WSGI application
# =============================================================================

def database_wrapper(environ, start_response):
    """WSGI application entry point.

    Provides a wrapper around the main WSGI application in order to trap
    database errors, so that a commit or rollback is guaranteed, and so a crash
    cannot leave the database in a locked state and thereby mess up other
    processes.
    """

    if environ["wsgi.multithread"]:
        logger.critical("Started in multithreaded mode")
        raise RuntimeError("Cannot be run in multithreaded mode")
    else:
        logger.debug("Started in single-threaded mode")

    # Set global variables, connect/reconnect to database, etc.
    pls.set_from_environ_and_ping_db(environ, as_client_db=True)

    # Trap any errors from here.
    # http://doughellmann.com/2009/06/19/python-exception-handling-techniques.html  # noqa

    try:
        result = database_application(environ, start_response)
        # ... it will commit (the earlier the better for speed)
        return result
    except:
        try:
            raise  # re-raise the original error
        finally:
            try:
                pls.db.rollback()
            except:
                pass  # ignore errors in rollback


def database_application(environ, start_response):
    """Main WSGI application handler. Very simple."""
    # Call main
    t0 = time.time()  # in seconds
    try:
        resultdict = main_http_processor(environ)
        resultdict[PARAM.SUCCESS] = 1
        status = '200 OK'
    except UserErrorException as e:
        logger.warn("CLIENT-SIDE SCRIPT ERROR: " + str(e))
        resultdict = {
            PARAM.SUCCESS: 0,
            PARAM.ERROR: escape_newlines(str(e))
        }
        status = '200 OK'
    except ServerErrorException as e:
        logger.error("SERVER-SIDE SCRIPT ERROR: " + str(e))
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
        logger.exception("Unhandled exception")
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
    text = u""
    for k, v in resultdict.iteritems():
        text += nvp(k, v)
    output = text.encode("utf-8")

    # Commit
    t1 = time.time()
    pls.db.commit()
    t2 = time.time()

    # logger.debug("Reply: {}".format(repr(output)))
    # ... don't send Unicode to the logger...
    logger.info(
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
# Command-line processor
# =============================================================================

def cli_main():
    """Command-line processor."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    import argparse
    import os

    parser = argparse.ArgumentParser(
        prog="camcops_db",  # name the user will use to call it
        description=("CamCOPS database script (command-line interface)")
    )
    parser.add_argument("configfilename", nargs="?", default=None,
                        help="Configuration file")
    args = parser.parse_args()

    print("""CamCOPS tablet database access script, version {version}
By Rudolf Cardinal. See {url}
COMMAND-LINE ACCESS IS ONLY FOR UNIT TESTING.
Launch via Apache/mod_wsgi for normal use; see documentation.
    """.format(
        version=cc_version.CAMCOPS_SERVER_VERSION,
        url=CAMCOPS_URL,
    ))

    if not args.configfilename:
        sys.exit()

    os.environ["CAMCOPS_CONFIG_FILE"] = args.configfilename
    print("Using configuration file: {}".format(args.configfilename))

    try:
        print("Processing configuration information and connecting "
              "to database (this may take some time)...")
        pls.set_from_environ_and_ping_db(os.environ, as_client_db=True)
    except ConfigParser.NoSectionError:
        print("""
You may not have the necessary privileges to read the configuration file, or it
may not exist, or be incomplete.
""")
        raise
    except rnc_db.NoDatabaseError():
        print("""
If the database failed to open, ensure it has been created. To create a
database, for example, in MySQL:
    CREATE DATABASE camcops;
""")
        raise

    unit_tests()


# =============================================================================
# Unit tests
# =============================================================================

def unit_tests():
    """Unit tests for database script."""
    # -------------------------------------------------------------------------
    # DELAYED IMPORTS
    # -------------------------------------------------------------------------
    from cc_unittest import (
        unit_test_ignore,
        unit_test_must_raise,
        unit_test_verify
    )

    # a = (UserErrorException, ServerErrorException)
    u = (UserErrorException)
    s = (ServerErrorException)

    print("pls.VALID_TABLE_NAMES: {}".format(pls.VALID_TABLE_NAMES))

    unit_test_ignore("", succeed_generic, "testmsg")
    unit_test_must_raise("", fail_user_error, u, "testmsg")
    unit_test_must_raise("", fail_server_error, s, "testmsg")
    unit_test_must_raise("", fail_unsupported_operation, u, "duffop")
    unit_test_verify("", nvp, u"n:v\n", "n", "v")

    # Encoding/decoding tests
    data = bytearray("hello")
    enc_b64data = special_base64_encode(data)
    enc_hexdata = special_hex_encode(data)
    not_enc_1 = "X'012345'"
    not_enc_2 = "64'aGVsbG8='"
    teststring = """one, two, 3, 4.5, NULL, 'hello "hi
        with linebreak"', 'NULL', 'quote''s here', {b}, {h}, {s1}, {s2}"""
    SQL_CSV_TESTDICT = {
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
    for k, v in SQL_CSV_TESTDICT.iteritems():
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

# =============================================================================
# WSGI entry point
# =============================================================================

application = database_wrapper
if PROFILE:
    application = werkzeug.contrib.profiler.ProfilerMiddleware(application)


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == '__main__':
    cli_main()
