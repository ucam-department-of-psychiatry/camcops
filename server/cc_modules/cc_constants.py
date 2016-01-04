#!/usr/bin/env python3
# cc_constants.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Helpful UTF-8 characters: ‘’ “” – — × • ≤ ≥ ≠ ± →

from pythonlib.rnc_lang import AttrDict

# =============================================================================
# Number of ID numbers. Don't alter this lightly; influences database fields.
# =============================================================================

NUMBER_OF_IDNUMS = 8  # Determines number of ID number fields

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE_MAIN_SECTION = "server"
DEFAULT_DB_PORT = 3306
DEFAULT_DB_SERVER = "localhost"

# =============================================================================
# HTTP actions, parameters, values
# =============================================================================

ACTION = AttrDict({
    "ADD_SPECIAL_NOTE": "add_special_note",
    "ADD_USER": "add_user",
    "AGREE_TERMS": "agree_terms",
    "APPLY_FILTER_COMPLETE": "apply_filter_complete",
    "APPLY_FILTER_DEVICE": "apply_filter_device",
    "APPLY_FILTER_DOB": "apply_filter_dob",
    "APPLY_FILTER_END_DATETIME": "apply_filter_end_datetime",
    "APPLY_FILTER_FORENAME": "apply_filter_forename",
    "APPLY_FILTER_IDNUMS": "apply_filter_idnums",
    "APPLY_FILTER_INCLUDE_OLD_VERSIONS": "apply_filter_include_old_versions",
    "APPLY_FILTERS": "apply_filters",
    "APPLY_FILTER_SEX": "apply_filter_sex",
    "APPLY_FILTER_START_DATETIME": "apply_filter_start_datetime",
    "APPLY_FILTER_SURNAME": "apply_filter_surname",
    "APPLY_FILTER_TASK": "apply_filter_task",
    "APPLY_FILTER_TEXT": "apply_filter_text",
    "APPLY_FILTER_USER": "apply_filter_user",
    "ASK_DELETE_USER": "ask_delete_user",
    "ASK_TO_ADD_USER": "ask_to_add_user",
    "BASIC_DUMP": "basic_dump",
    "CHANGE_NUMBER_TO_VIEW": "change_number_to_view",
    "CHANGE_PASSWORD": "change_password",
    "CHANGE_USER": "change_user",
    "CHOOSE_CLINICALTEXTVIEW": "choose_clinicaltextview",
    "CHOOSE_TRACKER": "choose_tracker",
    "CLEAR_FILTER_COMPLETE": "clear_filter_complete",
    "CLEAR_FILTER_DEVICE": "clear_filter_device",
    "CLEAR_FILTER_DOB": "clear_filter_dob",
    "CLEAR_FILTER_END_DATETIME": "clear_filter_end_datetime",
    "CLEAR_FILTER_FORENAME": "clear_filter_forename",
    "CLEAR_FILTER_IDNUMS": "clear_filter_idnums",
    "CLEAR_FILTER_INCLUDE_OLD_VERSIONS": "clear_filter_include_old_versions",
    "CLEAR_FILTERS": "clear_filters",
    "CLEAR_FILTER_SEX": "clear_filter_sex",
    "CLEAR_FILTER_START_DATETIME": "clear_filter_start_datetime",
    "CLEAR_FILTER_SURNAME": "clear_filter_surname",
    "CLEAR_FILTER_TASK": "clear_filter_task",
    "CLEAR_FILTER_TEXT": "clear_filter_text",
    "CLEAR_FILTER_USER": "clear_filter_user",
    "CLINICALTEXTVIEW": "clinicaltextview",
    "CRASH": "crash",
    "DELETE_PATIENT": "delete_patient",
    "DELETE_USER": "delete_user",
    "EDIT_PATIENT": "edit_patient",
    "EDIT_USER": "edit_user",
    "ENABLE_USER": "enable_user",
    "ENTER_NEW_PASSWORD": "enter_new_password",
    "ERASE_TASK": "erase_task",
    "FILTER": "filter",
    "FIRST_PAGE": "first_page",
    "FORCIBLY_FINALIZE": "forcibly_finalize",
    "INSPECT_TABLE_DEFS": "view_table_definitions",
    "INSPECT_TABLE_VIEW_DEFS": "view_table_and_view_definitions",
    "INTROSPECT": "introspect",
    "LAST_PAGE": "last_page",
    "LOGIN": "login",
    "LOGOUT": "logout",
    "MAIN_MENU": "main_menu",
    "MANAGE_USERS": "manage_users",
    "NEXT_PAGE": "next_page",
    "OFFER_AUDIT_TRAIL_OPTIONS": "offer_audit_trail_options",
    "OFFER_BASIC_DUMP": "offer_basic_dump",
    "OFFER_HL7_LOG_OPTIONS": "offer_hl7_log",
    "OFFER_HL7_RUN_OPTIONS": "offer_hl7_run",
    "OFFER_INTROSPECTION": "offer_introspect",
    "OFFER_REGENERATE_SUMMARIES": "offer_regenerate_summary_tables",
    "OFFER_REPORT": "offer_report",
    "OFFER_TABLE_DUMP": "offer_table_dump",
    "PREVIOUS_PAGE": "previous_page",
    "PROVIDE_REPORT": "report",
    "REGENERATE_SUMMARIES": "regenerate_summary_tables",
    "REPORTS_MENU": "reports_menu",
    "TABLE_DUMP": "table_dump",
    "TASK": "task",
    "TRACKER": "tracker",
    "VIEW_AUDIT_TRAIL": "view_audit_trail",
    "VIEW_HL7_LOG": "view_hl7_log",
    "VIEW_HL7_RUN": "view_hl7_run",
    "VIEW_POLICIES": "view_policies",
    "VIEW_TASKS": "view_tasks",
})

PARAM = AttrDict({
    "ACTION": "action",
    "ADDRESS": "address",
    "ANONYMISE": "anonymise",
    "BASIC_DUMP_TYPE": "basic_dump_type",
    "COMPLETE": "complete",
    "CONFIRMATION_SEQUENCE": "confirmation_sequence",
    "DEVICE": "device",
    "DOB": "dob",
    "END_DATETIME": "end_datetime",
    "FILENAME": "filename",
    "FORENAME": "forename",
    "GP": "gp",
    "HL7RUNID": "hl7runid",
    "IDNUM_VALUE": "idnum_value",
    "IDNUM_PREFIX": "idnum_prefix",
    "INCLUDE_BLOBS": "include_blobs",
    "INCLUDE_CALCULATED": "include_calculated",
    "INCLUDE_COMMENTS": "include_comments",
    "INCLUDE_OLD_VERSIONS": "include_old_versions",
    "INCLUDE_PATIENT": "include_patient",
    "IPADDR": "ipaddr",
    "LABEL": "label",
    "MAY_ADD_NOTES": "may_add_notes",
    "MAY_DUMP_DATA": "may_dump_data",
    "MAY_REGISTER_DEVICES": "may_register_devices",
    "MAY_RUN_REPORTS": "may_run_reports",
    "MAY_UPLOAD": "may_upload",
    "MAY_USE_WEBSTORAGE": "may_use_webstorage",
    "MAY_USE_WEBVIEWER": "may_use_webviewer",
    "MAY_VIEW_OTHER_USERS_RECORDS": "may_view_other_users_records",
    "MUST_CHANGE_PASSWORD": "must_change_password",
    "NAME": "name",
    "NEW_PASSWORD_1": "new_password_1",
    "NEW_PASSWORD_2": "new_password_2",
    "NOTE": "note",
    "NROWS": "nrows",
    "NTASKS": "ntasks",
    "NUMBER_TO_VIEW": "number_to_view",
    "OLD_PASSWORD": "old_password",
    "OTHER": "other",
    "OUTPUTTYPE": "outputtype",
    "PASSWORD_1": "password_1",
    "PASSWORD_2": "password_2",
    "PASSWORD": "password",
    "REDIRECT": "redirect",
    "REPORT_ID": "report_id",
    "SERVERPK": "serverpk",
    "SEX": "sex",
    "SHOWMESSAGE": "show_message",
    "SHOWREPLY": "show_reply",
    "START_DATETIME": "start_datetime",
    "SOURCE": "source",
    "SUPERUSER": "superuser",
    "SURNAME": "surname",
    "TABLENAME": "tablename",
    "TABLES_BLOB": "tables_blob",
    "TABLES": "tables",
    "TASK": "task",
    "TASKTYPES": "tasktypes",
    "TEXT": "text",
    "TRUNCATE": "truncate",
    "TYPE": "type",
    "USERNAME": "username",
    "USER": "user",
    "VIEW_ALL_PTS_WHEN_UNFILTERED": "view_all_patients_when_unfiltered",
    "VIEWS": "views",
    "WHICH_IDNUM": "which_idnum",
})

VALUE = AttrDict({
    "DUMPTYPE_AS_TASK_FILTER": "as_task_filter",
    "DUMPTYPE_EVERYTHING": "everything",
    "DUMPTYPE_SPECIFIC_TASKS": "specific_tasks",
    "OUTPUTTYPE_PDF": "pdf",
    "OUTPUTTYPE_HTML": "html",
    "OUTPUTTYPE_PDFHTML": "pdfhtml",  # debugging: HTML used to make PDF
    "OUTPUTTYPE_TSV": "tsv",
    "OUTPUTTYPE_SQL": "sql",
    "OUTPUTTYPE_XML": "xml",
})

# =============================================================================
# Date formats
# =============================================================================

DATEFORMAT = AttrDict({
    "SHORT_DATE": "%d %b %Y",  # e.g. 24 Jul 2013
    "LONG_DATE": "%d %B %Y",  # e.g. 24 July 2013
    "LONG_DATE_WITH_DAY": "%a %d %B %Y",  # e.g. Wed 24 July 2013
    "LONG_DATETIME": "%d %B %Y, %H:%M %z",
    # ... e.g. 24 July 2013, 20:04 +0100
    "LONG_DATETIME_WITH_DAY": "%a %d %B %Y, %H:%M %z",
    # ... e.g. Wed 24 July 2013, 20:04 +0100
    "LONG_DATETIME_WITH_DAY_NO_TZ": "%a %d %B %Y, %H:%M",
    # ... e.g. Wed 24 July 2013, 20:04
    "SHORT_DATETIME_WITH_DAY_NO_TZ": "%a %d %b %Y, %H:%M",
    # ... e.g. Wed 24 Jul 2013, 20:04
    "LONG_DATETIME_SECONDS": "%d %B %Y, %H:%M:%S %z",
    "SHORT_DATETIME": "%d %b %Y, %H:%M %z",
    "SHORT_DATETIME_SECONDS": "%d %b %Y, %H:%M:%S %z",
    "HOURS_MINUTES": "%H:%M",
    "ISO8601": "%Y-%m-%dT%H:%M:%S%z",  # e.g. 2013-07-24T20:04:07+0100
    "ISO8601_DATE_ONLY": "%Y-%m-%d",  # e.g. 2013-07-24
    "FILENAME": "%Y-%m-%dT%H%M",  # e.g. 20130724T2004
    "FILENAME_DATE_ONLY": "%Y-%m-%d",  # e.g. 20130724
    "HL7_DATETIME": "%Y%m%d%H%M%S%z",  # e.g. 20130724200407+0100
    "HL7_DATE": "%Y%m%d",  # e.g. 20130724
    "ERA": "%Y-%m-%dT%H:%M:%SZ",  # e.g. 2013-07-24T20:03:07Z
    # http://www.hl7standards.com/blog/2008/07/25/hl7-time-zone-qualification/
    "RIO_EXPORT_UK": "%d/%m/%Y %H:%M",  # e.g. 01/12/2014 09:45
})

# =============================================================================
# Permitted values in fields: some common settings
# =============================================================================

PV = AttrDict({
    "BIT": [0, 1],
})

NO_CHAR = 'N'
YES_CHAR = 'Y'

# =============================================================================
# Field names/specifications
# =============================================================================

ISO8601_STRING_LENGTH = 32
# ... max length e.g. 2013-07-24T20:04:07.123456+01:00
# (microseconds, colon in timezone).

PKNAME = "_pk"
MOVE_OFF_TABLET_FIELD = "_move_off_tablet"
CLIENT_DATE_FIELD = "when_last_modified"

# VALID KEYS FOR FIELDSPECS:
# - all those listed in rnc_db.py
# - cctype
# - identifies_patient (Boolean)
STANDARD_GENERIC_FIELDSPECS = [
    # server side:
    dict(name=PKNAME, cctype="INT_UNSIGNED", pk=True,
         autoincrement=True, comment="(SERVER) Primary key (on the server)"),
    # ... server PK; must always be first in the fieldlist
    dict(name="_device", cctype="DEVICE", notnull=True,
         comment="(SERVER) ID of the source tablet device",
         indexed=True, index_nchar=50),
    dict(name="_era", cctype="ISO8601", notnull=True,
         comment="(SERVER) 'NOW', or when this row was preserved and removed "
                 "from the source device (UTC ISO 8601)",
         indexed=True, index_nchar=ISO8601_STRING_LENGTH),
    # ... note that _era is TEXT so that plain comparison
    # with "=" always works, i.e. no NULLs
    dict(name="_current", cctype="BOOL", notnull=True,
         comment="(SERVER) Is the row current (1) or not (0)?", indexed=True),
    dict(name="_when_added_exact", cctype="ISO8601",
         comment="(SERVER) Date/time this row was added (ISO 8601)"),
    dict(name="_when_added_batch_utc", cctype="DATETIME",
         comment="(SERVER) Date/time of the upload batch that added this "
                 "row (DATETIME in UTC)"),
    dict(name="_adding_user", cctype="USERNAME",
         comment="(SERVER) User that added this row"),
    dict(name="_when_removed_exact", cctype="ISO8601",
         comment="(SERVER) Date/time this row was removed, i.e. made "
                 "not current (ISO 8601)"),
    dict(name="_when_removed_batch_utc", cctype="DATETIME",
         comment="(SERVER) Date/time of the upload batch that removed "
                 "this row (DATETIME in UTC)"),
    dict(name="_removing_user", cctype="USERNAME",
         comment="(SERVER) User that removed this row"),
    dict(name="_preserving_user", cctype="USERNAME",
         comment="(SERVER) User that preserved this row"),
    dict(name="_forcibly_preserved", cctype="BOOL",
         comment="(SERVER) Forcibly preserved by superuser (rather than "
                 "normally preserved by tablet)?"),
    dict(name="_predecessor_pk", cctype="INT_UNSIGNED",
         comment="(SERVER) PK of predecessor record, prior to modification"),
    dict(name="_successor_pk", cctype="INT_UNSIGNED",
         comment="(SERVER) PK of successor record  (after modification) "
                 "or NULL (after deletion)"),
    dict(name="_manually_erased", cctype="BOOL",
         comment="(SERVER) Record manually erased (content destroyed)?"),
    dict(name="_manually_erased_at", cctype="ISO8601",
         comment="(SERVER) Date/time of manual erasure (ISO 8601)"),
    dict(name="_manually_erasing_user", cctype="USERNAME",
         comment="(SERVER) User that erased this row manually"),
    dict(name="_camcops_version", cctype="FLOAT",
         comment="(SERVER) CamCOPS version number of the uploading device"),
    dict(name="_addition_pending", cctype="BOOL",
         notnull=True, comment="(SERVER) Addition pending?"),
    dict(name="_removal_pending", cctype="BOOL",
         notnull=True, comment="(SERVER) Removal pending?"),
    dict(name=MOVE_OFF_TABLET_FIELD, cctype="BOOL",
         comment="(SERVER/TABLET) Record-specific preservation pending?"),
    # fields that *all* client tables have:
    dict(name=CLIENT_DATE_FIELD, cctype="ISO8601",
         comment="(STANDARD) Date/time this row was last modified on the "
                 "source tablet device (ISO 8601)"),
]

# =============================================================================
# Other special values
# =============================================================================

CAMCOPS_URL = "http://www.camcops.org/"
ERA_NOW = "NOW"  # defines the current era in database records
