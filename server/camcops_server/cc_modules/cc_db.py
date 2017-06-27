#!/usr/bin/env python
# cc_db.py

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

import datetime
import logging
from typing import Any, Iterable, List, Optional, Union, Type, TypeVar

import cardinal_pythonlib.rnc_db as rnc_db
from cardinal_pythonlib.rnc_db import (
    DatabaseSupporter,
    FIELDSPEC_TYPE,
    FIELDSPECLIST_TYPE,
)

from .cc_constants import (
    DATEFORMAT,
    ERA_NOW,
    ISO8601_STRING_LENGTH,
    NUMBER_OF_IDNUMS,
    STANDARD_TASK_FIELDSPECS,
)
from . import cc_dt
# from .cc_logger import log
from .cc_pls import pls

log = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# Field types
# =============================================================================

# Keys in SQLTYPE are the valid values for the "cctype" field.
# Values are the corresponding SQL type.
class SQLTYPE(object):
    # Boolean
    BOOL = "BOOLEAN"

    # Date/time
    DATETIME = "DATETIME"
    ISO8601 = "VARCHAR({})".format(ISO8601_STRING_LENGTH)

    # Numeric
    BIGINT = "BIGINT"  # MySQL: -9223372036854775808 to 9223372036854775807
    BIGINT_UNSIGNED = "BIGINT UNSIGNED"  # MySQL: 0 to 18446744073709551615
    INT = "INT"  # MySQL: -2147483648 to 2147483647
    INT_UNSIGNED = "INT UNSIGNED"  # MySQL: 0 to 4294967295

    # Real
    FLOAT = "REAL"

    # BLOB
    LONGBLOB = "LONGBLOB"

    # Textual
    AUDITSOURCE = "VARCHAR(20)"
    CHAR = "VARCHAR(1)"
    DEVICE = "VARCHAR(255)"
    FILTER_TEXT = "VARCHAR(255)"
    HASHEDPASSWORD = "VARCHAR(255)"
    HOSTNAME = "VARCHAR(255)"
    IDDESCRIPTOR = "VARCHAR(255)"
    IPADDRESS = "VARCHAR(45)"  # http://stackoverflow.com/questions/166132
    LONGTEXT = "LONGTEXT"  # http://stackoverflow.com/questions/6766781
    PATIENTNAME = "VARCHAR(255)"
    SENDINGFORMAT = "VARCHAR(50)"
    SEX = "VARCHAR(1)"
    TABLENAME = "VARCHAR(255)"
    TEXT = "TEXT"
    TIME = "TIME"  # v2
    TOKEN = "VARCHAR(50)"
    USERNAME = "VARCHAR(255)"
    STOREDVARNAME = "VARCHAR(255)"  # probably overkill!
    STOREDVARTYPE = "VARCHAR(255)"  # probably overkill!
    # If you insert something too long into a VARCHAR, it just gets truncated.

    SEMANTICVERSIONTYPE = "VARCHAR(147)"
    # ... https://github.com/mojombo/semver/issues/79


# =============================================================================
# Field creation assistance
# =============================================================================

# noinspection PyShadowingBuiltins
def repeat_fieldspec(prefix: str,
                     start: int,
                     end: int,
                     cctype: str = "INT",
                     comment_fmt: str = None,
                     comment_strings: List[str] = None,
                     min: int = None,  # TODO: float?
                     max: int = None,  # TODO: float?
                     pv: List[Any] = None) -> FIELDSPECLIST_TYPE:
    """Return a list of field specifications for numerically sequenced
    fields.

    Args:
        prefix: Fieldname will be prefix + str(n), where n defined as below.
        start: Start of range.
        end: End of range. Thus:
            ... i will range from 0 to (end - start) inclusive
            ... n will range from start to end inclusive
        cctype: CamCOPS type of field (must be a key in SQLTYPE).
        comment_fmt: Format string defining field comments. Substitutable
            values are:
                {n}     field number (from range)
                {s}     comment_strings[i], or "" if out of range
        comment_strings: see comment_fmt
        min: minimum permitted value, or None
        max: maximum permitted value, or None
        pv: list of permitted values, or None
    """
    comment_strings = comment_strings or []
    fieldspecs = []
    for n in range(start, end + 1):
        i = n - start
        d = dict(
            name=prefix + str(n),
            cctype=cctype
        )
        if comment_fmt:
            s = ""
            if 0 <= i < len(comment_strings):
                s = comment_strings[i] or ""
            d["comment"] = comment_fmt.format(n=n, s=s)
        if min is not None:
            d["min"] = min
        if max is not None:
            d["max"] = max
        if pv is not None:
            d["pv"] = pv
        fieldspecs.append(d)
    return fieldspecs


def repeat_fieldname(prefix: str, start: int, end: int) -> List[str]:
    """Return a list of fieldnames for numerically sequenced fields."""
    fd = []
    for i in range(start, end + 1):  # iterate from start to end inclusive
        fd.append(prefix + str(i))
    return fd


# =============================================================================
# Add sqltype field to fieldspecs defined by cctype
# =============================================================================

def ensure_valid_cctype(cctype: str) -> None:
    """Raises KeyError if cctype is not a valid key to SQLTYPE."""
    assert hasattr(SQLTYPE, cctype)


def cctype_is_string(cctype: str) -> bool:
    s = getattr(SQLTYPE, cctype).upper()
    return s[:7] == "VARCHAR" or s == "TEXT" or s == "LONGTEXT"


def cctype_is_date(cctype: str) -> bool:
    return cctype in ["DATETIME", "ISO8601"]


def add_sqltype_to_fieldspec_in_place(fieldspec: FIELDSPEC_TYPE) -> None:
    """Add sqltype field to fieldspec defined by cctype, where cctype is one of
    the keys to SQLTYPE. Returns the new fieldspec.
    """
    cctype = fieldspec["cctype"]  # raise KeyError if missing
    fieldspec["sqltype"] = getattr(SQLTYPE, cctype)  # raise AttributeError if invalid  # noqa


def add_sqltype_to_fieldspeclist_in_place(fieldspeclist: FIELDSPECLIST_TYPE) \
        -> None:
    """Add sqltype field to fieldspeclist having fieldspecs defined by
    cctype, where cctype is one of the keys to SQLTYPE.
    """
    for item in fieldspeclist:
        add_sqltype_to_fieldspec_in_place(item)


# =============================================================================
# Database routines.
# =============================================================================

def set_db_to_utf8(db: DatabaseSupporter) -> None:
    db.db_exec_literal("ALTER DATABASE DEFAULT CHARACTER SET utf8 "
                       "DEFAULT COLLATE utf8_general_ci")


def get_current_server_pk_by_client_info(table: str,
                                         device_id: int,
                                         clientpk: int,
                                         era: str):
    """Looks up the current server's PK given a device/clientpk/era triplet."""
    row = pls.db.fetchone(
        (
            "SELECT _pk FROM " + table +
            " WHERE _current AND _device_id=? AND id=? AND _era=?"
        ),
        device_id,
        clientpk,
        era
    )
    if row is None:
        return None
    return row[0]


def get_contemporaneous_server_pk_by_client_info(
        table: str,
        device_id: int,
        clientpk: int,
        era: str,
        referrer_added_utc: datetime.datetime,
        referrer_removed_utc: datetime.datetime) -> Optional[int]:
    """Looks up a contemporaneous (i.e. potentially old) server PK given
    client-side details."""
    sql = ("SELECT _pk FROM " + table +
           " WHERE id=? AND _device_id=? AND _era=?"
           " AND _when_added_batch_utc <= ? AND ")
    args = [
        clientpk,
        device_id,
        era,
        referrer_added_utc
    ]
    if referrer_removed_utc is not None:
        sql += "_when_removed_batch_utc >= ?"
        args.append(referrer_removed_utc)
    else:
        sql += "_when_removed_batch_utc IS NULL"
    row = pls.db.fetchone(sql, *args)
    if row is None:
        return None
    return row[0]


def get_all_current_server_pks(table: str) -> List[int]:
    """Get all server PKs from the table for current records."""
    return pls.db.fetchallfirstvalues(
        "SELECT _pk FROM " + table + " WHERE _current")


def get_contemporaneous_matching_field_pks_by_fk(
        table: str,
        pkname: str,
        fk_fieldname: str,
        fk_value: Any,
        device_id: int,
        era: str,
        referrer_added_utc: datetime.datetime,
        referrer_removed_utc: datetime.datetime,
        count_only: bool = False) -> Union[int, List[int]]:
    """Look up contemporaneous (i.e. potentially old) records using a
    foreign key and client-side details.
    If count_only is True, return the count instead."""
    if count_only:
        select = "SELECT COUNT(*)"
    else:
        select = "SELECT {}".format(pls.db.delimit(pkname))
    sql = """
        {select}
        FROM {table}
        WHERE
            {fkfield} = ?
            AND _device_id = ?
            AND _era = ?
            AND _when_added_batch_utc <= ?
            AND """.format(
        select=select,
        table=pls.db.delimit(table),
        fkfield=pls.db.delimit(fk_fieldname),
    )
    # _when_added_batch_utc condition:
    #       if it was added later, it wasn't contemporaneous
    # _when_removed_batch_utc IS NULL condition:
    #       if it hasn't been removed, it might still be valid
    args = [
        fk_value,
        device_id,
        era,
        referrer_added_utc
    ]
    if referrer_removed_utc is not None:
        sql += "_when_removed_batch_utc >= ?"
        # ... it might also be valid as long as it wasn't removed before the
        #     current record
        #     NB valid if it was removed AT THE SAME TIME as the current record
        args.append(referrer_removed_utc)
    else:
        sql += "_when_removed_batch_utc IS NULL"
    if count_only:
        return pls.db.fetchvalue(sql, *args)
    else:
        return pls.db.fetchallfirstvalues(sql, *args)


def get_contemporaneous_matching_ancillary_objects_by_fk(
        cls: Type[T],
        fk_value: Any,
        device_id: int,
        era: str,
        referrer_added_utc: datetime.datetime,
        referrer_removed_utc: datetime.datetime) -> List[T]:
    fieldlist = cls.get_fieldnames()
    sql = """
        SELECT {fields}
        FROM {table}
        WHERE {fkfield} = ?
        AND _device_id = ?
        AND _era = ?
        AND _when_added_batch_utc <= ?
        AND
    """.format(
        fields=",".join([pls.db.delimit(x) for x in fieldlist]),
        table=pls.db.delimit(cls.tablename),
        fkfield=pls.db.delimit(cls.fkname),
    )
    args = [
        fk_value,
        device_id,
        era,
        referrer_added_utc
    ]
    # As above:
    if referrer_removed_utc is not None:
        sql += "_when_removed_batch_utc >= ?"
        args.append(referrer_removed_utc)
    else:
        sql += "_when_removed_batch_utc IS NULL"
    rows = pls.db.fetchall(sql, *args)
    objects = []
    for row in rows:
        objects.append(rnc_db.create_object_from_list(cls, fieldlist, row))
    return objects


def get_server_pks_of_record_group(table: str,
                                   pkname: str,
                                   keyfieldname: str,
                                   keyvalue: Any,
                                   device_id: int,
                                   era: str) -> List[int]:
    """Returns server PKs of all records that represent versions of a specified
    one."""
    query = """
        SELECT {pkname}
        FROM {table}
        WHERE {keyfieldname} = ?
            AND _device_id = ?
            AND _era = ?
    """.format(
        pkname=pkname,
        table=table,
        keyfieldname=keyfieldname,
    )
    args = [keyvalue, device_id, era]
    return pls.db.fetchallfirstvalues(query, *args)


def delete_from_table_by_pklist(tablename: str,
                                pkname: str,
                                pklist: Iterable[int]) -> None:
    query = "DELETE FROM {} WHERE {} = ?".format(tablename, pkname)
    for pk in pklist:
        pls.db.db_exec(query, pk)


# noinspection PyProtectedMember
def manually_erase_record_object_and_save(obj: T,
                                          table: str,
                                          fields: Iterable[str],
                                          user_id: int) -> None:
    """Manually erases a standard record and marks it so erased.
    The object remains _current, as a placeholder, but its contents are wiped.
    WRITES TO DATABASE."""
    if obj._pk is None or obj._era == ERA_NOW:
        return
    standard_task_fields = [x["name"] for x in STANDARD_TASK_FIELDSPECS]
    erasure_fields = [
        x
        for x in fields
        if x not in standard_task_fields
    ]
    rnc_db.blank_object(obj, erasure_fields)
    obj._current = False
    obj._manually_erased = True
    obj._manually_erased_at = cc_dt.format_datetime(pls.NOW_LOCAL_TZ,
                                                    DATEFORMAT.ISO8601)
    obj._manually_erasing_user_id = user_id
    pls.db.update_object_in_db(obj, table, fields)


def delete_subtable_records_common(tablename: str,
                                   pkname: str,
                                   fkname: str,
                                   fkvalue: Any,
                                   device_id: int,
                                   era: str) -> None:
    """Used to delete records entirely from the database."""
    pklist = get_server_pks_of_record_group(
        tablename, pkname, fkname, fkvalue, device_id, era)
    delete_from_table_by_pklist(tablename, pkname, pklist)


def erase_subtable_records_common(itemclass: Type[T],
                                  tablename: str,
                                  fieldnames: Iterable[str],
                                  pkname: str,
                                  fkname: str,
                                  fkvalue: Any,
                                  device_id: int,
                                  era: str,
                                  user_id: int) -> None:
    """Used to wipe objects and re-save them."""
    pklist = get_server_pks_of_record_group(
        tablename, pkname, fkname, fkvalue, device_id, era)
    items = pls.db.fetch_all_objects_from_db_by_pklist(
        itemclass, tablename, fieldnames, pklist, True)
    for i in items:
        manually_erase_record_object_and_save(i, tablename, fieldnames,
                                              user_id)


def forcibly_preserve_client_table(table: str,
                                   device_id: int,
                                   user_id: int) -> None:
    """WRITES TO DATABASE."""
    new_era = cc_dt.format_datetime(pls.NOW_UTC_NO_TZ, DATEFORMAT.ERA)
    query = """
        UPDATE  {table}
        SET     _era = ?,
                _forcibly_preserved = 1,
                _preserving_user_id = ?
        WHERE   _device_id = ?
        AND     _era = '{now}'
    """.format(table=table, now=ERA_NOW)
    args = [
        new_era,
        user_id,
        device_id
    ]
    pls.db.db_exec(query, *args)


# =============================================================================
# More SQL
# =============================================================================

def mysql_select_utc_date_field_from_iso8601_field(fieldname: str) -> str:
    """SQL expression: converts ISO-8601 field into UTC DATETIME."""
    return ("CONVERT_TZ(STR_TO_DATE(LEFT({0}, 23), '%Y-%m-%dT%H:%i:%s.%f'), "
            "RIGHT({0},6), '+00:00')".format(fieldname))
    # 1. STR_TO_DATE(), with the leftmost 23 characters,
    #    giving microsecond precision, but not correct for timezone
    # 2. CONVERT_TZ(), converting from the timezone info in the rightmost 6
    #    characters to UTC (though losing fractional seconds)

# And how are datetime values sent to the database?
#       https://code.google.com/p/pyodbc/wiki/DataTypes
# I'm using pyodbc 2.1.7 (for Python 2), so Python datetime values are
# converted to/from SQL TIMESTAMP values... and TIMESTAMP is UTC:
#       https://dev.mysql.com/doc/refman/5.5/en/datetime.html
# so using the code above to convert everything to UTC should be fine.


def mysql_select_local_date_field_from_iso8601_field(fieldname: str) -> str:
    """SQL expression: converts ISO-8601 field into local DATETIME."""
    return ("STR_TO_DATE(LEFT({0}, 23), '%Y-%m-%dT%H:%i:%s.%f')".format(
        fieldname))
    # 1. STR_TO_DATE(), with the leftmost 23 characters,
    #    giving microsecond precision, but not correct for timezone


def create_or_update_table(tablename: str,
                           fieldspecs_with_cctype: FIELDSPECLIST_TYPE,
                           drop_superfluous_columns: bool = False) -> None:
    """Adds the sqltype to a set of fieldspecs using cctype, then creates the
    table."""
    add_sqltype_to_fieldspeclist_in_place(fieldspecs_with_cctype)
    # if False:
    #     for fs in fieldspecs_with_cctype:
    #         if "indexed" in fs:
    #             log.critical(fs)
    pls.db.create_or_update_table(
        tablename, fieldspecs_with_cctype,
        drop_superfluous_columns=drop_superfluous_columns,
        dynamic=True,
        compressed=False)
    if not pls.db.mysql_table_using_barracuda(tablename):
        pls.db.mysql_convert_table_to_barracuda(tablename, compressed=False)


def create_standard_table(tablename: str,
                          fieldspeclist: FIELDSPECLIST_TYPE,
                          drop_superfluous_columns: bool = False) -> None:
    """Create a table and its associated current view."""
    create_or_update_table(tablename, fieldspeclist,
                           drop_superfluous_columns=drop_superfluous_columns)
    create_simple_current_view(tablename)


def create_standard_task_table(tablename: str,
                               fieldspeclist: FIELDSPECLIST_TYPE,
                               anonymous: bool = False,
                               drop_superfluous_columns: bool = False) -> None:
    """Create a task's table and its associated current view."""
    create_standard_table(tablename, fieldspeclist,
                          drop_superfluous_columns=drop_superfluous_columns)
    if anonymous:
        create_simple_current_view(tablename)
    else:
        create_task_current_view(tablename)


def create_standard_ancillary_table(
        tablename: str,
        fieldspeclist: FIELDSPECLIST_TYPE,
        ancillaryfk: str,
        tasktable: str,
        drop_superfluous_columns: bool = False) -> None:
    """Create an ancillary table and its associated current view."""
    create_standard_table(tablename, fieldspeclist,
                          drop_superfluous_columns=drop_superfluous_columns)
    create_ancillary_current_view(tablename, ancillaryfk, tasktable)


def create_simple_current_view(table: str) -> None:
    """Create a current view for a table."""
    sql = """
        CREATE OR REPLACE VIEW {0}_current AS
        SELECT *
        FROM {0}
        WHERE _current
    """.format(table)
    pls.db.db_exec_literal(sql)


def create_task_current_view(tasktable: str) -> None:
    """Create tasks views that link to patient information (either giving the
    FK to the patient table, or bringing across more detail for convenience).

    Only to be used for non-anonymous tasks.
    """

    # Simple view
    sql = """
        CREATE OR REPLACE VIEW {0}_current AS
        SELECT {0}.*, patient._pk AS _patient_server_pk
        FROM {0}
        INNER JOIN patient
            ON {0}.patient_id = patient.id
            AND {0}._device_id = patient._device_id
            AND {0}._era = patient._era
        WHERE
            {0}._current
            AND patient._current
    """.format(tasktable)
    pls.db.db_exec_literal(sql)

    # View joined to patient info
    sql = """
        CREATE OR REPLACE VIEW {0}_current_withpt AS
        SELECT
            {0}_current.*
            , patient_current.forename AS patient_forename
            , patient_current.surname AS patient_surname
            , patient_current.dob AS patient_dob
            , patient_current.sex AS patient_sex
    """.format(tasktable)
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        sql += """
            , patient_current.idnum{0} AS patient_idnum{0}
        """.format(n)
    sql += """
            , patient_current.address AS patient_address
            , patient_current.gp AS patient_gp
            , patient_current.other AS patient_other
        FROM {0}_current
        INNER JOIN patient_current
            ON {0}_current._patient_server_pk = patient_current._pk
    """.format(tasktable)
    pls.db.db_exec_literal(sql)
    # MySQL can't add comments to view columns.


def create_ancillary_current_view(ancillarytable: str,
                                  ancillaryfk: str,
                                  tasktable: str) -> None:
    """Create an ancillary view that links to its task's table."""
    sql = """
        CREATE OR REPLACE VIEW {1}_current AS
        SELECT {1}.*, {0}._pk AS _task_server_pk
        FROM {1}
        INNER JOIN {0}
            ON {1}.{2} = {0}.id
            AND {1}._device_id = {0}._device_id
            AND {1}._era = {0}._era
        WHERE
            {1}._current
            AND {0}._current
    """.format(tasktable, ancillarytable, ancillaryfk)
    pls.db.db_exec_literal(sql)


def create_summary_table_current_view_withpt(
        summarytable: str,
        basetable: str,
        summarytable_fkfieldname: str) -> None:
    """Create a current view for the summary table, in versions with simple
    (FK) or more detailed patient information.

    Only to be used for non-anonymous tasks.
    """
    # Current view with patient ID
    sql = """
        CREATE OR REPLACE VIEW {0}_current AS
        SELECT {0}.*, patient._pk AS _patient_server_pk
        FROM {0}
        INNER JOIN {1}
            ON {0}.{2} = {1}._pk
        INNER JOIN patient
            ON {1}.patient_id = patient.id
            AND {1}._device_id = patient._device_id
            AND {1}._era = patient._era
        WHERE
            {1}._current
            AND patient._current
    """.format(summarytable, basetable, summarytable_fkfieldname)
    pls.db.db_exec_literal(sql)

    # Current view with patient info
    sql = """
        CREATE OR REPLACE VIEW {0}_current_withpt AS
        SELECT
            {0}_current.*
            , patient_current.forename AS patient_forename
            , patient_current.surname AS patient_surname
            , patient_current.dob AS patient_dob
            , patient_current.sex AS patient_sex
    """.format(summarytable)
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        sql += """
            , patient_current.idnum{0} AS patient_idnum{0}
        """.format(n)
    sql += """
            , patient_current.address AS patient_address
            , patient_current.gp AS patient_gp
            , patient_current.other AS patient_other
        FROM {0}_current
        INNER JOIN patient_current
            ON {0}_current._patient_server_pk = patient_current._pk
    """.format(summarytable)
    pls.db.db_exec_literal(sql)
