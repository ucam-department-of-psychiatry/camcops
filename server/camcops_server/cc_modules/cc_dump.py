#!/usr/bin/env python
# camcops_server/cc_modules/cc_dump.py

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
from typing import Any, Dict, Iterable, List, Set

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_inspect import (
    gen_columns,
    walk_orm_tree,
)
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column, ForeignKey, MetaData, Table

from .cc_blob import Blob
from .cc_db import GenericTabletRecordMixin
from .cc_device import Device
from .cc_group import Group, group_group_table
from .cc_membership import UserGroupMembership
from .cc_request import CamcopsRequest
from .cc_summaryelement import ExtraSummaryTable
from .cc_task import Task
from .cc_user import User

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

# Restrict specified tables to certain columns only:
DUMP_ONLY_COLNAMES = {  # mapping of tablename : list_of_column_names
    Device.__tablename__: [
        "camcops_version",
        "friendly_name",
        "id",
        "name",
    ],
    User.__tablename__: [
        "fullname",
        "id",
        "username",
    ]
}
# Drop specific columns from certain tables:
DUMP_DROP_COLNAMES = {  # mapping of tablename : list_of_column_names
}
# List of columns to be skipped regardless of table:
DUMP_SKIP_COLNAMES = [
    # We restrict to current records only, so many of these are irrelevant:
    "_addition_pending",
    "_forcibly_preserved",
    "_manually_erased",
    "_manually_erased_at",
    "_manually_erasing_user_id",
    "_move_off_tablet",
    "_removal_pending",
    "_removing_user_id",
    "_successor_pk",
    "_when_removed_batch_utc",
    "_when_removed_exact",
]
DUMP_SKIP_RELNAMES = [
    # List of *relationship* names to ignore
    "_manually_erasing_user",
    "_removing_user",
]
# List of table names to be skipped at all times:
DUMP_SKIP_TABLES = [
    group_group_table.name,
    UserGroupMembership.__tablename__,
]
# Tables for which no relationships will be traversed:
DUMP_SKIP_ALL_RELS_FOR_TABLES = [
    Group.__tablename__
]
FOREIGN_KEY_CONSTRAINTS_IN_DUMP = False


# =============================================================================
# Handy place to hold the controlling information
# =============================================================================

class DumpController(object):
    def __init__(self,
                 dst_engine: Engine,
                 dst_session: SqlASession,
                 include_blobs: bool,
                 req: CamcopsRequest) -> None:
        self.dst_engine = dst_engine
        self.dst_session = dst_session
        self.include_blobs = include_blobs
        self.req = req

        # We start with blank metadata.
        self.dst_metadata = MetaData()
        # Tables we are inserting into the destination database:
        self.dst_tables = {}  # type: Dict[str, Table]
        # Tables we've processed, though we may ignore them:
        self.tablenames_seen = set()  # type: Set[str]
        # ORM objects we've visited:
        self.instances_seen = set()  # type: Set[object]

    def consider_object(self, src_obj: object) -> None:
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: Table
        src_tablename = src_table.name
        if src_tablename not in self.tablenames_seen:
            # If we encounter a table we've not seen, offer our "table decider"
            # the opportunity to add it to the metadata and create the table.
            self._add_dump_table_for_src_object(src_obj)
        # If this table is going into the destination, copy the object
        # (and maybe remove columns from it, or add columns to it).
        if src_tablename in self.dst_tables:
            self._copy_object_to_dump(src_obj)

    def _add_dump_table_for_src_object(self, src_obj: object) -> None:
        """

        - Mark the object's table as seen.

        - If we want it, add it to the metadata and execute a CREATE TABLE
          command.

        - We may translate the table en route.

        """
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: Table
        tablename = src_table.name
        self.tablenames_seen.add(tablename)

        # Skip the table?
        if self._dump_skip_table(tablename):
            return
        # Copy columns, dropping any we don't want, and dropping FK constraints
        dst_columns = []  # type: List[Column]
        for src_column in src_table.columns:
            # log.critical("trying {!r}", src_column.name)
            if self._dump_skip_column(tablename, src_column.name):
                # log.critical("... skipping {!r}", src_column.name)
                continue
            # You can't add the source column directly; you get
            # "sqlalchemy.exc.ArgumentError: Column object 'ccc' already
            # assigned to Table 'ttt'"
            copied_column = src_column.copy()
            copied_column.comment = src_column.comment
            # ... see SQLAlchemy trivial bug:
            # https://bitbucket.org/zzzeek/sqlalchemy/issues/4087/columncopy-doesnt-copy-comment-attribute  # noqa
            if FOREIGN_KEY_CONSTRAINTS_IN_DUMP:
                copied_column.foreign_keys = set(
                    fk.copy() for fk in src_column.foreign_keys
                )
                log.warning("NOT WORKING: foreign key commands not being "
                            "emitted")
                # but http://docs.sqlalchemy.org/en/latest/core/constraints.html  # noqa
                # works fine under SQLite, even if the other table hasn't been
                # created yet. Does the table to which the FK refer have to be
                # in the metadata already?
                # That's quite possible, but I've not checked.
                # Would need to iterate through tables in dependency order,
                # like merge_db() does.
            else:
                # Probably blank already, as the copy() command only copies
                # non-constraint-bound ForeignKey objects, but to be sure:
                copied_column.foreign_keys = set()  # type: Set[ForeignKey]
            # if src_column.foreign_keys:
            #     log.critical("Column {}, FKs {!r} -> {!r}", src_column.name,
            #                  src_column.foreign_keys,
            #                  copied_column.foreign_keys)
            dst_columns.append(copied_column)
        # Add extra columns?
        if isinstance(src_obj, GenericTabletRecordMixin):
            for summary_element in src_obj.get_summaries(self.req):
                dst_columns.append(Column(summary_element.name,
                                          summary_element.coltype,
                                          comment=summary_element.comment))
        # Create the table
        # log.critical("Adding table {!r} to dump output", tablename)
        dst_table = Table(tablename, self.dst_metadata, *dst_columns)
        self.dst_tables[tablename] = dst_table
        # You have to use an engine, not a session, to create tables (or you
        # get "AttributeError: 'Session' object has no attribute
        # '_run_visitor'").
        # However, you have to commit the session, or you get
        #     "sqlalchemy.exc.OperationalError: (sqlite3.OperationalError)
        #     database is locked", since a session is also being used.
        self.dst_session.commit()
        # log.critical("{!r}", dst_table)
        dst_table.create(self.dst_engine)

    def _copy_object_to_dump(self, src_obj: object) -> None:
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: Table

        # 1. Insert row for this object, potentially adding and removing
        #    columns.
        tablename = src_table.name
        dst_table = self.dst_tables[tablename]
        assert dst_table.name == tablename
        row = {}  # type: Dict[str, Any]
        # Copy columns, skipping any we don't want
        for attrname, column in gen_columns(src_obj):
            if self._dump_skip_column(tablename, column.name):
                continue
            row[column.name] = getattr(src_obj, attrname)
        # Any other columns to add for this table?
        if isinstance(src_obj, GenericTabletRecordMixin):
            for summary_element in src_obj.get_summaries(self.req):
                row[summary_element.name] = summary_element.value
        self.dst_session.execute(dst_table.insert(row))

        # 2. If required, add extra tables/rows that this task wants to
        #    offer (usually tables whose rows don't have a 1:1 correspondence
        #    to the task or its ancillary objects).
        if isinstance(src_obj, Task):
            estables = src_obj.get_extra_summary_tables(self.req)
            for est in estables:
                dst_summary_table = self._get_or_insert_summary_table(est)
                for row in est.rows:
                    self.dst_session.execute(dst_summary_table.insert(row))

    def _get_or_insert_summary_table(self, est: ExtraSummaryTable) -> Table:
        tablename = est.tablename
        if tablename not in self.tablenames_seen:
            self.tablenames_seen.add(tablename)
            table = Table(tablename, self.dst_metadata, *est.columns)
            self.dst_tables[tablename] = table
            self.dst_session.commit()
            table.create(self.dst_engine)
        return self.dst_tables[tablename]

    def _dump_skip_table(self, tablename: str) -> bool:
        if not self.include_blobs and tablename == Blob.__tablename__:
            return True
        if tablename in DUMP_SKIP_TABLES:
            return True
        return False

    @staticmethod
    def _dump_skip_column(tablename: str, columnname: str) -> bool:
        if columnname in DUMP_SKIP_COLNAMES:
            return True
        if (tablename in DUMP_ONLY_COLNAMES and
                columnname not in DUMP_ONLY_COLNAMES[tablename]):
            return True
        if (tablename in DUMP_DROP_COLNAMES and
                columnname in DUMP_DROP_COLNAMES[tablename]):
            return True
        return False


# =============================================================================
# Copying stuff to a dump
# =============================================================================

def copy_tasks_and_summaries(tasks: Iterable[Task],
                             dst_engine: Engine,
                             dst_session: SqlASession,
                             include_blobs: bool,
                             req: CamcopsRequest) -> None:
    # How best to create the structure that's required?
    #
    # https://stackoverflow.com/questions/21770829/sqlalchemy-copy-schema-and-data-of-subquery-to-another-database  # noqa
    # https://stackoverflow.com/questions/40155340/sqlalchemy-reflect-and-copy-only-subset-of-existing-schema  # noqa
    #
    # - Should we attempt to copy the MetaData object? That seems extremely
    #   laborious, since every ORM class is tied to it. Moreover,
    #   MetaData.tables is an immutabledict, so we're not going to be editing
    #   anything. Even if we cloned the MetaData, that's not going to give us
    #   ORM classes to walk.
    # - Shall we operate at a lower level? That seems sensible.
    # - Given that... we don't need to translate the PKs at all, unlike
    #   merge_db.
    # - Let's not create FK constraints explicitly. Most are not achievable
    #   anyway (e.g. linking on device/era; omission of BLOBs).

    controller = DumpController(dst_engine=dst_engine,
                                dst_session=dst_session,
                                include_blobs=include_blobs,
                                req=req)

    # We walk through all the objects.
    for startobj in tasks:
        for src_obj in walk_orm_tree(
                startobj,
                seen=controller.instances_seen,
                skip_relationships_always=DUMP_SKIP_RELNAMES,
                skip_all_relationships_for_tablenames=DUMP_SKIP_ALL_RELS_FOR_TABLES,  # noqa
                skip_all_objects_for_tablenames=DUMP_SKIP_TABLES):
            controller.consider_object(src_obj)
