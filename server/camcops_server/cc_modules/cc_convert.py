#!/usr/bin/env python
# cc_convert.py

"""
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
"""

import base64
import binascii
import re
from typing import Any, Generator, List

import cardinal_pythonlib.rnc_db as rnc_db
from ..cc_modules.cc_pls import pls

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
SQLSEP = ","
SQLQUOTE = "'"


# =============================================================================
# Conversion to/from quoted SQL values
# =============================================================================

def special_hex_encode(v: bytes) -> str:
    """Encode in X'{hex}' format."""
    return "X'{}'".format(binascii.hexlify(v))


def special_hex_decode(s: str) -> bytearray:  # TODO: change to bytes?
    """Reverse special_hex_encode()."""
    # SPECIAL HANDLING for BLOBs: a string like X'01FF' means a hex-
    # encoded BLOB. Titanium is rubbish at blobs, so we encode them as
    # special string literals.
    # Hex-encoded BLOB like X'CDE7A24B1A9DBA3148BCB7A0B9DA5BB6A424486C'
    # Strip off the start and end and convert it to a byte array:
    # http://stackoverflow.com/questions/5649407
    return bytearray.fromhex(s[2:-1])


def special_base64_encode(v: bytes) -> str:
    """Encode in 64'{base64encoded}' format."""
    return "64'{}'".format(base64.b64encode(v))


def special_base64_decode(s: str) -> bytearray:  # TODO: change to bytes?
    """Reverse special_base64_encode()."""
    # OTHER WAY OF DOING BLOBS: base64 encoding
    # e.g. a string like 64'cGxlYXN1cmUu' is a base-64-encoded BLOB
    # (the 64'...' bit is my representation)
    # regex from http://stackoverflow.com/questions/475074
    # better one from http://www.perlmonks.org/?node_id=775820
    return bytearray(base64.b64decode(s[3:-1]))


def escape_newlines(s: str) -> str:
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


def unescape_newlines(s: str) -> str:
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


def encode_single_value(v: Any, is_blob=False) -> str:
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
    if isinstance(v, str):
        return escape_newlines(rnc_db.sql_quote_string(v))
    # for int, float, etc.:
    return str(v)


def gen_items_from_sql_csv(s: str) -> Generator[str, None, None]:
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


def decode_single_value(v: str) -> Any:
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
        # log.debug("MATCHES HEX-ENCODED BLOB")
        return special_hex_decode(t)
    if REGEX_BLOB_BASE64.match(t):
        # log.debug("MATCHES BASE64-ENCODED BLOB")
        return special_base64_decode(t)

    if len(v) >= 2 and v[0] == SQLQUOTE and v[-1] == SQLQUOTE:
        # v is a quoted string
        s = rnc_db.sql_dequote_string(v)
        # s is the underlying string that the source started with
        # log.debug("UNDERLYING STRING: {}".format(s))
        return s

    # Not a quoted string.
    # int?
    try:
        return int(v)
    except (TypeError, ValueError):
        pass
    # float?
    try:
        return float(v)
    except (TypeError, ValueError):
        pass
    # Who knows; something odd. Allow it as a string. "Be conservative in what
    # you send, liberal in what you accept", and all that.
    return v


def decode_values(valuelist: str) -> List[Any]:
    """Takes a SQL CSV value list and returns the corresponding list of decoded
    values."""
    # log.debug("decode_values: valuelist={}".format(valuelist))
    v = [decode_single_value(v) for v in gen_items_from_sql_csv(valuelist)]
    # log.debug("decode_values: values={}".format(v))
    return v


def delimit(f: str) -> str:
    """Delimits a field for SQL queries."""
    return pls.db.delimit(f)
