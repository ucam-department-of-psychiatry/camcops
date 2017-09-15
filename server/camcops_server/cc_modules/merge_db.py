#!/usr/bin/env python
# camcops_server/tools/merge_db.py

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
from pprint import pformat
from typing import List, Optional, Type, TYPE_CHECKING

from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.sqlalchemy.merge_db import merge_db, TranslationContext
from cardinal_pythonlib.sqlalchemy.orm_schema import (
    create_table_from_orm_class,
)
from cardinal_pythonlib.sqlalchemy.orm_query import exists_orm
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_engine
from cardinal_pythonlib.sqlalchemy.table_identity import TableIdentity
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import column, func, select, table, text
from camcops_server.cc_modules.cc_audit import AuditEntry
from camcops_server.cc_modules.cc_constants import (
    FP_ID_NUM_DEFUNCT,
    NUMBER_OF_IDNUMS_DEFUNCT,
)
from camcops_server.cc_modules.cc_db import GenericTabletRecordMixin
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_group import Group
from camcops_server.cc_modules.cc_hl7 import HL7Message, HL7Run
from camcops_server.cc_modules.cc_jointables import user_group_table, group_group_table
from camcops_server.cc_modules.cc_patient import Patient
from camcops_server.cc_modules.cc_patientidnum import (
    fake_tablet_id_for_patientidnum,
    PatientIdNum,
)
from camcops_server.cc_modules.cc_request import command_line_request
from camcops_server.cc_modules.cc_session import CamcopsSession
from camcops_server.cc_modules.cc_storedvar import ServerStoredVar
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_user import (
    SecurityAccountLockout,
    SecurityLoginFailure,
    User,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import ResultProxy

log = BraceStyleAdapter(logging.getLogger(__name__))

DEBUG_VIA_PDB = False


# =============================================================================
# Preprocess
# =============================================================================

def preprocess(src_engine: Engine) -> List[TableIdentity]:
    skip_tables = []  # type: List[TableIdentity]

    src_tables = get_table_names(src_engine)

    # Check we have some core tables present in the sources

    for tname in [Patient.__tablename__, User.__tablename__]:
        if tname not in src_tables:
            raise ValueError(
                "Cannot proceed; table {!r} missing from source; unlikely "
                "that the source is any sort of old CamCOPS database!".format(
                    tname))

    # In general, we allow missing source tables.
    # However, we can't allow source tables to be missing if they are
    # automatically eager-loaded by relationships. This is only true in
    # CamCOPS for some high-performance queries: Patient, User,
    # PatientIdNum. In the context of merges we're going to run, that means
    # PatientIdNum.

    if False:  # SKIP -- disable eager loading instead
        # Create patient ID number table, because it's eager-loaded
        if PatientIdNum.__tablename__ not in src_tables:
            create_table_from_orm_class(engine=src_engine,
                                        ormclass=PatientIdNum,
                                        without_constraints=True)

    if Group.__tablename__ not in src_tables:
        log.warning("No Group information in source database; skipping source "
                    "table {!r}; will create a default group",
                    Group.__tablename__)
        skip_tables.append(TableIdentity(tablename=Group.__tablename__))

    return skip_tables


# =============================================================================
# Extra translation to be applied to individual objects
# =============================================================================
# The extra logic for this database:

def flush_session(dst_session: Session) -> None:
    log.debug("Flushing session")
    dst_session.flush()


def group_exists(group_id: int, dst_session: Session) -> bool:
    return exists_orm(dst_session, Group, Group.id == group_id)


def fetch_group_id_by_name(group_name: str, dst_session: Session) -> int:
    try:
        group = dst_session.query(Group)\
            .filter(Group.name == group_name)\
            .one()  # type: Group
        # ... will fail if there are 0 or >1 results
    except MultipleResultsFound:
        log.critical("Nasty bug: can't have two groups with the same name! "
                     "Group name was {!r}", group_name)
        raise
    except NoResultFound:
        log.warning("Creating new group named {!r}", group_name)
        group = Group()
        group.name = group_name
        dst_session.add(group)
        flush_session(dst_session)  # creates the PK
        # https://stackoverflow.com/questions/1316952/sqlalchemy-flush-and-get-inserted-id  # noqa
        log.warning("... new group has ID {!r}", group.id)
    return group.id


def ensure_default_group_id(trcon: TranslationContext) -> None:
    default_group_id = trcon.info["default_group_id"]
    if default_group_id is not None:
        # The user specified a group ID to use for records without one
        assert group_exists(group_id=default_group_id,
                            dst_session=trcon.dst_session), (
            "User specified default_group_id={!r}, and object {!r} needs "
            "a _group_id (directly or indirectly), but that ID doesn't exist "
            "in the {!r} table of the destination database".format(
                default_group_id, trcon.oldobj, Group.__tablename__)
        )
    else:
        default_group_name = trcon.info["default_group_name"]
        if not default_group_name:
            assert False, (
                "User specified neither default_group_id or "
                "default_group_name, but object {!r} needs a "
                "_group_id, directly or indirectly".format(trcon.oldobj)
            )
        default_group_id = fetch_group_id_by_name(
            group_name=default_group_name,
            dst_session=trcon.dst_session
        )
        trcon.info["default_group_id"] = default_group_id  # for next time!


# noinspection PyProtectedMember
def translate_fn(trcon: TranslationContext) -> None:
    log.debug("Translating: {!r}", trcon.oldobj)

    # -------------------------------------------------------------------------
    # Set _group_id, if it's blank
    # -------------------------------------------------------------------------
    if (isinstance(trcon.oldobj, GenericTabletRecordMixin) and
            ("_group_id" in trcon.missing_src_columns or
             trcon.oldobj._group_id is None)):
        # ... order that carefully; if the _group_id column is missing from the
        # source, don't touch trcon.oldobj._group_id or it'll trigger a DB
        # query that fails.
        ensure_default_group_id(trcon)
        default_group_id = trcon.info["default_group_id"]
        log.debug("Assiging new _group_id of {!r}", default_group_id)
        trcon.newobj._group_id = default_group_id

    # -------------------------------------------------------------------------
    # If an identical user is found, merge on it rather than creating a new
    # one. Users with matching usernames are considered to be identical.
    # -------------------------------------------------------------------------
    if trcon.tablename == User.__tablename__:
        src_user = trcon.oldobj  # type: User
        src_username = src_user.username
        matching_user = trcon.dst_session.query(User) \
            .filter(User.username == src_username) \
            .one_or_none()  # type: Optional[User]
        if matching_user is not None:
            log.debug("Matching User (username {!r}) found; merging",
                      matching_user.username)
            trcon.newobj = matching_user  # so that related records will work

    # -------------------------------------------------------------------------
    # If an identical device is found, merge on it rather than creating a
    # new one. Devices with matching names are considered to be identical.
    # -------------------------------------------------------------------------
    if trcon.tablename == Device.__tablename__:
        src_device = trcon.oldobj  # type: Device
        src_devicename = src_device.name
        matching_device = trcon.dst_session.query(Device) \
            .filter(Device.name == src_devicename) \
            .one_or_none()  # type: Optional[Device]
        if matching_device is not None:
            log.debug("Matching Device (name {!r}) found; merging",
                      matching_device.name)
            trcon.newobj = matching_device

        # BUT BEWARE, BECAUSE IF YOU MERGE THE SAME DATABASE TWICE (even if
        # that's a silly thing to do...), MERGING DEVICES WILL BREAK THE KEY
        # RELATIONSHIPS. For example,
        #   source:
        #       pk = 1, id = 1, device = 100, era = 'NOW', current = 1
        #   dest after first merge:
        #       pk = 1, id = 1, device = 100, era = 'NOW', current = 1
        #   dest after second merge:
        #       pk = 1, id = 1, device = 100, era = 'NOW', current = 1
        #       pk = 2, id = 1, device = 100, era = 'NOW', current = 1
        # ... so you get a clash/duplicate.
        # Mind you, that's fair, because there is a duplicate.
        # SO WE DO SEPARATE DUPLICATE CHECKING, below.

    # -------------------------------------------------------------------------
    # If an identical group is found, merge on it rather than creating a
    # new one. Groups with matching names are considered to be identical.
    # -------------------------------------------------------------------------
    if trcon.tablename == Group.__tablename__:
        src_group = trcon.oldobj  # type: Group
        src_groupname = src_group.name
        matching_group = trcon.dst_session.query(Group) \
            .filter(Group.name == src_groupname) \
            .one_or_none()  # type: Optional[Group]
        if matching_group is not None:
            log.debug("Matching Group (name {!r}) found; merging",
                      matching_group.name)
            trcon.newobj = matching_group

    # -------------------------------------------------------------------------
    # If there are any patient numbers in the old format (as a set of
    # columns in the Patient table) which were not properly converted
    # to the new format (as individual records in the PatientIdNum
    # table), create new entries.
    # Only worth bothering with for _current entries.
    # (More explicitly: do not create new PatientIdNum entries for non-current
    # patients; it's very fiddly if there might be asynchrony between
    # Patient and PatientIdNum objects for that patient.)
    # -------------------------------------------------------------------------
    if trcon.tablename == Patient.__tablename__:
        # (a) Find old patient numbers
        old_patient = trcon.oldobj  # type: Patient
        # noinspection PyPep8
        src_pt_query = select([text('*')])\
            .select_from(table(trcon.tablename))\
            .where(column(Patient.id.name) == old_patient.id)\
            .where(column(Patient._current.name) == True)\
            .where(column(Patient._device_id.name) == old_patient._device_id)\
            .where(column(Patient._era.name) == old_patient._era)
        rows = trcon.src_session.execute(src_pt_query)  # type: ResultProxy
        list_of_dicts = [dict(row.items()) for row in rows]
        assert len(list_of_dicts) == 1, (
            "Failed to fetch old patient IDs correctly; bug?"
        )
        # log.critical("list_of_dicts: {}", pformat(list_of_dicts))
        old_patient_dict = list_of_dicts[0]

        # (b) If any don't exist in the new database, create them.
        # -- no, that's not right; we will be processing Patient before
        # PatientIdNum, so that should be: if any don't exist in the *source*
        # database, create them.
        for which_idnum in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
            old_fieldname = FP_ID_NUM_DEFUNCT + str(which_idnum)
            idnum_value = old_patient_dict[old_fieldname]
            if idnum_value is None:
                continue
            src_idnum_query = select([func.count()])\
                .select_from(table(PatientIdNum.__tablename__))\
                .where(column(PatientIdNum.patient_id.name) == old_patient.id)\
                .where(column(PatientIdNum._current.name) ==
                       old_patient._current)\
                .where(column(PatientIdNum._device_id.name) ==
                       old_patient._device_id)\
                .where(column(PatientIdNum._era.name) == old_patient._era)\
                .where(column(PatientIdNum.which_idnum.name) == which_idnum)
            n_present = trcon.dst_session.execute(src_idnum_query).scalar()
            # log.critical("{} -> {}", src_idnum_query, n_present)
            if n_present != 0:
                continue
            pidnum = PatientIdNum()
            # PatientIdNum fields:
            pidnum.id = fake_tablet_id_for_patientidnum(
                patient_id=old_patient.id, which_idnum=which_idnum)
            # ... guarantees a pseudo client (tablet) PK
            pidnum.patient_id = old_patient.id
            pidnum.which_idnum = which_idnum
            pidnum.idnum_value = idnum_value
            # GenericTabletRecordMixin fields:
            # _pk: autogenerated
            pidnum._device_id = (
                trcon.objmap[old_patient._device].id
            )
            pidnum._era = old_patient._era
            pidnum._current = old_patient._current
            pidnum._when_added_exact = old_patient._when_added_exact
            pidnum._when_added_batch_utc = old_patient._when_added_batch_utc
            pidnum._adding_user_id = (
                trcon.objmap[old_patient._adding_user].id
                if old_patient._adding_user is not None else None
            )
            pidnum._when_removed_exact = old_patient._when_removed_exact
            pidnum._when_removed_batch_utc = old_patient._when_removed_batch_utc  # noqa
            pidnum._removing_user_id = (
                trcon.objmap[old_patient._removing_user].id
                if old_patient._removing_user is not None else None
            )
            pidnum._preserving_user_id = (
                trcon.objmap[old_patient._preserving_user].id
                if old_patient._preserving_user is not None else None
            )
            pidnum._forcibly_preserved = old_patient._forcibly_preserved
            pidnum._predecessor_pk = None  # Impossible to calculate properly
            pidnum._successor_pk = None  # Impossible to calculate properly
            pidnum._manually_erased = old_patient._manually_erased
            pidnum._manually_erased_at = old_patient._manually_erased_at
            pidnum._manually_erasing_user_id = (
                trcon.objmap[old_patient._manually_erasing_user].id
                if old_patient._manually_erasing_user is not None else None
            )
            pidnum._camcops_version = old_patient._camcops_version
            pidnum._addition_pending = old_patient._addition_pending
            pidnum._removal_pending = old_patient._removal_pending
            pidnum._group_id = trcon.newobj._group_id
            # ... will have been set above if it was blank

            # OK.
            log.debug("Inserting new PatientIdNum: {}", pidnum)
            trcon.dst_session.add(pidnum)

    # -------------------------------------------------------------------------
    # Check we're not creating duplicates for anything uploaded
    # -------------------------------------------------------------------------
    if isinstance(trcon.oldobj, GenericTabletRecordMixin):
        old_instance = trcon.oldobj
        cls = trcon.newobj.__class__  # type: Type[GenericTabletRecordMixin]
        # Records uploaded from tablets must be unique on the combination of:
        #       id                  = table PK
        #       _device_id          = device
        #       _era                = device era
        #       _when_removed_exact = removal date or NULL
        exists_query = select([func.count()])\
            .select_from(table(trcon.tablename))\
            .where(column(cls.id.name) == old_instance.id)\
            .where(column(cls._device_id.name) ==
                   trcon.objmap[old_instance._device].id)\
            .where(column(cls._era.name) == old_instance._era)\
            .where(column(cls._when_removed_exact.name) ==
                   old_instance._when_removed_exact)
        # Note re NULLs... Although it's an inconvenient truth in SQL that
        #   SELECT NULL = NULL; -> NULL
        # in this code we have a comparison of a column to a Python value.
        # SQLAlchemy is clever and renders "IS NULL" if the Python value is
        # None, or an "=" comparison otherwise.
        # If we were comparing a column to another column, we'd have to do
        # more; e.g.
        #
        # WRONG one-to-one join to self:
        #
        #   SELECT a._pk, b._pk, a._when_removed_exact
        #   FROM phq9 a
        #   INNER JOIN phq9 b
        #       ON a._pk = b._pk
        #       AND a._when_removed_exact = b._when_removed_exact;
        #
        #   -- drops all rows
        #
        # CORRECT one-to-one join to self:
        #
        #   SELECT a._pk, b._pk, a._when_removed_exact
        #   FROM phq9 a
        #   INNER JOIN phq9 b
        #       ON a._pk = b._pk
        #       AND (a._when_removed_exact = b._when_removed_exact
        #            OR (a._when_removed_exact IS NULL AND
        #                b._when_removed_exact IS NULL));
        #
        #   -- returns all rows
        n_exists = trcon.dst_session.execute(exists_query).scalar()
        if n_exists > 0:
            existing_rec_q = select(['*'])\
                .select_from(table(trcon.tablename))\
                .where(column(cls.id.name) == old_instance.id)\
                .where(column(cls._device_id.name) ==
                       trcon.objmap[old_instance._device].id) \
                .where(column(cls._era.name) == old_instance._era)\
                .where(column(cls._when_removed_exact.name) ==
                       old_instance._when_removed_exact)
            resultproxy = trcon.dst_session.execute(existing_rec_q).fetchall()
            existing_rec = [dict(row) for row in resultproxy]
            errmsg = (
                "Source record, inheriting from GenericTabletRecordMixin and "
                "shown below, already exists in destination database:\n\n"
                "{o}\n\n"
                "... in table {t!r}, clashing on: id="
                "{i!r}, device_id={d!r}, era={e!r}, "
                "_when_removed_exact={w!r}.\n"
                "The existing record(s) in the destination database "
                "was/were:\n\n"
                "{rec}.\n\n"
                "ARE YOU TRYING TO MERGE THE SAME DATABASE IN TWICE? "
                "DON'T.".format(
                    o=pformat(old_instance.__dict__),
                    t=trcon.tablename,
                    i=old_instance.id,
                    d=old_instance._device_id,
                    e=old_instance._era,
                    w=old_instance._when_removed_exact,
                    rec=pformat(existing_rec),
                )
            )
            log.critical("{}", errmsg)
            if (trcon.tablename == PatientIdNum.__tablename__ and
                    old_instance.id == 0):
                log.critical(
                    'Since this error has occurred for table {!r} and '
                    'id == 0, this error likely indicates a previous bug in '
                    'the patient ID number fix for the database upload '
                    'script, in which all ID numbers for patients with '
                    'patient.id = n were given patient_idnum.id = n * {} '
                    'themselves (or possibly were all given patient_idnum.id '
                    '= 0). Fix this by running, on the source database:\n\n'
                    '    UPDATE patient_idnum SET id = _pk;\n\n'.format(
                        trcon.tablename, NUMBER_OF_IDNUMS_DEFUNCT,
                    )
                )
            raise ValueError("Attempt to insert duplicate record; see log "
                             "message above.")


# =============================================================================
# Postprocess
# =============================================================================

# noinspection PyUnusedLocal
def postprocess(src_engine: Engine, dst_session: Session) -> None:
    log.warning("NOT IMPLEMENTED AUTOMATICALLY: copying user/group mapping "
                "from table {!r}; do this by hand.", user_group_table.name)
    log.warning("NOT IMPLEMENTED AUTOMATICALLY: copying group/group mapping "
                "from table {!r}; do this by hand.", group_group_table.name)


# =============================================================================
# Main
# =============================================================================

def merge_camcops_db(src: str,
                     echo: bool,
                     report_every: int,
                     dummy_run: bool,
                     info_only: bool,
                     skip_hl7_logs: bool,
                     skip_audit_logs: bool,
                     default_group_id: Optional[int],
                     default_group_name: Optional[str]) -> None:

    req = command_line_request()
    src_engine = create_engine(src, echo=echo, pool_pre_ping=True)
    log.info("SOURCE: " + get_safe_url_from_engine(src_engine))
    log.info("DESTINATION: " + get_safe_url_from_engine(req.engine))

    # Delay the slow import until we've checked our syntax
    log.info("Loading all models...")
    from ..cc_modules.cc_all_models import all_models_no_op  # delayed import
    all_models_no_op()
    log.info("Models loaded.")

    # Now, any special dependencies?
    # From the point of view of translating any tablet-related fields, the
    # actual (server) PK values are irrelevant; all relationships will be
    # identical if you change any PK (not standard database practice, but
    # convenient here).
    # The dependencies that do matter are server-side things, like user_id
    # variables.

    # For debugging only, some junk:
    # test_dependencies = [
    #     TableDependency(parent_tablename="patient",
    #                     child_tablename="_dirty_tables")
    # ]

    # -------------------------------------------------------------------------
    # Tables to skip
    # -------------------------------------------------------------------------

    skip_tables = [
        # Transient stuff we don't want to copy across, or wouldn't want to
        # overwrite the destination with, or where the PK structure has
        # changed and we don't care about old data:
        TableIdentity(tablename=CamcopsSession.__tablename__),
        TableIdentity(tablename=ServerStoredVar.__tablename__),
        TableIdentity(tablename=SecurityAccountLockout.__tablename__),
        TableIdentity(tablename=SecurityLoginFailure.__tablename__),
    ]

    # Tedious and bulky stuff the user may want to skip:
    if skip_hl7_logs:
        skip_tables.extend([
            TableIdentity(tablename=HL7Message.__tablename__),
            TableIdentity(tablename=HL7Run.__tablename__),
        ])
    if skip_audit_logs:
        skip_tables.append(TableIdentity(tablename=AuditEntry.__tablename__))

    # -------------------------------------------------------------------------
    # Initial operations on SOURCE database
    # -------------------------------------------------------------------------

    skip_tables += preprocess(src_engine=src_engine)

    # -------------------------------------------------------------------------
    # Merge
    # -------------------------------------------------------------------------

    # Merge! It's easy...
    dst_session = req.dbsession
    trcon_info = dict(default_group_id=default_group_id,
                      default_group_name=default_group_name)
    merge_db(
        base_class=Base,
        src_engine=src_engine,
        dst_session=dst_session,
        allow_missing_src_tables=True,
        allow_missing_src_columns=True,
        translate_fn=translate_fn,
        skip_tables=skip_tables,
        only_tables=None,
        tables_to_keep_pks_for=None,
        # extra_table_dependencies=test_dependencies,
        extra_table_dependencies=None,
        dummy_run=dummy_run,
        info_only=info_only,
        report_every=report_every,
        flush_per_table=True,
        flush_per_record=False,
        commit_with_flush=False,
        commit_at_end=True,
        prevent_eager_load=True,
        trcon_info=trcon_info
    )

    # -------------------------------------------------------------------------
    # Postprocess
    # -------------------------------------------------------------------------

    postprocess(src_engine=src_engine, dst_session=dst_session)

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------

    dst_session.commit()
