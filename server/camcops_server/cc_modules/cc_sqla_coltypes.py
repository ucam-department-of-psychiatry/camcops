#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_sqla_coltypes.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

**SQLAlchemy column types used by CamCOPS.**

Note these built-in SQLAlchemy types
(http://docs.sqlalchemy.org/en/latest/core/type_basics.html#generic-types):

    =============== ===========================================================
    SQLAlchemy type Comment
    =============== ===========================================================
    BigInteger      MySQL: -9,223,372,036,854,775,808 to
                    9,223,372,036,854,775,807 (64-bit)
                    (compare NHS number: up to 9,999,999,999)
    Boolean
    Date
    DateTime
    Enum
    Float
    Integer         MySQL: -2,147,483,648 to 2,147,483,647 (32-bit)
    Interval        For ``datetime.timedelta``
    LargeBinary     Under MySQL, maps to ``BLOB``
    MatchType       For the return type of the ``MATCH`` operator
    Numeric         For fixed-precision numbers like ``NUMERIC`` or ``DECIMAL``
    PickleType
    SchemaType
    SmallInteger
    String          ``VARCHAR``
    Text            Variably sized string type.
                    (Under MySQL, renders as ``TEXT``.)
    Time
    Unicode         Implies that the underlying column explicitly supports
                    Unicode
    UnicodeText     Variably sized version of Unicode
                    (Under MySQL, renders as ``TEXT`` too.)
    =============== ===========================================================

Not supported across all platforms:

    =============== ===========================================================
    SQL type        Comment
    =============== ===========================================================
    BIGINT UNSIGNED MySQL: 0 to 18,446,744,073,709,551,615 (64-bit).
                    Use ``sqlalchemy.dialects.mysql.BIGINT(unsigned=True)``.
    INT UNSIGNED    MySQL: 0 to 4,294,967,295 (32-bit).
                    Use ``sqlalchemy.dialects.mysql.INTEGER(unsigned=True)``.
    =============== ===========================================================

Other MySQL sizes:

    =============== ===========================================================
    MySQL type      Comment
    =============== ===========================================================
    TINYBLOB        2^8 bytes = 256 bytes
    BLOB            2^16 bytes = 64 KiB
    MEDIUMBLOB      2^24 bytes = 16 MiB
    LONGBLOB        2^32 bytes = 4 GiB
    TINYTEXT        255 (2^8 - 1) bytes
    TEXT            65,535 bytes (2^16 - 1) = 64 KiB
    MEDIUMTEXT      16,777,215 (2^24 - 1) bytes = 16 MiB
    LONGTEXT        4,294,967,295 (2^32 - 1) bytes = 4 GiB
    =============== ===========================================================

See https://stackoverflow.com/questions/13932750/tinytext-text-mediumtext-and-longtext-maximum-storage-sizes.

Also notes:

- Columns may need their character set specified explicitly under MySQL:
  https://stackoverflow.com/questions/2108824/mysql-incorrect-string-value-error-when-save-unicode-string-in-django

"""  # noqa

# =============================================================================
# Imports
# =============================================================================

import datetime
import logging
from typing import (Any, Generator, List, Optional, Tuple, Type, TYPE_CHECKING,
                    Union)
import unittest

from cardinal_pythonlib.datetimefunc import (
    coerce_to_pendulum,
    convert_datetime_to_utc,
    duration_from_iso,
    duration_to_iso,
    PotentialDatetimeType,
)
from cardinal_pythonlib.lists import chunks
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.randomness import create_base64encoded_randomness
from cardinal_pythonlib.reprfunc import auto_repr
from cardinal_pythonlib.sqlalchemy.dialect import SqlaDialectName
from cardinal_pythonlib.sqlalchemy.orm_inspect import (
    gen_columns,
    gen_relationships,
)
from cardinal_pythonlib.sqlalchemy.session import SQLITE_MEMORY_URL
from cardinal_pythonlib.sqlalchemy.sqlfunc import (
    fail_unknown_dialect,
    fetch_processed_single_clause
)
from isodate.isoerror import ISO8601Error
from pendulum import DateTime as Pendulum, Duration
from pendulum.parsing.exceptions import ParserError
from semantic_version import Version
from sqlalchemy import util
from sqlalchemy.dialects import mysql
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.elements import conv
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.functions import func, FunctionElement
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import (
    Boolean,
    DateTime,
    Integer,
    LargeBinary,
    String,
    Text,
    Unicode,
    UnicodeText,
)
from sqlalchemy.sql.type_api import TypeDecorator

from camcops_server.cc_modules.cc_constants import PV
from camcops_server.cc_modules.cc_simpleobjects import IdNumReference
from camcops_server.cc_modules.cc_sqlalchemy import (
    LONG_COLUMN_NAME_WARNING_LIMIT,
)
from camcops_server.cc_modules.cc_version import make_version

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ClauseElement
    from sqlalchemy.sql.compiler import SQLCompiler
    from camcops_server.cc_modules.cc_db import GenericTabletRecordMixin

log = BraceStyleAdapter(logging.getLogger(__name__))

# =============================================================================
# Debugging options
# =============================================================================

DEBUG_DATETIME_AS_ISO_TEXT = False
DEBUG_DURATION_AS_ISO_TEXT = False
DEBUG_IDNUMDEF_LIST = False
DEBUG_INT_LIST_COLTYPE = False
DEBUG_SEMANTIC_VERSION = False
DEBUG_STRING_LIST_COLTYPE = False

if any([DEBUG_DATETIME_AS_ISO_TEXT,
        DEBUG_DURATION_AS_ISO_TEXT,
        DEBUG_SEMANTIC_VERSION,
        DEBUG_IDNUMDEF_LIST,
        DEBUG_INT_LIST_COLTYPE,
        DEBUG_STRING_LIST_COLTYPE]):
    log.warning("Debugging options enabled!")

# =============================================================================
# Constants
# =============================================================================
#
# Note: "191" relates to MySQL indexing of VARCHAR fields using utf8mb4;
# - https://stackoverflow.com/questions/6172798/
# - https://dev.mysql.com/doc/refman/5.7/en/innodb-restrictions.html
# There are alternative workarounds, but these fields are OK at 191.
#
# Re commenting variables in Sphinx:
# - https://stackoverflow.com/questions/20227051/how-to-document-a-module-constant-in-python  # noqa
# - http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directive-autodata  # noqa
# - URLs are a bit tricky; the colons get re-interpreted sometimes; it seems
#   that inserting an extra colon after "#:", e.g. "#: : see http://somewhere"
#   works.
# - If a comment needs "# noqa" for the linter, then make it a docstring,
#   because it will appear in the Sphinx string.

AUDIT_SOURCE_MAX_LEN = 20  #: our choice based on use in CamCOPS code

#: : See https://docs.python.org/3.7/library/codecs.html#standard-encodings.
#: Probably ~18 so give it some headroom.
CHARSET_MAX_LEN = 64

CURRENCY_MAX_LEN = 3  #: Can have Unicode symbols like € or text like "GBP"

DATABASE_TITLE_MAX_LEN = 255  #: our choice

#: 191 is the maximum for MySQL + InnoDB + VARCHAR + utf8mb4 + index;
#: must be compatible with tablet
DEVICE_NAME_MAX_LEN = 191

#: : See https://en.wikipedia.org/wiki/Email_address.
EMAIL_ADDRESS_MAX_LEN = 255

#: 191 is the maximum for MySQL + InnoDB + VARCHAR + utf8mb4 + index
EXPORT_RECIPIENT_NAME_MAX_LEN = 191

#: Our choice
FILTER_TEXT_MAX_LEN = 255

#: Our choice; used for user full names on the server
FULLNAME_MAX_LEN = 255

#: Our choice
FILESPEC_MAX_LEN = 255

#: Our choice
GROUP_DESCRIPTION_MAX_LEN = 255

#: 191 is the maximum for MySQL + InnoDB + VARCHAR + utf8mb4 + index
GROUP_NAME_MAX_LEN = 191

HASHED_PW_MAX_LEN = 60
"""
:
We use ``bcrypt``. Empirically, the length of its hashed output is:

.. code-block:: none

       "$2a$" (4)
       cost parameter, e.g. "$09" for 9 rounds (3)
       b64-enc 128-bit salt (22)
       b64enc 184-bit hash (31)

    ... total 60

See https://stackoverflow.com/questions/5881169/what-column-type-length-should-i-use-for-storing-a-bcrypt-hashed-password-in-a-d
"""  # noqa

HOSTNAME_MAX_LEN = 255
"""
FQDN; see
https://stackoverflow.com/questions/8724954/what-is-the-maximum-number-of-characters-for-a-host-name-in-unix
"""  # noqa

ICD9_CODE_MAX_LEN = 6
"""
Longest is "xxx.xx"; thus, 6; see
https://www.cms.gov/Medicare/Quality-Initiatives-Patient-Assessment-Instruments/HospitalQualityInits/Downloads/HospitalAppendix_F.pdf
"""  # noqa

#: longest is e.g. "F00.000"; "F10.202"; thus, 7
ICD10_CODE_MAX_LEN = 7

DIAGNOSTIC_CODE_MAX_LEN = max(ICD9_CODE_MAX_LEN, ICD10_CODE_MAX_LEN)

HL7_AA_MAX_LEN = 20
"""
- The AA appears in Table 4.6 "Extended composite ID", p46-47 of
  hl7guide-1-4-2012-08.pdf
- ... but is defined in Table 4.9 "Entity Identifier", p50, in which:

  - component 2 is the Assigning Authority (see component 1)
  - component 2 is also a Namespace ID with a length of 20

- ... and multiple other examples of an Assigning Authority being one example
  of a Namespace ID

- ... and examples are in Table 0363 (p229 of the PDF), which are all 3-char.

- ... and several other examples of "Namespace ID" being of length 1..20
  meaning 1-20.
"""

HL7_ID_TYPE_MAX_LEN = 5
"""
Table 4.6 "Extended composite ID", p46-47 of hl7guide-1-4-2012-08.pdf,
and Table 0203 "Identifier type", p204 of that PDF, in Appendix B.
"""

#: Our choice
ID_DESCRIPTOR_MAX_LEN = 255

#: Our choice
ID_POLICY_MAX_LEN = 255

#: : See http://stackoverflow.com/questions/166132
IP_ADDRESS_MAX_LEN = 45

ISO8601_DATETIME_STRING_MAX_LEN = 32
"""
Max length e.g.

.. code-block:: none

    2013-07-24T20:04:07.123456+01:00
    1234567890123456789012345678901234567890
    
(with punctuation, T, microseconds, colon in timezone).
"""

#: See :func:`cardinal_pythonlib.datetimefunc.duration_to_iso`
ISO8601_DURATION_STRING_MAX_LEN = 29

LANGUAGE_CODE_MAX_LEN = 6  # two-letter language, hyphen, 2/3-letter country

# LONGBLOB_LONGTEXT_MAX_LEN = (2 ** 32) - 1
# ... https://dev.mysql.com/doc/refman/8.0/en/storage-requirements.html

#: See https://stackoverflow.com/questions/643690
MIMETYPE_MAX_LEN = 255

#: For forename and surname, each; our choice but must match tablet
PATIENT_NAME_MAX_LEN = 255

RFC_2822_DATE_MAX_LEN = 31
"""
e.g. ``Fri, 09 Nov 2001 01:08:47 -0000``; 3.3 in
https://tools.ietf.org/html/rfc2822, assuming extra white space not added
"""

#: for export; our choice based on use in CamCOPS code
SENDING_FORMAT_MAX_LEN = 50

#: our choice; 64 bytes => 512 bits, which is a lot in 2017
SESSION_TOKEN_MAX_BYTES = 64

SESSION_TOKEN_MAX_LEN = len(
    create_base64encoded_randomness(SESSION_TOKEN_MAX_BYTES))

TABLENAME_MAX_LEN = 128
"""
For

- MySQL: 64 -- https://dev.mysql.com/doc/refman/5.7/en/identifiers.html
- SQL Server: 128  -- https://msdn.microsoft.com/en-us/library/ms191240.aspx
- Oracle: 32, then 128 from v12.2 (2017)
"""

TASK_SUMMARY_TEXT_FIELD_DEFAULT_MAX_LEN = 50
"""
... our choice, contains short strings like "normal", "abnormal", "severe".
Easy to change, since it's only used when exporting summaries, and not in
the core database.
"""

#: Our choice
URL_MAX_LEN = 255

#: 191 is the maximum for MySQL + InnoDB + VARCHAR + utf8mb4 + index
USERNAME_CAMCOPS_MAX_LEN = 191

#: Our choice
USERNAME_EXTERNAL_MAX_LEN = 255


class RelationshipInfo(object):
    """
    Used as keys the ``info`` (user-defined) dictionary parameter to SQLAlchemy
    ``relationship`` calls; see
    https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship.
    """  # noqa
    IS_ANCILLARY = "is_ancillary"
    IS_BLOB = "is_blob"


# =============================================================================
# Simple derivative column types
# =============================================================================
# If you insert something too long into a VARCHAR, it just gets truncated.

AuditSourceColType = String(length=AUDIT_SOURCE_MAX_LEN)

# BigIntUnsigned = Integer().with_variant(mysql.BIGINT(unsigned=True), 'mysql')
# ... partly because Alembic breaks on variants (Aug 2017), and partly because
#     it's nonstandard and unnecessary, changed all BigIntUnsigned to
#     BigInteger (2017-08-25).

CharColType = String(length=1)
CharsetColType = String(length=CHARSET_MAX_LEN)
CurrencyColType = Unicode(length=CURRENCY_MAX_LEN)

DatabaseTitleColType = Unicode(length=DATABASE_TITLE_MAX_LEN)
DeviceNameColType = String(length=DEVICE_NAME_MAX_LEN)
DiagnosticCodeColType = String(length=DIAGNOSTIC_CODE_MAX_LEN)

EmailAddressColType = Unicode(length=EMAIL_ADDRESS_MAX_LEN)
EraColType = String(length=ISO8601_DATETIME_STRING_MAX_LEN)  # underlying SQL type  # noqa
ExportRecipientNameColType = String(length=EXPORT_RECIPIENT_NAME_MAX_LEN)
ExportTransmissionMethodColType = String(length=SENDING_FORMAT_MAX_LEN)

FilterTextColType = Unicode(length=FILTER_TEXT_MAX_LEN)
FileSpecColType = Unicode(length=FILESPEC_MAX_LEN)
FullNameColType = Unicode(length=FULLNAME_MAX_LEN)

GroupDescriptionColType = Unicode(length=GROUP_DESCRIPTION_MAX_LEN)
GroupNameColType = Unicode(length=GROUP_NAME_MAX_LEN)

HashedPasswordColType = String(length=HASHED_PW_MAX_LEN)
# ... You might think that we must ensure case-SENSITIVE comparison on this
# field. That would require the option collation='utf8mb4_bin' to String(),
# for MySQL. However, that is MySQL-specific, and SQLAlchemy currently (Oct
# 2017) doesn't support database-specific *per-column* collations. SQLite
# accepts COLLATE commands but chokes on 'utf8mb4_bin'. Now, the hashed
# password from bcrypt() is case-sensitive. HOWEVER, the important thing is
# that we always retrieve the string from the database and do a case-sensitive
# comparison in Python (see calls to is_password_valid()). So the database
# collation doesn't matter. So we don't set it.
# See further notes in cc_sqlalchemy.py
HL7AssigningAuthorityType = String(length=HL7_AA_MAX_LEN)
HL7IdTypeType = String(length=HL7_ID_TYPE_MAX_LEN)
HostnameColType = String(length=HOSTNAME_MAX_LEN)

IdDescriptorColType = Unicode(length=ID_DESCRIPTOR_MAX_LEN)
IdPolicyColType = String(length=ID_POLICY_MAX_LEN)
# IntUnsigned = Integer().with_variant(mysql.INTEGER(unsigned=True), 'mysql')
IPAddressColType = String(length=IP_ADDRESS_MAX_LEN)
# This is a plain string.
# See also e.g. http://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/types/ip_address.html  # noqa

LanguageCodeColType = String(length=LANGUAGE_CODE_MAX_LEN)

# Large BLOB:
# https://stackoverflow.com/questions/43791725/sqlalchemy-how-to-make-a-longblob-column-in-mysql  # noqa
# One of these:
LongBlob = LargeBinary().with_variant(mysql.LONGBLOB, "mysql")
# LongBlob = LargeBinary(length=LONGBLOB_LONGTEXT_MAX_LEN)  # doesn't translate to SQL Server  # noqa

LongText = UnicodeText().with_variant(mysql.LONGTEXT, "mysql")
# LongText = UnicodeText(length=LONGBLOB_LONGTEXT_MAX_LEN)  # doesn't translate to SQL Server  # noqa

MimeTypeColType = String(length=MIMETYPE_MAX_LEN)

PatientNameColType = Unicode(length=PATIENT_NAME_MAX_LEN)

Rfc2822DateColType = String(length=RFC_2822_DATE_MAX_LEN)

SessionTokenColType = String(length=SESSION_TOKEN_MAX_LEN)
SexColType = String(length=1)
SummaryCategoryColType = String(length=TASK_SUMMARY_TEXT_FIELD_DEFAULT_MAX_LEN)  # pretty generic  # noqa

TableNameColType = String(length=TABLENAME_MAX_LEN)

UrlColType = String(length=URL_MAX_LEN)
UserNameCamcopsColType = String(length=USERNAME_CAMCOPS_MAX_LEN)
UserNameExternalColType = String(length=USERNAME_EXTERNAL_MAX_LEN)


# =============================================================================
# Helper operations for PendulumDateTimeAsIsoTextColType
# =============================================================================
# Database string format is e.g.
#   2013-07-24T20:04:07.123456+01:00
#   2013-07-24T20:04:07.123+01:00
#   0        1         2         3      } position in string; 1-based
#   12345678901234567890123456789012    }
#
# So: rightmost 6 characters are time zone; rest is date/time.
#     leftmost 23 characters are time up to millisecond precision.
#     overall length is typically 29 (milliseconds) or 32 (microseconds)

_TZ_LEN = 6  # length of the timezone part of the ISO8601 string
_UTC_TZ_LITERAL = "'+00:00'"
_SQLITE_DATETIME_FMT_FOR_PYTHON = "'%Y-%m-%d %H:%M:%f'"

_MYSQL_DATETIME_LEN = 19
_SQLSERVER_DATETIME_LEN = 19
_SQLSERVER_DATETIME2_LEN = 27


# -----------------------------------------------------------------------------
# isotzdatetime_to_utcdatetime
# -----------------------------------------------------------------------------

# noinspection PyPep8Naming
class isotzdatetime_to_utcdatetime(FunctionElement):
    """
    Used as an SQL operation by :class:`PendulumDateTimeAsIsoTextColType`.

    Creates an SQL expression wrapping a field containing our ISO-8601 text,
    making a ``DATETIME`` out of it, in the UTC timezone.

    Implemented for different SQL dialects.
    """
    type = DateTime()
    name = 'isotzdatetime_to_utcdatetime'


# noinspection PyUnusedLocal
@compiles(isotzdatetime_to_utcdatetime)
def isotzdatetime_to_utcdatetime_default(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> None:
    """
    Default implementation for :class:`isotzdatetime_to_utcdatetime`: fail.
    """
    fail_unknown_dialect(compiler, "perform isotzdatetime_to_utcdatetime")


# noinspection PyUnusedLocal
@compiles(isotzdatetime_to_utcdatetime, SqlaDialectName.MYSQL)
def isotzdatetime_to_utcdatetime_mysql(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`isotzdatetime_to_utcdatetime` for MySQL.

    For format, see
    https://dev.mysql.com/doc/refman/5.5/en/date-and-time-functions.html#function_date-format

    Note the use of "%i" for minutes.

    Things after ``func.`` get passed to the database engine as literal SQL
    functions; http://docs.sqlalchemy.org/en/latest/core/tutorial.html
    """  # noqa
    x = fetch_processed_single_clause(element, compiler)

    # Let's do this in a clear way:
    date_time_part = f"LEFT({x}, LENGTH({x}) - {_TZ_LEN})"
    # ... drop the rightmost 6 chars (the timezone component)
    fmt = compiler.process(text("'%Y-%m-%dT%H:%i:%S.%f'"))
    # ... the text() part deals with the necessary escaping of % for the DBAPI
    the_date_time = f"STR_TO_DATE({date_time_part}, {fmt})"
    # ... STR_TO_DATE() returns a DATETIME if the string contains both date and
    #     time components.
    old_timezone = f"RIGHT({x}, {_TZ_LEN})"
    result_utc = (
        f"CONVERT_TZ({the_date_time}, {old_timezone}, {_UTC_TZ_LITERAL})"
    )

    # log.debug(result_utc)
    return result_utc


# noinspection PyUnusedLocal
@compiles(isotzdatetime_to_utcdatetime, SqlaDialectName.SQLITE)
def isotzdatetime_to_utcdatetime_sqlite(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`isotzdatetime_to_utcdatetime` for SQLite.
    """
    x = fetch_processed_single_clause(element, compiler)

    # https://sqlite.org/lang_corefunc.html#substr
    # https://sqlite.org/lang_datefunc.html
    # http://www.sqlite.org/lang_expr.html
    #
    # Get an SQL expression for the timezone adjustment in hours.
    # Note that if a time is 12:00+01:00, that means e.g. midday BST, which
    # is 11:00+00:00 or 11:00 UTC. So you SUBTRACT the displayed timezone from
    # the time, which I've always thought is a bit odd.
    #
    # Ha! Was busy implementing this, but SQLite is magic; if there's a
    # timezone at the end, STRFTIME() will convert it to UTC automatically!
    # Moreover, the format is the OUTPUT format that a Python datetime will
    # recognize, so no 'T'.
    fmt = compiler.process(text(_SQLITE_DATETIME_FMT_FOR_PYTHON))
    result = f"STRFTIME({fmt}, {x})"

    # log.debug(result)
    return result


# noinspection PyUnusedLocal
@compiles(isotzdatetime_to_utcdatetime, SqlaDialectName.SQLSERVER)
def isotzdatetime_to_utcdatetime_sqlserver(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`isotzdatetime_to_utcdatetime` for SQL Server.

    **Converting strings to DATETIME values**

    - ``CAST()``: Part of ANSI SQL.
    - ``CONVERT()``: Not part of ANSI SQL; has some extra formatting options.

    Both methods work:

    .. code-block:: sql

      SELECT CAST('2001-01-31T21:30:49.123' AS DATETIME) AS via_cast,
             CONVERT(DATETIME, '2001-01-31T21:30:49.123') AS via_convert;

    ... fine on SQL Server 2005, with milliseconds in both cases.
    However, going beyond milliseconds doesn't fail gracefully, it causes an
    error (e.g. "...21:30.49.123456") both for CAST and CONVERT.

    The ``DATETIME2`` format accepts greater precision, but requires SQL Server
    2008 or higher. Then this works:

    .. code-block:: sql

      SELECT CAST('2001-01-31T21:30:49.123456' AS DATETIME2) AS via_cast,
             CONVERT(DATETIME2, '2001-01-31T21:30:49.123456') AS via_convert;

    So as not to be too optimistic: ``CAST(x AS DATETIME2)`` ignores (silently)
    any timezone information in the string. So does ``CONVERT(DATETIME2, x, {0
    or 1})``.

    **Converting between time zones**

    NO TIME ZONE SUPPORT in SQL Server 2005.
    e.g. https://stackoverflow.com/questions/3200827/how-to-convert-timezones-in-sql-server-2005.

    .. code-block:: none

        TODATETIMEOFFSET(expression, time_zone):
              expression: something that evaluates to a DATETIME2 value
              time_zone: integer minutes, or string hours/minutes e.g. "+13.00"
          -> produces a DATETIMEOFFSET value

    Available from SQL Server 2008
    (https://docs.microsoft.com/en-us/sql/t-sql/functions/todatetimeoffset-transact-sql).

    .. code-block:: none

        SWITCHOFFSET
          -> converts one DATETIMEOFFSET value to another, preserving its UTC
             time, but changing the displayed (local) time zone.

    ... however, is that unnecessary? We want a plain ``DATETIME2`` in UTC, and
    .conversion to UTC is automatically achieved by ``CONVERT(DATETIME2,
    .some_datetimeoffset, 1)``

    ... https://stackoverflow.com/questions/4953903/how-can-i-convert-a-sql-server-2008-datetimeoffset-to-a-datetime

    ... but not by ``CAST(some_datetimeoffset AS DATETIME2)``, and not by
    ``CONVERT(DATETIME2, some_datetimeoffset, 0)``

    ... and styles 0 and 1 are the only ones permissible from SQL Server 2012
    and up (empirically, and documented for the reverse direction at
    https://docs.microsoft.com/en-us/sql/t-sql/functions/cast-and-convert-transact-sql?view=sql-server-2017)

    ... this is not properly documented re UTC conversion, as far as I can
    see. Let's use ``SWITCHOFFSET -> CAST`` to be explicit and clear.

    ``AT TIME ZONE``: From SQL Server 2016 only.
    https://docs.microsoft.com/en-us/sql/t-sql/queries/at-time-zone-transact-sql?view=sql-server-2017

    **Therefore**

    - We need to require SQL Server 2008 or higher.
    - Therefore we can use the ``DATETIME2`` type.
    - Note that ``LEN()``, not ``LENGTH()``, is ANSI SQL; SQL Server only
      supports ``LEN``.

    **Example (tested on SQL Server 2014)**

    .. code-block:: sql

        DECLARE @source AS VARCHAR(100) = '2001-01-31T21:30:49.123456+07:00';

        SELECT CAST(
            SWITCHOFFSET(
                TODATETIMEOFFSET(
                    CAST(LEFT(@source, LEN(@source) - 6) AS DATETIME2),
                    RIGHT(@source, 6)
                ),
                '+00:00'
            )
            AS DATETIME2
        )  -- 2001-01-31 14:30:49.1234560

    """  # noqa
    x = fetch_processed_single_clause(element, compiler)

    date_time_part = f"LEFT({x}, LEN({x}) - {_TZ_LEN})"  # a VARCHAR
    old_timezone = f"RIGHT({x}, {_TZ_LEN})"  # a VARCHAR
    date_time_no_tz = f"CAST({date_time_part} AS DATETIME2)"  # a DATETIME2
    date_time_offset_with_old_tz = (
        f"TODATETIMEOFFSET({date_time_no_tz}, {old_timezone})"
        # a DATETIMEOFFSET
    )
    date_time_offset_with_utc_tz = (
        f"SWITCHOFFSET({date_time_offset_with_old_tz}, {_UTC_TZ_LITERAL})"
        # a DATETIMEOFFSET in UTC
    )
    result_utc = f"CAST({date_time_offset_with_utc_tz} AS DATETIME2)"

    # log.debug(result_utc)
    return result_utc


# -----------------------------------------------------------------------------
# unknown_field_to_utcdatetime
# -----------------------------------------------------------------------------

# noinspection PyPep8Naming
class unknown_field_to_utcdatetime(FunctionElement):
    """
    Used as an SQL operation by :class:`PendulumDateTimeAsIsoTextColType`.

    Creates an SQL expression wrapping a field containing something unknown,
    which might be a ``DATETIME`` or an ISO-formatted field, and
    making a ``DATETIME`` out of it, in the UTC timezone.

    Implemented for different SQL dialects.
    """
    type = DateTime()
    name = 'unknown_field_to_utcdatetime'


# noinspection PyUnusedLocal
@compiles(unknown_field_to_utcdatetime)
def unknown_field_to_utcdatetime_default(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> None:
    """
    Default implementation for :class:`unknown_field_to_utcdatetime`: fail.
    """
    fail_unknown_dialect(compiler, "perform unknown_field_to_utcdatetime")


# noinspection PyUnusedLocal
@compiles(unknown_field_to_utcdatetime, SqlaDialectName.MYSQL)
def unknown_field_to_utcdatetime_mysql(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`unknown_field_to_utcdatetime` for MySQL.

    If it's the length of a plain ``DATETIME`` e.g. ``2013-05-30 00:00:00``
    (19), leave it as a ``DATETIME``; otherwise convert ISO -> ``DATETIME``.
    """
    x = fetch_processed_single_clause(element, compiler)
    converted = isotzdatetime_to_utcdatetime_mysql(element, compiler, **kw)
    result = f"IF(LENGTH({x}) = {_MYSQL_DATETIME_LEN}, {x}, {converted})"
    # log.debug(result)
    return result


# noinspection PyUnusedLocal
@compiles(unknown_field_to_utcdatetime, SqlaDialectName.SQLITE)
def unknown_field_to_utcdatetime_sqlite(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`unknown_field_to_utcdatetime` for SQLite.
    """
    x = fetch_processed_single_clause(element, compiler)
    fmt = compiler.process(text(_SQLITE_DATETIME_FMT_FOR_PYTHON))
    result = f"STRFTIME({fmt}, {x})"
    # log.debug(result)
    return result


# noinspection PyUnusedLocal
@compiles(unknown_field_to_utcdatetime, SqlaDialectName.SQLSERVER)
def unknown_field_to_utcdatetime_sqlserver(
        element: "ClauseElement",
        compiler: "SQLCompiler", **kw) -> str:
    """
    Implementation of :class:`unknown_field_to_utcdatetime` for SQL Server.

    We should cope also with the possibility of a ``DATETIME2`` field, not just
    ``DATETIME``. It seems consistent that ``LEN(DATETIME2) = 27``, with
    precision tenth of a microsecond, e.g. ``2001-01-31 21:30:49.1234567``
    (27).

    So, if it looks like a ``DATETIME`` or a ``DATETIME2``, then we leave it
    alone; otherwise we put it through our ISO-to-datetime function.

    Importantly, note that neither ``_SQLSERVER_DATETIME_LEN`` nor
    ``_SQLSERVER_DATETIME2_LEN`` are the length of any of our ISO strings.
    """
    x = fetch_processed_single_clause(element, compiler)
    # https://stackoverflow.com/questions/5487892/sql-server-case-when-or-then-else-end-the-or-is-not-supported  # noqa
    converted = isotzdatetime_to_utcdatetime_sqlserver(element, compiler, **kw)
    result = (
        f"CASE WHEN LEN({x}) IN " 
        f"({_SQLSERVER_DATETIME_LEN}, {_SQLSERVER_DATETIME2_LEN}) THEN {x} "
        f"ELSE {converted} "
        f"END"
    )
    # log.debug(result)
    return result


# =============================================================================
# Custom date/time field as ISO-8601 text including timezone, using
# pendulum.DateTime on the Python side.
# =============================================================================

class PendulumDateTimeAsIsoTextColType(TypeDecorator):
    """
    Stores date/time values as ISO-8601, in a specific format.
    Uses Pendulum on the Python side.
    """

    impl = String(length=ISO8601_DATETIME_STRING_MAX_LEN)  # underlying SQL type  # noqa

    _coltype_name = "PendulumDateTimeAsIsoTextColType"

    @property
    def python_type(self) -> type:
        """
        The Python type of the object.
        """
        return Pendulum

    @staticmethod
    def pendulum_to_isostring(x: PotentialDatetimeType) -> Optional[str]:
        """
        From a Python datetime to an ISO-formatted string in our particular
        format.
        """
        # https://docs.python.org/3.4/library/datetime.html#strftime-strptime-behavior  # noqa
        x = coerce_to_pendulum(x)
        try:
            mainpart = x.strftime("%Y-%m-%dT%H:%M:%S.%f")  # microsecond accuracy  # noqa
            timezone = x.strftime("%z")  # won't have the colon in
            return mainpart + timezone[:-2] + ":" + timezone[-2:]
        except AttributeError:
            return None

    @staticmethod
    def isostring_to_pendulum(x: Optional[str]) -> Optional[Pendulum]:
        """
        From an ISO-formatted string to a Python Pendulum, with timezone.
        """
        try:
            return coerce_to_pendulum(x)
        except (ParserError, ValueError):
            log.warning("Bad ISO date/time string: {!r}", x)
            return None

    def process_bind_param(self, value: Optional[Pendulum],
                           dialect: Dialect) -> Optional[str]:
        """
        Convert parameters on the way from Python to the database.
        """
        retval = self.pendulum_to_isostring(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "{}.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Optional[Pendulum],
                              dialect: Dialect) -> Optional[str]:
        """
        Convert literals on the way from Python to the database.
        """
        retval = self.pendulum_to_isostring(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "{}.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> Optional[Pendulum]:
        """
        Convert things on the way from the database to Python.
        """
        retval = self.isostring_to_pendulum(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "{}.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    # noinspection PyPep8Naming
    class comparator_factory(TypeDecorator.Comparator):
        """
        Process SQL for when we are comparing our column, in the database,
        to something else.

        We make this dialect-independent by calling functions like

        .. code-block:: none

            unknown_field_to_utcdatetime
            isotzdatetime_to_utcdatetime

        ... which we then specialize for specific dialects.
        """

        def operate(self, op, *other, **kwargs):
            assert len(other) == 1
            assert not kwargs
            other = other[0]
            try:
                processed_other = convert_datetime_to_utc(
                    coerce_to_pendulum(other))
            except (AttributeError, ParserError, ValueError):
                # OK. At this point, "other" could be a plain DATETIME field,
                # or a PendulumDateTimeAsIsoTextColType field (or potentially
                # something else that we don't really care about). If it's a
                # DATETIME, then we assume it is already in UTC.
                processed_other = unknown_field_to_utcdatetime(other)
            if DEBUG_DATETIME_AS_ISO_TEXT:
                log.debug("operate(self={!r}, op={!r}, other={!r})",
                          self, op, other)
                log.debug("self.expr = {!r}", self.expr)
                # traceback.print_stack()
            return op(isotzdatetime_to_utcdatetime(self.expr),
                      processed_other)

        def reverse_operate(self, op, *other, **kwargs):
            assert False, "I don't think this is ever being called"


# =============================================================================
# Custom duration field as ISO-8601 text, using pendulum.Duration on the Python
# side.
# =============================================================================

class PendulumDurationAsIsoTextColType(TypeDecorator):
    """
    Stores time durations as ISO-8601, in a specific format.
    Uses :class:`pendulum.Duration` on the Python side.
    """

    impl = String(length=ISO8601_DURATION_STRING_MAX_LEN)  # underlying SQL type  # noqa

    _coltype_name = "PendulumDurationAsIsoTextColType"

    @property
    def python_type(self) -> type:
        """
        The Python type of the object.
        """
        return Duration

    @staticmethod
    def pendulum_duration_to_isostring(x: Optional[Duration]) -> Optional[str]:
        """
        From a :class:`pendulum.Duration` (or ``None``) an ISO-formatted string
        in our particular format (or ``NULL``).
        """
        if x is None:
            return None
        return duration_to_iso(x, permit_years_months=True,
                               minus_sign_at_front=True)

    @staticmethod
    def isostring_to_pendulum_duration(x: Optional[str]) -> Optional[Duration]:
        """
        From an ISO-formatted string to a Python Pendulum, with timezone.
        """
        if not x:  # None (NULL) or blank string
            return None
        try:
            return duration_from_iso(x)
        except (ISO8601Error, ValueError):
            log.warning("Bad ISO duration string: {!r}", x)
            return None

    def process_bind_param(self, value: Optional[Pendulum],
                           dialect: Dialect) -> Optional[str]:
        """
        Convert parameters on the way from Python to the database.
        """
        retval = self.pendulum_duration_to_isostring(value)
        if DEBUG_DURATION_AS_ISO_TEXT:
            log.debug(
                "{}.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Optional[Pendulum],
                              dialect: Dialect) -> Optional[str]:
        """
        Convert literals on the way from Python to the database.
        """
        retval = self.pendulum_duration_to_isostring(value)
        if DEBUG_DURATION_AS_ISO_TEXT:
            log.debug(
                "{}.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> Optional[Pendulum]:
        """
        Convert things on the way from the database to Python.
        """
        retval = self.isostring_to_pendulum_duration(value)
        if DEBUG_DURATION_AS_ISO_TEXT:
            log.debug(
                "{}.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    # No comparator_factory; we do not use SQL to compare ISO durations.


# =============================================================================
# Semantic version column type
# =============================================================================

class SemanticVersionColType(TypeDecorator):
    """
    Stores semantic versions in the database.
    Uses :class:`semantic_version.Version` on the Python side.
    """

    impl = String(length=147)  # https://github.com/mojombo/semver/issues/79

    _coltype_name = "SemanticVersionColType"

    @property
    def python_type(self) -> type:
        """
        The Python type of the object.
        """
        return Version

    def process_bind_param(self, value: Optional[Version],
                           dialect: Dialect) -> Optional[str]:
        """
        Convert parameters on the way from Python to the database.
        """
        retval = str(value) if value is not None else None
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "{}.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Optional[Version],
                              dialect: Dialect) -> Optional[str]:
        """
        Convert literals on the way from Python to the database.
        """
        retval = str(value) if value is not None else None
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "{}.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> !r",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> Optional[Version]:
        """
        Convert things on the way from the database to Python.
        """
        if value is None:
            retval = None
        else:
            # Here we do some slightly fancier conversion to deal with all
            # sorts of potential rubbish coming in, so we get a properly
            # ordered Version out:
            retval = make_version(value)
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "{}.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    '''
    # noinspection PyPep8Naming
    class comparator_factory(TypeDecorator.Comparator):
        """
        Process SQL for when we are comparing our column, in the database,
        to something else.
        
        See https://docs.sqlalchemy.org/en/13/core/type_api.html#sqlalchemy.types.TypeEngine.comparator_factory.

        .. warning::

            I'm not sure this is either (a) correct or (b) used; it may
            produce a string comparison of e.g. ``14.0.0`` versus ``2.0.0``,
            which will be alphabetical and therefore wrong.
            Disabled on 2019-04-28.

        """  # noqa

        def operate(self, op, *other, **kwargs):
            assert len(other) == 1
            assert not kwargs
            other = other[0]
            if isinstance(other, Version):
                processed_other = str(Version)
            else:
                processed_other = other
            return op(self.expr, processed_other)

        def reverse_operate(self, op, *other, **kwargs):
            assert False, "I don't think this is ever being called"
    '''


# =============================================================================
# IdNumReferenceListColType
# =============================================================================

class IdNumReferenceListColType(TypeDecorator):
    """
    Stores a list of IdNumReference objects.
    On the database side, uses a comma-separated list of integers.
    """

    impl = Text()
    _coltype_name = "IdNumReferenceListColType"

    @property
    def python_type(self) -> type:
        """
        The Python type of the object.
        """
        return list

    @staticmethod
    def _idnumdef_list_to_dbstr(
            idnumdef_list: Optional[List[IdNumReference]]) -> str:
        """
        Converts an optional list of
        :class:`camcops_server.cc_modules.cc_simpleobjects.IdNumReference`
        objects to a CSV string suitable for storing in the database.
        """
        if not idnumdef_list:
            return ""
        elements = []  # type: List[int]
        for idnumdef in idnumdef_list:
            elements.append(idnumdef.which_idnum)
            elements.append(idnumdef.idnum_value)
        return ",".join(str(x) for x in elements)

    @staticmethod
    def _dbstr_to_idnumdef_list(dbstr: Optional[str]) -> List[IdNumReference]:
        """
        Converts a CSV string (from the database) to a list of
        :class:`camcops_server.cc_modules.cc_simpleobjects.IdNumReference`
        objects.
        """
        idnumdef_list = []  # type: List[IdNumReference]
        try:
            intlist = [int(numstr) for numstr in dbstr.split(",")]
        except (AttributeError, TypeError, ValueError):
            return []
        length = len(intlist)
        if length == 0 or length % 2 != 0:  # enforce pairs
            return []
        for which_idnum, idnum_value in chunks(intlist, n=2):
            if which_idnum < 0 or idnum_value < 0:  # enforce positive integers
                return []
            idnumdef_list.append(IdNumReference(which_idnum=which_idnum,
                                                idnum_value=idnum_value))
        return idnumdef_list

    def process_bind_param(self, value: Optional[List[IdNumReference]],
                           dialect: Dialect) -> str:
        """
        Convert parameters on the way from Python to the database.
        """
        retval = self._idnumdef_list_to_dbstr(value)
        if DEBUG_IDNUMDEF_LIST:
            log.debug(
                "{}.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Optional[List[IdNumReference]],
                              dialect: Dialect) -> str:
        """
        Convert literals on the way from Python to the database.
        """
        retval = self._idnumdef_list_to_dbstr(value)
        if DEBUG_IDNUMDEF_LIST:
            log.debug(
                "{}.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> !r",
                self._coltype_name, self, value, dialect, retval)
        return retval

    def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> List[IdNumReference]:
        """
        Convert things on the way from the database to Python.
        """
        retval = self._dbstr_to_idnumdef_list(value)
        if DEBUG_IDNUMDEF_LIST:
            log.debug(
                "{}.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self._coltype_name, self, value, dialect, retval)
        return retval


# =============================================================================
# PermittedValueChecker: used by CamcopsColumn
# =============================================================================

class PermittedValueChecker(object):
    """
    Represents permitted values (in columns belonging to CamCOPS tasks), and
    checks a value against them.
    """
    def __init__(self,
                 not_null: bool = False,
                 minimum: Union[int, float] = None,
                 maximum: Union[int, float] = None,
                 permitted_values: List[Any] = None) -> None:
        """
        Args:
            not_null: must the value not be NULL?
            minimum: if specified, a numeric minimum value
            maximum: if specified, a numeric maximum value
            permitted_values: if specified, a list of permitted values
        """
        self.not_null = not_null
        self.minimum = minimum
        self.maximum = maximum
        self.permitted_values = permitted_values

    def is_ok(self, value: Any) -> bool:
        """
        Does the value pass our tests?
        """
        if value is None:
            return not self.not_null
            # If not_null is True, then the value is not OK; return False.
            # If not_null is False, then a null value passes all other tests.
        if self.permitted_values is not None and value not in self.permitted_values:  # noqa
            return False
        if self.minimum is not None and value < self.minimum:
            return False
        if self.maximum is not None and value > self.maximum:
            return False
        return True

    def failure_msg(self, value: Any) -> str:
        """
        Why does the value not pass our tests?
        """
        if value is None:
            if self.not_null:
                return "value is None and NULL values are not permitted"
            else:
                return ""  # value is OK
        if self.permitted_values is not None and value not in self.permitted_values:  # noqa
            return (
                f"value {value!r} not in permitted values "
                f"{self.permitted_values!r}"
            )
        if self.minimum is not None and value < self.minimum:
            return f"value {value!r} less than minimum of {self.minimum!r}"
        if self.maximum is not None and value > self.maximum:
            return f"value {value!r} more than maximum of {self.maximum!r}"
        return ""

    def __repr__(self):
        return auto_repr(self)


# Specific instances, to reduce object duplication and magic numbers:

MIN_ZERO_CHECKER = PermittedValueChecker(minimum=0)

BIT_CHECKER = PermittedValueChecker(permitted_values=PV.BIT)
ZERO_TO_ONE_CHECKER = PermittedValueChecker(minimum=0, maximum=1)
ZERO_TO_TWO_CHECKER = PermittedValueChecker(minimum=0, maximum=2)
ZERO_TO_THREE_CHECKER = PermittedValueChecker(minimum=0, maximum=3)
ZERO_TO_FOUR_CHECKER = PermittedValueChecker(minimum=0, maximum=4)
ZERO_TO_FIVE_CHECKER = PermittedValueChecker(minimum=0, maximum=5)
ZERO_TO_10_CHECKER = PermittedValueChecker(minimum=0, maximum=10)
ZERO_TO_100_CHECKER = PermittedValueChecker(minimum=0, maximum=100)

ONE_TO_TWO_CHECKER = PermittedValueChecker(minimum=1, maximum=2)
ONE_TO_THREE_CHECKER = PermittedValueChecker(minimum=1, maximum=3)
ONE_TO_FOUR_CHECKER = PermittedValueChecker(minimum=1, maximum=4)
ONE_TO_FIVE_CHECKER = PermittedValueChecker(minimum=1, maximum=5)
ONE_TO_SIX_CHECKER = PermittedValueChecker(minimum=1, maximum=6)
ONE_TO_SEVEN_CHECKER = PermittedValueChecker(minimum=1, maximum=7)
ONE_TO_EIGHT_CHECKER = PermittedValueChecker(minimum=1, maximum=8)
ONE_TO_NINE_CHECKER = PermittedValueChecker(minimum=1, maximum=9)


# =============================================================================
# CamcopsColumn: provides extra functions over Column.
# =============================================================================

# noinspection PyAbstractClass
class CamcopsColumn(Column):
    """
    A SQLAlchemy :class:`Column` class that supports some CamCOPS-specific
    flags, such as:

    - whether a field is a BLOB reference;
    - how it should be treated for anonymisation;
    - which values are permitted in the field (in a soft sense: duff values
      cause errors to be reported, but they're still stored).
    """
    def __init__(self,
                 *args,
                 cris_include: bool = False,
                 exempt_from_anonymisation: bool = False,
                 identifies_patient: bool = False,
                 is_blob_id_field: bool = False,
                 blob_relationship_attr_name: str = "",
                 permitted_value_checker: PermittedValueChecker = None,
                 **kwargs) -> None:
        self.cris_include = cris_include
        self.exempt_from_anonymisation = exempt_from_anonymisation
        self.identifies_patient = identifies_patient
        self.is_blob_id_field = is_blob_id_field
        self.blob_relationship_attr_name = blob_relationship_attr_name
        self.permitted_value_checker = permitted_value_checker
        if is_blob_id_field:
            assert blob_relationship_attr_name, (
                "If specifying a BLOB ID field, must give the attribute name "
                "of the relationship too")
        super().__init__(*args, **kwargs)

    def _constructor(self, *args, **kwargs) -> "CamcopsColumn":
        """
        SQLAlchemy method (not clearly documented) to assist in copying
        objects. Returns a copy of this object.

        See
        https://bitbucket.org/zzzeek/sqlalchemy/issues/2284/please-make-column-easier-to-subclass
        """  # noqa
        kwargs['cris_include'] = self.cris_include
        kwargs['exempt_from_anonymisation'] = self.exempt_from_anonymisation
        kwargs['identifies_patient'] = self.identifies_patient
        kwargs['is_blob_id_field'] = self.is_blob_id_field
        kwargs['blob_relationship_attr_name'] = self.blob_relationship_attr_name  # noqa
        kwargs['permitted_value_checker'] = self.permitted_value_checker
        return self.__class__(*args, **kwargs)

    def __repr__(self) -> str:
        def kvp(attrname: str) -> str:
            return f"{attrname}={getattr(self, attrname)!r}"
        elements = [
            kvp("cris_include"),
            kvp("exempt_from_anonymisation"),
            kvp("identifies_patient"),
            kvp("is_blob_id_field"),
            kvp("blob_relationship_attr_name"),
            kvp("permitted_value_checker"),
            f"super()={super().__repr__()}",
        ]
        return f"CamcopsColumn({', '.join(elements)})"

    def set_permitted_value_checker(
            self, permitted_value_checker: PermittedValueChecker) -> None:
        """
        Sets the :class:`PermittedValueChecker` attribute.
        """
        self.permitted_value_checker = permitted_value_checker


# =============================================================================
# Operate on Column/CamcopsColumn properties
# =============================================================================

def gen_columns_matching_attrnames(obj, attrnames: List[str]) \
        -> Generator[Tuple[str, Column], None, None]:
    """
    Find columns of an SQLAlchemy ORM object whose attribute names match a
    list.

    Args:
        obj: SQLAlchemy ORM object to inspect
        attrnames: attribute names

    Yields:
        ``attrname, column`` tuples

    """
    for attrname, column in gen_columns(obj):
        if attrname in attrnames:
            yield attrname, column


def gen_camcops_columns(obj) -> Generator[Tuple[str, CamcopsColumn],
                                          None, None]:
    """
    Finds all columns of an object that are
    :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn` columns.

    Args:
        obj: SQLAlchemy ORM object to inspect

    Yields:
        ``attrname, column`` tuples
    """
    for attrname, column in gen_columns(obj):
        if isinstance(column, CamcopsColumn):
            yield attrname, column


def gen_camcops_blob_columns(obj) -> Generator[Tuple[str, CamcopsColumn],
                                               None, None]:
    """
    Finds all columns of an object that are
    :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn` columns
    referencing the BLOB table.

    Args:
        obj: SQLAlchemy ORM object to inspect

    Yields:
        ``attrname, column`` tuples
    """
    for attrname, column in gen_camcops_columns(obj):
        if column.is_blob_id_field:
            if attrname != column.name:
                log.warning("BLOB field where attribute name {!r} != SQL "
                            "column name {!r}", attrname, column.name)
            yield attrname, column


def get_column_attr_names(obj) -> List[str]:
    """
    Get a list of column attribute names from an SQLAlchemy ORM object.
    """
    return [attrname for attrname, _ in gen_columns(obj)]


def get_camcops_column_attr_names(obj) -> List[str]:
    """
    Get a list of
    :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn` column
    attribute names from an SQLAlchemy ORM object.
    """
    return [attrname for attrname, _ in gen_camcops_columns(obj)]


def get_camcops_blob_column_attr_names(obj) -> List[str]:
    """
    Get a list of
    :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn` BLOB
    column attribute names from an SQLAlchemy ORM object.
    """
    return [attrname for attrname, _ in gen_camcops_blob_columns(obj)]


def permitted_value_failure_msgs(obj) -> List[str]:
    """
    Checks a SQLAlchemy ORM object instance against its permitted value checks
    (via its :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn`
    columns), if it has any.

    Returns a list of failure messages (empty list means all OK).

    If you just want to know whether it passes, a quicker way is via
    :func:`permitted_values_ok`.
    """
    failure_msgs = []
    for attrname, camcops_column in gen_camcops_columns(obj):
        pv_checker = camcops_column.permitted_value_checker  # type: Optional[PermittedValueChecker]  # noqa
        if pv_checker is None:
            continue
        value = getattr(obj, attrname)
        failure_msg = pv_checker.failure_msg(value)
        if failure_msg:
            failure_msgs.append(
                f"Invalid value for {attrname}: {failure_msg}")
    return failure_msgs


def permitted_values_ok(obj) -> bool:
    """
    Checks whether an instance passes its permitted value checks, if it has
    any.

    If you want to know why it failed, see
    :func:`permitted_value_failure_msgs`.
    """
    for attrname, camcops_column in gen_camcops_columns(obj):
        pv_checker = camcops_column.permitted_value_checker  # type: Optional[PermittedValueChecker]  # noqa
        if pv_checker is None:
            continue
        value = getattr(obj, attrname)
        if not pv_checker.is_ok(value):
            return False
    return True


def gen_ancillary_relationships(obj) -> Generator[
        Tuple[str, RelationshipProperty, Type["GenericTabletRecordMixin"]],
        None, None]:
    """
    For an SQLAlchemy ORM object, yields tuples of ``attrname,
    relationship_property, related_class`` for all relationships that are
    marked as a CamCOPS ancillary relationship.
    """
    for attrname, rel_prop, related_class in gen_relationships(obj):
        if rel_prop.info.get(RelationshipInfo.IS_ANCILLARY, None) is True:
            yield attrname, rel_prop, related_class


def gen_blob_relationships(obj) -> Generator[
        Tuple[str, RelationshipProperty, Type["GenericTabletRecordMixin"]],
        None, None]:
    """
    For an SQLAlchemy ORM object, yields tuples of ``attrname,
    relationship_property, related_class`` for all relationships that are
    marked as a CamCOPS BLOB relationship.
    """
    for attrname, rel_prop, related_class in gen_relationships(obj):
        if rel_prop.info.get(RelationshipInfo.IS_BLOB, None) is True:
            yield attrname, rel_prop, related_class


# =============================================================================
# Specializations of CamcopsColumn to save typing
# =============================================================================

def _name_type_in_column_args(args: Tuple[Any, ...]) -> Tuple[bool, bool]:
    """
    SQLAlchemy doesn't encourage deriving from Column. If you do, you have to
    implement ``__init__()`` and ``_constructor()`` carefully. The
    ``__init__()`` function will be called by user code, and via SQLAlchemy
    internals, including via ``_constructor`` (e.g. from
    ``Column.make_proxy()``).

    It is likely that ``__init__`` will experience many combinations of the
    column name and type being passed either in ``*args`` or ``**kwargs``. It
    must pass them on to :class:`Column`. If you don't mess with the type,
    that's easy; just pass them on unmodified. But if you plan to mess with the
    type, as we do in :class:`BoolColumn` below, we must make sure that we
    don't pass either of ``name`` or ``type_`` in *both* ``args`` and
    ``kwargs``.

    This function tells you whether ``name`` and ``type_`` are present in args,
    using the same method as ``Column.__init__()``.
    """
    name_in_args = False
    type_in_args = False
    args = list(args)  # make a copy, and make it a list not a tuple
    if args:
        if isinstance(args[0], util.string_types):
            name_in_args = True
            args.pop(0)
    if args:
        coltype = args[0]
        if hasattr(coltype, "_sqla_type"):
            type_in_args = True
    return name_in_args, type_in_args


# noinspection PyAbstractClass
class BoolColumn(CamcopsColumn):
    """
    A :class:`camcops_server.cc_modules.cc_sqla_coltypes.CamcopsColumn`
    representing a boolean value.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Must pass on all arguments, ultimately to Column, or when using
        # AbstractConcreteBase, you can get this:
        #
        # TypeError: Could not create a copy of this <class 'camcops_server.
        # cc_modules.cc_sqla_coltypes.BoolColumn'> object.  Ensure the class
        # includes a _constructor() attribute or method which accepts the
        # standard Column constructor arguments, or references the Column class
        # itself.
        #
        # During internal copying, "type_" can arrive here within kwargs, so
        # we must make sure that we don't send it on twice to super().__init().
        # Also, Column.make_proxy() calls our _constructor() with name and type
        # in args, so we must handle that, too...

        _, type_in_args = _name_type_in_column_args(args)
        self.constraint_name = kwargs.pop("constraint_name", None)  # type: Optional[str]  # noqa
        if not type_in_args:
            if self.constraint_name:
                constraint_name_conv = conv(self.constraint_name)
                # ... see help for ``conv``
            else:
                constraint_name_conv = None
            kwargs['type_'] = Boolean(name=constraint_name_conv)
            # The "name" parameter to Boolean() specifies the  name of the
            # (0, 1) constraint.
        kwargs['permitted_value_checker'] = BIT_CHECKER
        super().__init__(*args, **kwargs)
        if (not self.constraint_name and
                len(self.name) >= LONG_COLUMN_NAME_WARNING_LIMIT):
            log.warning(
                "BoolColumn with long column name and no constraint name: "
                "{!r}", self.name
            )

    def __repr__(self) -> str:
        def kvp(attrname: str) -> str:
            return f"{attrname}={getattr(self, attrname)!r}"
        elements = [
            kvp("constraint_name"),
            f"super()={super().__repr__()}",
        ]
        return f"BoolColumn({', '.join(elements)})"

    def _constructor(self, *args: Any, **kwargs: Any) -> "BoolColumn":
        """
        Make a copy; see
        https://bitbucket.org/zzzeek/sqlalchemy/issues/2284/please-make-column-easier-to-subclass
        """
        kwargs["constraint_name"] = self.constraint_name
        return super()._constructor(*args, **kwargs)


# =============================================================================
# Unit testing
# =============================================================================

class SqlaColtypesTest(unittest.TestCase):
    """
    Unit tests.
    """
    # don't inherit from ExtendedTestCase; circular import

    @staticmethod
    def _assert_dt_equal(a: Union[datetime.datetime, Pendulum],
                         b: Union[datetime.datetime, Pendulum]) -> None:
        # Accept that one may have been truncated or rounded to milliseconds.
        a = coerce_to_pendulum(a)
        b = coerce_to_pendulum(b)
        diff = a - b
        assert diff.microseconds < 1000, f"{a!r} != {b!r}"

    def test_iso_datetime_field(self) -> None:
        log.info("test_iso_datetime_field")

        # from pprint import pformat
        import pendulum
        from sqlalchemy.engine import create_engine
        from sqlalchemy.sql.expression import select
        from sqlalchemy.sql.schema import MetaData, Table

        engine = create_engine(SQLITE_MEMORY_URL, echo=True)
        meta = MetaData()
        meta.bind = engine  # adds execute() method to select() etc.
        # ... http://docs.sqlalchemy.org/en/latest/core/connections.html

        id_colname = 'id'
        dt_local_colname = 'dt_local'
        dt_utc_colname = 'dt_utc'
        iso_colname = 'iso'
        id_col = Column(id_colname, Integer, primary_key=True)
        dt_local_col = Column(dt_local_colname, DateTime)
        dt_utc_col = Column(dt_utc_colname, DateTime)
        iso_col = Column(iso_colname, PendulumDateTimeAsIsoTextColType)

        table = Table('testtable', meta,
                      id_col, dt_local_col, dt_utc_col, iso_col)
        table.create()

        now = Pendulum.now()
        now_utc = now.in_tz(pendulum.UTC)
        yesterday = now.subtract(days=1)
        yesterday_utc = yesterday.in_tz(pendulum.UTC)

        table.insert().values([
            {
                id_colname: 1,
                dt_local_colname: now,
                dt_utc_colname: now_utc,
                iso_colname: now,
            },
            {
                id_colname: 2,
                dt_local_colname: yesterday,
                dt_utc_colname: yesterday_utc,
                iso_colname: yesterday
            },
        ]).execute()
        select_fields = [
            id_col,
            dt_local_col,
            dt_utc_col,
            iso_col,
            func.length(dt_local_col).label("len_dt_local_col"),
            func.length(dt_utc_col).label("len_dt_utc_col"),
            func.length(iso_col).label("len_iso_col"),
            isotzdatetime_to_utcdatetime(iso_col).label("iso_to_utcdt"),
            unknown_field_to_utcdatetime(dt_utc_col).label("uk_utcdt_to_utcdt"),
            unknown_field_to_utcdatetime(iso_col).label("uk_iso_to_utc_dt"),
        ]
        rows = list(
            select(select_fields)
            .select_from(table)
            .order_by(id_col)
            .execute()
        )
        # for row in rows:
        #     log.debug("\n{}", pformat(dict(row)))
        self._assert_dt_equal(rows[0][dt_local_col], now)
        self._assert_dt_equal(rows[0][dt_utc_col], now_utc)
        self._assert_dt_equal(rows[0][iso_colname], now)
        self._assert_dt_equal(rows[0]["iso_to_utcdt"], now_utc)
        self._assert_dt_equal(rows[0]["uk_utcdt_to_utcdt"], now_utc)
        self._assert_dt_equal(rows[0]["uk_iso_to_utc_dt"], now_utc)
        self._assert_dt_equal(rows[1][dt_local_col], yesterday)
        self._assert_dt_equal(rows[1][dt_utc_col], yesterday_utc)
        self._assert_dt_equal(rows[1][iso_colname], yesterday)
        self._assert_dt_equal(rows[1]["iso_to_utcdt"], yesterday_utc)
        self._assert_dt_equal(rows[1]["uk_utcdt_to_utcdt"], yesterday_utc)
        self._assert_dt_equal(rows[1]["uk_iso_to_utc_dt"], yesterday_utc)

    @staticmethod
    def _assert_duration_equal(a: Duration, b: Duration) -> None:
        assert a == b, f"{a!r} != {b!r}"

    def test_iso_duration_field(self) -> None:
        log.info("test_iso_duration_field")

        from sqlalchemy.engine import create_engine
        from sqlalchemy.sql.expression import select
        from sqlalchemy.sql.schema import MetaData, Table

        # As above:
        engine = create_engine(SQLITE_MEMORY_URL, echo=True)
        meta = MetaData()
        meta.bind = engine

        id_colname = 'id'
        duration_colname = 'duration_iso'
        id_col = Column(id_colname, Integer, primary_key=True)
        duration_col = Column(duration_colname,
                              PendulumDurationAsIsoTextColType)

        table = Table('testtable', meta,
                      id_col, duration_col)
        table.create()

        d1 = Duration(years=1, months=3, seconds=3, microseconds=4)
        d2 = Duration(seconds=987.654321)
        d3 = Duration(days=-5)

        table.insert().values([
            {
                id_colname: 1,
                duration_colname: d1,
            },
            {
                id_colname: 2,
                duration_colname: d2,
            },
            {
                id_colname: 3,
                duration_colname: d3,
            },
        ]).execute()
        select_fields = [
            id_col,
            duration_col,
        ]
        rows = list(
            select(select_fields)
            .select_from(table)
            .order_by(id_col)
            .execute()
        )
        self._assert_duration_equal(rows[0][duration_col], d1)
        self._assert_duration_equal(rows[1][duration_col], d2)
        self._assert_duration_equal(rows[2][duration_col], d3)

    @staticmethod
    def _assert_version_equal(a: Version, b: Version) -> None:
        assert a == b, f"{a!r} != {b!r}"

    def test_semantic_version_field(self) -> None:
        log.info("test_semantic_version_field")

        from sqlalchemy.engine import create_engine
        from sqlalchemy.sql.expression import select
        from sqlalchemy.sql.schema import MetaData, Table

        # As above:
        engine = create_engine(SQLITE_MEMORY_URL, echo=True)
        meta = MetaData()
        meta.bind = engine

        id_colname = 'id'
        version_colname = 'version'
        id_col = Column(id_colname, Integer, primary_key=True)
        version_col = Column(version_colname, SemanticVersionColType)

        table = Table('testtable', meta,
                      id_col, version_col)
        table.create()

        v1 = Version("1.1.0")
        v2 = Version("2.0.1")
        v3 = Version("14.0.0")

        table.insert().values([
            {
                id_colname: 1,
                version_colname: v1,
            },
            {
                id_colname: 2,
                version_colname: v2,
            },
            {
                id_colname: 3,
                version_colname: v3,
            },
        ]).execute()
        select_fields = [
            id_col,
            version_col,
        ]
        rows = list(
            select(select_fields)
            .select_from(table)
            .order_by(id_col)
            .execute()
        )
        self._assert_version_equal(rows[0][version_col], v1)
        self._assert_version_equal(rows[1][version_col], v2)
        self._assert_version_equal(rows[2][version_col], v3)


# =============================================================================
# main
# =============================================================================
# run with "python -m camcops_server.cc_modules.cc_sqla_coltypes -v" to be verbose  # noqa

if __name__ == "__main__":
    main_only_quicksetup_rootlogger(level=logging.DEBUG)
    unittest.main()
