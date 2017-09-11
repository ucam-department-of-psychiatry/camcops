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

import argparse
import logging
import os
# from pprint import pformat
from typing import Optional, Type, TYPE_CHECKING

from cardinal_pythonlib.debugging import pdb_run
from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from cardinal_pythonlib.sqlalchemy.merge_db import (
    merge_db,
    TableIdentity,
    TranslationContext,
)
from cardinal_pythonlib.sqlalchemy.orm_schema import (
    create_table_from_orm_class,
)
from cardinal_pythonlib.sqlalchemy.schema import get_table_names
from cardinal_pythonlib.sqlalchemy.session import get_safe_url_from_engine
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import column, func, select, table, text
from ..cc_modules.cc_audit import AuditEntry
from ..cc_modules.cc_baseconstants import ENVVAR_CONFIG_FILE
from ..cc_modules.cc_constants import FP_ID_NUM, NUMBER_OF_IDNUMS_DEFUNCT
from ..cc_modules.cc_db import GenericTabletRecordMixin
from ..cc_modules.cc_device import Device
from ..cc_modules.cc_hl7 import HL7Message, HL7Run
from ..cc_modules.cc_patient import Patient
from ..cc_modules.cc_patientidnum import PatientIdNum
from ..cc_modules.cc_request import command_line_request
from ..cc_modules.cc_session import CamcopsSession
from ..cc_modules.cc_storedvar import ServerStoredVar
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_user import User

if TYPE_CHECKING:
    from sqlalchemy.engine import ResultProxy

log = BraceStyleAdapter(logging.getLogger(__name__))

DEBUG_VIA_PDB = False


# =============================================================================
# Preprocess
# =============================================================================

def preprocess(src_engine: Engine) -> None:
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


# =============================================================================
# Extra translation to be applied to individual objects
# =============================================================================
# The extra logic for this database:

# noinspection PyProtectedMember
def translate_fn(trcon: TranslationContext) -> None:
    if trcon.tablename == User.__tablename__:
        # ---------------------------------------------------------------------
        # If an identical user is found, merge on it rather than creating a new
        # one. Users with matching usernames are considered to be identical.
        # ---------------------------------------------------------------------
        src_user = trcon.oldobj  # type: User
        src_username = src_user.username
        matching_user = trcon.dst_session.query(User) \
            .filter(User.username == src_username) \
            .one_or_none()  # type: Optional[User]
        if matching_user is not None:
            log.info("Matching User (username {!r}) found; merging",
                     matching_user.username)
            trcon.newobj = matching_user  # so that related records will work

    elif trcon.tablename == Device.__tablename__:
        # -------------------------------------------------------------------
        # If an identical device is found, merge on it rather than creating a
        # new one. Devices with matching names are considered to be identical.
        # -------------------------------------------------------------------
        src_device = trcon.oldobj  # type: Device
        src_devicename = src_device.name
        matching_device = trcon.dst_session.query(Device) \
            .filter(Device.name == src_devicename) \
            .one_or_none()  # type: Optional[Device]
        if matching_device is not None:
            log.info("Matching Device (name {!r}) found; merging",
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

    elif trcon.tablename == Patient.__tablename__:
        # ---------------------------------------------------------------------
        # If there are any patient numbers in the old format (as a set of
        # columns in the Patient table) which were not properly converted
        # to the new format (as individual records in the PatientIdNum
        # table), create new entries.
        # ---------------------------------------------------------------------

        # (a) Find old patient numbers
        old_patient = trcon.oldobj  # type: Patient
        # noinspection PyPep8
        src_query = select([text('*')])\
            .select_from(table(trcon.tablename))\
            .where(column(Patient.id.name) == old_patient.id)\
            .where(column(Patient._current.name) == True)\
            .where(column(Patient._device_id.name) == old_patient._device_id)\
            .where(column(Patient._era.name) == old_patient._era)
        rows = trcon.src_session.execute(src_query)  # type: ResultProxy
        list_of_dicts = [dict(row.items()) for row in rows]
        assert len(list_of_dicts) == 1, (
            "Failed to fetch old patient IDs correctly; bug?"
        )
        # log.critical("list_of_dicts: {}", pformat(list_of_dicts))
        old_patient_dict = list_of_dicts[0]

        # (b) If any don't exist in the new database, create them.
        for which_idnum in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
            old_fieldname = FP_ID_NUM + str(which_idnum)
            idnum_value = old_patient_dict[old_fieldname]
            if idnum_value is None:
                continue
            dst_query = select([func.count()])\
                .select_from(table(PatientIdNum.__tablename__))\
                .where(column(PatientIdNum.patient_id.name) == old_patient.id)\
                .where(column(PatientIdNum._current.name) ==
                       old_patient._current)\
                .where(column(PatientIdNum._device_id.name) ==
                       old_patient._device_id)\
                .where(column(PatientIdNum._era.name) == old_patient._era)\
                .where(column(PatientIdNum.which_idnum.name) == which_idnum)
            n_present = trcon.dst_session.execute(dst_query).scalar()
            if n_present != 0:
                continue
            pidnum = PatientIdNum()
            # PatientIdNum fields:
            pidnum.id = old_patient.id * NUMBER_OF_IDNUMS_DEFUNCT
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
            # OK.
            log.info("Inserting new PatientIdNum: {}", pidnum)
            trcon.dst_session.add(pidnum)

    # -------------------------------------------------------------------------
    # Check we're not creating duplicates for anything uploaded
    # -------------------------------------------------------------------------
    if (isinstance(trcon.oldobj, GenericTabletRecordMixin) and
            trcon.oldobj._current):
        old_instance = trcon.oldobj
        cls = trcon.newobj.__class__  # type: Type[GenericTabletRecordMixin]
        exists_query = select([func.count()])\
            .select_from(table(trcon.tablename))\
            .where(column(cls.id.name) == old_instance.id)\
            .where(column(cls._era.name) == old_instance._era)\
            .where(column(cls._device_id.name) ==
                   trcon.objmap[old_instance._device].id)
        n_exists = trcon.dst_session.execute(exists_query).scalar()
        if n_exists > 0:
            errmsg = (
                "Record inheriting from GenericTabletRecordMixin already "
                "exists in destination database: {o!r} in table {t!r}; id="
                "{i!r}, era={e!r}, device_id={d!r}, _current={c!r}. ARE YOU "
                "TRYING TO MERGE THE SAME DATABASE IN TWICE? DON'T.".format(
                    o=old_instance,
                    t=trcon.tablename,
                    i=old_instance.id,
                    e=old_instance._era,
                    d=old_instance._device_id,
                    c=old_instance._current,
                )
            )
            log.critical(errmsg)
            raise ValueError(errmsg)


# =============================================================================
# Postprocess
# =============================================================================

def postprocess(src_engine: Engine, dst_session: Session) -> None:
    pass


# =============================================================================
# Main
# =============================================================================

def merge_main() -> None:
    # Arguments
    parser = argparse.ArgumentParser(
        description="Merge CamCOPS databases",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--config',
        default=os.environ.get(ENVVAR_CONFIG_FILE, None),
        help="Specify the CamCOPS configuration file. If this is not "
             "specified on the command line, the environment variable {} is "
             "examined.".format(ENVVAR_CONFIG_FILE))
    parser.add_argument(
        '--report_every', type=int, default=10000,
        help="Report progress every n rows"
    )
    parser.add_argument(
        '--echo', action="store_true",
        help="Echo SQL to source database"
    )
    parser.add_argument(
        '--dummy_run', action="store_true",
        help="Perform a dummy run only; do not alter destination database"
    )
    parser.add_argument(
        '--info_only', action="store_true",
        help="Show table information only; don't do any work"
    )
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Be verbose"
    )
    parser.add_argument(
        '--skip_hl7_logs', action="store_true",
        help="Skip the {!r} table".format(HL7Run.__tablename__)
    )
    parser.add_argument(
        '--skip_audit_logs', action="store_true",
        help="Skip the {!r} table".format(HL7Run.__tablename__)
    )
    required_named = parser.add_argument_group('required named arguments')
    # https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments  # noqa
    required_named.add_argument(
        '--src',
        required=True,  # bad form, but there is safety in being explicit
        help="Source database (specified as an SQLAlchemy URL). The contents "
             "of this database will be merged into the database specified "
             "in the config file."
    )
    args = parser.parse_args()

    # Logging
    loglevel = logging.DEBUG if args.verbose else logging.INFO
    main_only_quicksetup_rootlogger(level=loglevel)

    # Config; database connections
    os.environ[ENVVAR_CONFIG_FILE] = args.config
    req = command_line_request()
    src_engine = create_engine(args.src, echo=args.echo,
                               pool_pre_ping=True)
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
        # overwrite the destination with:
        TableIdentity(tablename=CamcopsSession.__tablename__),
        TableIdentity(tablename=ServerStoredVar.__tablename__),
    ]

    # Tedious and bulky stuff the user may want to skip:
    if args.skip_hl7_logs:
        skip_tables.extend([
            TableIdentity(tablename=HL7Message.__tablename__),
            TableIdentity(tablename=HL7Run.__tablename__),
        ])
    if args.skip_audit_logs:
        skip_tables.append(TableIdentity(tablename=AuditEntry.__tablename__))

    # -------------------------------------------------------------------------
    # Initial operations on SOURCE database
    # -------------------------------------------------------------------------

    preprocess(src_engine=src_engine)

    # -------------------------------------------------------------------------
    # Merge
    # -------------------------------------------------------------------------

    # Merge! It's easy...
    dst_session = req.dbsession
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
        dummy_run=args.dummy_run,
        info_only=args.info_only,
        report_every=args.report_every,
        flush_per_table=True,
        flush_per_record=False,
        commit_with_flush=False,
        commit_at_end=True,
        prevent_eager_load=True
    )

    # -------------------------------------------------------------------------
    # Postprocess
    # -------------------------------------------------------------------------

    postprocess(src_engine=src_engine, dst_session=dst_session)

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------

    dst_session.commit()


def main() -> None:
    if DEBUG_VIA_PDB:
        pdb_run(merge_main)
    else:
        merge_main()


if __name__ == "__main__":
    main()
