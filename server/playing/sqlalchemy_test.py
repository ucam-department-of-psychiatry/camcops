#!/usr/bin/python

"""

Things to achieve before a switch to SQL Alchemy is viable:

- Proper processing of dates in our text-based ISO-8601 format.

- Ability to specify fieldspecs (etc.) in a table class, with CamCOPS extras
  like permitted values and comments, and then have them be mapped, via
  SQLA's mapper() function, to objects.

  See

    http://stackoverflow.com/questions/5424942/sqlalchemy-model-definition-at-execution
    http://stackoverflow.com/questions/4678115/how-to-dynamically-create-sqlalchemy-columns

"""  # noqa

import dateutil.parser
import sqlalchemy  # sudo apt-get install python-sqlalchemy
import sqlalchemy.types
from sqlalchemy import (
    Column,
    # ForeignKey,
    Integer,
    MetaData,
    Sequence,
    # String,
    Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import Comparator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func
import sys
sys.path.append('/srv/www/pythonlib')
import pythonlib.rnc_ui as rnc_ui

Base = declarative_base()


def engine_mysql(user, password, host, port, database):
    CONNECTSTRING = "mysql://{}:{}@{}:{}/{}?charset=utf8&use_unicode=0".format(
        user,
        password,
        host,
        port,
        database
    )
    return sqlalchemy.create_engine(CONNECTSTRING, echo=True)


def engine_mysql_commandline():
    host = rnc_ui.ask_user("Host", "localhost")
    port = 3306
    database = rnc_ui.ask_user("Database", "camcops")
    user = rnc_ui.ask_user("User", "root")
    password = rnc_ui.ask_user_password("Password")
    return engine_mysql(user, password, host, port, database)


engine = engine_mysql_commandline()
conn = engine.connect()
metadata = MetaData()

Session = sessionmaker()
Session.configure(bind=engine)  # once engine is available
session = Session()

# Define a table
junktable = Table(
    'junk',
    metadata,
    Column('_pk', Integer, Sequence('_pk_seq'), primary_key=True),
    Column('q1', Integer)
)
# Create tables
metadata.create_all(engine)


class DateTimeAsIsoTextComparator(Comparator):
    # cf. """
    #   CONVERT_TZ(
    #       STR_TO_DATE(
    #           LEFT({0}, 23),
    #           '%Y-%m-%dT%H:%i:%s.%f'),
    #       RIGHT({0},6), "+00:00")
    # """.format(fieldname)
    def operate(self, op, other):
        return op(
            func.convert_tz(
                func.str_to_date(
                    func.left(self.__clause_element__(), 23),
                    '%Y-%m-%dT%H:%i:%s.%f'
                ),
                func.right(self.__clause_element__(), 6),
                "+00:00"
            ),
            func.convert_tz(
                func.str_to_date(
                    func.left(other, 23),
                    '%Y-%m-%dT%H:%i:%s.%f'
                ),
                func.right(other, 6),
                "+00:00"
            ),
        )


# Date-conversion type
class DateTimeAsIsoText(sqlalchemy.types.TypeDecorator):
    '''Stores date/time values as ISO-8601.
    '''

    impl = sqlalchemy.types.Text  # underlying SQL type

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.strftime("%Y-%m-%dT%H:%M:%S%z")

    def process_result_value(self, value, dialect):
        print "VALUE: " + str(value)  # ***
        if not value:
            return None
        return dateutil.parser.parse(value)


class DateTimeAsIsoText2(sqlalchemy.types.UserDefinedType):
    '''Stores date/time values as ISO-8601. Needs SQLAlchemy 0.8.
    '''
    print "CLASSCREATION"

    def get_col_spec(self):
        print "GET_COL_SPEC"
        return "TEXT"

    def bind_expression(self, bindvalue):
        # applies specialfunc to create e.g. "WHERE mycol > specialfunc(%s)"
        print "BIND_EXPRESSION"
        return func.upper(bindvalue, type_=self)

    def column_expression(self, col):
        # applies specialfunc to create e.g.
        # "SELECT specialfunc(mycol) AS mycol"
        print "COLUMN_EXPRESSION"
        return func.lower(col, type_=self)


class Task():
    # don't inherit from Base, because we don't want to define an actual table
    # for Task. It merely serves to include common fields and functions - but
    # that works OK.
    _pk = Column('_pk', Integer, Sequence('_pk_seq'), primary_key=True)
    when_created = Column('when_created', DateTimeAsIsoText)

    def create_view(self):
        print "CREATE VIEW {}_current AS SELECT * FROM {} WHERE blah".format(
            self.__tablename__,
            self.__tablename__,
        )


class Phq9(Task, Base):
    __tablename__ = 'phq9'
    q1 = Column('q1', Integer)

    def report(self):
        print "_pk = {}, q1 = {}".format(self._pk, self.q1)
        print self.when_created.strftime("%d %B %Y, %H:%M:%S %z")


# Simple query, with restriction
phq9table = Table(
    'phq9',
    metadata,
    Column('_pk', Integer, Sequence('_pk_seq'), primary_key=True),
    Column('when_created', DateTimeAsIsoText),
    Column('q1', Integer)
)
enddate = dateutil.parser.parse("2013-04-30T00:26:03.400+05:00")
s = select([phq9table]).where(phq9table.c.when_created > enddate)
# ... does LEXICAL comparison, so the timezone bit will be ignored
result = conn.execute(s)
for row in result:
    print row

for p in session.query(Phq9):
    p.report()
    print p.create_view()
