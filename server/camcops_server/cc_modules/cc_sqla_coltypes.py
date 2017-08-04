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
    LargeBinary
    MatchType       -- for the return type of the MATCH operator
    Numeric         -- for fixed-precision numbers like NUMERIC or DECIMAL
    PickleType
    SchemaType
    SmallInteger
    String          -- VARCHAR
    Text            -- variably sized string type
    Time
    Unicode         -- implies that the underlying column explicitly supports unicode
    UnicodeText
    
Not supported across all platforms:

    BIGINT UNSIGNED -- MySQL: 0 to 18446744073709551615
                    -- use sqlalchemy.dialects.mysql.BIGINT(unsigned=True)
    INT UNSIGNED    -- MySQL: 0 to 4294967295
                    -- use sqlalchemy.dialects.mysql.INTEGER(unsigned=True)

"""  # noqa

# =============================================================================
# Imports
# =============================================================================

import datetime
import logging
from typing import Any, Generator, List, Optional, Tuple, Union

import arrow
from arrow import Arrow
import dateutil.parser
import pytz
from semantic_version import Version
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import Mapper
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import String, Unicode
from sqlalchemy.sql.type_api import TypeDecorator

from .cc_lang import simple_repr
from .cc_version import make_version

log = logging.getLogger(__name__)  # don't use BraceAdapter here; we use {}


# =============================================================================
# Constants
# =============================================================================

DEBUG_CUSTOM_COLTYPES = True
ISO8601_STRING_LENGTH = 32
# ... max length e.g. 2013-07-24T20:04:07.123456+01:00
#     (microseconds, colon in timezone).

# =============================================================================
# Simple derivative column types
# =============================================================================
# If you insert something too long into a VARCHAR, it just gets truncated.

AuditSourceColType = String(length=20)
BigIntUnsigned = BIGINT(unsigned=True)  # *** DEPRECATED; MySQL-specific

CharColType = String(length=1)

DeviceNameColType = String(length=255)

EraColType = String(length=ISO8601_STRING_LENGTH)  # underlying SQL type

FilterTextColType = Unicode(length=255)

HashedPasswordColType = String(length=255)
HostnameColType = String(length=255)

IdDescriptorColType = Unicode(length=255)
IntUnsigned = INTEGER(unsigned=True)  # *** DEPRECATED; MySQL-specific
IPAddressColType = String(length=45)  # http://stackoverflow.com/questions/166132  # noqa
# This is a plain string.
# See also e.g. http://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/types/ip_address.html  # noqa

LongText = LONGTEXT()

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
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "DateTimeAsIsoTextColType.process_bind_param("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        return arrow_to_isostring(value)

    def process_literal_param(self, value: Any, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "DateTimeAsIsoTextColType.process_literal_param("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        return arrow_to_isostring(value)

    def process_result_value(self, value: Any,
                             dialect: Dialect) -> Optional[Arrow]:
        """Convert things on the way from the database to Python."""
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "DateTimeAsIsoTextColType.process_result_value("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        return isostring_to_arrow(value)

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
            log.debug("operate(self={}, op={}, other={})".format(
                repr(self), repr(op), repr(other)))
            log.debug("self.expr = {}".format(repr(self.expr)))
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
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "SemanticVersionColType.process_bind_param("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        return str(value)

    def process_literal_param(self, value: Version, dialect: Dialect) -> str:
        """Convert things on the way from Python to the database."""
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "SemanticVersionColType.process_literal_param("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        return str(value)

    def process_result_value(self, value: str,
                             dialect: Dialect) -> Optional[Version]:
        """Convert things on the way from the database to Python."""
        if DEBUG_CUSTOM_COLTYPES:
            log.debug(
                "SemanticVersionColType.process_result_value("
                "self={}, value={}, dialect={})".format(
                    repr(self), repr(value), repr(dialect)))
        if value is None:
            return None
        # Here we do some slightly fancier conversion to deal with all sorts
        # of potential rubbish coming in, so we get a properly ordered Version
        # out:
        return make_version(value)

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
        return simple_repr(self)


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
    def __init__(self, *args, **kwargs) -> None:
        self.cris_include = bool(kwargs.pop('cris_include', False))
        self.exempt_from_anonymisation = bool(
            kwargs.pop('exempt_from_anonymisation', False))
        self.identifies_patient = bool(kwargs.pop('identifies_patient', False))

        self.is_blob_id_field = bool(kwargs.pop('is_blob_id_field', False))
        self.blob_field_xml_name = str(kwargs.pop('blob_field_xml_name', ""))

        self.permitted_value_checker = kwargs.pop(
            'permitted_value_checker', None)  # type: Optional[PermittedValueChecker]  # noqa
        assert (self.permitted_value_checker is None or
                isinstance(self.permitted_value_checker,
                           PermittedValueChecker))

        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        def kvp(attrname: str) -> str:
            return "{}={!r}".format(attrname, getattr(self, attrname))
        elements = [
            kvp("cris_include"),
            kvp("exempt_from_anonymisation"),
            kvp("identifies_patient"),
            kvp("is_blob_id_field"),
            kvp("blob_field_xml_name"),
            kvp("permitted_value_checker"),
            super().__repr__(),
        ]
        return "CamcopsColumn<{}>".format(",".join(elements))


def gen_columns(obj) -> Generator[Tuple[str, Column], None, None]:
    """
    Yields tuples of (attr_name, Column) from an object.
    """
    mapper = obj.__mapper__ # type: Mapper
    assert mapper, "gen_columns called on {!r} which is not an " \
                   "SQLAlchemy ORM object".format(obj)
    if not mapper.columns:
        return
    for attrname, column in mapper.columns.items():
        # NB: column.name is the SQL column name, not the attribute name
        yield attrname, column

    # Don't bother using
    #   cls = obj.__class_
    #   for attrname in dir(cls):
    #       cls_attr = getattr(cls, attrname)
    #       # ... because, for columns, these will all be instances of
    #       # sqlalchemy.orm.attributes.InstrumentedAttribute.



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
                            "column name {!r}".format(attrname, column.name))
            yield attrname, column


def get_column_attr_names(obj) -> List[str]:
    return [attrname for attrname, _ in gen_columns(obj)]


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
