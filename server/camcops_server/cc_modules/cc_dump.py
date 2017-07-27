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

import configparser
import io
import subprocess
from typing import Dict, List, Optional, Sequence, Tuple
import zipfile

from .cc_audit import audit
from .cc_blob import Blob
from .cc_constants import CONFIG_FILE_MAIN_SECTION
from .cc_patient import Patient
from .cc_pls import pls
from .cc_task import Task
from .cc_unittest import unit_test_ignore

# =============================================================================
# Constants
# =============================================================================

NOTHING_VALID_SPECIFIED = "No valid tables or views specified"
POSSIBLE_SYSTEM_TABLES = [  # always exist
    Blob.TABLENAME,
    Patient.TABLENAME,
]
POSSIBLE_SYSTEM_VIEWS = [
]


# =============================================================================
# Ancillary functions
# =============================================================================

def get_possible_task_tables_views() -> Tuple[List[str], List[str]]:
    """Returns (tables, views) pertaining to tasks."""
    tables = []
    views = []
    for cls in Task.all_subclasses(sort_tablename=True):
        (tasktables, taskviews) = cls.get_all_table_and_view_names()
        tables.extend(tasktables)
        views.extend(taskviews)
    return tables, views


def get_permitted_tables_and_views() -> List[str]:
    """Returns list of tables/views suitable for downloading."""
    tables_that_exist = pls.db.get_all_table_names()
    (tasktables, taskviews) = get_possible_task_tables_views()
    return list(set(tables_that_exist).intersection(POSSIBLE_SYSTEM_TABLES +
                                                    POSSIBLE_SYSTEM_VIEWS +
                                                    tasktables +
                                                    taskviews))


def get_permitted_tables_views_sorted_labelled() -> List[Dict[str, bool]]:
    """Returns sorted list of tables/views suitable for downloading.

    Each list element is a dictionary with attributes:
        name: name of table/view
        view: Boolean
    """
    (tasktables, taskviews) = get_possible_task_tables_views()
    tables_that_exist = pls.db.get_all_table_names()
    valid_system_tables = list(set(tables_that_exist).intersection(
        POSSIBLE_SYSTEM_TABLES))
    # VIEWS DISABLED FOR NOW ***
    valid_system_views = []  # type: List[str]
    # valid_system_views = list(set(tables_that_exist).intersection(
    #     POSSIBLE_SYSTEM_VIEWS))
    valid_tasktables = list(set(tables_that_exist).intersection(tasktables))
    valid_taskviews = []  # type: List[str]
    # valid_taskviews = list(set(tables_that_exist).intersection(taskviews))

    system_list = (
        [{"view": False, "name": x} for x in valid_system_tables] +
        [{"view": True, "name": x} for x in valid_system_views]
    )
    task_list = (
        [{"view": False, "name": x} for x in valid_tasktables] +
        [{"view": True, "name": x} for x in valid_taskviews]
    )
    return (
        sorted(system_list, key=lambda k: k["name"]) +
        sorted(task_list, key=lambda k: k["name"])
    )
    # ... makes system tables be at one end of the list for visibility


def validate_table_list(tables: Sequence[str]) -> List[str]:
    """Returns the list supplied, minus any invalid tables/views."""
    return sorted(list(
        set(tables).intersection(get_permitted_tables_and_views())
    ))


def validate_single_table(table: str) -> Optional[str]:
    """Returns the table name supplied, or None if it's not valid."""
    tl = list({table}.intersection(get_permitted_tables_and_views()))
    if not tl:
        return None
    return tl[0]


# =============================================================================
# Providing user with database dump output in various formats
# =============================================================================

def get_database_dump_as_sql(tables: List[str] = None) -> str:
    """Returns a database dump of all the tables requested, in SQL format."""
    tables = tables or []
    tables = validate_table_list(tables)
    if not tables:
        return NOTHING_VALID_SPECIFIED

    # We'll need to re-fetch the database password,
    # since we don't store it (for security reasons).
    config = configparser.ConfigParser()
    config.read(pls.CAMCOPS_CONFIG_FILE)

    # -------------------------------------------------------------------------
    # SECURITY: from this point onwards, consider the possibility of a
    # password leaking via a debugging exception handler
    # -------------------------------------------------------------------------
    try:
        db_password = config.get(CONFIG_FILE_MAIN_SECTION, "DB_PASSWORD")
    except Exception as e:  # deliberately conceal details for security
        raise RuntimeError(
            "Problem reading DB_PASSWORD from config: {}".format(e))
    if db_password is None:
        raise RuntimeError("No database password specified")
        # OK from a security perspective: if there's no password, there's no
        # password to leak via a debugging exception handler

    # Database:
    try:
        audit("dump as SQL: " + " ".join(tables))
        return subprocess.check_output([
            pls.MYSQLDUMP,
            "-h", pls.DB_SERVER,  # rather than --host=X
            "-P", str(pls.DB_PORT),  # rather than --port=X
            "-u", pls.DB_USER,  # rather than --user=X
            "-p{}".format(db_password),
            # neither -pPASSWORD nor --password=PASSWORD accept spaces
            "--opt",
            "--hex-blob",
            "--default-character-set=utf8",
            pls.DB_NAME,
        ] + tables).decode('utf8')
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem opening or reading from database; "
                           "details concealed for security reasons")
    finally:
        # Executed whether an exception is raised or not.
        # noinspection PyUnusedLocal
        db_password = None


def get_query_as_tsv(sql: str) -> str:
    """Returns the result of the SQL query supplied, in TSV format."""
    # Security considerations as above.
    config = configparser.ConfigParser()
    config.read(pls.CAMCOPS_CONFIG_FILE)
    try:
        db_password = config.get(CONFIG_FILE_MAIN_SECTION, "DB_PASSWORD")
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem reading DB_PASSWORD from config")
    if db_password is None:
        raise RuntimeError("No database password specified")
    try:
        return subprocess.check_output([
            pls.MYSQL,
            "-h", pls.DB_SERVER,
            # ... rather than --host=X; the subprocess call handles arguments
            # with spaces much better (e.g. escaping for us)
            "-P", str(pls.DB_PORT),  # rather than --port=X
            "-u", pls.DB_USER,  # rather than --user=X
            "-p{}".format(db_password),
            # ... neither -pPASSWORD nor --password=PASSWORD accept spaces
            "-D", pls.DB_NAME,  # rather than --database=X
            "-e", sql,
            # ... rather than --execute="X"; this is the real reason we use
            # this format, so that subprocess can escape the query
            # appropriately for us
            "--batch",
            # ... create TSV output (will escape actual tabs, unless --raw also
            # specified); note that NULLs come out as the string literal NULL,
            # which is not ideal.
            "--default-character-set=utf8",
        ]).decode('utf8')
        # This will throw an error if BLOBs are used (the binary will screw up
        # the UTF8 decoding).
    except:  # deliberately conceal details for security
        raise RuntimeError("Problem opening or reading from database; "
                           "details concealed for security reasons")
    finally:
        # Executed whether an exception is raised or not.
        # noinspection PyUnusedLocal
        db_password = None


def get_view_data_as_tsv(view: str,
                         prevalidated: bool = False,
                         audit_individually: bool = True) -> str:
    """Returns the data from the view specified, in TSV format."""
    # Views need special handling: mysqldump will provide the view-generating
    # SQL, not the contents. If the output is saved as .XLS, Excel will open it
    # without prompting for conversion.
    if not prevalidated:
        view = validate_single_table(view)
        if not view:
            return "Invalid table or view"
    # Special blob handling...
    if view == Blob.TABLENAME:
        query = (
            "SELECT " +
            ",".join(Blob.FIELDS_WITHOUT_BLOB) +
            ",HEX(theblob) FROM " + Blob.TABLENAME
        )
    else:
        query = "SELECT * FROM " + view
    if audit_individually:
        audit("dump as TSV: " + view)
    return get_query_as_tsv(query)


def get_multiple_views_data_as_tsv_zip(tables: List[str]) -> Optional[bytes]:
    """Returns the data from multiple views, as multiple TSV files in a ZIP."""
    tables = validate_table_list(tables)
    if not tables:
        return None
    memfile = io.BytesIO()
    z = zipfile.ZipFile(memfile, "w")
    for t in tables:
        result = get_view_data_as_tsv(t, prevalidated=True,
                                      audit_individually=False)
        z.writestr(t + ".tsv", result.encode("utf-8"))
    z.close()
    audit("dump as TSV ZIP: " + " ".join(tables))
    return memfile.getvalue()


# =============================================================================
# Unit tests
# =============================================================================

def ccdump_unit_tests() -> None:
    """Unit tests for the cc_dump module."""
    unit_test_ignore("", get_possible_task_tables_views)
    unit_test_ignore("", get_permitted_tables_and_views)
    unit_test_ignore("", get_permitted_tables_views_sorted_labelled)
    unit_test_ignore("", validate_table_list, [None, "phq9",
                                               "nonexistent_table"])
    unit_test_ignore("", validate_single_table, None)
    unit_test_ignore("", validate_single_table, "phq9")
    unit_test_ignore("", validate_single_table, "nonexistent_table")
    unit_test_ignore("", get_database_dump_as_sql)
    # get_query_as_tsv tested indirectly
    unit_test_ignore("", get_view_data_as_tsv, "phq9")
    unit_test_ignore("", get_view_data_as_tsv, "nonexistent_table")
    unit_test_ignore("", get_multiple_views_data_as_tsv_zip,
                     [None, "phq9", "nonexistent_table"])
