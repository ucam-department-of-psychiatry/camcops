#!/usr/bin/env python
# camcops_server/client_api.py

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

We use primarily SQLAlchemy Core here (in contrast to the ORM used elsewhere).

"""

# =============================================================================
# Imports
# =============================================================================

import cgi
import logging
import re
import time
from typing import (Any, Dict, Iterable, List,
                    Optional, Sequence, Tuple, Type)

from cardinal_pythonlib.convert import (
    base64_64format_encode,
    hex_xformat_encode,
)
from cardinal_pythonlib.datetimefunc import format_datetime
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.pyramid.responses import TextResponse
import cardinal_pythonlib.rnc_db as rnc_db
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.core_query import (
    exists_in_table,
    fetch_all_first_values,
)
from cardinal_pythonlib.text import escape_newlines, unescape_newlines
from pendulum import Pendulum
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.security import Authenticated, NO_PERMISSION_REQUIRED
from sqlalchemy.engine.result import ResultProxy
from sqlalchemy.sql.expression import column, exists, select, text, update
from sqlalchemy.sql.schema import Table

from ..cc_modules import cc_audit  # avoids "audit" name clash
from .cc_all_models import CLIENT_TABLE_MAP, RESERVED_FIELDS
from .cc_client_api_core import (
    exception_description,
    fail_server_error,
    fail_server_error_from_exception,
    fail_unsupported_operation,
    fail_user_error,
    fail_user_error_from_exception,
    require_keys,
    ServerErrorException,
    TabletParam,
    UserErrorException,
)
from .cc_constants import (
    CLIENT_DATE_FIELD,
    DateFormat,
    ERA_NOW,
    FP_ID_NUM_DEFUNCT,
    FP_ID_DESC_DEFUNCT,
    FP_ID_SHORT_DESC_DEFUNCT,
    MOVE_OFF_TABLET_FIELD,
    NUMBER_OF_IDNUMS_DEFUNCT,  # allowed; for old tablet versions
)
from .cc_convert import (
    decode_values,
    delimit,
    encode_single_value,
)
from .cc_device import Device
from .cc_dirtytables import DirtyTable
from .cc_group import Group
from .cc_patient import Patient
from .cc_patientidnum import fake_tablet_id_for_patientidnum, PatientIdNum
from .cc_pyramid import RequestMethod, Routes
from .cc_request import CamcopsRequest
from .cc_session import CamcopsSession
from .cc_specialnote import SpecialNote
from .cc_serversettings import ServerSettings
from .cc_tabletsession import TabletSession
from .cc_taskfilter import TaskFilter
from .cc_unittest import (
    unit_test_ignore,
    unit_test_must_raise,
    unit_test_verify
)
from .cc_version import CAMCOPS_SERVER_VERSION, CAMCOPS_SERVER_VERSION_STRING

log = BraceStyleAdapter(logging.getLogger(__name__))


# *** handle DeviceStoredVar table from old clients?

# =============================================================================
# Constants
# =============================================================================

COPE_WITH_DELETED_PATIENT_DESCRIPTIONS = True
# ... as of client 2.0.0, ID descriptions are no longer duplicated.
# As of server 2.0.0, the fields still exist in the database, but the reporting
# and consistency check has been removed. In the next version of the server,
# the fields will be removed, and then the server should cope with old clients,
# at least for a while.

DUPLICATE_FAILED = "Failed to duplicate record"
INSERT_FAILED = "Failed to insert record"

# REGEX_INVALID_TABLE_FIELD_CHARS = re.compile("[^a-zA-Z0-9_]")
# ... the ^ within the [] means the expression will match any character NOT in
# the specified range


# =============================================================================
# Validators
# =============================================================================

def ensure_valid_table_name(tablename: str) -> None:
    """
    Ensures a table name doesn't contain bad characters, isn't a reserved
    table that the user is prohibited from accessing, and is a valid table name
    that's in the database. Raises UserErrorException upon failure.

    ... 2017-10-08: shortcut to all that: it's OK if it's listed as a valid
    client table.
    """
    if tablename not in CLIENT_TABLE_MAP:
        fail_user_error("Invalid client table name: {}".format(tablename))


def ensure_valid_field_name(table: Table, fieldname: str) -> None:
    """
    Ensures a field name contains only valid characters, and isn't a
    reserved fieldname that the user isn't allowed to access.
    Raises UserErrorException upon failure.

    ... 2017-10-08: shortcut: it's OK if it's a column name for a particular
    table.
    """
    if fieldname in RESERVED_FIELDS:
        fail_user_error("Reserved field name for table {!r}: {!r}".format(
            table.name, fieldname))
    if fieldname not in table.columns.keys():
        fail_user_error("Invalid field name for table {!r}: {!r}".format(
            table.name, fieldname))


# =============================================================================
# Extracting information from the POST request
# =============================================================================

def get_post_var(req: CamcopsRequest,
                 var: str,
                 mandatory: bool = True,
                 valtype: Type[Any] = None) -> Any:
    """
    Retrieves a variable from CamcopsRequest, raising an error that gets passed
    to the client device if it's invalidly missing or of an invalid type.

    Args:
        req: CamcopsRequest
        var: name of variable to retrieve
        mandatory: if True, script aborts if variable missing
        valtype: if not None, valtype() is performed on the result -- for
            example, valtype=int will perform conversion to int.
    Returns:
        value
    """
    val = req.get_str_param(var, default=None)
    if mandatory and val is None:
        fail_user_error("Must provide the variable: {}".format(var))
    if valtype is not None:
        try:
            val = valtype(val)
        except (TypeError, ValueError):
            fail_user_error("Variable {} is of invalid type".format(var))
    return val


def get_table_from_req(req: CamcopsRequest, var: str) -> Table:
    """
    Retrieves a table name from a CGI form and checks it's a valid client
    table.
    """
    tablename = get_post_var(req, var, mandatory=True)
    ensure_valid_table_name(tablename)
    return CLIENT_TABLE_MAP[tablename]


def get_single_field_from_post_var(req: CamcopsRequest,
                                   table: Table,
                                   var: str,
                                   mandatory: bool = True) -> str:
    """
    Retrieves a field name from a the request and checks it's not a bad
    fieldname.
    """
    field = get_post_var(req, var, mandatory=mandatory)
    ensure_valid_field_name(table, field)
    return field


def get_fields_from_post_var(req: CamcopsRequest,
                             table: Table,
                             var: str,
                             mandatory: bool = True) -> List[str]:
    """
    Get a comma-separated list of field names from a request and checks that
    all are acceptable. Returns a list of fieldnames.
    """
    csfields = get_post_var(req, var, mandatory=mandatory)
    if not csfields:
        return []
    # can't have any commas in fields, so it's OK to use a simple
    # split() command
    fields = [x.strip() for x in csfields.split(",")]
    for f in fields:
        ensure_valid_field_name(table, f)
    return fields


def get_values_from_post_var(req: CamcopsRequest,
                             var: str,
                             mandatory: bool = True) -> List[Any]:
    """
    Retrieves a list of values from a CSV-separated list of SQL values
    stored in a CGI form (including e.g. NULL, numbers, quoted strings, and
    special handling for base-64/hex-encoded BLOBs.)
    """
    csvalues = get_post_var(req, var, mandatory=mandatory)
    if not csvalues:
        return []
    return decode_values(csvalues)


def get_fields_and_values(req: CamcopsRequest,
                          table: Table,
                          fields_var: str,
                          values_var: str,
                          mandatory: bool = True) -> Dict[str, Any]:
    """
    Gets fieldnames and matching values from two variables in a request.
    """
    fields = get_fields_from_post_var(req, table, fields_var,
                                      mandatory=mandatory)
    values = get_values_from_post_var(req, values_var, mandatory=mandatory)
    if len(fields) != len(values):
        fail_user_error(
            "Number of fields ({f}) doesn't match number of values "
            "({v})".format(f=len(fields), v=len(values))
        )
    return dict(list(zip(fields, values)))


def get_tables_from_post_var(req: CamcopsRequest,
                             var: str,
                             mandatory: bool = True) -> List[str]:
    """
    Gets a list of tables from a CGI form variable, and ensures all are
    valid.
    """
    cstables = get_post_var(req, var, mandatory=mandatory)
    if not cstables:
        return []
    # can't have any commas in table names, so it's OK to use a simple
    # split() command
    tables = [x.strip() for x in cstables.split(",")]
    for t in tables:
        ensure_valid_table_name(t)
    return tables


# =============================================================================
# Sending stuff to the client
# =============================================================================

def get_server_id_info(req: CamcopsRequest) -> Dict[str, str]:
    """Returns a reply for the tablet giving details of the server."""
    group = Group.get_group_by_id(req.dbsession, req.user.upload_group_id)
    reply = {
        TabletParam.DATABASE_TITLE: req.database_title,
        TabletParam.ID_POLICY_UPLOAD: group.upload_policy or "",
        TabletParam.ID_POLICY_FINALIZE: group.finalize_policy or "",
        TabletParam.SERVER_CAMCOPS_VERSION: CAMCOPS_SERVER_VERSION_STRING,
    }
    for n in req.valid_which_idnums:
        nstr = str(n)
        reply[TabletParam.ID_DESCRIPTION_PREFIX + nstr] = \
            req.get_id_desc(n, "")
        reply[TabletParam.ID_SHORT_DESCRIPTION_PREFIX + nstr] = \
            req.get_id_shortdesc(n, "")
    return reply


def get_select_reply(fields: Sequence[str],
                     rows: Sequence[Sequence[Any]]) -> Dict:
    """
    Return format:
        nfields:X
        fields:X
        nrecords:X
        record0:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
            ...
        record{n}:VALUES_AS_CSV_LIST_OF_ENCODED_SQL_VALUES
    """
    nrecords = len(rows)
    reply = {
        TabletParam.NFIELDS: len(fields),
        TabletParam.FIELDS: ",".join(fields),
        TabletParam.NRECORDS: nrecords,
    }
    for r in range(nrecords):
        row = rows[r]
        encodedvalues = []  # type: List[str]
        for val in row:
            encodedvalues.append(encode_single_value(val))
        reply[TabletParam.RECORD_PREFIX + str(r)] = ",".join(encodedvalues)
    return reply


# =============================================================================
# CamCOPS table functions
# =============================================================================

def get_server_pks_of_active_records(req: CamcopsRequest,
                                     table: Table) -> List[int]:
    """
    Gets server PKs of active records (_current and in the 'NOW' era) for
    the specified device/table.
    """
    query = select([table.c._pk])\
        .where(table.c._device_id == req.tabletsession.device_id)\
        .where(table.c._current)\
        .where(table.c._era == ERA_NOW)
    return fetch_all_first_values(req.dbsession, query)


def record_exists(req: CamcopsRequest,
                  table: Table,
                  clientpk_name: str,
                  clientpk_value: Any) -> Tuple[bool, Optional[int]]:
    """
    Checks if a record exists, using the device's perspective of a
    table/client PK combination.
    Returns (exists, serverpk), where exists is Boolean.
    If exists is False, serverpk will be None.
    """
    query = select([table.c._pk])\
        .where(table.c._device_id == req.tabletsession.device_id)\
        .where(table.c._current)\
        .where(table.c._era == ERA_NOW)\
        .where(column(clientpk_name) == clientpk_value)
    pklist = fetch_all_first_values(req.dbsession, query)
    exists = bool(len(pklist) >= 1)
    serverpk = pklist[0] if exists else None
    return exists, serverpk
    # Consider a warning/failure if we have >1 row meeting these criteria.
    # Not currently checked for.


def get_server_pks_of_specified_records(req: CamcopsRequest,
                                        table: Table,
                                        wheredict: Dict) -> List[int]:
    """
    Retrieves server PKs for a table, for a given device, given a set of
    'where' conditions specified in wheredict (as field/value combinations,
    joined with AND).
    """
    query = select([table.c._pk])\
        .where(table.c._device_id == req.tabletsession.device_id)\
        .where(table.c._current)\
        .where(table.c._era == ERA_NOW)
    for fieldname, value in wheredict.items():
        query = query.where(column(fieldname) == value)
    return fetch_all_first_values(req.dbsession, query)


def record_identical_full(req: CamcopsRequest,
                          table: Table,
                          serverpk: int,
                          wheredict: Dict) -> bool:
    """
    If a record with the specified server PK exists in the specified table
    having all its values matching the field/value combinations in wheredict
    (joined with AND), returns True. Otherwise, returns False.
    Used to detect if an incoming record matches the database record.

    CURRENTLY UNUSED.
    """
    criteria = [table.c._pk == serverpk]
    for fieldname, value in wheredict.items():
        criteria.append(column(fieldname) == value)
    return exists_in_table(req.dbsession, table, *criteria)


def record_identical_by_date(req: CamcopsRequest,
                             table: Table,
                             serverpk: int,
                             client_date_value: Pendulum) -> bool:
    """
    Shortcut to detecting a record being identical. Returns true if the
    record (defined by its table/server PK) has a CLIENT_DATE_FIELD field
    that matches that of the incoming record. As long as the tablet always
    updates the CLIENT_DATE_FIELD when it saves a record, and the clock on the
    device doesn't go backwards by a certain exact millisecond-precision value,
    this is a valid method.
    """
    criteria = [
        table.c._pk == serverpk,
        table.c[CLIENT_DATE_FIELD] == client_date_value,
    ]
    return exists_in_table(req.dbsession, table, *criteria)


# ***
def upload_record_core(req: CamcopsRequest,
                       table: Table,
                       clientpk_name: str,
                       valuedict: Dict,
                       recordnum: int) -> Tuple[int, int]:
    """
    Uploads a record. Deals with IDENTICAL, NEW, and MODIFIED records.
    """
    sm = req.tabletsession
    require_keys(valuedict, [clientpk_name, CLIENT_DATE_FIELD,
                             MOVE_OFF_TABLET_FIELD])
    clientpk_value = valuedict[clientpk_name]
    found, oldserverpk = record_exists(req, table, clientpk_name,
                                       clientpk_value)
    newserverpk = None
    if found:
        client_date_value = valuedict[CLIENT_DATE_FIELD]
        if record_identical_by_date(req, table, oldserverpk,
                                    client_date_value):
            # IDENTICAL. No action needed...
            # UNLESS MOVE_OFF_TABLET_FIELDNAME is set
            if valuedict[MOVE_OFF_TABLET_FIELD]:
                flag_record_for_preservation(req, table, oldserverpk)
                log.debug("Table {table}, uploaded record {recordnum}: "
                          "identical but moving off tablet",
                          table=table, recordnum=recordnum)
            else:
                log.debug("Table {table}, uploaded record {recordnum}: "
                          "identical", table=table, recordnum=recordnum)
        else:
            # MODIFIED
            if table == Patient.__tablename__:
                if sm.cope_with_deleted_patient_descriptors:
                    # Old tablets (pre-2.0.0) will upload copies of the ID
                    # descriptions with the patient. To cope with that, we
                    # remove those here:
                    for n in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
                        nstr = str(n)
                        fn_desc = FP_ID_DESC_DEFUNCT + nstr
                        fn_shortdesc = FP_ID_SHORT_DESC_DEFUNCT + nstr
                        valuedict.pop(fn_desc, None)  # remove item, if exists
                        valuedict.pop(fn_shortdesc, None)
                if sm.cope_with_old_idnums:
                    # Insert records into the new ID number table from the old
                    # patient table:
                    for which_idnum in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
                        nstr = str(which_idnum)
                        fn_idnum = FP_ID_NUM_DEFUNCT + nstr
                        idnum_value = valuedict.get(fn_idnum, None)
                        patient_id = valuedict.get("id", None)
                        if idnum_value is None or patient_id is None:
                            continue
                        mark_table_dirty(req, PatientIdNum.__table__)
                        _, _ = upload_record_core(
                            req=req,
                            table=PatientIdNum.__table__,
                            clientpk_name='id',
                            valuedict={
                                'id': fake_tablet_id_for_patientidnum(
                                    patient_id=patient_id,
                                    which_idnum=which_idnum
                                ),
                                # ... guarantees a pseudo client PK
                                'patient_id': patient_id,
                                'which_idnum': which_idnum,
                                'idnum_value': idnum_value,
                                CLIENT_DATE_FIELD: client_date_value,
                                MOVE_OFF_TABLET_FIELD: valuedict[MOVE_OFF_TABLET_FIELD],  # noqa
                            },
                            recordnum=recordnum
                        )
                    # Now, how to deal with deletion, i.e. records missing
                    # from the tablet?
                    # See our caller, upload_table().

            newserverpk = insert_record(req, table, valuedict, oldserverpk)
            flag_modified(req, table, oldserverpk, newserverpk)
            log.debug("Table {table}, record {recordnum}: modified",
                      table=table.name, recordnum=recordnum)
    else:
        # NEW
        newserverpk = insert_record(req, table, valuedict, None)
    return oldserverpk, newserverpk


def insert_record(req: CamcopsRequest,
                  table: Table,
                  valuedict: Dict,
                  predecessor_pk: Optional[int]) -> int:
    """
    Inserts a record, or raises an exception if that fails.
    """
    mark_table_dirty(req, table)
    ts = req.tabletsession
    valuedict.update({
        "_device_id": ts.device_id,
        "_era": ERA_NOW,
        "_current": 0,
        "_addition_pending": 1,
        "_removal_pending": 0,
        "_predecessor_pk": predecessor_pk,
        "_camcops_version": ts.tablet_version_str,
    })
    rp = req.dbsession.execute(
        table.insert().values(valuedict)
    )  # type: ResultProxy
    return rp.inserted_primary_key


def duplicate_record(req: CamcopsRequest, table: Table, serverpk: int) -> int:
    """
    Duplicates the record defined by the table/serverpk combination.
    Will raise an exception if the insert fails. Otherwise...
    The old record then NEEDS MODIFICATION by flag_modified().
    The new record NEEDS MODIFICATION by update_new_copy_of_record().
    """
    mark_table_dirty(req, table)
    # Fetch the existing record.
    query = select([text('*')])\
        .select_from(table)\
        .where(table.c._pk == serverpk)
    row = req.dbsession.execute(query).one()
    if not row:
        raise ServerErrorException(
            "Tried to fetch nonexistent record: table {t}, PK {pk}".format(
                t=table.name, pk=serverpk))
    valuedict = dict(row)
    # Remove the PK from what we insert back (that will be autogenerated)
    valuedict.pop("_pk", None)
    # ... or del d["_pk"]; http://stackoverflow.com/questions/5447494
    # Perform the insert
    insert_rp = req.dbsession.execute(
        table.insert().values(valuedict)
    )  # type: ResultProxy
    return insert_rp.inserted_primary_key


def update_new_copy_of_record(req: CamcopsRequest,
                              table: Table,
                              serverpk: int,
                              valuedict: Dict,
                              predecessor_pk: int) -> None:
    """
    Following duplicate_record(), use this to modify the new copy (defined
    by the table/serverpk combination).
    """
    valuedict.update(dict(
        _current=0,
        _addition_pending=1,
        _predecessor_pk=predecessor_pk,
        _camcops_version=req.tabletsession.tablet_version_str
    ))
    req.dbsession.execute(
        update(table)
        .where(table.c._pk == serverpk)
        .values(valuedict)
    )


# =============================================================================
# Batch (atomic) upload and preserving
# =============================================================================

def get_batch_details_start_if_needed(req: CamcopsRequest) \
        -> Tuple[Optional[Pendulum], Optional[bool]]:
    """
    Gets a (upload_batch_utc, currently_preserving) tuple.

    upload_batch_utc: the batchtime; UTC date/time of the current upload batch.
    currently_preserving: Boolean; whether preservation (shifting to an older
        era) is currently taking place.

    SIDE EFFECT: if the username is different from the username that started
    a previous upload batch for this device, we restart the upload batch (thus
    rolling back previous pending changes).
    """
    query = (
        select([Device.ongoing_upload_batch_utc,
                Device.uploading_user_id,
                Device.currently_preserving])
        .select_from(Device.__table__)
        .where(Device.id == req.tabletsession.device_id)
    )
    row = req.dbsession.execute(query).fetchone()
    if not row:
        return None, None
    upload_batch_utc, uploading_user_id, currently_preserving = row
    if not upload_batch_utc or uploading_user_id != req.user_id:
        # SIDE EFFECT: if the username changes, we restart (and thus roll back
        # previous pending changes)
        start_device_upload_batch(req)
        return req.now_utc, False
    log.debug("get_batch_details_start_if_needed: upload_batch_utc = {!r}",
              upload_batch_utc)
    return upload_batch_utc, currently_preserving


def start_device_upload_batch(req: CamcopsRequest) -> None:
    """
    Starts an upload batch for a device.
    """
    rollback_all(req)
    req.dbsession.execute(
        update(Device.__table__)
            .where(Device.id == req.tabletsession.device_id)
            .values(last_upload_batch_utc=req.now_utc,
                    ongoing_upload_batch_utc=req.now_utc,
                    uploading_user_id=req.tabletsession.user_id)
    )


def end_device_upload_batch(req: CamcopsRequest,
                            batchtime: Pendulum,
                            preserving: bool) -> None:
    """
    Ends an upload batch, committing all changes made thus far.
    """
    commit_all(req, batchtime, preserving)
    req.dbsession.execute(
        update(Device.__table__)
            .where(Device.id == req.tabletsession.device_id)
            .values(ongoing_upload_batch_utc=None,
                    uploading_user_id=None,
                    currently_preserving=0)
    )


def start_preserving(req: CamcopsRequest) -> None:
    """
    Starts preservation (the process of moving records from the NOW era to
    an older era, so they can be removed safely from the tablet).
    """
    req.dbsession.execute(
        update(Device.__table__)
            .where(Device.id == req.tabletsession.device_id)
            .values(currently_preserving=1)
    )


def mark_table_dirty(req: CamcopsRequest, table: Table) -> None:
    """
    Marks a table as having been modified during the current upload.
    """
    dbsession = req.dbsession
    ts = req.tabletsession
    exists = exists_in_table(
        dbsession,
        DirtyTable.__table__,
        DirtyTable.device_id == ts.device_id,
        DirtyTable.tablename == table.name
    )
    if not exists:
        dbsession.execute(
            DirtyTable.__table__.insert().values(
                device_id=ts.device_id,
                tablename=table.name
            )
        )


def get_dirty_tables(req: CamcopsRequest) -> List[Table]:
    """
    Returns tables marked as dirty for this device.
    """
    query = select([DirtyTable.tablename])\
        .where(DirtyTable.device_id == req.tabletsession.device_id)
    tablenames = fetch_all_first_values(req.dbsession, query)
    return [CLIENT_TABLE_MAP[tn] for tn in tablenames]


def flag_deleted(req: CamcopsRequest, table: Table,
                 pklist: Iterable[int]) -> None:
    """
    Marks record(s) as deleted, specified by a list of server PKs.
    """
    mark_table_dirty(req, table)
    req.dbsession.execute(
        update(table)
            .where(table.c._pk.in_(pklist))
            .values(_removal_pending=1,
                    _successor_pk=None)
    )


def flag_all_records_deleted(req: CamcopsRequest, table: Table) -> None:
    """
    Marks all records in a table as deleted (that are current and in the
    current era).
    """
    mark_table_dirty(req, table)
    req.dbsession.execute(
        update(table)
            .where(table.c._device_id == req.tabletsession.device_id)
            .where(table.c._current)
            .where(table.c._era == ERA_NOW)
            .values(_removal_pending=1,
                    _successor_pk=None)
    )


def flag_deleted_where_clientpk_not(req: CamcopsRequest,
                                    table: Table,
                                    clientpk_name: str,
                                    clientpk_values: Sequence[Any]) -> None:
    """
    Marks for deletion all current/current-era records for a device, defined
    by a list of client-side PK values.
    """
    mark_table_dirty(req, table)
    req.dbsession.execute(
        update(table)
            .where(table.c._device_id == req.tabletsession.device_id)
            .where(table.c._current)
            .where(table.c._era == ERA_NOW)
            .where(table.c[clientpk_name].notin_(clientpk_values))
            .values(_removal_pending=1,
                    _successor_pk=None)
    )


def flag_modified(req: CamcopsRequest,
                  table: Table,
                  pk: int,
                  successor_pk: int) -> None:
    """
    Marks a record as old, storing its successor's details.
    """
    mark_table_dirty(req, table)
    req.dbsession.execute(
        update(table)
            .where(table.c._pk == pk)
            .values(_removal_pending=1,
                    _successor_pk=successor_pk)
    )


def flag_record_for_preservation(req: CamcopsRequest,
                                 table: Table,
                                 pk: int) -> None:
    """
    Marks a record for preservation (moving off the tablet, changing its
    era details).
    """
    req.dbsession.execute(
        update(table)
            .where(table.c._pk == pk)
            .values(_move_off_tablet=1)
    )


def commit_all(req: CamcopsRequest,
               batchtime: Pendulum,
               preserving: bool) -> None:
    """
    Commits additions, removals, and preservations for all tables.
    """
    tables = get_dirty_tables(req)
    auditsegments = []
    for table in tables:
        n_added, n_removed, n_preserved = commit_table(
            req, batchtime, preserving, table, clear_dirty=False)
        auditsegments.append(
            "{tablename} ({n_added},{n_removed},{n_preserved})".format(
                tablename=table.name,
                n_added=n_added,
                n_removed=n_removed,
                n_preserved=n_preserved,
            )
        )
    clear_dirty_tables(req)
    details = "Upload [table (n_added,n_removed,n_preserved)]: {}".format(
        ", ".join(auditsegments)
    )
    audit(req, details)


def commit_table(req: CamcopsRequest,
                 batchtime: Pendulum,
                 preserving: bool,
                 table: Table,
                 clear_dirty: bool = True) -> Tuple[int, int, int]:
    """
    Commits additions, removals, and preservations for one table.
    """
    user_id = req.user_id
    device_id = req.tabletsession.device_id
    exacttime = req.now

    # Additions
    addition_rp = req.dbsession.execute(
        update(table)
            .where(table.c._device_id == device_id)
            .where(table.c._addition_pending)
            .values(_current=1,
                    _addition_pending=0,
                    _adding_user_id=user_id,
                    _when_added_exact=exacttime,
                    _when_added_batch_utc=batchtime)
    )  # type: ResultProxy
    n_added = addition_rp.rowcount

    # Removals
    removal_rp = req.dbsession.execute(
        update(table)
            .where(table.c._device_id == device_id)
            .where(table.c._removal_pending)
            .values(_current=0,
                    _removal_pending=0,
                    _removing_user_id=user_id,
                    _when_removed_exact=exacttime,
                    _when_removed_batch_utc=batchtime)
    )  # type: ResultProxy
    n_removed = removal_rp.rowcount

    # Preservation
    new_era = format_datetime(batchtime, DateFormat.ERA)
    if preserving:
        # Preserve all relevant records
        preserve_rp = req.dbsession.execute(
            update(table)
                .where(table.c._device_id == device_id)
                .where(table.c._era == ERA_NOW)
                .values(_era=new_era,
                        _preserving_user_id=user_id,
                        _move_off_tablet=0)
        )  # type: ResultProxy
        n_preserved = preserve_rp.rowcount

        # Also preserve/finalize any corresponding special notes (2015-02-01)
        req.dbsession.execute(
            update(SpecialNote.__table__)
                .where(SpecialNote.basetable == table.name)
                .where(SpecialNote.device_id == device_id)
                .where(SpecialNote.era == ERA_NOW)
                .values(_era=new_era)
        )

    else:
        # Preserve any individual records
        preserve_rp = req.dbsession.execute(
            update(table)
                .where(table.c._device_id == device_id)
                .where(table.c._move_off_tablet)
                .values(_era=new_era,
                        _preserving_user_id=user_id,
                        _move_off_tablet=0)
        )  # type: ResultProxy
        n_preserved = preserve_rp.rowcount

        # Also preserve/finalize any corresponding special notes (2015-02-01)
        req.dbsession.execute(
            update(SpecialNote.__table__)
                .where(SpecialNote.basetable == table.name)
                .where(SpecialNote.device_id == device_id)
                .where(SpecialNote.era == ERA_NOW)
                .where(exists().select_from(table)
                       .where(table.c.id == SpecialNote.task_id)
                       .where(table.c._device_id == SpecialNote.device_id)
                       .where(table.c._era == new_era))
                .values(_era=new_era)
        )

    # Remove individually from list of dirty tables?
    if clear_dirty:
        req.dbsession.execute(
            DirtyTable.__table__.delete()
                .where(DirtyTable.device_id == device_id)
                .where(DirtyTable.tablename == table.name)
        )
        # ... otherwise a call to clear_dirty_tables() must be made.

    return n_added, n_removed, n_preserved


def rollback_all(req: CamcopsRequest) -> None:
    """
    Rolls back all pending changes for a device.
    """
    tables = get_dirty_tables(req)
    for table in tables:
        rollback_table(req, table)
    clear_dirty_tables(req)


def rollback_table(req: CamcopsRequest, table: Table) -> None:
    """
    Rolls back changes for an individual table for a device.
    """
    device_id = req.tabletsession.device_id
    # Pending additions
    req.dbsession.execute(
        table.delete()
            .where(table.c._device_id == device_id)
            .where(table.c._addition_pending)
    )
    # Pending deletions
    req.dbsession.execute(
        update(table)
            .where(table.c._device_id == device_id)
            .where(table.c._removal_pending)
            .values(_removal_pending=0,
                    _when_removed_exact=None,
                    _when_removed_batch_utc=None,
                    _removing_user_id=None,
                    _successor_pk=None)
    )
    # Record-specific preservation (set by flag_record_for_preservation())
    req.dbsession.execute(
        update(table)
            .where(table.c._device_id == device_id)
            .values(_move_off_tablet=0)
    )


def clear_dirty_tables(req: CamcopsRequest) -> None:
    """
    Clears the dirty-table list for a device.
    """
    req.dbsession.execute(
        DirtyTable.__table__.delete()
            .where(DirtyTable.device_id == req.tabletsession.device_id)
    )


# =============================================================================
# Audit functions
# =============================================================================

def audit(req: CamcopsRequest,
          details: str,
          patient_server_pk: int = None,
          tablename: str = None,
          server_pk: int = None) -> None:
    """
    Audit something.
    """
    # Add parameters and pass on:
    cc_audit.audit(
        details=details,
        patient_server_pk=patient_server_pk,
        table=tablename,
        server_pk=server_pk,
        device_id=req.tabletsession.device_id,  # added
        remote_addr=req.remote_addr,  # added
        user_id=req.user_id,  # added
        from_console=False,  # added
        from_dbclient=True  # added
    )


# =============================================================================
# Action processors: allowed to any user
# =============================================================================
# If they return None, the framework uses the operation name as the reply in
# the success message. Not returning anything is the same as returning None.
# Authentication is performed in advance of these.

def check_device_registered(req: CamcopsRequest) -> None:
    """
    Check that a device is registered, or raise UserErrorException.
    """
    req.tabletsession.ensure_device_registered()


# =============================================================================
# Action processors that require REGISTRATION privilege
# =============================================================================

# ***
def register(sm: TabletSession) -> Dict:
    """Register a device with the server."""
    device_friendly_name = get_post_var(sm.form, "devicefriendlyname",
                                        mandatory=False)

    table = Device.__tablename__
    count = pls.db.fetchvalue(
        "SELECT COUNT(*) FROM {table} WHERE name=?".format(table=table),
        sm.device_name)
    if count > 0:
        # device already registered, but accept re-registration
        query = """
            UPDATE {table}
            SET
                friendly_name=?,
                camcops_version=?,
                registered_by_user_id=?,
                when_registered_utc=?
            WHERE name=?
        """.format(table=table)
        pls.db.db_exec(query,
                       device_friendly_name,
                       sm.tablet_version_str,
                       sm.user_id,
                       pls.NOW_UTC_NO_TZ,
                       sm.device_name)
    else:
        # new registration
        valuedict = {
            "name": sm.device_name,
            "friendly_name": device_friendly_name,
            "camcops_version": sm.tablet_version_str,
            "registered_by_user_id": sm.user_id,
            "when_registered_utc": pls.NOW_UTC_NO_TZ,
        }
        newpk = pls.db.insert_record_by_dict(table, valuedict)
        if newpk is None:
            fail_user_error(INSERT_FAILED)

    sm.reload_device()
    audit(
        sm,
        "register, device_id={}, friendly_name={}".format(
            sm.device_id, device_friendly_name),
        tablename=table
    )
    return get_server_id_info()


# ***
def get_extra_strings(sm: TabletSession) -> Dict:
    """Fetch all local extra strings from the server."""
    fields = ["task", "name", "value"]
    rows = get_all_extra_strings_as_task_name_value_tuples()
    reply = get_select_reply(fields, rows)
    audit(sm, "get_extra_strings")
    return reply


# =============================================================================
# Action processors that require UPLOAD privilege
# =============================================================================

# ***
# noinspection PyUnusedLocal
def check_upload_user_and_device(sm: TabletSession) -> None:
    """Stub function for the operation to check that a user is valid."""
    pass  # don't need to do anything!


# ***
# noinspection PyUnusedLocal
def get_id_info(sm: TabletSession) -> Dict:
    """Fetch server ID information."""
    return get_server_id_info()


# ***
def start_upload(sm: TabletSession) -> None:
    """Begin an upload."""
    start_device_upload_batch(sm)


# ***
def end_upload(sm: TabletSession) -> None:
    """Ends an upload and commits changes."""
    batchtime, preserving = get_batch_details_start_if_needed(sm)
    # ensure it's the same user finishing as starting!
    end_device_upload_batch(sm, batchtime, preserving)


# ***
def upload_table(sm: TabletSession) -> str:
    """Upload a table. Incoming information in the CGI form includes a CSV list
    of fields, a count of the number of records being provided, and a set of
    CGI variables named record0 ... record{nrecords}, each containing a CSV
    list of SQL-encoded values. Typically used for smaller tables, i.e. most
    except for BLOBs."""
    table = get_table_from_req(sm.form, TabletParam.TABLE)
    fields = get_fields_from_post_var(sm.form, TabletParam.FIELDS)
    nrecords = get_post_var(sm.form, TabletParam.NRECORDS, valtype=int)

    nfields = len(fields)
    if nfields < 1:
        fail_user_error("nfields={}: can't be less than 1".format(nfields))
    if nrecords < 0:
        fail_user_error("nrecords={}: can't be less than 0".format(nrecords))

    _, _ = get_batch_details_start_if_needed(sm)
    clientpk_name = fields[0]
    server_uploaded_pks = []
    new_or_updated = 0
    server_active_record_pks = get_server_pks_of_active_records(sm, table)
    mark_table_dirty(sm, table)
    for r in range(nrecords):
        recname = "record{}".format(r)
        values = get_values_from_post_var(sm.form, recname)
        nvalues = len(values)
        if nvalues != nfields:
            errmsg = (
                "Number of fields in field list ({nfields}) doesn't match "
                "number of values in record {r} ({nvalues})".format(
                    nfields=nfields, r=r, nvalues=nvalues)
            )
            log.warning(errmsg)
            log.warning("fields: {0!r}", fields)
            log.warning("values: {0!r}", values)
            fail_user_error(errmsg)
        valuedict = dict(list(zip(fields, values)))
        # CORE: CALLS upload_record_core
        oldserverpk, newserverpk = upload_record_core(sm,
                                                      table,
                                                      clientpk_name,
                                                      valuedict,
                                                      r)
        new_or_updated += 1
        server_uploaded_pks.append(oldserverpk)

    # Now deal with any ABSENT (not in uploaded data set) conditions.
    server_pks_for_deletion = [x for x in server_active_record_pks
                               if x not in server_uploaded_pks]
    flag_deleted(sm, table, server_pks_for_deletion)

    # Special for old tablets:
    if sm.cope_with_old_idnums and table == Patient.__tablename__:
        mark_table_dirty(sm, PatientIdNum.__tablename__)
        for delete_patient_pk in server_pks_for_deletion:
            pls.db.db_exec(
                """
                    UPDATE {idtable} AS i
                    INNER JOIN {patienttable} AS p
                    SET i._removal_pending = 1, i._successor_pk = NULL
                    WHERE i._device_id = p._device_id
                    AND i._era = '{now}'
                    AND i.patient_id = p.id
                    AND p._pk = ?
                """.format(
                    idtable=PatientIdNum.__tablename__,
                    patienttable=Patient.__tablename__,
                    now=ERA_NOW,
                ),
                delete_patient_pk
            )

    # Success
    log.debug("server_active_record_pks: {}", server_active_record_pks)
    log.debug("server_uploaded_pks: {}", server_uploaded_pks)
    log.debug("server_pks_for_deletion: {}", server_pks_for_deletion)
    log.debug("Table {table}, number of missing records (deleted): {d}",
              table=table, d=len(server_pks_for_deletion))
    # Auditing occurs at commit_all.
    log.info("Upload successful; {n} records uploaded to table {t}",
             n=nrecords, t=table)
    return "Table {} upload successful".format(table)


# ***
def upload_record(sm: TabletSession) -> str:
    """Upload an individual record. (Typically used for BLOBs.) Incoming
    CGI information includes a CSV list of fields and a CSV list of values."""
    table = get_table_from_req(sm.form, TabletParam.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, TabletParam.PKNAME)
    valuedict = get_fields_and_values(sm.form, TabletParam.FIELDS, TabletParam.VALUES)
    require_keys(valuedict, [clientpk_name, CLIENT_DATE_FIELD])
    clientpk_value = valuedict[clientpk_name]
    wheredict = {clientpk_name: clientpk_value}

    serverpks = get_server_pks_of_specified_records(sm, table, wheredict)
    if not serverpks:
        # Insert
        insert_record(sm, table, valuedict, None)
        log.info("upload-insert")
        return "UPLOAD-INSERT"
    else:
        # Update
        oldserverpk = serverpks[0]
        client_date_value = valuedict[CLIENT_DATE_FIELD]
        exists = record_identical_by_date(table, oldserverpk,
                                          client_date_value)
        if exists:
            log.info("upload-update: skipping existing record")
        else:
            newserverpk = duplicate_record(sm, table, oldserverpk)
            flag_modified(sm, table, oldserverpk, newserverpk)
            update_new_copy_of_record(sm, table, newserverpk, valuedict,
                                      oldserverpk)
            log.info("upload-update")
        return "UPLOAD-UPDATE"
    # Auditing occurs at commit_all.


# ***
def upload_empty_tables(sm: TabletSession) -> str:
    """The tablet supplies a list of tables that are empty at its end, and we
    will 'wipe' all appropriate tables; this reduces the number of HTTP
    requests."""
    tables = get_tables_from_post_var(sm.form, TabletParam.TABLES)

    _, _ = get_batch_details_start_if_needed(sm)
    for table in tables:
        flag_all_records_deleted(sm, table)
    log.info("upload_empty_tables")
    # Auditing occurs at commit_all.
    return "UPLOAD-EMPTY-TABLES"


# ***
def start_preservation(sm: TabletSession) -> str:
    """Marks this upload batch as one in which all records will be preserved
    (i.e. moved from NOW-era to an older era, so they can be deleted safely
    from the tablet).

    Without this, individual records can still be marked for preservation if
    their MOVE_OFF_TABLET_FIELD field (_move_off_tablet) is set; see
    upload_record and its functions."""
    _, _ = get_batch_details_start_if_needed(sm)
    start_preserving(sm)
    log.info("start_preservation successful")
    # Auditing occurs at commit_all.
    return "STARTPRESERVATION"


# ***
def delete_where_key_not(sm: TabletSession) -> str:
    """Marks records for deletion, for a device/table, where the client PK
    is not in a specified list."""
    table = get_table_from_req(sm.form, TabletParam.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, TabletParam.PKNAME)
    clientpk_values = get_values_from_post_var(sm.form, TabletParam.PKVALUES)

    _, _ = get_batch_details_start_if_needed(sm)
    flag_deleted_where_clientpk_not(sm, table, clientpk_name, clientpk_values)
    # Auditing occurs at commit_all.
    log.info("delete_where_key_not successful; table {} trimmed", table)
    return "Trimmed"


# ***
def which_keys_to_send(sm: TabletSession) -> str:
    """Intended use: "For my device, and a specified table, here are my client-
    side PKs (as a CSV list), and the modification dates for each corresponding
    record (as a CSV list). Please tell me which records have mismatching dates
    on the server, i.e. those that I need to re-upload."

    Used particularly for BLOBs, to reduce traffic, i.e. so we don't have to
    send a lot of BLOBs."""
    table = get_table_from_req(sm.form, TabletParam.TABLE)
    clientpk_name = get_single_field_from_post_var(sm.form, TabletParam.PKNAME)
    clientpk_values = get_values_from_post_var(sm.form, TabletParam.PKVALUES,
                                               mandatory=False)
    client_dates = get_values_from_post_var(sm.form, TabletParam.DATEVALUES,
                                            mandatory=False)

    npkvalues = len(clientpk_values)
    ndatevalues = len(client_dates)
    if npkvalues != ndatevalues:
        fail_user_error(
            "Number of PK values ({npk}) doesn't match number of dates "
            "({nd})".format(npk=npkvalues, nd=ndatevalues))

        _, _ = get_batch_details_start_if_needed(sm)

    # 1. The client sends us all its PKs. So "delete" anything not in that
    #    list.
    flag_deleted_where_clientpk_not(sm, table, clientpk_name, clientpk_values)

    # 2. See which ones are new or updates.
    pks_needed = []
    for i in range(npkvalues):
        clientpkval = clientpk_values[i]
        client_date_value = client_dates[i]
        found, serverpk = record_exists(sm, table, clientpk_name, clientpkval)
        if not found or not record_identical_by_date(table, serverpk,
                                                     client_date_value):
            pks_needed.append(clientpkval)

    # Success
    pk_csv_list = ",".join([str(x) for x in pks_needed if x is not None])
    log.info("which_keys_to_send successful: table {}", table)
    return pk_csv_list


# =============================================================================
# Action maps
# =============================================================================

OPERATIONS_ANYONE = {
    "check_device_registered": check_device_registered,
}
OPERATIONS_REGISTRATION = {
    "register": register,
    "get_extra_strings": get_extra_strings,
}
OPERATIONS_UPLOAD = {
    "check_upload_user_and_device": check_upload_user_and_device,
    "get_id_info": get_id_info,
    "start_upload": start_upload,
    "end_upload": end_upload,
    "upload_table": upload_table,
    "upload_record": upload_record,
    "upload_empty_tables": upload_empty_tables,
    "start_preservation": start_preservation,
    "delete_where_key_not": delete_where_key_not,
    "which_keys_to_send": which_keys_to_send,
}


# =============================================================================
# Client API main functions
# =============================================================================

def main_client_api(req: CamcopsRequest) -> Dict[str, str]:
    """
    Main HTTP processor.

    For success, returns a dictionary to send (will use status '200 OK')
    For failure, raises an exception.
    """
    log.info("CamCOPS database script starting at {}",
             format_datetime(req.now, DateFormat.ISO8601))
    ts = req.tabletsession
    fn = None

    if ts.operation in OPERATIONS_ANYONE:
        fn = OPERATIONS_ANYONE.get(ts.operation)

    if ts.operation in OPERATIONS_REGISTRATION:
        ts.ensure_valid_user_for_device_registration()
        fn = OPERATIONS_REGISTRATION.get(ts.operation)

    if ts.operation in OPERATIONS_UPLOAD:
        ts.ensure_valid_device_and_user_for_uploading()
        fn = OPERATIONS_UPLOAD.get(ts.operation)

    if not fn:
        fail_unsupported_operation(ts.operation)
    result = fn(req)
    if result is None:
        result = {TabletParam.RESULT: ts.operation}
    elif not isinstance(result, dict):
        result = {TabletParam.RESULT: result}
    return result


@view_config(route_name=Routes.CLIENT_API, permission=NO_PERMISSION_REQUIRED)
def client_api(req: CamcopsRequest) -> Response:
    """
    View for client API. All tablet interaction comes through here.
    Wraps main_client_api().
    """
    if req.method != RequestMethod.POST:
        raise HTTPBadRequest("Must use POST method")
        # ... this is for humans to view, so it has a pretty error

    t0 = time.time()  # in seconds

    try:
        resultdict = main_client_api(req)
        resultdict[TabletParam.SUCCESS] = 1
        status = '200 OK'
    except UserErrorException as e:
        log.warning("CLIENT-SIDE SCRIPT ERROR: {}", e)
        resultdict = {
            TabletParam.SUCCESS: 0,
            TabletParam.ERROR: escape_newlines(str(e))
        }
        status = '200 OK'
    except ServerErrorException as e:
        log.error("SERVER-SIDE SCRIPT ERROR: {}", e)
        # rollback? Not sure
        resultdict = {
            TabletParam.SUCCESS: 0,
            TabletParam.ERROR: escape_newlines(str(e))
        }
        status = "503 Database Unavailable: " + str(e)
    except Exception as e:
        # All other exceptions. May include database write failures.
        # Let's return with status '200 OK'; though this seems dumb, it means
        # the tablet user will at least see the message.
        log.exception("Unhandled exception")  # + traceback.format_exc()
        resultdict = {
            TabletParam.SUCCESS: 0,
            TabletParam.ERROR: escape_newlines(exception_description(e))
        }
        status = '200 OK'

    # Add session token information
    ts = req.tabletsession
    resultdict[TabletParam.SESSION_ID] = ts.session_id
    resultdict[TabletParam.SESSION_TOKEN] = ts.session_token

    # Convert dictionary to text in name-value pair format
    text = "".join("{}:{}\n".format(k, v) for k, v in resultdict.items())

    t1 = time.time()
    log.info("Time in script (s): {t}", t=t1 - t0)

    return TextResponse(text, status=status)


# =============================================================================
# Unit tests
# =============================================================================

def database_unit_tests() -> None:
    """Unit tests for database script."""
    # a = (UserErrorException, ServerErrorException)
    u = UserErrorException
    s = ServerErrorException

    print("pls.VALID_TABLE_NAMES: {}".format(pls.VALID_TABLE_NAMES))

    unit_test_ignore("", succeed_generic, "testmsg")
    unit_test_must_raise("", fail_user_error, u, "testmsg")
    unit_test_must_raise("", fail_server_error, s, "testmsg")
    unit_test_must_raise("", fail_unsupported_operation, u, "duffop")
    unit_test_verify("", nvp, "n:v\n", "n", "v")

    # Encoding/decoding tests
    # data = bytearray("hello")
    data = b"hello"
    enc_b64data = base64_64format_encode(data)
    enc_hexdata = hex_xformat_encode(data)
    not_enc_1 = "X'012345'"
    not_enc_2 = "64'aGVsbG8='"
    teststring = """one, two, 3, 4.5, NULL, 'hello "hi
        with linebreak"', 'NULL', 'quote''s here', {b}, {h}, {s1}, {s2}"""
    sql_csv_testdict = {
        teststring.format(
            b=enc_b64data,
            h=enc_hexdata,
            s1=rnc_db.sql_quote_string(not_enc_1),
            s2=rnc_db.sql_quote_string(not_enc_2),
        ): [
            "one",
            "two",
            3,
            4.5,
            None,
            'hello "hi\n        with linebreak"',
            "NULL",
            "quote's here",
            data,
            data,
            not_enc_1,
            not_enc_2,
        ],
        "": [],
    }
    for k, v in sql_csv_testdict.items():
        r = decode_values(k)
        if r != v:
            raise AssertionError(
                "Mismatch! Result: {r!s}\n"
                "Should have been: {v!s}\n"
                "Key was: {k!s}".format(r=r, v=v, k=k))

    # Newline encoding/decodine
    ts2 = "slash \\ newline \n ctrl_r \r special \\n other special \\r " \
          "quote ' doublequote \" "
    if unescape_newlines(escape_newlines(ts2)) != ts2:
        raise AssertionError("Bug in escape_newlines() or unescape_newlines()")

    # more... ?
