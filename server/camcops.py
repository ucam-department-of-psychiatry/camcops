#!/usr/bin/env python3
# camcops.py

import argparse
import codecs
import configparser
import getpass
import os
import sys

import werkzeug.contrib.profiler
from werkzeug.wsgi import SharedDataMiddleware

import pythonlib.rnc_db as rnc_db
import pythonlib.wsgi_errorreporter as wsgi_errorreporter

import webview
from webview import (
    get_database_title,
    make_summary_tables,
)
import database
import cc_modules.cc_analytics as cc_analytics
from cc_modules.cc_audit import (
    audit,
    SECURITY_AUDIT_TABLENAME,
    SECURITY_AUDIT_FIELDSPECS
)
from cc_modules.cc_constants import (
    CAMCOPS_URL,
    NUMBER_OF_IDNUMS,
    SEPARATOR_EQUALS,
    SEPARATOR_HYPHENS,
    URL_ROOT_DATABASE,
    URL_ROOT_STATIC,
    URL_ROOT_WEBVIEW,
)
import cc_modules.cc_blob as cc_blob
import cc_modules.cc_db as cc_db
import cc_modules.cc_device as cc_device
import cc_modules.cc_dump as cc_dump
from cc_modules.cc_logger import logger
import cc_modules.cc_hl7 as cc_hl7
import cc_modules.cc_hl7core as cc_hl7core
import cc_modules.cc_patient as cc_patient
from cc_modules.cc_pls import pls
import cc_modules.cc_policy as cc_policy
import cc_modules.cc_report as cc_report
import cc_modules.cc_session as cc_session
from cc_modules.cc_specialnote import SpecialNote
from cc_modules.cc_storedvar import DeviceStoredVar, ServerStoredVar
import cc_modules.cc_task as cc_task
import cc_modules.cc_tracker as cc_tracker  # will import matplotlib
import cc_modules.cc_user as cc_user
from cc_modules.cc_version import CAMCOPS_SERVER_VERSION


# =============================================================================
# Debugging options
# =============================================================================

# Not possible to put the next two flags in environment variables, because we
# need them at load-time and the WSGI system only gives us environments at
# run-time.

# For debugging, set the next variable to True, and it will provide much
# better HTML debugging output.
# Use caution enabling this on a production system.
# However, system passwords should be concealed regardless (see cc_shared.py).
DEBUG_TO_HTTP_CLIENT = True

# Report profiling information to the HTTPD log? (Adds overhead; do not enable
# for production systems.)
PROFILE = False

SERVE_STATIC_FILES = True

# The other debugging control is in cc_shared: see the logger.setLevel() calls,
# controlled primarily by the configuration file's DEBUG_OUTPUT option.

# =============================================================================
# Other constants
# =============================================================================

DEFAULT_CONFIG_FILENAME = "/etc/camcops/camcops.conf"

# System tables without a class representation:
DIRTY_TABLES_TABLENAME = "_dirty_tables"
DIRTY_TABLES_FIELDSPECS = [
    dict(name="device", cctype="DEVICE",
         comment="Source tablet device ID"),
    dict(name="tablename", cctype="TABLENAME",
         comment="Table in the process of being preserved"),
]


# =============================================================================
# WSGI entry point
# =============================================================================
# The WSGI framework looks for: def application(environ, start_response)
# ... must be called "application"

webview_application = webview.camcops_application_db_wrapper
database_application = database.database_wrapper

# Don't apply ZIP compression here as middleware: it needs to be done
# selectively by content type, and is best applied automatically by Apache
# (which is easy).
if DEBUG_TO_HTTP_CLIENT:
    webview_application = wsgi_errorreporter.ErrorReportingMiddleware(
        webview_application)
if PROFILE:
    webview_application = werkzeug.contrib.profiler.ProfilerMiddleware(
        webview_application)
    database_application = werkzeug.contrib.profiler.ProfilerMiddleware(
        database_application)


def application(environ, start_response):
    """Master WSGI entry point."""
    # logger.debug("WSGI environment: {}".format(repr(environ)))
    path = environ['PATH_INFO']
    logger.debug("PATH_INFO: {}".format(path))
    if path == URL_ROOT_WEBVIEW:
        return webview_application(environ, start_response)
    elif path == URL_ROOT_DATABASE:
        return database_application(environ, start_response)
    else:
        # No URL matches
        msg = "Not found."
        output = msg.encode('utf-8')
        start_response('404 Not Found', [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(output))),
        ])
        return [output]


if SERVE_STATIC_FILES:
    application = SharedDataMiddleware(application, {
        URL_ROOT_STATIC: os.path.join(os.path.dirname(__file__), 'static')
    })


# =============================================================================
# User command-line interaction
# =============================================================================

def ask_user(prompt, default=None):
    """Prompts the user, with a default. Returns a string."""
    if default is None:
        prompt = prompt + ": "
    else:
        prompt = prompt + " [" + default + "]: "
    result = input(prompt)
    return result if len(result) > 0 else default


def ask_user_password(prompt):
    """Read a password from the console."""
    return getpass.getpass(prompt + ": ")


# =============================================================================
# Version-specific database changes
# =============================================================================

def report_database_upgrade_step(version):
    print("PERFORMING UPGRADE TASKS FOR VERSION {}".format(version))


def modify_column(table, field, newdef):
    pls.db.modify_column_if_table_exists(table, field, newdef)


def change_column(tablename, oldfieldname, newfieldname, newdef):
    pls.db.change_column_if_table_exists(tablename, oldfieldname, newfieldname,
                                         newdef)


def rename_table(from_table, to_table):
    pls.db.rename_table(from_table, to_table)


def upgrade_database(old_version):
    print("Old database version: {}. New version: {}.".format(
        old_version,
        CAMCOPS_SERVER_VERSION
    ))
    if old_version is None:
        logger.warning("Don't know old database version; can't upgrade "
                       "structure")
        return

    # Proceed IN SEQUENCE from older to newer versions.
    # Don't assume that tables exist already.
    # The changes are performed PRIOR to making tables afresh (which will
    # make any new columns required, and thereby block column renaming).
    # DO NOT DO THINGS THAT WOULD DESTROY USERS' DATA.

    if (old_version < 1.06):
        report_database_upgrade_step("1.06")
        pls.db.drop_table("_dirty_tables")

    if (old_version < 1.07):
        report_database_upgrade_step("1.07")
        pls.db.drop_table("_security_webviewer_sessions")

    if (old_version < 1.08):
        report_database_upgrade_step("1.08")
        change_column("_security_users",
                      "may_alter_users", "superuser", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_commentary", "hv_commentary", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_discussing", "hv_discussing", "BOOLEAN")
        change_column("icd10schizophrenia",
                      "tpah_from_body", "hv_from_body", "BOOLEAN")

    if (old_version < 1.10):
        report_database_upgrade_step("1.10")
        modify_column("patient", "forename", "VARCHAR(255) NULL")
        modify_column("patient", "surname", "VARCHAR(255) NULL")
        modify_column("patient", "dob", "VARCHAR(32) NULL")
        modify_column("patient", "sex", "VARCHAR(1) NULL")

    if (old_version < 1.11):
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

    if (old_version < 1.15):
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

    # (etc.)


# =============================================================================
# Command-line debugging
# =============================================================================

# a = cc_task.TaskFactory("ace3", 6)
# a = cc_task.TaskFactory("ace3", 10)
# a.dump()
# a.write_pdf_to_disk("ace3test.pdf")

# p = cc_task.TaskFactory("phq9", 86)
# p = cc_task.TaskFactory("phq9", 1)
# p = cc_task.TaskFactory("phq9", 15)
# p.dump()
# p.write_pdf_to_disk("phq9test.pdf")

# b = cc_blob.Blob(3)

# create_demo_user()


# =============================================================================
# Command-line functions
# =============================================================================

def make_tables(drop_superfluous_columns=False):
    """Make database tables."""

    print(SEPARATOR_EQUALS)
    print("Checking +/- modifying database structure.")
    print("If this pauses, run 'sudo apachectl restart' in another terminal.")
    if drop_superfluous_columns:
        print("DROPPING SUPERFLUOUS COLUMNS")
    print(SEPARATOR_EQUALS)

    # MySQL engine settings
    failed = False
    INSERTMSG = " into my.cnf [mysqld] section, and restart MySQL"
    if not pls.db.mysql_using_innodb_strict_mode():
        logger.error("NOT USING innodb_strict_mode; please insert "
                     "'innodb_strict_mode = 1'" + INSERTMSG)
        failed = True
    max_allowed_packet = pls.db.mysql_get_max_allowed_packet()
    size_32M = 32 * 1024 * 1024
    if max_allowed_packet < size_32M:
        logger.error(
            "MySQL max_allowed_packet < 32M (it's {} and needs to be {}); "
            "please insert 'max_allowed_packet = 32M'".format(
                max_allowed_packet,
                size_32M,
            ) + INSERTMSG)
        failed = True
    if not pls.db.mysql_using_file_per_table():
        logger.error(
            "NOT USING innodb_file_per_table; please insert "
            "'innodb_file_per_table = 1'" + INSERTMSG)
        failed = True
    if not pls.db.mysql_using_innodb_barracuda():
        logger.error(
            "innodb_file_format IS NOT Barracuda; please insert "
            "'innodb_file_per_table = Barracuda'" + INSERTMSG)
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
    sv_version = ServerStoredVar("serverCamcopsVersion", "real")
    old_version = sv_version.getValue()
    upgrade_database(old_version)
    # Important that we write the new version now:
    sv_version.setValue(CAMCOPS_SERVER_VERSION)
    # This value must only be written in conjunction with the database
    # upgrade process.

    print(SEPARATOR_HYPHENS)
    print("Making core tables")
    print(SEPARATOR_HYPHENS)

    # Other system tables
    cc_user.User.make_tables(drop_superfluous_columns)
    cc_device.Device.make_tables(drop_superfluous_columns)
    cc_hl7.HL7Run.make_tables(drop_superfluous_columns)
    cc_hl7.HL7Message.make_tables(drop_superfluous_columns)
    cc_session.Session.make_tables(drop_superfluous_columns)
    SpecialNote.make_tables(drop_superfluous_columns)

    # Core client tables
    cc_patient.Patient.make_tables(drop_superfluous_columns)
    cc_blob.Blob.make_tables(drop_superfluous_columns)
    DeviceStoredVar.make_tables(drop_superfluous_columns)

    # System tables without a class representation
    cc_db.create_or_update_table(
        DIRTY_TABLES_TABLENAME, DIRTY_TABLES_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)
    pls.db.create_or_replace_primary_key(DIRTY_TABLES_TABLENAME,
                                         ["device", "tablename"])
    cc_db.create_or_update_table(
        SECURITY_AUDIT_TABLENAME, SECURITY_AUDIT_FIELDSPECS,
        drop_superfluous_columns=drop_superfluous_columns)

    # Task tables
    print(SEPARATOR_HYPHENS)
    print("Making task tables")
    print(SEPARATOR_HYPHENS)
    for cls in cc_task.Task.__subclasses__():
        print(
            "Making table(s) and view(s) for task: "
            + cls.get_taskshortname()
        )
        cls.make_tables(drop_superfluous_columns)

    audit("Created/recreated main tables", from_console=True)


def export_descriptions_comments():
    """Export an HTML version of database fields/comments to a file of the
    user's choice."""
    filename = ask_user("Output HTML file",
                        "camcops_table_descriptions.html")
    include_views = ask_user(
        "Include views (leave blank for no, anything else for yes)? "
    )
    with open(filename, 'wb') as file:
        webview.write_descriptions_comments(file, include_views)
    print("Done.")


def reset_storedvars():
    """Copy key descriptions (database title, ID descriptions, policies) from
    the config file to the database.

    These are stored so researchers can access them from the database.
    However, they're not used directly by the server (or the database.pl upload
    script).
    """
    print("Setting database title/ID descriptions from configuration file")
    dbt = ServerStoredVar("databaseTitle", "text")
    dbt.setValue(pls.DATABASE_TITLE)
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        i = n - 1
        nstr = str(n)
        sv_id = ServerStoredVar("idDescription" + nstr, "text")
        sv_id.setValue(pls.IDDESC[i])
        sv_sd = ServerStoredVar("idShortDescription" + nstr, "text")
        sv_sd.setValue(pls.IDSHORTDESC[i])
    sv_id_policy_upload = ServerStoredVar("idPolicyUpload", "text")
    sv_id_policy_upload.setValue(pls.ID_POLICY_UPLOAD_STRING)
    sv_id_policy_finalize = ServerStoredVar("idPolicyFinalize", "text")
    sv_id_policy_finalize.setValue(pls.ID_POLICY_FINALIZE_STRING)
    audit("Reset stored variables", from_console=True)


def generate_anonymisation_staging_db():
    db = pls.get_anonymisation_database()  # may raise
    ddfilename = pls.EXPORT_CRIS_DATA_DICTIONARY_TSV_FILE
    classes = cc_task.Task.__subclasses__()
    classes.sort(key=lambda cls: cls.get_taskshortname())
    with codecs.open(ddfilename, mode="w", encoding="utf8") as f:
        written_header = False
        for cls in classes:
            if cls.is_anonymous():
                continue
            # Drop, make and populate tables
            cls.make_cris_tables(db)
            # Add info to data dictionary
            rows = cls.get_cris_dd_rows()
            if not rows:
                continue
            if not written_header:
                f.write(webview.get_tsv_header_from_dict(rows[0]) + "\n")
                written_header = True
            for r in rows:
                f.write(webview.get_tsv_line_from_dict(r) + "\n")
    db.commit()
    print("Draft data dictionary written to {}".format(ddfilename))


def make_superuser():
    """Make a superuser from the command line."""
    print("MAKE SUPERUSER")
    username = ask_user("New superuser")
    if cc_user.user_exists(username):
        print("... user already exists!")
        return
    password1 = ask_user_password("New superuser password")
    password2 = ask_user_password("New superuser password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = cc_user.create_superuser(username, password1)
    print("Success: " + str(result))


def reset_password():
    """Reset a password from the command line."""
    print("RESET PASSWORD")
    username = ask_user("Username")
    if not cc_user.user_exists(username):
        print("... user doesn't exist!")
        return
    password1 = ask_user_password("New password")
    password2 = ask_user_password("New password (again)")
    if password1 != password2:
        print("... passwords don't match; try again")
        return
    result = cc_user.set_password_directly(username, password1)
    print("Success: " + str(result))


def enable_user_cli():
    """Re-enable a locked user account from the command line."""
    print("ENABLE LOCKED USER ACCOUNT")
    username = ask_user("Username")
    if not cc_user.user_exists(username):
        print("... user doesn't exist!")
        return
    cc_user.enable_user(username)
    print("Enabled.")


# -----------------------------------------------------------------------------
# Test rig
# -----------------------------------------------------------------------------

def test():
    """Run all unit tests."""
    # We do some rollbacks so as not to break performance of ongoing tasks.

    print("-- Testing camcopswebview")
    webview.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_analytics")
    cc_analytics.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_blob")
    cc_blob.unit_tests()
    pls.db.rollback()

    # cc_constants: no functions

    print("-- Testing cc_device")
    cc_device.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_dump")
    cc_dump.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_hl7core")
    cc_hl7core.unit_tests()
    pls.db.rollback()

    # cc_namedtuples: simple, and doesn't need cc_shared

    print("-- Testing cc_patient")
    cc_patient.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_policy")
    cc_policy.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_report")
    cc_report.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_session")
    cc_session.unit_tests()
    pls.db.rollback()

    # at present only tested implicitly: cc_shared

    print("-- Testing cc_tracker")
    cc_tracker.unit_tests()
    pls.db.rollback()

    print("-- Testing cc_user")
    cc_user.unit_tests()
    pls.db.rollback()

    # cc_version: no functions

    # Done last (slowest)
    print("-- Testing cc_task")
    cc_task.unit_tests()
    pls.db.rollback()


# =============================================================================
# Command-line processor
# =============================================================================

def cli_main():
    """Command-line entry point."""
    # Fetch command-line options.
    silent = False
    parser = argparse.ArgumentParser(
        prog="camcops",  # name the user will use to call it
        description=("CamCOPS command-line tool. "
                     "Run with no arguments for an interactive menu.")
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version="CamCOPS {}".format(CAMCOPS_SERVER_VERSION))
    parser.add_argument(
        "-m", "--maketables",
        action="store_true", default=False,
        help="Make/remake tables and views")
    parser.add_argument(
        "--dropsuperfluous", action="store_true",
        help="Additional option to --maketables to drop superfluous columns; "
        "requires both confirmatory flags as well")
    parser.add_argument(
        "--confirm_drop_superfluous_1", action="store_true",
        help="Confirmatory flag 1/2 for --dropsuperfluous")
    parser.add_argument(
        "--confirm_drop_superfluous_2", action="store_true",
        help="Confirmatory flag 2/2 for --dropsuperfluous")
    parser.add_argument(
        "-r", "--resetstoredvars", action="store_true", default=False,
        help="Redefine database title/patient ID number meanings/ID policy")
    parser.add_argument(
        "-t", "--title", action="store_true", default=False, dest="showtitle",
        help="Show database title")
    parser.add_argument(
        "-s", "--summarytables", action="store_true", default=False,
        help="Make summary tables")
    parser.add_argument(
        "-u", "--superuser", action="store_true", default=False,
        help="Make superuser")
    parser.add_argument(
        "-p", "--password", action="store_true", default=False,
        help="Reset a user's password")
    parser.add_argument(
        "-e", "--enableuser", action="store_true", default=False,
        help="Re-enable a locked user account")
    parser.add_argument(
        "-d", "--descriptions", action="store_true", default=False,
        help="Export table descriptions")
    parser.add_argument(
        "-7", "--hl7", action="store_true", default=False,
        help="Send pending HL7 messages and outbound files")
    parser.add_argument(
        "-q", "--queue", action="store_true", default=False,
        dest="show_hl7_queue",
        help="View outbound HL7/file queue (without sending)")
    parser.add_argument(
        "-y", "--anonstaging", action="store_true", default=False,
        help="Generate/regenerate anonymisation staging database")
    parser.add_argument(
        "-x", "--test", action="store_true", default=False,
        help="Test internal code")
    parser.add_argument(
        "--dbunittest", action="store_true", default=False,
        help="Unit tests for database code")
    parser.add_argument(
        "configfilename", nargs="?", default=None,
        help="Configuration file. (When run in WSGI mode, this is read from "
             "the CAMCOPS_CONFIG_FILE variable in (1) the WSGI environment, "
             "or (2) the operating system environment.)")
    args = parser.parse_args()

    if args.show_hl7_queue:
        silent = True

    # Say hello
    if not silent:
        print("CamCOPS version {}".format(CAMCOPS_SERVER_VERSION))
        print("By Rudolf Cardinal. See " + CAMCOPS_URL)

    # If we don't know the config filename yet, ask the user
    if not args.configfilename:
        args.configfilename = ask_user("Configuration file",
                                       DEFAULT_CONFIG_FILENAME)
    # The set_from_environ_and_ping_db() function wants the config filename in
    # the environment:
    os.environ["CAMCOPS_CONFIG_FILE"] = args.configfilename
    if not silent:
        print("Using configuration file: {}".format(args.configfilename))

    # Set all other variables (inc. read from config file, open database)
    try:
        if not silent:
            print("Processing configuration information and connecting "
                  "to database (this may take some time)...")
        pls.set_from_environ_and_ping_db(os.environ)
    except configparser.NoSectionError:
        print("""
You may not have the necessary privileges to read the configuration file, or it
may not exist, or be incomplete.
""")
        raise
    except rnc_db.NoDatabaseError:
        print("""
If the database failed to open, ensure it has been created. To create a
database, for example, in MySQL:
    CREATE DATABASE camcops;
""")
        raise

    # In order:
    n_actions = 0

    if args.maketables:
        drop_superfluous_columns = False
        if (args.dropsuperfluous and args.confirm_drop_superfluous_1
                and args.confirm_drop_superfluous_2):
            drop_superfluous_columns = True
        make_tables(drop_superfluous_columns)
        n_actions += 1

    if args.resetstoredvars:
        reset_storedvars()
        n_actions += 1

    if args.showtitle:
        print("Database title: {}".format(get_database_title()))
        n_actions += 1

    if args.summarytables:
        make_summary_tables()
        n_actions += 1

    if args.superuser:
        make_superuser()
        n_actions += 1

    if args.password:
        reset_password()
        n_actions += 1

    if args.descriptions:
        export_descriptions_comments()
        n_actions += 1

    if args.enableuser:
        enable_user_cli()
        n_actions += 1

    if args.hl7:
        cc_hl7.send_all_pending_hl7_messages()
        n_actions += 1

    if args.show_hl7_queue:
        cc_hl7.send_all_pending_hl7_messages(show_queue_only=True)
        n_actions += 1

    if args.anonstaging:
        generate_anonymisation_staging_db()
        n_actions += 1

    if args.test:
        test()
        n_actions += 1

    if args.dbunittest:
        database.unit_tests()
        n_actions += 1

    if n_actions > 0:
        pls.db.commit()  # command-line non-interactive route commit
        sys.exit()
        # ... otherwise proceed to the menu

    # Menu
    while True:
        print("""
{sep}
CamCOPS version {version} (command line).
Using database: {dbname} ({dbtitle}).

1) Make/remake tables and views
   ... MUST be the first action on a new database
   ... will not destroy existing data
   ... also performs item 3 below
2) Show database title
3) Copy database title/patient ID number meanings/ID policy into database
4) Make summary tables
5) Make superuser
6) Reset a user's password
7) Enable a locked user account
8) Export table descriptions with field comments
9) Test internal code (should always succeed)
10) Send all pending HL7 messages
11) Show HL7 queue without sending
12) Regenerate anonymisation staging database
13) Exit
""".format(sep=SEPARATOR_EQUALS,
           version=CAMCOPS_SERVER_VERSION,
           dbname=pls.DB_NAME,
           dbtitle=get_database_title()))

        # avoid input():
        # http://www.gossamer-threads.com/lists/python/python/46911
        choice = input("Choose: ")
        try:
            choice = int(choice)
        except ValueError:
            choice = None

        if choice == 1:
            make_tables(drop_superfluous_columns=False)
            reset_storedvars()
        elif choice == 2:
            print("Database title: {}".format(get_database_title()))
        elif choice == 3:
            reset_storedvars()
        elif choice == 4:
            make_summary_tables(from_console=True)
        elif choice == 5:
            make_superuser()
        elif choice == 6:
            reset_password()
        elif choice == 7:
            enable_user_cli()
        elif choice == 8:
            export_descriptions_comments()
        elif choice == 9:
            test()
        elif choice == 10:
            cc_hl7.send_all_pending_hl7_messages()
        elif choice == 11:
            cc_hl7.send_all_pending_hl7_messages(show_queue_only=True)
        elif choice == 12:
            generate_anonymisation_staging_db()
        elif choice == 13:
            sys.exit()

        # Must commit, or we may lock the database while watching the menu
        pls.db.commit()  # command-line interactive menu route commit


# =============================================================================
# Command-line entry point
# =============================================================================

if __name__ == '__main__':
    cli_main()
