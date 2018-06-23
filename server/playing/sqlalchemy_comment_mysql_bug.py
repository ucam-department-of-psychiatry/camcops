#!/usr/bin/env python
# sqlalchemy_comment_mysql_bug.py

"""
-- In MySQL:

DROP DATABASE dummy;
CREATE DATABASE dummy;
GRANT ALL PRIVILEGES ON dummy.* TO 'scott'@'localhost' IDENTIFIED BY 'tiger';
"""

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Integer, UnicodeText

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    weight_loss = Column(Boolean, comment="Weight loss of 5% or more")
    test_unicode_text = Column(UnicodeText)


# url = "mysql+mysqldb://scott:tiger@127.0.0.1:3306/dummy?charset=utf8"
url = "mysql+mysqldb://scott:tiger@127.0.0.1:3306/dummy"
engine = create_engine(url, echo=True)
Base.metadata.create_all(engine)
