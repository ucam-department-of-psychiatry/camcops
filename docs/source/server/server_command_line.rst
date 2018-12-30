..  docs/source/server/server_command_line.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

.. _server_command_line_tools:

CamCOPS command-line tools
==========================

.. _camcops_cli:

camcops_server
--------------

The ``camcops_server`` command is the main interface to the CamCOPS server.
Options as of 2018-12-30 (output from ``camcops_server --allhelp``):

.. code-block:: none

    usage: camcops_server [-h] [--allhelp] [--version] [-v]
                          {docs,demo_camcops_config,demo_supervisor_config,demo_apache_config,demo_mysql_create_db,demo_mysql_dump_script,upgrade_db,dev_upgrade_to,dev_downgrade_db,show_db_title,merge_db,create_db,ddl,reindex,make_superuser,reset_password,enable_user,export,show_export_queue,serve_cherrypy,serve_gunicorn,serve_pyramid,convert_athena_icd_snomed_to_xml,launch_workers,launch_scheduler,launch_monitor,show_tests,self_test,dev_cli}
                          ...

    CamCOPS server, created by Rudolf Cardinal; version 2.3.1.
    Use 'camcops_server <COMMAND> --help' for more detail on each command.

    optional arguments:
      -h, --help            show this help message and exit
      --allhelp             show help for all commands and exit
      --version             show program's version number and exit
      -v, --verbose         Be verbose

    commands:
      Valid CamCOPS commands are as follows.

      {docs,demo_camcops_config,demo_supervisor_config,demo_apache_config,demo_mysql_create_db,demo_mysql_dump_script,upgrade_db,dev_upgrade_to,dev_downgrade_db,show_db_title,merge_db,create_db,ddl,reindex,make_superuser,reset_password,enable_user,export,show_export_queue,serve_cherrypy,serve_gunicorn,serve_pyramid,convert_athena_icd_snomed_to_xml,launch_workers,launch_scheduler,launch_monitor,show_tests,self_test,dev_cli}
                            Specify one command.
        docs                Launch the main documentation (CamCOPS manual)
        demo_camcops_config
                            Print a demo CamCOPS config file
        demo_supervisor_config
                            Print a demo 'supervisor' config file for CamCOPS
        demo_apache_config  Print a demo Apache config file section for CamCOPS
        demo_mysql_create_db
                            Print demo instructions to create a MySQL database for
                            CamCOPS
        demo_mysql_dump_script
                            Print demo instructions to dump all current MySQL
                            databases
        upgrade_db          Upgrade database to most recent version (via Alembic)
        dev_upgrade_to      (DEVELOPER OPTION ONLY.) Upgrade a database to a
                            specific revision.
        dev_downgrade_db    (DEVELOPER OPTION ONLY.) Downgrades a database to a
                            specific revision. May DESTROY DATA.
        show_db_title       Show database title
        merge_db            Merge in data from an old or recent CamCOPS database
        create_db           Create CamCOPS database from scratch (AVOID; use the
                            upgrade facility instead)
        ddl                 Print database schema (data definition language; DDL)
        reindex             Recreate task index
        make_superuser      Make superuser, or give superuser status to an
                            existing user
        reset_password      Reset a user's password
        enable_user         Re-enable a locked user account
        export              Trigger pending exports
        show_export_queue   View outbound export queue (without sending)
        serve_cherrypy      Start web server via CherryPy
        serve_gunicorn      Start web server via Gunicorn (not available under
                            Windows)
        serve_pyramid       Start test web server via Pyramid (single-thread,
                            single-process, HTTP-only; for development use only)
        convert_athena_icd_snomed_to_xml
                            Fetch SNOMED-CT codes for ICD-9-CM and ICD-10 from the
                            Athena OHDSI data set (http://athena.ohdsi.org/) and
                            write them to the CamCOPS XML format
        launch_workers      Launch Celery workers, for background processing
        launch_scheduler    Launch Celery Beat scheduler, to schedule background
                            jobs
        launch_monitor      Launch Celery Flower monitor, to monitor background
                            jobs
        show_tests          Show available self-tests
        self_test           Test internal code
        dev_cli             Developer command-line interface, with config loaded
                            as 'config'.

    ===============================================================================
    Help for command 'docs'
    ===============================================================================
    usage: camcops_server docs [-h] [-v]

    Launch the main documentation (CamCOPS manual)

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_camcops_config'
    ===============================================================================
    usage: camcops_server demo_camcops_config [-h] [-v]

    Print a demo CamCOPS config file

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_supervisor_config'
    ===============================================================================
    usage: camcops_server demo_supervisor_config [-h] [-v]

    Print a demo 'supervisor' config file for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_apache_config'
    ===============================================================================
    usage: camcops_server demo_apache_config [-h] [-v]

    Print a demo Apache config file section for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_mysql_create_db'
    ===============================================================================
    usage: camcops_server demo_mysql_create_db [-h] [-v]

    Print demo instructions to create a MySQL database for CamCOPS

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'demo_mysql_dump_script'
    ===============================================================================
    usage: camcops_server demo_mysql_dump_script [-h] [-v]

    Print demo instructions to dump all current MySQL databases

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'upgrade_db'
    ===============================================================================
    usage: camcops_server upgrade_db [-h] [-v] --config CONFIG [--show_sql_only]

    Upgrade database to most recent version (via Alembic)

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --show_sql_only  Show SQL only (to stdout); don't execute it (default:
                       False)

    required named arguments:
      --config CONFIG  Configuration file (default: None)

    ===============================================================================
    Help for command 'dev_upgrade_to'
    ===============================================================================
    usage: camcops_server dev_upgrade_to [-h] [-v] --config CONFIG
                                         --destination_db_revision
                                         DESTINATION_DB_REVISION [--show_sql_only]

    (DEVELOPER OPTION ONLY.) Upgrade a database to a specific revision.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --destination_db_revision DESTINATION_DB_REVISION
                            The target database revision (default: None)
      --show_sql_only       Show SQL only (to stdout); don't execute it (default:
                            False)

    required named arguments:
      --config CONFIG       Configuration file (default: None)

    ===============================================================================
    Help for command 'dev_downgrade_db'
    ===============================================================================
    usage: camcops_server dev_downgrade_db [-h] [-v] --config CONFIG
                                           --destination_db_revision
                                           DESTINATION_DB_REVISION
                                           [--confirm_downgrade_db]
                                           [--show_sql_only]

    (DEVELOPER OPTION ONLY.) Downgrades a database to a specific revision. May
    DESTROY DATA.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --destination_db_revision DESTINATION_DB_REVISION
                            The target database revision (default: None)
      --confirm_downgrade_db
                            Must specify this too, as a safety measure (default:
                            False)
      --show_sql_only       Show SQL only (to stdout); don't execute it (default:
                            False)

    required named arguments:
      --config CONFIG       Configuration file (default: None)

    ===============================================================================
    Help for command 'show_db_title'
    ===============================================================================
    usage: camcops_server show_db_title [-h] [-v] [--config CONFIG]

    Show database title

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'merge_db'
    ===============================================================================
    usage: camcops_server merge_db [-h] [-v] --config CONFIG
                                   [--report_every REPORT_EVERY] [--echo]
                                   [--dummy_run] [--info_only] [--skip_hl7_logs]
                                   [--skip_audit_logs]
                                   [--default_group_id DEFAULT_GROUP_ID]
                                   [--default_group_name DEFAULT_GROUP_NAME] --src
                                   SRC

    Merge in data from an old or recent CamCOPS database

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --report_every REPORT_EVERY
                            Report progress every n rows (default: 10000)
      --echo                Echo SQL to source database (default: False)
      --dummy_run           Perform a dummy run only; do not alter destination
                            database (default: False)
      --info_only           Show table information only; don't do any work
                            (default: False)
      --skip_hl7_logs       Skip the HL7 message log table (default: False)
      --skip_audit_logs     Skip the audit log table (default: False)
      --default_group_id DEFAULT_GROUP_ID
                            Default group ID (integer) to apply to old records
                            without one. If none is specified, a new group will be
                            created for such records. (default: None)
      --default_group_name DEFAULT_GROUP_NAME
                            If default_group_id is not specified, use this group
                            name. The group will be looked up if it exists, and
                            created if not. (default: None)

    required named arguments:
      --config CONFIG       Configuration file (default: None)
      --src SRC             Source database (specified as an SQLAlchemy URL). The
                            contents of this database will be merged into the
                            database specified in the config file. (default: None)

    ===============================================================================
    Help for command 'create_db'
    ===============================================================================
    usage: camcops_server create_db [-h] [-v] --config CONFIG --confirm_create_db

    Create CamCOPS database from scratch (AVOID; use the upgrade facility instead)

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)

    required named arguments:
      --config CONFIG      Configuration file (default: None)
      --confirm_create_db  Must specify this too, as a safety measure (default:
                           False)

    ===============================================================================
    Help for command 'ddl'
    ===============================================================================
    usage: camcops_server ddl [-h] [-v] [--config CONFIG] [--dialect DIALECT]

    Print database schema (data definition language; DDL)

    optional arguments:
      -h, --help         show this help message and exit
      -v, --verbose      Be verbose (default: False)
      --config CONFIG    Configuration file (if not specified, the environment
                         variable CAMCOPS_CONFIG_FILE is checked) (default: None)
      --dialect DIALECT  SQL dialect (options: oracle, mysql, firebird, sybase,
                         mssql, sqlite, postgresql) (default: mysql)

    ===============================================================================
    Help for command 'reindex'
    ===============================================================================
    usage: camcops_server reindex [-h] [-v] [--config CONFIG]

    Recreate task index

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'make_superuser'
    ===============================================================================
    usage: camcops_server make_superuser [-h] [-v] [--config CONFIG]
                                         [--username USERNAME]

    Make superuser, or give superuser status to an existing user

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username of superuser to create/promote (if omitted,
                           you will be asked to type it in) (default: None)

    ===============================================================================
    Help for command 'reset_password'
    ===============================================================================
    usage: camcops_server reset_password [-h] [-v] [--config CONFIG]
                                         [--username USERNAME]

    Reset a user's password

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username to change password for (if omitted, you will
                           be asked to type it in) (default: None)

    ===============================================================================
    Help for command 'enable_user'
    ===============================================================================
    usage: camcops_server enable_user [-h] [-v] [--config CONFIG]
                                      [--username USERNAME]

    Re-enable a locked user account

    optional arguments:
      -h, --help           show this help message and exit
      -v, --verbose        Be verbose (default: False)
      --config CONFIG      Configuration file (if not specified, the environment
                           variable CAMCOPS_CONFIG_FILE is checked) (default:
                           None)
      --username USERNAME  Username to enable (if omitted, you will be asked to
                           type it in) (default: None)

    ===============================================================================
    Help for command 'export'
    ===============================================================================
    usage: camcops_server export [-h] [-v] [--config CONFIG]
                                 [--recipients [RECIPIENTS [RECIPIENTS ...]]]
                                 [--all_recipients] [--disable_task_index]

    Trigger pending exports

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --recipients [RECIPIENTS [RECIPIENTS ...]]
                            Export recipients (as named in config file) (default:
                            None)
      --all_recipients      Use all recipients (default: False)
      --disable_task_index  Disable use of the task index (for debugging only)
                            (default: False)

    ===============================================================================
    Help for command 'show_export_queue'
    ===============================================================================
    usage: camcops_server show_export_queue [-h] [-v] [--config CONFIG]
                                            [--recipients [RECIPIENTS [RECIPIENTS ...]]]
                                            [--all_recipients]
                                            [--disable_task_index] [--pretty]

    View outbound export queue (without sending)

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --recipients [RECIPIENTS [RECIPIENTS ...]]
                            Export recipients (as named in config file) (default:
                            None)
      --all_recipients      Use all recipients (default: False)
      --disable_task_index  Disable use of the task index (for debugging only)
                            (default: False)
      --pretty              Pretty (but slower) formatting for tasks (default:
                            False)

    ===============================================================================
    Help for command 'serve_cherrypy'
    ===============================================================================
    usage: camcops_server serve_cherrypy [-h] [-v] [--config CONFIG]

    Start web server via CherryPy

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'serve_gunicorn'
    ===============================================================================
    usage: camcops_server serve_gunicorn [-h] [-v] [--config CONFIG]

    Start web server via Gunicorn (not available under Windows)

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'serve_pyramid'
    ===============================================================================
    usage: camcops_server serve_pyramid [-h] [-v] [--config CONFIG]

    Start test web server via Pyramid (single-thread, single-process, HTTP-only;
    for development use only)

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'convert_athena_icd_snomed_to_xml'
    ===============================================================================
    usage: camcops_server convert_athena_icd_snomed_to_xml [-h] [-v]
                                                           [--config CONFIG]
                                                           --athena_concept_tsv_filename
                                                           ATHENA_CONCEPT_TSV_FILENAME
                                                           --athena_concept_relationship_tsv_filename
                                                           ATHENA_CONCEPT_RELATIONSHIP_TSV_FILENAME
                                                           --icd9_xml_filename
                                                           ICD9_XML_FILENAME
                                                           --icd10_xml_filename
                                                           ICD10_XML_FILENAME

    Fetch SNOMED-CT codes for ICD-9-CM and ICD-10 from the Athena OHDSI data set
    (http://athena.ohdsi.org/) and write them to the CamCOPS XML format

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be verbose (default: False)
      --config CONFIG       Configuration file (if not specified, the environment
                            variable CAMCOPS_CONFIG_FILE is checked) (default:
                            None)
      --athena_concept_tsv_filename ATHENA_CONCEPT_TSV_FILENAME
                            Path to CONCEPT.csv file from Athena download
                            (default: None)
      --athena_concept_relationship_tsv_filename ATHENA_CONCEPT_RELATIONSHIP_TSV_FILENAME
                            Path to CONCEPT_RELATIONSHIP.csv file from Athena
                            download (default: None)
      --icd9_xml_filename ICD9_XML_FILENAME
                            Filename of ICD-9-CM/SNOMED-CT XML file to write
                            (default: None)
      --icd10_xml_filename ICD10_XML_FILENAME
                            Filename of ICD-10/SNOMED-CT XML file to write
                            (default: None)

    ===============================================================================
    Help for command 'launch_workers'
    ===============================================================================
    usage: camcops_server launch_workers [-h] [-v] [--config CONFIG]

    Launch Celery workers, for background processing

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'launch_scheduler'
    ===============================================================================
    usage: camcops_server launch_scheduler [-h] [-v] [--config CONFIG]

    Launch Celery Beat scheduler, to schedule background jobs

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)

    ===============================================================================
    Help for command 'launch_monitor'
    ===============================================================================
    usage: camcops_server launch_monitor [-h] [-v] [--config CONFIG]
                                         [--address ADDRESS] [--port PORT]

    Launch Celery Flower monitor, to monitor background jobs

    optional arguments:
      -h, --help         show this help message and exit
      -v, --verbose      Be verbose (default: False)
      --config CONFIG    Configuration file (if not specified, the environment
                         variable CAMCOPS_CONFIG_FILE is checked) (default: None)
      --address ADDRESS  Address to use for Flower (default: 127.0.0.1)
      --port PORT        Port to use for Flower (default: 5555)

    ===============================================================================
    Help for command 'show_tests'
    ===============================================================================
    usage: camcops_server show_tests [-h] [-v]

    Show available self-tests

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'self_test'
    ===============================================================================
    usage: camcops_server self_test [-h] [-v]

    Test internal code

    optional arguments:
      -h, --help     show this help message and exit
      -v, --verbose  Be verbose (default: False)

    ===============================================================================
    Help for command 'dev_cli'
    ===============================================================================
    usage: camcops_server dev_cli [-h] [-v] [--config CONFIG]

    Developer command-line interface, with config loaded as 'config'.

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Be verbose (default: False)
      --config CONFIG  Configuration file (if not specified, the environment
                       variable CAMCOPS_CONFIG_FILE is checked) (default: None)


.. _camcops_server_meta:

camcops_server_meta
-------------------

The ``camcops_server_meta`` tool allows you to run CamCOPS over multiple
CamCOPS configuration files/databases. It’s less useful than it was, because
the dominant mode of “one database per research group” has been replaced by the
concept of “a single database with group-level security”.

Options as of 2018-11-09:

.. code-block:: none

    usage: camcops_server_meta [-h] --filespecs FILESPECS [FILESPECS ...]
                               [--ccargs [CCARGS [CCARGS ...]]] [--python PYTHON]
                               [--camcops CAMCOPS] [-d] [-v]
                               cc_command

    Run commands across multiple CamCOPS databases

    positional arguments:
      cc_command            Main command to pass to CamCOPS

    optional arguments:
      -h, --help            show this help message and exit
      --filespecs FILESPECS [FILESPECS ...]
                            List of CamCOPS config files (wildcards OK)
      --ccargs [CCARGS [CCARGS ...]]
                            List of CamCOPS arguments, to which '--' will be
                            prefixed
      --python PYTHON       Python interpreter (default:
                            /home/rudolf/dev/venvs/camcops/bin/python3)
      --camcops CAMCOPS     CamCOPS server executable (default: /home/rudolf/Docum
                            ents/code/camcops/server/camcops_server.py)
      -d, --dummyrun        Dummy run (show filenames only)
      -v, --verbose         Verbose


.. _camcops_backup_mysql_database:

camcops_backup_mysql_database
-----------------------------

This simple tool uses MySQL to dump a MySQL database to a .SQL file (from which
you can restore it), and names the file according to the name of the database
plus a timestamp.

Options as of 2017-10-23:

.. code-block:: none

    usage: camcops_backup_mysql_database [-h]
                                         [--max_allowed_packet MAX_ALLOWED_PACKET]
                                         [--mysqldump MYSQLDUMP]
                                         [--username USERNAME]
                                         [--password PASSWORD]
                                         [--with_drop_create_database] [--verbose]
                                         databases [databases ...]

    Back up a specific MySQL database

    positional arguments:
      databases             Database(s) to back up

    optional arguments:
      -h, --help            show this help message and exit
      --max_allowed_packet MAX_ALLOWED_PACKET
                            Maximum size of buffer (default: 1GB)
      --mysqldump MYSQLDUMP
                            mysqldump executable (default: mysqldump)
      --username USERNAME   MySQL user (default: root)
      --password PASSWORD   MySQL password (AVOID THIS OPTION IF POSSIBLE; VERY
                            INSECURE; VISIBLE TO OTHER PROCESSES; if you don't use
                            it, you'll be prompted for the password) (default:
                            root)
      --with_drop_create_database
                            Include DROP DATABASE and CREATE DATABASE commands
                            (default: False)
      --verbose             Verbose output (default: False)
