#!/usr/bin/env python
# camcops_server/cc_modules/cc_sqla_coltypes.py

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

Note these built-in SQLAlchemy types:
http://docs.sqlalchemy.org/en/latest/core/type_basics.html#generic-types

    BigInteger      -- MySQL: -9223372036854775808 to 9223372036854775807
    Boolean
    Date
    DateTime
    Enum
    Float
    Integer         -- MySQL: -2147483648 to 2147483647
    Interval        -- for datetime.timedelta
    LargeBinary     -- under MySQL, maps to BLOB
    MatchType       -- for the return type of the MATCH operator
    Numeric         -- for fixed-precision numbers like NUMERIC or DECIMAL
    PickleType
    SchemaType
    SmallInteger
    String          -- VARCHAR
    Text            -- variably sized string type
                        ... under MySQL, renders as TEXT
    Time
    Unicode         -- implies that the underlying column explicitly supports unicode
    UnicodeText     -- variably sized version of Unicode
                        ... under MySQL, renders as TEXT too
    
Not supported across all platforms:

    BIGINT UNSIGNED -- MySQL: 0 to 18446744073709551615
                    -- use sqlalchemy.dialects.mysql.BIGINT(unsigned=True)
    INT UNSIGNED    -- MySQL: 0 to 4294967295
                    -- use sqlalchemy.dialects.mysql.INTEGER(unsigned=True)

Other MySQL sizes:

    TINYBLOB        -- 2^8 bytes = 256 bytes
    BLOB            -- 2^16 bytes = 64 KiB
    MEDIUMBLOB      -- 2^24 bytes = 16 MiB
    LONGBLOB        -- 2^32 bytes = 4 GiB 

    TINYTEXT        -- 255 (2^8 - 1) bytes
    TEXT            -- 65,535 bytes (2^16 - 1) = 64 KiB
    MEDIUMTEXT      -- 16,777,215 (2^24 - 1) bytes = 16 MiB
    LONGTEXT        -- 4,294,967,295 (2^32 - 1) bytes = 4 GiB
        ... https://stackoverflow.com/questions/13932750/tinytext-text-mediumtext-and-longtext-maximum-storage-sizes

Also:

    Columns may need their character set specified explicitly under MySQL:
        https://stackoverflow.com/questions/2108824/mysql-incorrect-string-value-error-when-save-unicode-string-in-django

"""  # noqa

# =============================================================================
# Imports
# =============================================================================

import datetime
import logging
from typing import Any, Generator, List, Optional, Tuple, Union

import arrow
from arrow import Arrow
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.reprfunc import auto_repr
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_columns
import dateutil.parser
import pytz
from semantic_version import Version
from sqlalchemy.dialects import mysql
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import (
    Boolean,
    Integer,
    LargeBinary,
    String,
    Unicode,
    UnicodeText,
)
from sqlalchemy.sql.type_api import TypeDecorator

from .cc_constants import PV
from .cc_version import make_version

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

DEBUG_DATETIME_AS_ISO_TEXT = False
DEBUG_SEMANTIC_VERSION = False

ICD9_CODE_MAX_LENGTH = 6  # longest is "xxx.xx"; thus, 6; see
# https://www.cms.gov/Medicare/Quality-Initiatives-Patient-Assessment-Instruments/HospitalQualityInits/Downloads/HospitalAppendix_F.pdf  # noqa
ICD10_CODE_MAX_LENGTH = 7  # longest is e.g. "F00.000"; "F10.202"; thus, 7
MAX_DIAGNOSTIC_CODE_LENGTH = max(
    ICD9_CODE_MAX_LENGTH,
    ICD10_CODE_MAX_LENGTH
)
ISO8601_STRING_LENGTH = 32
# ... max length e.g. 2013-07-24T20:04:07.123456+01:00
#     (microseconds, colon in timezone).

# =============================================================================
# Simple derivative column types
# =============================================================================
# If you insert something too long into a VARCHAR, it just gets truncated.

AuditSourceColType = String(length=20)
BigIntUnsigned = Integer().with_variant(mysql.BIGINT(unsigned=True), 'mysql')

CharColType = String(length=1)

DeviceNameColType = String(length=255)
DiagnosticCodeColType = String(length=MAX_DIAGNOSTIC_CODE_LENGTH)

EraColType = String(length=ISO8601_STRING_LENGTH)  # underlying SQL type

FilterTextColType = Unicode(length=255)

HashedPasswordColType = String(length=255)
HostnameColType = String(length=255)

IdDescriptorColType = Unicode(length=255)
IntUnsigned = Integer().with_variant(mysql.INTEGER(unsigned=True), 'mysql')
IPAddressColType = String(length=45)  # http://stackoverflow.com/questions/166132  # noqa
# This is a plain string.
# See also e.g. http://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/types/ip_address.html  # noqa

# Large BLOB:
# https://stackoverflow.com/questions/43791725/sqlalchemy-how-to-make-a-longblob-column-in-mysql  # noqa
# One of these:
# LongBlob = LargeBinary().with_variant(mysql.LONGBLOB, "mysql")
LongBlob = LargeBinary(length=(2 ** 32) - 1)

LongText = UnicodeText().with_variant(mysql.LONGTEXT, 'mysql')

MimeTypeColType = String(length=255)  # https://stackoverflow.com/questions/643690  # noqa

PatientNameColType = Unicode(length=255)

SendingFormatColType = String(length=50)
SessionTokenColType = String(length=50)  # previously: TOKEN
SexColType = String(length=1)
StoredVarNameColType = String(length=255)  # probably overkill!
StoredVarTypeColType = String(length=255)  # probably overkill!
SummaryCategoryColType = String(length=50)  # pretty generic

TableNameColType = String(length=255)

UserNameColType = String(length=255)


# =============================================================================
# Custom date/time field as ISO-8601 text including timezone, using Arrow
# on the Python side.
# =============================================================================

def arrow_to_isostring(x: Arrow) -> Optional[str]:
    """
    From a Python datetime to an ISO-formatted string in our particular format.
    """
    # https://docs.python.org/3.4/library/datetime.html#strftime-strptime-behavior  # noqa
    try:
        mainpart = x.strftime("%Y-%m-%dT%H:%M:%S.%f")  # microsecond accuracy
        timezone = x.strftime("%z")  # won't have the colon in
        return mainpart + timezone[:-2] + ":" + timezone[-2:]
    except AttributeError:
        return None


def isostring_to_arrow(x: str) -> Optional[Arrow]:
    """From an ISO-formatted string to a Python Arrow, with timezone."""
    if not x:
        return None  # otherwise Arrow will give us the current date
    try:
        return dateutil.parser.parse(x)
    except arrow.arrow.parser.ParserError:
        return None


def python_datetime_to_utc(x):
    """From a Python datetime, with timezone, to a UTC Python version."""
    try:
        return x.astimezone(pytz.utc)
    except AttributeError:
        return None


def mysql_isotzdatetime_to_utcdatetime(x):
    """
    Creates an SQL expression wrapping a field containing our ISO-8601 text,
    making a DATETIME out of it, in the UTC timezone.

    For format, see
        https://dev.mysql.com/doc/refman/5.5/en/date-and-time-functions.html#function_date-format  # noqa
    Note the use of "%i" for minutes.
    Things after "func." get passed to the database engine as literal SQL
    functions; http://docs.sqlalchemy.org/en/latest/core/tutorial.html
    """
    return func.CONVERT_TZ(  # convert a DATETIME's timezone...
        func.STR_TO_DATE(    # for this DATETIME...
            func.LEFT(x, func.LENGTH(x) - 6),  # drop the rightmost 6 chars
            '%Y-%m-%dT%H:%i:%S.%f'             # and read from this format
        ),
        func.RIGHT(x, 6),    # from this old timezone...
        "+00:00"             # ... to this new timezone.
    )


def mysql_unknown_field_to_utcdatetime(x):
    """The field might be a DATETIME, or an ISO-formatted field."""
    return func.IF(
        func.LENGTH(x) == 19,
        # ... length of a plain DATETIME e.g. 2013-05-30 00:00:00
        x,
        mysql_isotzdatetime_to_utcdatetime(x)
    )


class DateTimeAsIsoTextColType(TypeDecorator):
    """
    Stores date/time values as ISO-8601, in a specific format.
    Uses Arrow on the Python side.
    """

    impl = String(length=ISO8601_STRING_LENGTH)  # underlying SQL type

    @property
    def python_type(self):
        return Arrow

    def process_bind_param(self, value: Any, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        retval = arrow_to_isostring(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "DateTimeAsIsoTextColType.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Any, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        retval = arrow_to_isostring(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "DateTimeAsIsoTextColType.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self, value, dialect, retval)
        return retval

    def process_result_value(self, value: Any,
                             dialect: Dialect) -> Optional[Arrow]:
        """Convert things on the way from the database to Python."""
        retval = isostring_to_arrow(value)
        if DEBUG_DATETIME_AS_ISO_TEXT:
            log.debug(
                "DateTimeAsIsoTextColType.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self, value, dialect, retval)
        return retval

    # noinspection PyPep8Naming
    class comparator_factory(TypeDecorator.Comparator):
        """Process SQL for when we are comparing our column, in the database,
        to something else."""

        def operate(self, op, *other, **kwargs):
            assert len(other) == 1
            assert not kwargs
            other = other[0]
            if isinstance(other, datetime.datetime):
                processed_other = python_datetime_to_utc(other)
            else:
                # OK. At this point, "other" could be a plain DATETIME field,
                # or a DateTimeAsIsoText field (or potentially something
                # else that we don't really care about). If it's a DATETIME,
                # then we assume it is already in UTC.
                processed_other = mysql_unknown_field_to_utcdatetime(other)
            if DEBUG_DATETIME_AS_ISO_TEXT:
                log.debug("operate(self={!r}, op={!r}, other={!r})",
                          self, op, other)
                log.debug("self.expr = {!r}", self.expr)
                # traceback.print_stack()
            return op(mysql_isotzdatetime_to_utcdatetime(self.expr),
                      processed_other)
            # NOT YET IMPLEMENTED: dialects other than MySQL, and how to
            # detect the dialect at this point.

        def reverse_operate(self, op, *other, **kwargs):
            assert False, "I don't think this is ever being called"


# =============================================================================
# Semantic version column type
# =============================================================================

class SemanticVersionColType(TypeDecorator):
    """
    Stores semantic versions in the database.
    Uses semantic_version.Version on the Python side.
    """

    impl = String(length=147)  # https://github.com/mojombo/semver/issues/79

    @property
    def python_type(self):
        return Version

    def process_bind_param(self, value: Version, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        retval = str(value)
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "SemanticVersionColType.process_bind_param("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self, value, dialect, retval)
        return retval

    def process_literal_param(self, value: Version, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        retval = str(value)
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "SemanticVersionColType.process_literal_param("
                "self={!r}, value={!r}, dialect={!r}) -> !r",
                self, value, dialect, retval)
        return retval

    def process_result_value(self, value: str,
                             dialect: Dialect) -> Optional[Version]:
        """Convert things on the way from the database to Python."""
        if value is None:
            retval = None
        else:
            # Here we do some slightly fancier conversion to deal with all
            # sorts of potential rubbish coming in, so we get a properly
            # ordered Version out:
            retval = make_version(value)
        if DEBUG_SEMANTIC_VERSION:
            log.debug(
                "SemanticVersionColType.process_result_value("
                "self={!r}, value={!r}, dialect={!r}) -> {!r}",
                self, value, dialect, retval)
        return retval

    # noinspection PyPep8Naming
    class comparator_factory(TypeDecorator.Comparator):
        """Process SQL for when we are comparing our column, in the database,
        to something else."""

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


# =============================================================================
# PermittedValueChecker: used by CamcopsColumn
# =============================================================================

class PermittedValueChecker(object):
    """
    Represents permitted values, and checks a value against them.
    """
    def __init__(self,
                 not_null: bool = False,
                 minimum: Union[int, float] = None,
                 maximum: Union[int, float] = None,
                 permitted_values: List[Any] = None) -> None:
        self.not_null = not_null
        self.minimum = minimum
        self.maximum = maximum
        self.permitted_values = permitted_values

    def is_ok(self, value: Any) -> bool:
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
        if value is None:
            if self.not_null:
                return "value is None and NULL values are not permitted"
            else:
                return ""  # value is OK
        if self.permitted_values is not None and value not in self.permitted_values:  # noqa
            return "value {!r} not in permitted values {!r}".format(
                value, self.permitted_values)
        if self.minimum is not None and value < self.minimum:
            return "value {!r} less than minimum of {!r}".format(
                value, self.minimum)
        if self.maximum is not None and value > self.maximum:
            return "value {!r} more than maximum of {!r}".format(
                value, self.maximum)
        return ""

    def __repr__(self):
        return auto_repr(self)


# Specific instances, to reduce object duplication:

MIN_ZERO_CHECKER = PermittedValueChecker(minimum=0)

BIT_CHECKER = PermittedValueChecker(permitted_values=PV.BIT)
ZERO_TO_ONE_CHECKER = PermittedValueChecker(minimum=0, maximum=1)
ZERO_TO_TWO_CHECKER = PermittedValueChecker(minimum=0, maximum=2)
ZERO_TO_THREE_CHECKER = PermittedValueChecker(minimum=0, maximum=3)
ZERO_TO_FOUR_CHECKER = PermittedValueChecker(minimum=0, maximum=4)
ZERO_TO_FIVE_CHECKER = PermittedValueChecker(minimum=0, maximum=5)

ONE_TO_FOUR_CHECKER = PermittedValueChecker(minimum=1, maximum=4)
ONE_TO_FIVE_CHECKER = PermittedValueChecker(minimum=1, maximum=5)
ONE_TO_SIX_CHECKER = PermittedValueChecker(minimum=1, maximum=6)


# =============================================================================
# CamcopsColumn: provides extra functions over Column.
# =============================================================================

# noinspection PyAbstractClass
class CamcopsColumn(Column):
    """
    A Column class that supports some CamCOPS-specific flags, such as whether
    a field is a BLOB reference; how it should be treated for anonymisation;
    and which values are permitted in the field (in a soft sense: duff values
    cause errors to be reported, but they're still stored.
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

    def __repr__(self) -> str:
        def kvp(attrname: str) -> str:
            return "{}={!r}".format(attrname, getattr(self, attrname))
        elements = [
            kvp("cris_include"),
            kvp("exempt_from_anonymisation"),
            kvp("identifies_patient"),
            kvp("is_blob_id_field"),
            kvp("blob_relationship_attr_name"),
            kvp("permitted_value_checker"),
            super().__repr__(),
        ]
        return "CamcopsColumn<{}>".format(",".join(elements))

    def set_permitted_value_checker(
            self, permitted_value_checker: PermittedValueChecker) -> None:
        self.permitted_value_checker = permitted_value_checker


# =============================================================================
# Operate on Column/CamcopsColumn properties
# =============================================================================

def gen_columns_matching_attrnames(obj, attrnames: List[str]) \
        -> Generator[Tuple[str, Column], None, None]:
    for attrname, column in gen_columns(obj):
        if attrname in attrnames:
            yield attrname, column


def gen_camcops_columns(obj) -> Generator[Tuple[str, CamcopsColumn],
                                          None, None]:
    """
    Yields tuples of (attr_name, CamcopsColumn) from an object.
    """
    for attrname, column in gen_columns(obj):
        if isinstance(column, CamcopsColumn):
            yield attrname, column


def gen_camcops_blob_columns(obj) -> Generator[Tuple[str, CamcopsColumn],
                                               None, None]:
    """
    Yields tuples of (attr_name, CamcopsColumn) from a class where those
    CamcopsColumns are for fields referencing the BLOB table.
    """
    for attrname, column in gen_camcops_columns(obj):
        if column.is_blob_id_field:
            if attrname != column.name:
                log.warning("BLOB field where attribute name {!r} != SQL "
                            "column name {!r}", attrname, column.name)
            yield attrname, column


def get_column_attr_names(obj) -> List[str]:
    return [attrname for attrname, _ in gen_columns(obj)]


def get_camcops_column_attr_names(obj) -> List[str]:
    return [attrname for attrname, _ in gen_camcops_columns(obj)]


def get_camcops_blob_column_attr_names(obj) -> List[str]:
    return [attrname for attrname, _ in gen_camcops_blob_columns(obj)]


def permitted_value_failure_msgs(obj) -> List[str]:
    """
    Checks a SQLAlchemy ORM object instance against its PermittedValueColumn
    checks, if it has any.
    Returns a list of failure messages (empty list means all OK).
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
                "Invalid value for {}: {}".format(attrname, failure_msg))
    return failure_msgs


def permitted_values_ok(obj) -> bool:
    """
    Faster way of checking WHETHER an instance passes its PermittedValueColumn
    checks, if it has any.
    """
    for attrname, camcops_column in gen_camcops_columns(obj):
        pv_checker = camcops_column.permitted_value_checker  # type: Optional[PermittedValueChecker]  # noqa
        if pv_checker is None:
            continue
        value = getattr(obj, attrname)
        if not pv_checker.is_ok(value):
            return False
    return True


# =============================================================================
# Specializations of CamcopsColumn to save typing
# =============================================================================

# noinspection PyAbstractClass
class BoolColumn(CamcopsColumn):
    def __init__(self, name: str):
        super().__init__(
            name, Boolean,
            permitted_value_checker=BIT_CHECKER
        )
