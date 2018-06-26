#!/usr/bin/env python
# camcops_server/cc_modules/cc_convert.py

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

import logging
import re
from typing import Any, Dict, Iterable, List

from cardinal_pythonlib.convert import (
    base64_64format_decode,
    base64_64format_encode,
    hex_xformat_decode,
    REGEX_BASE64_64FORMAT,
    REGEX_HEX_XFORMAT,
)
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sql.literals import (
    gen_items_from_sql_csv,
    SQUOTE,
    sql_dequote_string,
    sql_quote_string,
)
from cardinal_pythonlib.text import escape_newlines
from markupsafe import escape, Markup

log = BraceStyleAdapter(logging.getLogger(__name__))

REGEX_WHITESPACE = re.compile("\s")
TAB_REGEX = re.compile("\t", re.MULTILINE)
NEWLINE_REGEX = re.compile("\n", re.MULTILINE)


# =============================================================================
# Conversion to/from quoted SQL values
# =============================================================================

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
        return base64_64format_encode(v)
    if isinstance(v, str):
        return escape_newlines(sql_quote_string(v))
    # for int, float, etc.:
    return str(v)


def decode_single_value(v: str) -> Any:
    """
    Takes a string representing an SQL value. Returns the value. Value
    types/examples:

        ==========  ===========================================================
        int         ``35``, ``-12``
        float       ``7.23``
        str         ``'hello, here''s an apostrophe'``
                    (starts and ends with a quote)
        NULL        ``NULL``
                    (case-insensitive)
        BLOB        ``X'4D7953514C'``
                    (hex-encoded; matches MySQL method;
                    http://dev.mysql.com/doc/refman/5.0/en/hexadecimal-literals.html)
        BLOB        ``64'TXlTUUw='``
                    (base-64-encoded; this notation is my invention)
        ==========  ===========================================================

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
    if REGEX_HEX_XFORMAT.match(t):
        # log.debug("MATCHES HEX-ENCODED BLOB")
        return hex_xformat_decode(t)
    if REGEX_BASE64_64FORMAT.match(t):
        # log.debug("MATCHES BASE64-ENCODED BLOB")
        return base64_64format_decode(t)

    if len(v) >= 2 and v[0] == SQUOTE and v[-1] == SQUOTE:
        # v is a quoted string
        s = sql_dequote_string(v)
        # s is the underlying string that the source started with
        # log.debug("UNDERLYING STRING: {}", s)
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
    """
    Takes a SQL CSV value list and returns the corresponding list of decoded
    values.
    """
    # log.debug("decode_values: valuelist={}", valuelist)
    v = [decode_single_value(v) for v in gen_items_from_sql_csv(valuelist)]
    # log.debug("decode_values: values={}", v)
    return v


# =============================================================================
# Conversion to TSV
# =============================================================================

def tsv_escape(value: Any) -> str:
    """Escapes value for tab-separated value (TSV) format.

    Converts to unicode/str and escapes tabs/newlines.
    """
    if value is None:
        return ""
    s = str(value)
    # escape tabs and newlines:
    s = TAB_REGEX.sub("\\t", s)
    s = NEWLINE_REGEX.sub("\\n", s)
    return s


def get_tsv_header_from_dict(d: Dict) -> str:
    """Returns a TSV header line from a dictionary."""
    return "\t".join([tsv_escape(x) for x in d.keys()])


def get_tsv_line_from_dict(d: Dict) -> str:
    """Returns a TSV data line from a dictionary."""
    return "\t".join([tsv_escape(x) for x in d.values()])


def tsv_from_query(rows: Iterable[Iterable[Any]],
                   descriptions: Iterable[str]) -> str:
    """Converts rows from an SQL query result to TSV format."""
    tsv = "\t".join([tsv_escape(x) for x in descriptions]) + "\n"
    for row in rows:
        tsv += "\t".join([tsv_escape(x) for x in row]) + "\n"
    return tsv


# =============================================================================
# Escape for HTML/XML
# =============================================================================

def br_html(text: str) -> str:
    r"""
    Filter that esscapes text safely whilst also converting \n to <br>.
    """
    # https://stackoverflow.com/questions/2285507/converting-n-to-br-in-mako-files
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/br
    return escape(text).replace('\n', Markup('<br>'))
