"""
camcops_server/cc_modules/cc_dump.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Methods for providing a dump of data from the server to the web user.**

"""

import logging
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TYPE_CHECKING,
)

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.orm_inspect import (
    gen_columns,
    gen_orm_classes_from_base,
    walk_orm_tree,
)
from sqlalchemy import insert, Integer
from sqlalchemy.exc import CompileError
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session as SqlASession
from sqlalchemy.sql.schema import Column, MetaData, Table

from camcops_server.cc_modules.cc_blob import Blob
from camcops_server.cc_modules.cc_db import (
    GenericTabletRecordMixin,
    TaskDescendant,
)
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_email import Email
from camcops_server.cc_modules.cc_exportmodels import (
    ExportedTask,
    ExportedTaskEmail,
    ExportedTaskFileGroup,
    ExportedTaskHL7Message,
)
from camcops_server.cc_modules.cc_exportrecipient import ExportRecipient
from camcops_server.cc_modules.cc_group import Group, group_group_table
from camcops_server.cc_modules.cc_membership import UserGroupMembership
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import (
    all_extra_id_columns,
    PatientIdNum,
)
from camcops_server.cc_modules.cc_sqla_coltypes import camcops_column
from camcops_server.cc_modules.cc_task import Task
from camcops_server.cc_modules.cc_user import User

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_summaryelement import ExtraSummaryTable
    from camcops_server.cc_modules.cc_simpleobjects import TaskExportOptions

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# Constants
# =============================================================================

# Restrict specified tables to certain columns only:
DUMP_ONLY_COLNAMES = {  # mapping of tablename : list_of_column_names
    Device.__tablename__: ["camcops_version", "friendly_name", "id", "name"],
    User.__tablename__: ["fullname", "id", "username"],
}
# Drop specific columns from certain tables:
# mapping of tablename : list_of_column_names
DUMP_DROP_COLNAMES: dict[str, list[str]] = {}
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
    # We don't have to list all admin tables here; we process the dump starting
    # with tasks, so only things that have ORM relationships to a task might
    # feature. (The Email/ExportedTask* set don't, so this is just caution in
    # case we add a relationship later!)
    Email.__tablename__,
    ExportedTask.__tablename__,
    ExportedTaskEmail.__tablename__,
    ExportedTaskFileGroup.__tablename__,
    ExportedTaskHL7Message.__tablename__,
    ExportRecipient.__tablename__,
    group_group_table.name,
    UserGroupMembership.__tablename__,
]
# Tables for which no relationships will be traversed:
DUMP_SKIP_ALL_RELS_FOR_TABLES = [Group.__tablename__]
FOREIGN_KEY_CONSTRAINTS_IN_DUMP = False
# ... the keys will be present, but should we try to enforce constraints?


# =============================================================================
# Handy place to hold the controlling information
# =============================================================================


class DumpController(object):
    """
    A controller class that manages the copying (dumping) of information from
    our database to another SQLAlchemy :class:`Engine`/:class:`Session`.
    """

    def __init__(
        self,
        dst_engine: Engine,
        dst_session: SqlASession,
        export_options: "TaskExportOptions",
        req: "CamcopsRequest",
    ) -> None:
        """
        Args:
            dst_engine: destination SQLAlchemy Engine
            dst_session:  destination SQLAlchemy Session
            export_options: :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`
            req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """  # noqa
        self.dst_engine = dst_engine
        self.dst_session = dst_session
        self.export_options = export_options
        self.req = req

        # We start with blank metadata.
        self.dst_metadata = MetaData()
        # Tables we are inserting into the destination database:
        self.dst_tables = {}  # type: Dict[str, Table]
        # ... note that creating a Table() for a given SQLAlchemy metadata is
        #     permitted only once, so we add to self.dst_tables as soon
        #     as we create that.
        # Tables we've created:
        self.tablenames_created = set()  # type: Set[str]
        # Tables we've processed, though we may ignore them:
        self.tablenames_seen = set()  # type: Set[str]
        # ORM objects we've visited:
        self.instances_seen = set()  # type: Set[object]

        if export_options.db_make_all_tables_even_empty:
            self._create_all_dest_tables()

    def _create_all_dest_tables(self) -> None:
        """
        Creates all tables in the destination database, even ones that may
        not be used.
        """
        log.debug("Creating all destination tables...")
        for table in self.gen_all_dest_tables():
            self._create_dest_table(table)
        log.debug("... all destination tables created.")

    def gen_all_dest_tables(self) -> Generator[Table, None, None]:
        """
        Generates all destination tables.
        """
        tablenames_seen = set()  # type: Set[str]
        for cls in gen_orm_classes_from_base(
            GenericTabletRecordMixin
        ):  # type: Type[GenericTabletRecordMixin]
            instance = cls()
            for table in self.gen_all_dest_tables_for_obj(instance):
                if table.name in tablenames_seen:
                    continue
                tablenames_seen.add(table.name)
                yield table

    def gen_all_dest_tables_for_obj(
        self, src_obj: object
    ) -> Generator[Table, None, None]:
        """
        Generates all destination tables for an object.
        """
        # Main table
        yield self.get_dest_table_for_src_object(src_obj)
        # Additional tables
        if isinstance(src_obj, Task):
            add_extra_id_cols = (
                self.export_options.db_patient_id_in_each_row
                and not src_obj.is_anonymous
            )
            estables = src_obj.get_all_summary_tables(self.req)
            for est in estables:
                yield self.get_dest_table_for_est(
                    est, add_extra_id_cols=add_extra_id_cols
                )

    def gen_all_dest_columns(self) -> Generator[Column, None, None]:
        """
        Generates all destination columns.
        """
        for table in self.gen_all_dest_tables():
            if not self._dump_skip_table(table.name):
                for col in table.columns:
                    if col.name not in DUMP_SKIP_COLNAMES:
                        yield col

    def consider_object(self, src_obj: object) -> None:
        """
        Think about an SQLAlchemy ORM object. If it comes from a table we
        want dumped, add this object to the dump.
        """
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: ignore[attr-defined]
        src_tablename = src_table.name
        if src_tablename not in self.tablenames_seen:
            # If we encounter a table we've not seen, offer our "table decider"
            # the opportunity to add it to the metadata and create the table.
            self._add_dump_table_for_src_object(src_obj)
        # If this table is going into the destination, copy the object
        # (and maybe remove columns from it, or add columns to it).
        if src_tablename in self.dst_tables and not self._dump_skip_table(
            src_tablename
        ):
            self._copy_object_to_dump(src_obj)

    @staticmethod
    def _merits_extra_id_num_columns(
        obj: object,
    ) -> Tuple[bool, Optional[Patient]]:
        """
        Is the source object one that would support the addition of extra
        ID number information if the export option ``DB_PATIENT_ID_PER_ROW`` is
        set? If so, return the relevant patient.

        Args:
            obj: an SQLAlchemy ORM object

        Returns:
            tuple: ``(merits, patient)``, where ``merits`` is a ``bool`` (does
            it merit this?) and ``patient`` is a relevant
            :class:`camcops_server.cc_modules.cc_patient.Patient``, if found.
            It is also guaranteed that if a patient is returned, ``merits`` is
            ``True`` (but not guaranteed that if ``merits`` is true, that
            ``patient`` is not ``None``).

        """
        if not isinstance(obj, GenericTabletRecordMixin):
            # Must be data that originated from the client.
            return False, None
        if isinstance(obj, PatientIdNum):
            # PatientIdNum already has this info.
            return False, None
        if isinstance(obj, Patient):
            return True, obj
        if isinstance(obj, Task):
            if obj.is_anonymous:
                # Anonymous tasks don't.
                return False, None
            return True, obj.patient
        if isinstance(obj, TaskDescendant):
            merits = obj.task_ancestor_might_have_patient()
            patient = obj.task_ancestor_patient()
            return merits, patient
        log.warning(
            f"_merits_extra_id_num_columns_if_requested: don't know "
            f"how to handle {obj!r}"
        )
        return False, None

    def get_dest_table_for_src_object(self, src_obj: object) -> Table:
        """
        Produces the destination table for the source object.

        Args:
            src_obj:
                An SQLAlchemy ORM object. It will *not* be a
                :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`;
                those are handled instead by
                :meth:`_get_or_insert_summary_table`.

        Returns:
            an SQLAlchemy :class:`Table`
        """
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: ignore[attr-defined]
        tablename = src_table.name

        # Don't create it twice in the SQLAlchemy metadata.
        if tablename in self.dst_tables:
            return self.dst_tables[tablename]

        dst_table = src_table.to_metadata(self.dst_metadata)

        # Copy columns, dropping any we don't want, and dropping FK constraints
        changed_columns = []  # type: List[Column]

        for dst_column in dst_table.columns:
            if dst_column.foreign_keys:
                changed_columns.append(
                    # Trying to set index=dst_column.index here results in
                    # index ... already exists error when the table is created.
                    Column(
                        dst_column.name,
                        Integer,
                        nullable=dst_column.nullable,
                        comment=dst_column.comment,
                    )
                )
            elif self._dump_skip_column(tablename, dst_column.name):
                changed_columns.append(Column(dst_column.name, Integer))

        # Add extra columns?
        if self.export_options.db_include_summaries:
            if isinstance(src_obj, GenericTabletRecordMixin):
                for summary_element in src_obj.get_summaries(self.req):
                    changed_columns.append(
                        camcops_column(
                            summary_element.name,
                            summary_element.coltype,
                            exempt_from_anonymisation=True,
                            comment=summary_element.decorated_comment,
                        )
                    )
        if self.export_options.db_patient_id_in_each_row:
            merits, _ = self._merits_extra_id_num_columns(src_obj)
            if merits:
                changed_columns.extend(all_extra_id_columns(self.req))
            if isinstance(src_obj, TaskDescendant):
                changed_columns += src_obj.extra_task_xref_columns()

        dst_table = Table(
            tablename,
            self.dst_metadata,
            *changed_columns,
            extend_existing=True,
        )
        # ... that modifies the metadata, so:
        self.dst_tables[tablename] = dst_table
        return dst_table

    def get_dest_table_for_est(
        self, est: "ExtraSummaryTable", add_extra_id_cols: bool = False
    ) -> Table:
        """
        Add an additional summary table to the dump, if it's not there already.
        Return the table (from the destination database).

        Args:
            est:
                a
                :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`
            add_extra_id_cols:
                Add extra ID columns, for the ``DB_PATIENT_ID_PER_ROW``
                export option?
        """
        tablename = est.tablename
        if tablename in self.dst_tables:
            return self.dst_tables[tablename]

        columns = est.columns.copy()
        if add_extra_id_cols:
            columns.extend(all_extra_id_columns(self.req))
            columns.extend(est.extra_task_xref_columns())
        table = Table(tablename, self.dst_metadata, *columns)
        # ... that modifies the metadata, so:
        self.dst_tables[tablename] = table
        return table

    def _add_dump_table_for_src_object(self, src_obj: object) -> None:
        """
        - Mark the object's table as seen.

        - If we want it, add it to the metadata and execute a CREATE TABLE
          command.

        - We may translate the table en route.

        Args:
            src_obj:
                An SQLAlchemy ORM object. It will *not* be a
                :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`;
                those are handled instead by
                :meth:`_get_or_insert_summary_table`.
        """
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: ignore[attr-defined]
        tablename = src_table.name
        self.tablenames_seen.add(tablename)

        # Skip the table?
        if self._dump_skip_table(tablename):
            return

        # Get the table definition
        dst_table = self.get_dest_table_for_src_object(src_obj)
        # Create it
        self._create_dest_table(dst_table)

    def _create_dest_table(self, dst_table: Table) -> None:
        """
        Creates a table in the destination database.
        """
        tablename = dst_table.name
        if tablename in self.tablenames_created:
            return  # don't create it twice
        # Create the table
        # log.debug("Adding table {!r} to dump output", tablename)
        # You have to use an engine, not a session, to create tables (or you
        # get "AttributeError: 'Session' object has no attribute
        # '_run_visitor'").
        # However, you have to commit the session, or you get
        #     "sqlalchemy.exc.OperationalError: (sqlite3.OperationalError)
        #     database is locked", since a session is also being used.
        self.dst_session.commit()
        dst_table.create(self.dst_engine)
        self.tablenames_created.add(tablename)

    def _copy_object_to_dump(self, src_obj: object) -> None:
        """
        Copy the SQLAlchemy ORM object to the dump.
        """
        # noinspection PyUnresolvedReferences
        src_table = src_obj.__table__  # type: ignore[attr-defined]
        adding_extra_ids = False
        patient = None  # type: Optional[Patient]
        if self.export_options.db_patient_id_in_each_row:
            adding_extra_ids, patient = self._merits_extra_id_num_columns(
                src_obj
            )

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
            if self.export_options.db_include_summaries:
                for summary_element in src_obj.get_summaries(self.req):
                    row[summary_element.name] = summary_element.value
            if adding_extra_ids:
                if patient:
                    patient.add_extra_idnum_info_to_row(row)
                if isinstance(src_obj, TaskDescendant):
                    src_obj.add_extra_task_xref_info_to_row(row)
        try:
            self.dst_session.execute(insert(dst_table).values(row))
        except CompileError:
            log.critical("\ndst_table:\n{}\nrow:\n{}", dst_table, row)
            raise

        # 2. If required, add extra tables/rows that this task wants to
        #    offer (usually tables whose rows don't have a 1:1 correspondence
        #    to the task or its ancillary objects).
        if isinstance(src_obj, Task):
            estables = src_obj.get_all_summary_tables(self.req)
            # ... includes SNOMED
            for est in estables:
                dst_summary_table = self._get_or_insert_summary_table(
                    est, add_extra_id_cols=adding_extra_ids
                )
                for row in est.rows:
                    if patient:
                        patient.add_extra_idnum_info_to_row(row)
                    if adding_extra_ids:
                        est.add_extra_task_xref_info_to_row(row)
                    try:
                        self.dst_session.execute(
                            insert(dst_summary_table).values(row)
                        )
                    except CompileError:
                        log.critical(
                            "\ndst_summary_table:\n{}\nrow:\n{}",
                            dst_table,
                            row,
                        )
                        raise

    def _get_or_insert_summary_table(
        self, est: "ExtraSummaryTable", add_extra_id_cols: bool = False
    ) -> Table:
        """
        Add an additional summary table to the dump, if it's not there already.
        Return the table (from the destination database).

        Args:
            est:
                a
                :class:`camcops_server.cc_modules.cc_summaryelement.ExtraSummaryTable`
            add_extra_id_cols:
                Add extra ID columns, for the ``DB_PATIENT_ID_PER_ROW``
                export option?
        """
        tablename = est.tablename
        if tablename not in self.tablenames_created:
            table = self.get_dest_table_for_est(
                est, add_extra_id_cols=add_extra_id_cols
            )
            self._create_dest_table(table)
        return self.dst_tables[tablename]

    def _dump_skip_table(self, tablename: str) -> bool:
        """
        Should we skip this table (omit it from the dump)?
        """
        if (
            not self.export_options.include_blobs
            and tablename == Blob.__tablename__
        ):
            return True
        if tablename in DUMP_SKIP_TABLES:
            return True
        return False

    @staticmethod
    def _dump_skip_column(tablename: str, columnname: str) -> bool:
        """
        Should we skip this column (omit it from the dump)?
        """
        if columnname in DUMP_SKIP_COLNAMES:
            return True
        if (
            tablename in DUMP_ONLY_COLNAMES
            and columnname not in DUMP_ONLY_COLNAMES[tablename]
        ):
            return True
        if (
            tablename in DUMP_DROP_COLNAMES
            and columnname in DUMP_DROP_COLNAMES[tablename]
        ):
            return True
        return False


# =============================================================================
# Copying stuff to a dump
# =============================================================================


def copy_tasks_and_summaries(
    tasks: Iterable[Task],
    dst_engine: Engine,
    dst_session: SqlASession,
    export_options: "TaskExportOptions",
    req: "CamcopsRequest",
) -> None:
    """
    Copy a set of tasks, and their associated related information (found by
    walking the SQLAlchemy ORM tree), to the dump.

    Args:
        tasks: tasks to copy
        dst_engine: destination SQLAlchemy Engine
        dst_session:  destination SQLAlchemy Session
        export_options: :class:`camcops_server.cc_modules.cc_simpleobjects.TaskExportOptions`
        req: :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
    """  # noqa
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

    controller = DumpController(
        dst_engine=dst_engine,
        dst_session=dst_session,
        export_options=export_options,
        req=req,
    )

    # We walk through all the objects.
    log.debug("Starting to copy tasks...")
    for startobj in tasks:
        log.debug("Processing task: {!r}", startobj)
        for src_obj in walk_orm_tree(
            startobj,
            seen=controller.instances_seen,
            skip_relationships_always=DUMP_SKIP_RELNAMES,
            skip_all_relationships_for_tablenames=DUMP_SKIP_ALL_RELS_FOR_TABLES,  # noqa
            skip_all_objects_for_tablenames=DUMP_SKIP_TABLES,
        ):
            controller.consider_object(src_obj)
    log.debug("... finished copying tasks.")
