#!/usr/bin/env python
# camcops_server/discarded_upgrade_code.py

# noinspection PySingleQuotedDocstring
'''
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

SEPARATOR_HYPHENS = "-" * 79
SEPARATOR_EQUALS = "=" * 79

# =============================================================================
# Version-specific database changes
# =============================================================================

def report_database_upgrade_step(version: str) -> None:
    print("PERFORMING UPGRADE TASKS FOR VERSION {}".format(version))


def modify_column(table: str, field: str, newdef: str) -> None:
    pls.db.modify_column_if_table_exists(table, field, newdef)


def change_column(tablename: str,
                  oldfieldname: str,
                  newfieldname: str,
                  newdef: str) -> None:
    # Fine to have old/new column with the same name
    # BUT see also modify_column
    pls.db.change_column_if_table_exists(tablename, oldfieldname, newfieldname,
                                         newdef)


def rename_table(from_table: str, to_table: str) -> None:
    pls.db.rename_table(from_table, to_table)


def drop_all_views_and_summary_tables() -> None:
    for cls in get_all_task_classes():
        cls.drop_views()
        cls.drop_summary_tables()
    Blob.drop_views()
    Patient.drop_views()
    DeviceStoredVar.drop_views()


def v1_5_alter_device_table() -> None:
    tablename = Device.TABLENAME
    if not pls.db.table_exists(tablename):
        return
    if pls.db.column_exists(tablename, 'id'):
        log.warning("Column 'id' already exists in table {}", tablename)
        return
    ex = pls.db.db_exec_literal
    ex("ALTER TABLE {table} ADD COLUMN id "
       "INT UNSIGNED UNIQUE KEY AUTO_INCREMENT".format(table=tablename))
    # Must be a key to be AUTO_INCREMENT
    ex("ALTER TABLE {table} DROP PRIMARY KEY".format(table=tablename))
    # The manual addition of the PRIMARY KEY may be superfluous.
    ex("ALTER TABLE {table} ADD PRIMARY KEY (id)".format(table=tablename))
    ex("ALTER TABLE {table} CHANGE COLUMN device name "
       "VARCHAR(255)".format(table=tablename))
    ex("ALTER TABLE {table} ADD UNIQUE KEY (name)".format(table=tablename))


def v1_5_alter_user_table() -> None:
    tablename = User.TABLENAME
    if not pls.db.table_exists(tablename):
        return
    if pls.db.column_exists(tablename, 'id'):
        log.warning("Column 'id' already exists in table {}", tablename)
        return
    ex = pls.db.db_exec_literal
    ex("ALTER TABLE {table} ADD COLUMN id "
       "INT UNSIGNED UNIQUE KEY AUTO_INCREMENT".format(table=tablename))
    # Must be a key to be AUTO_INCREMENT
    ex("ALTER TABLE {table} DROP PRIMARY KEY".format(table=tablename))
    # The manual addition of the PRIMARY KEY may be superfluous.
    ex("ALTER TABLE {table} ADD PRIMARY KEY (id)".format(table=tablename))
    ex("ALTER TABLE {table} CHANGE COLUMN user username "
       "VARCHAR(255)".format(table=tablename))
    ex("ALTER TABLE {table} ADD UNIQUE KEY (username)".format(table=tablename))


def v1_5_alter_generic_table_devicecol(tablename: str,
                                       from_col: str,
                                       to_col: str,
                                       with_index: bool = True) -> None:
    if not pls.db.table_exists(tablename):
        return
    if pls.db.column_exists(tablename, to_col):
        log.warning("Column '{}' already exists in table {}",
                    to_col, tablename)
        return
    ex = pls.db.db_exec_literal
    ex("ALTER TABLE {table} ADD COLUMN {to_col} INT UNSIGNED".format(
        table=tablename, to_col=to_col))
    ex("UPDATE {table} AS altering "
       "INNER JOIN {lookup} AS lookup "
       "ON altering.{from_col} = lookup.name "
       "SET altering.{to_col} = lookup.id".format(
        table=tablename, lookup=Device.TABLENAME,
        from_col=from_col, to_col=to_col))
    ex("ALTER TABLE {table} DROP COLUMN {from_col}".format(table=tablename,
                                                           from_col=from_col))
    if with_index:
        ex("CREATE INDEX _idx_{to_col} ON {table} ({to_col})".format(
            to_col=to_col, table=tablename))


def v1_5_alter_generic_table_usercol(tablename: str,
                                     from_col: str,
                                     to_col: str) -> None:
    if not pls.db.table_exists(tablename):
        return
    if pls.db.column_exists(tablename, to_col):
        log.warning("Column '{}' already exists in table {}",
                    to_col, tablename)
        return
    ex = pls.db.db_exec_literal
    ex("ALTER TABLE {table} ADD COLUMN {to_col} INT UNSIGNED".format(
        table=tablename, to_col=to_col))
    ex("UPDATE {table} AS altering "
       "INNER JOIN {lookup} AS lookup "
       "ON altering.{from_col} = lookup.username "
       "SET altering.{to_col} = lookup.id".format(
        table=tablename, lookup=User.TABLENAME,
        from_col=from_col, to_col=to_col))
    ex("ALTER TABLE {table} DROP COLUMN {from_col}".format(table=tablename,
                                                           from_col=from_col))


def v1_5_alter_generic_table(tablename: str) -> None:
    # Device ID
    v1_5_alter_generic_table_devicecol(tablename,
                                       '_device',
                                       '_device_id')
    # User IDs
    v1_5_alter_generic_table_usercol(tablename,
                                     '_adding_user',
                                     '_adding_user_id')
    v1_5_alter_generic_table_usercol(tablename,
                                     '_removing_user',
                                     '_removing_user_id')
    v1_5_alter_generic_table_usercol(tablename,
                                     '_preserving_user',
                                     '_preserving_user_id')
    v1_5_alter_generic_table_usercol(tablename,
                                     '_manually_erasing_user',
                                     '_manually_erasing_user_id')


def v2_0_0_alter_generic_table(tablename: str) -> None:
    # Version goes from float (e.g. 1.06) to semantic version (e.g. 2.0.0).
    modify_column(tablename, "_camcops_version",
                  cc_db.SQLTYPE.SEMANTICVERSIONTYPE)


def v2_0_0_move_png_rotation_field(tablename: str, blob_id_fieldname: str,
                                   rotation_fieldname: str) -> None:
    sql = """
        UPDATE {blobtable} b
        INNER JOIN {tablename} t ON
            b.id = t.{blob_id_fieldname}
            AND b._device_id = t._device_id
            AND b._era = t._era
            AND b._when_added_batch_utc <= t._when_added_batch_utc
            AND (b._when_removed_batch_utc = t._when_removed_batch_utc
                 OR (b._when_removed_batch_utc IS NULL
                     AND t._when_removed_batch_utc IS NULL))
        SET b.image_rotation_deg_cw = t.{rotation_fieldname}
    """.format(
        blobtable=Blob.TABLENAME,
        tablename=tablename,
        blob_id_fieldname=blob_id_fieldname,
        rotation_fieldname=rotation_fieldname,
    )
    pls.db.db_exec_literal(sql)


def upgrade_database_first_phase(old_version: Version) -> None:
    print("Old database version: {}. New version: {}.".format(
        old_version,
        CAMCOPS_SERVER_VERSION
    ))
    if old_version is None:
        log.warning("Don't know old database version; can't upgrade structure")
        return

    # Proceed IN SEQUENCE from older to newer versions.
    # Don't assume that tables exist already.
    # The changes are performed PRIOR to making tables afresh (which will
    # make any new columns required, and thereby block column renaming).
    # DO NOT DO THINGS THAT WOULD DESTROY USERS' DATA.

    # -------------------------------------------------------------------------
    # Older versions, from before semantic versioning system:
    # -------------------------------------------------------------------------

    if old_version < make_version(1.06):
        report_database_upgrade_step("1.06")
        pls.db.drop_table(DIRTY_TABLES_TABLENAME)

    if old_version < make_version(1.07):
        report_database_upgrade_step("1.07")
        pls.db.drop_table(Session.TABLENAME)

    if old_version < make_version(1.08):
        report_database_upgrade_step("1.08")
        change_column("_security_users",
                      "may_alter_users", "superuser", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_commentary", "hv_commentary", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_discussing", "hv_discussing", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_from_body", "hv_from_body", "BOOLEAN")

    if old_version < make_version(1.10):
        report_database_upgrade_step("1.10")
        modify_column("patient", "forename", "VARCHAR(255) NULL")
        modify_column("patient", "surname", "VARCHAR(255) NULL")
        modify_column("patient", "dob", "VARCHAR(32) NULL")
        modify_column("patient", "sex", "VARCHAR(1) NULL")

    if old_version < make_version(1.11):
        report_database_upgrade_step("1.11")
        # session
        modify_column("session", "ip_address", "VARCHAR(45) NULL")  # was 40
        # ExpDetThreshold
        pls.db.rename_table("expdetthreshold",
                            "cardinal_expdetthreshold")
        pls.db.rename_table("expdetthreshold_trials",
                            "cardinal_expdetthreshold_trials")
        change_column("cardinal_expdetthreshold_trials",
                      "expdetthreshold_id", "cardinal_expdetthreshold_id",
                      "INT")
        pls.db.drop_view("expdetthreshold_current")
        pls.db.drop_view("expdetthreshold_current_withpt")
        pls.db.drop_view("expdetthreshold_trials_current")
        # ExpDet
        pls.db.rename_table("expectationdetection",
                            "cardinal_expdet")
        pls.db.rename_table("expectationdetection_trialgroupspec",
                            "cardinal_expdet_trialgroupspec")
        pls.db.rename_table("expectationdetection_trials",
                            "cardinal_expdet_trials")
        pls.db.drop_table("expectationdetection_SUMMARY_TEMP")
        pls.db.drop_table("expectationdetection_BLOCKPROBS_TEMP")
        pls.db.drop_table("expectationdetection_HALFPROBS_TEMP")
        pls.db.drop_view("expectationdetection_current")
        pls.db.drop_view("expectationdetection_current_withpt")
        pls.db.drop_view("expectationdetection_trialgroupspec_current")
        pls.db.drop_view("expectationdetection_trials_current")
        pls.db.drop_view("expectationdetection_SUMMARY_TEMP_current")
        pls.db.drop_view("expectationdetection_SUMMARY_TEMP_current_withpt")
        pls.db.drop_view("expectationdetection_BLOCKPROBS_TEMP_current")
        pls.db.drop_view("expectationdetection_BLOCKPROBS_TEMP_current_withpt")
        pls.db.drop_view("expectationdetection_HALFPROBS_TEMP_current")
        pls.db.drop_view("expectationdetection_HALFPROBS_TEMP_current_withpt")
        change_column("cardinal_expdet_trials",
                      "expectationdetection_id", "cardinal_expdet_id", "INT")
        change_column("cardinal_expdet_trialgroupspec",
                      "expectationdetection_id", "cardinal_expdet_id", "INT")

    if old_version < make_version(1.15):
        report_database_upgrade_step("1.15")
        # these were INT UNSIGNED:
        modify_column("patient", "idnum1", "BIGINT UNSIGNED")
        modify_column("patient", "idnum2", "BIGINT UNSIGNED")
        modify_column("patient", "idnum3", "BIGINT UNSIGNED")
        modify_column("patient", "idnum4", "BIGINT UNSIGNED")
        modify_column("patient", "idnum5", "BIGINT UNSIGNED")
        modify_column("patient", "idnum6", "BIGINT UNSIGNED")
        modify_column("patient", "idnum7", "BIGINT UNSIGNED")
        modify_column("patient", "idnum8", "BIGINT UNSIGNED")

    if old_version < make_version(1.5):
        report_database_upgrade_step("1.5")
        # ---------------------------------------------------------------------
        # 1.
        #   Create:
        #     _security_devices.id INT UNSIGNED (autoincrement)
        #   Rename:
        #     _security_devices.device -> _security_devices.name
        #   Change references in everything else:
        #     _device VARCHAR(255) -> _device_id INT UNSIGNED
        # 2.
        #   Create:
        #     _security_users.id
        #   Rename:
        #     _security_users.user -> _security_users.username
        #   Change all references:
        #     _adding_user VARCHAR(255) -> _adding_user_id INT UNSIGNED
        #     _removing_user VARCHAR(255) -> _removing_user_id INT UNSIGNED
        #     _preserving_user VARCHAR(255) -> _preserving_user_id INT UNSIGNED
        #     _manually_erasing_user VARCHAR(255) -> _manually_erasing_user_id INT UNSIGNED  # noqa
        # ---------------------------------------------------------------------
        # Note: OK to drop columns even if a view is looking at them,
        # though the view will then be invalid.

        drop_all_views_and_summary_tables()

        v1_5_alter_device_table()
        v1_5_alter_user_table()
        v1_5_alter_generic_table_usercol(Device.TABLENAME,
                                         'registered_by_user',
                                         'registered_by_user_id')
        v1_5_alter_generic_table_usercol(Device.TABLENAME,
                                         'uploading_user',
                                         'uploading_user_id')
        for cls in get_all_task_classes():
            v1_5_alter_generic_table(cls.tablename)
            for tablename in cls.get_extra_table_names():
                v1_5_alter_generic_table(tablename)
        # Special tables with device or patient references:
        v1_5_alter_generic_table(Blob.TABLENAME)
        v1_5_alter_generic_table(Patient.TABLENAME)
        v1_5_alter_generic_table(DeviceStoredVar.TABLENAME)

        v1_5_alter_generic_table_usercol(
            AuditEntry.__tablename__, 'user', 'user_id')
        v1_5_alter_generic_table_devicecol(
            AuditEntry.__tablename__, 'device', 'device_id', with_index=False)
        v1_5_alter_generic_table_usercol(
            SpecialNote.TABLENAME, 'user', 'user_id')
        v1_5_alter_generic_table_devicecol(
            SpecialNote.TABLENAME, 'device', 'device_id', with_index=True)
        change_column(SECURITY_ACCOUNT_LOCKOUT_TABLENAME,
                      "user", "username", "VARCHAR(255)")
        change_column(SECURITY_LOGIN_FAILURE_TABLENAME,
                      "user", "username", "VARCHAR(255)")
        pls.db.drop_table(DIRTY_TABLES_TABLENAME)
        pls.db.drop_table(Session.TABLENAME)

    # -------------------------------------------------------------------------
    # Move to semantic versioning from 2.0.0
    # -------------------------------------------------------------------------

    if old_version < Version("2.0.0"):
        report_database_upgrade_step("2.0.0")

        # Server
        drop_all_views_and_summary_tables()
        pls.db.db_exec_literal("""
            UPDATE {table}
            SET type = 'text',
                valueText = CAST(valueReal AS CHAR),
                valueReal = NULL
            WHERE name = 'serverCamcopsVersion'
        """.format(table=ServerStoredVar.TABLENAME))
        # Tablet generic
        v2_0_0_alter_generic_table(Blob.TABLENAME)
        v2_0_0_alter_generic_table(Patient.TABLENAME)
        modify_column(Device.TABLENAME, "camcops_version",
                      cc_db.SQLTYPE.SEMANTICVERSIONTYPE)
        v2_0_0_alter_generic_table(DeviceStoredVar.TABLENAME)
        # Tasks
        for cls in get_all_task_classes():
            v2_0_0_alter_generic_table(cls.tablename)
            for tablename in cls.get_extra_table_names():
                v2_0_0_alter_generic_table(tablename)
        # Specifics
        modify_column("ciwa", "t", "REAL NULL")  # was erroneously INT; temperature (C)  # noqa
        modify_column("cpft_lps_referral", "marital_status_code",
                      "VARCHAR(1) NULL")  # was erroneously INT; single-char code  # noqa
        modify_column("cpft_lps_referral", "ethnic_category_code",
                      "VARCHAR(1) NULL")  # was erroneously INT; single-char code  # noqa

        # NOTE: from client version 2.0.0, "iddesc{n}" and "idshortdesc{n}"
        # fields are no longer uploaded - they are just duplicates of the
        # server's own values - DUE FOR REMOVAL FROM SERVER (plus handling
        # of old clients).


def upgrade_database_second_phase(old_version: Version) -> None:
    if old_version < Version("2.0.0"):
        report_database_upgrade_step("2.0.0")
        # BLOBs become more generalized and know about their own image rotation
        v2_0_0_move_png_rotation_field("ace3", "picture1_blobid", "picture1_rotation")  # noqa
        v2_0_0_move_png_rotation_field("ace3", "picture2_blobid", "picture2_rotation")  # noqa
        v2_0_0_move_png_rotation_field("demoquestionnaire", "photo_blobid", "photo_rotation")  # noqa
        v2_0_0_move_png_rotation_field("photo", "photo_blobid", "rotation")
        v2_0_0_move_png_rotation_field("photosequence_photos", "photo_blobid", "rotation")  # noqa
        pls.db.db_exec_literal("""
            UPDATE {blobtable} SET mimetype = 'image/png'
        """.format(blobtable=Blob.TABLENAME))

    if old_version < Version("2.0.1"):
        report_database_upgrade_step("2.0.1")
        # Move ID numbers into their own table, allowing an arbitrary number.
        for n in range(1, NUMBER_OF_IDNUMS_DEFUNCT + 1):
            nstr = str(n)
            pls.db.db_exec_literal("""
                INSERT INTO {idnumtable} (
                    -- _pk is autogenerated

                    _device_id,
                    _era,
                    _current,
                    _when_added_exact,
                    _when_added_batch_utc,

                    _adding_user_id,
                    _when_removed_exact,
                    _when_removed_batch_utc,
                    _removing_user_id,
                    _preserving_user_id,

                    _forcibly_preserved,
                    _predecessor_pk,
                    _successor_pk,
                    _manually_erased,
                    _manually_erased_at,
                    _manually_erasing_user_id,
                    _camcops_version,

                    _addition_pending,
                    _removal_pending,
                    _move_off_tablet,

                    id,
                    patient_id,
                    which_idnum,
                    idnum_value,
                    when_last_modified
                )
                SELECT
                    _device_id,
                    _era,
                    _current,
                    _when_added_exact,
                    _when_added_batch_utc,

                    _adding_user_id,
                    _when_removed_exact,
                    _when_removed_batch_utc,
                    _removing_user_id,
                    _preserving_user_id,

                    _forcibly_preserved,
                    NULL,  -- _predecessor_pk
                    NULL,  -- _successor_pk
                    _manually_erased,
                    _manually_erased_at,
                    _manually_erasing_user_id,
                    _camcops_version,

                    0,  -- _addition_pending
                    0,  -- _removal_pending
                    0,  -- _move_off_tablet

                    id * 8,  -- goes to id
                    id,  -- goes to patient_id
                    {which_idnum},  -- goes to which_idnum
                    {idnumfield},  -- goes to idnum_value
                    when_last_modified

                FROM {patienttable}
                WHERE {idnumfield} IS NOT NULL
            """.format(
                idnumtable=PatientIdNum.__tablename__,
                patienttable=Patient.TABLENAME,
                which_idnum=nstr,
                idnumfield=FP_ID_NUM + nstr,
            ))




def make_tables(drop_superfluous_columns: bool = False) -> None:
    """Make database tables."""

    print(SEPARATOR_EQUALS)
    print("Checking +/- modifying database structure.")
    print("If this pauses, and you are running CamCOPS via Apache/mod_wsgi,"
          "run 'sudo apachectl restart' in another terminal.")
    if drop_superfluous_columns:
        print("DROPPING SUPERFLUOUS COLUMNS")
    print(SEPARATOR_EQUALS)

    # MySQL engine settings
    failed = False
    insertmsg = " into my.cnf [mysqld] section, and restart MySQL"
    if not pls.db.mysql_using_innodb_strict_mode():
        log.error("NOT USING innodb_strict_mode; please insert "
                  "'innodb_strict_mode = 1'" + insertmsg)
        failed = True
    max_allowed_packet = pls.db.mysql_get_max_allowed_packet()
    size_32m = 32 * 1024 * 1024
    if max_allowed_packet < size_32m:
        log.error("MySQL max_allowed_packet < 32M (it's {} and needs to be "
                  "{}); please insert 'max_allowed_packet = 32M'" + insertmsg,
                  max_allowed_packet,
                  size_32m)
        failed = True
    if not pls.db.mysql_using_file_per_table():
        log.error("NOT USING innodb_file_per_table; please insert "
                  "'innodb_file_per_table = 1'" + insertmsg)
        failed = True
    if not pls.db.mysql_using_innodb_barracuda():
        log.error("innodb_file_format IS NOT Barracuda; please insert "
                  "'innodb_file_per_table = Barracuda'" + insertmsg)
        failed = True
    if failed:
        raise AssertionError("MySQL settings need fixing")

    # Database settings
    cc_db.set_db_to_utf8(pls.db)

    # Special system table, in which old database version number is kept
    ServerStoredVar.make_tables(drop_superfluous_columns)

    print(SEPARATOR_HYPHENS)
    print("Checking database version +/- upgrading.")
    print(SEPARATOR_HYPHENS)

    # Read old version number, and perform any special version-specific
    # upgrade tasks
    sv_version = ServerStoredVar(ServerStoredVarNames.SERVER_CAMCOPS_VERSION,
                                 ServerStoredVar.TYPE_TEXT)
    sv_potential_old_version = ServerStoredVar(
        ServerStoredVarNames.SERVER_CAMCOPS_VERSION,
        ServerStoredVar.TYPE_REAL)
    # !!! this bit above is buggered !!!
    old_version = make_version(sv_version.get_value() or
                               sv_potential_old_version.get_value())
    upgrade_database_first_phase(old_version)
    # Important that we write the new version now:
    sv_version.set_value(str(CAMCOPS_SERVER_VERSION))
    # This value must only be written in conjunction with the database
    # upgrade process.

    print(SEPARATOR_HYPHENS)
    print("Making core tables")
    print(SEPARATOR_HYPHENS)

    # Other system tables
    User.make_tables(drop_superfluous_columns)
    Device.make_tables(drop_superfluous_columns)
    HL7Run.make_tables(drop_superfluous_columns)
    HL7Message.make_tables(drop_superfluous_columns)
    Session.make_tables(drop_superfluous_columns)
    SpecialNote.make_tables(drop_superfluous_columns)

    # Core client tables
    Patient.make_tables(drop_superfluous_columns)
    PatientIdNum.make_tables(drop_superfluous_columns)
    Blob.make_tables(drop_superfluous_columns)
    DeviceStoredVar.make_tables(drop_superfluous_columns)

    # System tables without a class representation
    cc_db.create_or_update_table(
        DIRTY_TABLES_TABLENAME, DIRTY_TABLES_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)
    pls.db.create_or_replace_primary_key(DIRTY_TABLES_TABLENAME,
                                         ["device_id", "tablename"])
    cc_db.create_or_update_table(
        SECURITY_AUDIT_TABLENAME, SECURITY_AUDIT_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)

    upgrade_database_second_phase(old_version)

    # Task tables
    print(SEPARATOR_HYPHENS)
    print("Making task tables")
    print(SEPARATOR_HYPHENS)
    for cls in get_all_task_classes():
        print("Making table(s) and view(s) for task: " + cls.shortname)
        cls.make_tables(drop_superfluous_columns)

    audit("Created/recreated main tables", from_console=True)



'''
