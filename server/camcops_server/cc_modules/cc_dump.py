#!/usr/bin/env python
# camcops_server/cc_modules/cc_dump.py

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
from .cc_device import Device
from .cc_group import Group
from .cc_jointables import user_group_table, group_group_table
from .cc_request import CamcopsRequest
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
DUMP_DROP_COLNAMES = {
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
    user_group_table.name,
]
DUMP_SKIP_ALL_RELS_FOR_TABLES = [
    Group.__tablename__
]
FOREIGN_KEY_CONSTRAINTS_IN_DUMP = False


# =============================================================================
# Ancillary functions
# =============================================================================

def _dump_skip_table(tablename: str, include_blobs: bool) -> bool:
    if not include_blobs and tablename == Blob.__tablename__:
        return True
    if tablename in DUMP_SKIP_TABLES:
        return True
    return False


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


def _add_dump_table(dst_tables: Dict[str, Table],  # modified
                    dst_metadata: MetaData,  # modified
                    src_table: Table,
                    src_obj: object,
                    dst_session: SqlASession,
                    dst_engine: Engine,
                    include_blobs: bool,
                    req: CamcopsRequest) -> None:
    tablename = src_table.name
    # Skip the table?
    if _dump_skip_table(tablename, include_blobs):
        return
    # Copy columns, dropping any we don't want, and dropping FK constraints
    dst_columns = []  # type: List[Column]
    for src_column in src_table.columns:
        # log.critical("trying {!r}", src_column.name)
        if _dump_skip_column(tablename, src_column.name):
            # log.critical("... skipping {!r}", src_column.name)
            continue
        # You can't add the source column directly; you get
        # "sqlalchemy.exc.ArgumentError: Column object 'ccc' already assigned
        # to Table 'ttt'"
        copied_column = src_column.copy()
        copied_column.comment = src_column.comment
        # ... see SQLAlchemy trivial bug:
        # https://bitbucket.org/zzzeek/sqlalchemy/issues/4087/columncopy-doesnt-copy-comment-attribute  # noqa
        if FOREIGN_KEY_CONSTRAINTS_IN_DUMP:
            copied_column.foreign_keys = set(
                fk.copy() for fk in src_column.foreign_keys
            )
            log.warning("NOT WORKING: foreign key commands not being emitted")
            # but http://docs.sqlalchemy.org/en/latest/core/constraints.html
            # works fine under SQLite, even if the other table hasn't been
            # created yet. Does the table to which the FK refer have to be
            # in the metadata already?
            # That's quite possible, but I've not checked.
            # Would need to iterate through tables in dependency order, like
            # merge_db() does.
        else:
            # Probably blank already, as the copy() command only copies non-
            # constraint-bound ForeignKey objects, but to be sure:
            copied_column.foreign_keys = set()  # type: Set[ForeignKey]
        # if src_column.foreign_keys:
        #     log.critical("Column {}, FKs {!r} -> {!r}", src_column.name,
        #                  src_column.foreign_keys, copied_column.foreign_keys)
        dst_columns.append(copied_column)
    # Add extra columns?
    if isinstance(src_obj, Task):
        for summary_element in src_obj.get_summaries(req):
            dst_columns.append(Column(summary_element.name,
                                      summary_element.coltype))
    # Create the table
    # log.critical("Adding table {!r} to dump output", tablename)
    dst_table = Table(tablename, dst_metadata, *dst_columns)
    dst_tables[tablename] = dst_table
    # You have to use an engine, not a session, to create tables (or you get
    # "AttributeError: 'Session' object has no attribute '_run_visitor'").
    # However, you have to commit the session, or you get
    #     "sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database
    #     is locked", since a session is also being used.
    dst_session.commit()
    # log.critical("{!r}", dst_table)
    dst_table.create(dst_engine)


def _copy_object_to_dump(dst_table: Table,
                         dst_session: SqlASession,
                         src_obj: object,
                         req: CamcopsRequest) -> None:
    tablename = dst_table.name
    row = {}  # type: Dict[str, Any]
    # Copy columns, skipping any we don't want
    for attrname, column in gen_columns(src_obj):
        if _dump_skip_column(tablename, column.name):
            continue
        row[column.name] = getattr(src_obj, attrname)
    # Any other columns to add?
    if isinstance(src_obj, Task):
        for summary_element in src_obj.get_summaries(req):
            row[summary_element.name] = summary_element.value
    dst_session.execute(dst_table.insert(row))


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

    # We start with blank metadata.
    dst_metadata = MetaData()
    # Tables we are inserting into the destination database:
    dst_tables = {}  # type: Dict[str, Table]
    # Tables we've processed, though we may ignore them:
    tablenames_seen = set()  # type: Set[str]
    # ORM objects we've visited:
    instances_seen = set()  # type: Set[object]

    # We walk through all the objects.
    for startobj in tasks:
        for src_obj in walk_orm_tree(
                startobj,
                seen=instances_seen,
                skip_relationships_always=DUMP_SKIP_RELNAMES,
                skip_all_relationships_for_tablenames=DUMP_SKIP_ALL_RELS_FOR_TABLES,  # noqa
                skip_all_objects_for_tablenames=DUMP_SKIP_TABLES):
            # If we encounter a table we've not seen, offer our "table decider"
            # the opportunity to add it to the metadata and create the table.

            # noinspection PyUnresolvedReferences
            src_table = src_obj.__table__  # type: Table
            tablename = src_table.name
            if tablename not in tablenames_seen:
                _add_dump_table(dst_tables=dst_tables,
                                dst_metadata=dst_metadata,
                                src_table=src_table,
                                src_obj=src_obj,
                                dst_session=dst_session,
                                dst_engine=dst_engine,
                                include_blobs=include_blobs,
                                req=req)
                tablenames_seen.add(tablename)

            # If this table is going into the destination, copy the object
            # (and maybe remove columns from it, or add columns to it).
            if tablename in dst_tables:
                _copy_object_to_dump(dst_table=dst_tables[tablename],
                                     dst_session=dst_session,
                                     src_obj=src_obj,
                                     req=req)
