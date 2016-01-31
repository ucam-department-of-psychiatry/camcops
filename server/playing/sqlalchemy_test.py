#!/usr/bin/env python3

"""

Things to achieve before a switch to SQL Alchemy is viable:

- Proper processing of dates in our text-based ISO-8601 format.

    Recent changes to SQLA allow hybrid attributes:
    http://stackoverflow.com/questions/21126371/converting-string-to-date-timestamp-in-sqlalchemy

- Ability to specify fieldspecs (etc.) in a table class, with CamCOPS extras
  like permitted values and comments, and then have them be mapped, via
  SQLA's mapper() function, to objects.

  See

    http://stackoverflow.com/questions/5424942/sqlalchemy-model-definition-at-execution
    http://stackoverflow.com/questions/4678115/how-to-dynamically-create-sqlalchemy-columns

"""  # noqa

import datetime
import dateutil.parser
import getpass
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

import pytz
import sqlalchemy  # sudo apt-get install python-sqlalchemy
import sqlalchemy.types
from sqlalchemy import (
    Column,
    DateTime,
    # ForeignKey,
    Integer,
    # MetaData,
    # Sequence,
    String,
    # Table
)
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.ext.hybrid import Comparator
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func

Base = declarative_base()


# =============================================================================
# Ancillary functions
# =============================================================================

def heading(x):
    print("=" * 79)
    print(x)
    print("=" * 79)


def ask_user(prompt, default=None, returntype=None, mask=False):
    if default is not None:
        fullprompt = "{} [{}]: ".format(prompt, default)
    else:
        fullprompt = "{}: ".format(prompt)
    success = False
    while not success:
        if mask:
            value = getpass.getpass(fullprompt) or default
        else:
            value = input(fullprompt) or default
        if returntype is not None:
            try:
                value = returntype(value)
                success = True
            except:
                print("Bad value, try again")
        else:
            success = True
    return value


def engine_mysql(user, password, host, port, database, echo=True):
    CONNECTSTRING = "mysql://{}:{}@{}:{}/{}?charset=utf8&use_unicode=0".format(
        user,
        password,
        host,
        port,
        database
    )
    return sqlalchemy.create_engine(CONNECTSTRING, echo=echo)


def engine_mysql_commandline(echo=True):
    host = ask_user("Host", "localhost")
    port = 3306
    database = ask_user("Database", "testdb")
    user = ask_user("User", "root")
    password = ask_user("Password", mask=True)
    return engine_mysql(user, password, host, port, database, echo=echo)


# =============================================================================
# Custom date/time field as ISO-8601 text including timezone
# =============================================================================

"""
What do we expect to have to do, as a minimum?
- A Python representation-to-value and value-to-representation function
- A SQL representation-to-value function, for SELECT statements to pick out
  relevant values before anything gets to Python

Comparisons should be done with the UTC version of the datetime (not, for
example, the "ignore timezone" version).
- Python representation-to-value: dateutil.parser.parse()
- Python value-to-representation: strftime
- SQL representation-to-value: chop up the strings into bits and fiddle.
  (See below.) String looks like: 2015-01-30T21:30:42.123456+01:00
                                                         ^^^
                                                         may be absent

Example (Javascript output):
    2015-07-15T14:45:14.630+01:00           length = 29
Also acceptable (Python output):
    2015-07-15T14:45:14.630123+01:00        length = 32
Note that Python doesn't put the colon in the timezone by default, so we
insert it using python_datetime_to_iso().

http://docs.sqlalchemy.org/en/rel_1_0/core/custom_types.html
http://docs.sqlalchemy.org/en/latest/orm/extensions/hybrid.html#building-custom-comparators

Relevant methods:

- use TypeDecorator to augment existing type
    Python representation-to-value      process_bind_param
    Python value-to-representation      process_result_value
    SQL representation-to-value         ?

- use UserDefinedType to create a new type
    Python representation-to-value      bind_processor
    Python value-to-representation      result_processor
    SQL representation-to-value         ?

- create a custom Comparator for SQL comparison
    Python representation-to-value      -
    Python value-to-representation      -
    SQL representation-to-value         yes

- create a hybrid property, e.g.
    - class field is someisodatetime
    - class hybrid property is someisodatetime_utc, defined with

        @hybrid_property
        def someisodatetime_utc(self):
            return SomeComparator(self.someisodatetime)

    - another example, using the "@someproperty.expression" notation:
        http://stackoverflow.com/questions/21126371/converting-string-to-date-timestamp-in-sqlalchemy

However, what we'd like is a single field type, not a necessity for additional
hybrid_property attributes.

So, combining a TypeDecorator with a Comparator:

- https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DatabaseCrypt
- https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/SymmetricEncryption
    ... *** explore this; no explicit Comparator used; does it work?

"""


# -----------------------------------------------------------------------------
# Conversion functions
# -----------------------------------------------------------------------------

def python_datetime_to_iso(x):
    """From a Python datetime to an ISO-formatted string in our particular
    format."""
    # https://docs.python.org/3.4/library/datetime.html#strftime-strptime-behavior  # noqa
    try:
        mainpart = x.strftime("%Y-%m-%dT%H:%M:%S.%f")  # microsecond accuracy
        timezone = x.strftime("%z")  # won't have the colon in
        return mainpart + timezone[:-2] + ":" + timezone[-2:]
    except AttributeError:
        return None


def iso_to_python_datetime(x):
    """From an ISO-formatted string to a Python datetime, with timezone."""
    try:
        return dateutil.parser.parse(x)
    except (AttributeError, ValueError):
        return None


def python_datetime_to_utc(x):
    """From a Python datetime, with timezone, to a UTC Python version."""
    try:
        return x.astimezone(pytz.utc)
    except AttributeError:
        return None


def mysql_isotzdatetime_to_utcdatetime(x):
    """Creates an SQL expression wrapping a field containing our ISO-8601 text,
    making a DATETIME out of it, in the UTC timezone."""
    # For format, see
    #   https://dev.mysql.com/doc/refman/5.5/en/date-and-time-functions.html#function_date-format  # noqa
    # Note the use of "%i" for minutes.
    """
    Testing:

    SELECT
        when_created,
        LEFT(when_created, LENGTH(when_created) - 6) AS timepart,
        STR_TO_DATE(
            LEFT(when_created, LENGTH(when_created) - 6),
            '%Y-%m-%dT%H:%i:%S.%f'
        ) AS timepart_as_datetime,
        RIGHT(when_created, 6) AS timezone,
        CONVERT_TZ(
            STR_TO_DATE(
                LEFT(when_created, LENGTH(when_created) - 6),
                '%Y-%m-%dT%H:%i:%S.%f'
            ),
            RIGHT(when_created, 6),          -- timezone
            "+00:00"                    -- UTC
        ) AS final_datetime,

        when_deleted,
        LEFT(when_deleted, LENGTH(when_deleted) - 6) AS timepart,
        STR_TO_DATE(
            LEFT(when_deleted, LENGTH(when_deleted) - 6),
            '%Y-%m-%dT%H:%i:%S.%f'
        ) AS timepart_as_datetime,
        RIGHT(when_deleted, 6) AS timezone,
        CONVERT_TZ(
            STR_TO_DATE(
                LEFT(when_deleted, LENGTH(when_deleted) - 6),
                '%Y-%m-%dT%H:%i:%S.%f'
            ),
            RIGHT(when_deleted, 6),          -- timezone
            "+00:00"                    -- UTC
        ) AS final_datetime
    FROM phq9;
    """
    # Things after "func." get passed to the database engine as literal SQL
    # functions; http://docs.sqlalchemy.org/en/latest/core/tutorial.html
    return func.CONVERT_TZ(
        func.STR_TO_DATE(
            func.LEFT(x, func.LENGTH(x) - 6),
            '%Y-%m-%dT%H:%i:%S.%f'
        ),
        func.RIGHT(x, 6),
        "+00:00"
    )


def mysql_unknown_field_to_utcdatetime(x):
    """The field might be a DATETIME, or an ISO-formatted field."""
    return func.IF(
        func.LENGTH(x) == 19,
        # ... length of a plain DATETIME e.g. 2013-05-30 00:00:00
        x,
        mysql_isotzdatetime_to_utcdatetime(x)
    )


# -----------------------------------------------------------------------------
# Date-conversion field type
# -----------------------------------------------------------------------------

class DateTimeAsIsoText(sqlalchemy.types.TypeDecorator):
    '''
    Stores date/time values as ISO-8601.
    '''
    impl = sqlalchemy.types.String(32)  # underlying SQL type

    def process_bind_param(self, value, dialect):
        """Convert things on the way from Python to the database."""
        return python_datetime_to_iso(value)

    def process_result_value(self, value, dialect):
        """Convert things on the way from the database to Python."""
        return iso_to_python_datetime(value)

    class comparator_factory(String.Comparator):
        """Process SQL for when we are comparing our column, in the database,
        to something else.

        We start by overriding operate(self, op, other).
        operate() is the lowest level of operation.
        http://docs.sqlalchemy.org/en/rel_1_0/core/sqlelement.html

        However, we need to know what "other" is.
        If it's a literal (e.g. datetime), we shouldn't convert it.
        Likewise if it is a real DATETIME field, we shouldn't convert it.
        But if it's another of our kin, we should.

        http://docs.sqlalchemy.org/en/latest/core/custom_types.html#types-operators  # noqa
        http://docs.sqlalchemy.org/en/latest/core/type_api.html#sqlalchemy.types.TypeEngine.Comparator  # noqa
        http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.operators.Operators  # noqa

        So we could do:

        def operate(self, op, other):
            if isinstance(other, datetime.datetime):
                processed_other = other
            else:
                processed_other = mysql_isotzdatetime_to_utcdatetime(other)
            return op(mysql_isotzdatetime_to_utcdatetime(self.expr),
                      processed_other)

        However, that fails to distinguish between situations where "other"
        is a plain DATETIME field and when "other" is one of our kin.

        So, is the solution to leave "other" unprocessed but also to implement
        reverse_operate?

        def operate(self, op, other):
            return op(mysql_isotzdatetime_to_utcdatetime(self.expr),
                      other)

        def reverse_operate(self, op, other):
            return op(other,
                      mysql_isotzdatetime_to_utcdatetime(self.expr))

        No; reverse_operate wasn't called.

        """
        def operate(self, op, other):
            if isinstance(other, datetime.datetime):
                processed_other = python_datetime_to_utc(other)
            else:
                # OK. At this point, "other" could be a plain DATETIME field,
                # or a DateTimeAsIsoText field (or potentially something
                # else that we don't really care about). If it's a DATETIME,
                # then we assume it is already in UTC.
                processed_other = mysql_unknown_field_to_utcdatetime(other)
            return op(mysql_isotzdatetime_to_utcdatetime(self.expr),
                      processed_other)
            # NOT YET IMPLEMENTED: dialects other than MySQL, and how to
            # detect the dialect at this point.


class TestIso(Base):
    __tablename__ = 'test_iso_datetime'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    plain_datetime = Column(DateTime)
    when_created = Column(DateTimeAsIsoText)
    when_deleted = Column(DateTimeAsIsoText)

    def __repr__(self):
        return (
            "<TestIso(id={}, name={}, "
            "plain_datetime={}, when_created={}, when_deleted={})>".format(
                self.id, self.name,
                repr(self.plain_datetime),
                repr(self.when_created), repr(self.when_deleted),
                self.q1)
        )


# =============================================================================
# CamCOPS task structure, and field definition
# =============================================================================

class Task():
    # don't inherit from Base, because we don't want to define an actual table
    # for Task. It merely serves to include common fields and functions - but
    # that works OK.

    def create_view(self):
        print("CREATE VIEW {}_current AS SELECT * FROM {} WHERE blah".format(
            self.__tablename__,
            self.__tablename__,
        ))


# =============================================================================
# Main, with unit testing
# =============================================================================

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    engine = engine_mysql_commandline(echo=False)
    conn = engine.connect()

    Session = sessionmaker()
    Session.configure(bind=engine)  # once engine is available
    session = Session()

    # Create tables
    Base.metadata.create_all(engine)

    # -------------------------------------------------------------------------
    # Unit testing for DateTimeAsIsoText
    # -------------------------------------------------------------------------

    # Insert things
    t0 = dateutil.parser.parse("2013-04-30T00:26:03.000+05:00")  # prev. month

    t1 = dateutil.parser.parse("2013-05-30T03:26:00.000+01:00")  # Sweden
    t2 = dateutil.parser.parse("2013-05-30T03:00:00.000+00:00")  # London
    t3 = dateutil.parser.parse("2013-05-30T01:00:00.000-05:00")  # New York
    # t1 -> t3 decrease lexically, but increase temporally

    t2b = dateutil.parser.parse("2013-05-30T04:00:00.000+01:00")  # equals t2

    session.query(TestIso).delete()
    alice = TestIso(id=1, name="alice",
                    when_created=t1, when_deleted=t2,
                    plain_datetime=python_datetime_to_utc(t3))
    session.add(alice)
    bob = TestIso(id=2, name="bob",
                  when_created=t2, when_deleted=t3,
                  plain_datetime=python_datetime_to_utc(t0))
    session.add(bob)
    celia = TestIso(id=3, name="celia",
                    when_created=t3, when_deleted=t2,
                    plain_datetime=python_datetime_to_utc(t1))
    session.add(celia)
    david = TestIso(id=4, name="david",
                    when_created=t3, when_deleted=t3,
                    plain_datetime=python_datetime_to_utc(t1))
    session.add(david)
    edgar = TestIso(id=5, name="edgar",
                    when_created=t2b, when_deleted=t2,
                    plain_datetime=python_datetime_to_utc(t2b))
    session.add(edgar)
    session.commit()

    heading("DateTimeAsIsoText test: DateTimeAsIsoText field VERSUS literal")
    q = session.query(TestIso).filter(TestIso.when_created < t2)
    assert q.all() == [alice]
    q = session.query(TestIso).filter(TestIso.when_created == t2)
    assert q.all() == [bob, edgar]
    q = session.query(TestIso).filter(TestIso.when_created > t2)
    assert q.all() == [celia, david]

    heading("DateTimeAsIsoText test: literal VERSUS DateTimeAsIsoText field")
    q = session.query(TestIso).filter(t2 > TestIso.when_created)
    assert q.all() == [alice]
    q = session.query(TestIso).filter(t2 == TestIso.when_created)
    assert q.all() == [bob, edgar]
    q = session.query(TestIso).filter(t2 < TestIso.when_created)
    assert q.all() == [celia, david]

    heading("DateTimeAsIsoText test: DateTimeAsIsoText field VERSUS "
            "DateTimeAsIsoText field")
    q = session.query(TestIso).filter(TestIso.when_created <
                                      TestIso.when_deleted)
    assert q.all() == [alice, bob]
    q = session.query(TestIso).filter(TestIso.when_created ==
                                      TestIso.when_deleted)
    assert q.all() == [david, edgar]
    q = session.query(TestIso).filter(TestIso.when_created >
                                      TestIso.when_deleted)
    assert q.all() == [celia]

    heading("DateTimeAsIsoText test: DateTimeAsIsoText field VERSUS "
            "plain DATETIME field")
    q = session.query(TestIso).filter(TestIso.when_created <
                                      TestIso.plain_datetime)
    assert q.all() == [alice]
    q = session.query(TestIso).filter(TestIso.when_created ==
                                      TestIso.plain_datetime)
    # CAUTION: don't have any non-zero millisecond components; they'll get
    # stripped from the plain DATETIME and exact comparisons will then fail.
    assert q.all() == [edgar]
    q = session.query(TestIso).filter(TestIso.when_created >
                                      TestIso.plain_datetime)
    assert q.all() == [bob, celia, david]

    heading("DateTimeAsIsoText test: SELECT everything")
    q = session.query(TestIso)
    assert q.all() == [alice, bob, celia, david, edgar]
