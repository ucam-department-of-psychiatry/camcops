..  documentation/source/server/server_config_file.rst

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

.. _server_config_file:

The CamCOPS server configuration file
=====================================

CamCOPS needs a configuration file. Under Linux, this is normally something
that you create at `/etc/camcops/camcops.conf`, from a template produced by
CamCOPS. It is the configuration file that points to your database.

Databases and configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In general, it is best to have a single CamCOPS database and a single CamCOPS
configuration file. This is simple. You can add :ref:`groups <groups>`
dynamically, and use :ref:`group security <groups>` to manage data access.
Groups can be entirely isolated from each other, which mimics having multiple
databases, but they can also overlap in useful ways.

It’s also possible, of course, to have multiple CamCOPS databases, each with
its own configuration file.

If you do operate with multiple databases/configuration files, you may want to
use the :ref:`camcops_meta <camcops_meta>` tool, which allows you to run the
same :ref:`camcops <camcops_cli>` command over multiple configuration files in
one go (for example, to upgrade the databases for a new version of CamCOPS).

Format of the configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The config file is in standard `INI file format
<https://en.wikipedia.org/wiki/INI_file>`_.

Here’s a specimen configuration file, generated via the command `camcops
demo_camcops_config > demo_camcops_config.ini`:

.. code-block:: ini

    # Demonstration CamCOPS configuration file.
    # Created by CamCOPS version 2.2.1 at 2018-06-08T15:56:44.875146+01:00.

    # =============================================================================
    # Format of the CamCOPS configuration file
    # =============================================================================
    # COMMENTS. Hashes (#) and semicolons (;) mark out comments.
    # SECTIONS. Sections are indicated with: [section]
    # NAME/VALUE (KEY/VALUE) PAIRS.
    # - The parser used is ConfigParser (Python).
    # - It allows "name=value" or "name:value".
    # - BOOLEAN OPTIONS. For Boolean options, TRUE values are any of: 1, yes, true,
    #   on (case-insensitive). FALSE values are any of: 0, no, false, off.
    # - UTF-8 encoding. Use this. For ConfigParser, the file is explicitly opened
    #   in UTF-8 mode.
    # - Avoid indentation.

    # =============================================================================
    # Main section: [server]
    # =============================================================================

    [server]

    # -----------------------------------------------------------------------------
    # Database connection/tools
    # -----------------------------------------------------------------------------

    # DB_URL: SQLAlchemy connection URL.
    # See http://docs.sqlalchemy.org/en/latest/core/engines.html
    # Examples:
    # - MySQL under Linux via mysqlclient
    #   $$ pip install mysqlclient
    #   DB_URL = mysql+mysqldb://<username>:<password>@<host>:<port>/<database>?charset=utf8
    #
    #   (The default MySQL port is 3306, and 'localhost' is often the right host.)
    #
    # - SQL Server under Windows via ODBC and username/password authentication
    #   C:\> pip install pyodbc
    #   DB_URL = mssql+pyodbc://<username>:<password>@<odbc_dsn_name>
    #
    # - ... or via Windows authentication:
    #   DB_URL = mssql+pyodbc://@<odbc_dsn_name>

    DB_URL = mysql+mysqldb://YYY_USERNAME_REPLACE_ME:ZZZ_PASSWORD_REPLACE_ME@localhost:3306/camcops?charset=utf8

    # DB_ECHO: echo all SQL?

    DB_ECHO = False

    # -----------------------------------------------------------------------------
    # URLs and paths
    # -----------------------------------------------------------------------------
    #
    # A quick note on absolute and relative URLs, and how CamCOPS is mounted.
    #
    # Suppose your CamCOPS site is visible at
    #       https://www.somewhere.ac.uk/camcops_smith_lab/webview
    #       ^      ^^                 ^^                ^^      ^
    #       +------++-----------------++----------------++------+
    #       |       |                  |                 |
    #       1       2                  3                 4
    #
    # Part 1 is the protocol, and part 2 the machine name.
    # Part 3 is the mount point. The main server (e.g. Apache) knows where the
    # CamCOPS script is mounted (in this case /camcops_smith_lab). It does NOT
    # tell the script via the script's WSGI environment. Therefore, if the script
    # sends HTML including links, the script can operate only in relative mode.
    # For it to operate in absolute mode, it would need to know (3).
    # Part 4 is visible to the CamCOPS script.
    #
    # If CamCOPS emitted URLs starting with '/', it would need to be told at least
    # part (3). To use absolute URLs, it would need to know all of (1), (2), (3).
    # We will follow others (e.g. http://stackoverflow.com/questions/2005079) and
    # use only relative URLs.

    # LOCAL_INSTITUTION_URL: Clicking on your institution's logo in the CamCOPS
    # menu will take you to this URL.
    # Edit the next line to point to your institution:

    LOCAL_INSTITUTION_URL = http://www.mydomain/

    # LOCAL_LOGO_FILE_ABSOLUTE: Specify the full path to your institution's logo
    # file, e.g. /var/www/logo_local_myinstitution.png . It's used for PDF
    # generation; HTML views use the fixed string "static/logo_local.png", aliased
    # to your file via the Apache configuration file).
    # Edit the next line to point to your local institution's logo file:

    LOCAL_LOGO_FILE_ABSOLUTE = /home/rudolf/Documents/code/camcops/server/camcops_server/static/logo_local.png

    # CAMCOPS_LOGO_FILE_ABSOLUTE: similarly, but for the CamCOPS logo.
    # It's fine not to specify this.

    # CAMCOPS_LOGO_FILE_ABSOLUTE = /home/rudolf/Documents/code/camcops/server/camcops_server/static/logo_camcops.png

    # EXTRA_STRING_FILES: multiline list of filenames (with absolute paths), read
    # by the server, and used as EXTRA STRING FILES. Should at the MINIMUM point
    # to the string file camcops.xml
    # May use "glob" pattern-matching (see
    # https://docs.python.org/3.5/library/glob.html).

    EXTRA_STRING_FILES = /home/rudolf/Documents/code/camcops/server/camcops_server/extra_strings/*

    # INTROSPECTION: permits the offering of CamCOPS source code files to the user,
    # allowing inspection of tasks' internal calculating algorithms. Default is
    # true.

    INTROSPECTION = true

    # HL7_LOCKFILE: filename stem used for process locking for HL7 message
    # transmission. Default is /var/lock/camcops/camcops.hl7
    # The actual lockfile will, in this case, be called
    #     /var/lock/camcops/camcops.hl7.lock
    # and other process-specific files will be created in the same directory (so
    # the CamCOPS script must have permission from the operating system to do so).
    # The installation script will create the directory /var/lock/camcops

    HL7_LOCKFILE = /var/lock/camcops/camcops.hl7

    # SUMMARY_TABLES_LOCKFILE: file stem used for process locking for summary table
    # generation. Default is /var/lock/camcops/camcops.summarytables.
    # The lockfile will, in this case, be called
    #     /var/lock/camcops/camcops.summarytables.lock
    # and other process-specific files will be created in the same directory (so
    # the CamCOPS script must have permission from the operating system to do so).
    # The installation script will create the directory /var/lock/camcops

    SUMMARY_TABLES_LOCKFILE = /var/lock/camcops/camcops.summarytables

    # WKHTMLTOPDF_FILENAME: for the pdfkit PDF engine, specify a filename for
    # wkhtmltopdf that incorporates any need for an X Server (not the default
    # /usr/bin/wkhtmltopdf). See http://stackoverflow.com/questions/9604625/ .
    # A suitable one is bundled with CamCOPS, so you shouldn't have to alter this
    # default. Default is None, which usually ends up calling /usr/bin/wkhtmltopdf

    WKHTMLTOPDF_FILENAME =

    # -----------------------------------------------------------------------------
    # Login and session configuration
    # -----------------------------------------------------------------------------

    # SESSION_COOKIE_SECRET: Secret used for HTTP cookie signing via Pyramid.
    # Put something random in here and keep it secret.
    # (When you make a CamCOPS demo config, the value shown is fresh and random.)

    SESSION_COOKIE_SECRET = camcops_autogenerated_secret_uld31SfdoTT-IjNQKmAZxOXtIXl0QbWrGGiZQv89hoCvG3_SpDkhxZWSBxDpmIveRzmhH3SSoi4C7KB-3qnZNQ==

    # SESSION_TIMEOUT_MINUTES: Time after which a session will expire (default 30).

    SESSION_TIMEOUT_MINUTES = 30

    # PASSWORD_CHANGE_FREQUENCY_DAYS: Force password changes (at webview login)
    # with this frequency (0 for never). Note that password expiry will not prevent
    # uploads from tablets, but when the user next logs on, a password change will
    # be forced before they can do anything else.

    PASSWORD_CHANGE_FREQUENCY_DAYS = 0

    # LOCKOUT_THRESHOLD: Lock user accounts after every n login failures (default
    # 10).

    LOCKOUT_THRESHOLD = 10

    # LOCKOUT_DURATION_INCREMENT_MINUTES: Account lockout time increment (default
    # 10).
    # Suppose LOCKOUT_THRESHOLD = 10 and LOCKOUT_DURATION_INCREMENT_MINUTES = 20.
    # After the first 10 failures, the account will be locked for 20 minutes.
    # After the next 10 failures, the account will be locked for 40 minutes.
    # After the next 10 failures, the account will be locked for 60 minutes, and so
    # on. Time and administrators can unlock accounts.

    LOCKOUT_DURATION_INCREMENT_MINUTES = 10

    # DISABLE_PASSWORD_AUTOCOMPLETE: if true, asks browsers not to autocomplete the
    # password field on the main login page. The correct setting for maximum
    # security is debated (don't cache passwords, versus allow a password manager
    # so that users can use better/unique passwords). Default: true.
    # Note that some browsers (e.g. Chrome v34 and up) may ignore this.

    DISABLE_PASSWORD_AUTOCOMPLETE = true

    # -----------------------------------------------------------------------------
    # Suggested filenames for saving PDFs from the web view
    # -----------------------------------------------------------------------------
    # Try with Chrome, Firefox. Internet Explorer may be less obliging.

    # PATIENT_SPEC_IF_ANONYMOUS: for anonymous tasks, this fixed string is
    # used as the patient descriptor (see also PATIENT_SPEC below).
    # Typically "anonymous".

    PATIENT_SPEC_IF_ANONYMOUS = anonymous

    # PATIENT_SPEC: string, into which substitutions will be made, that defines the
    # {patient} element available for substitution into the *_FILENAME_SPEC
    # variables (see below). Possible substitutions:
    #
    #   {surname}      : patient's surname in upper case
    #   {forename}     : patient's forename in upper case
    #   {dob}          : patient's date of birth (format "%Y-%m-%d", e.g.
    #                    2013-07-24)
    #   {sex}          : patient's sex (M, F, X)
    #
    #   {idshortdesc1} : short description of the relevant ID number, if that ID
    #   {idshortdesc2}   number is not blank; otherwise blank
    #   ...
    #
    #   {idnum1}       : ID numbers
    #   {idnum2}
    #   ...
    #
    #   {allidnums}    : all available ID numbers in "shortdesc-value" pairs joined
    #                    by "_". For example, if ID numbers 1, 4, and 5 are
    #                    non-blank, this would have the format
    #                    idshortdesc1-idnum1_idshortdesc4-idnum4_idshortdesc5-idnum5

    PATIENT_SPEC = {surname}_{forename}_{allidnums}

    # TASK_FILENAME_SPEC:
    # TRACKER_FILENAME_SPEC:
    # CTV_FILENAME_SPEC:
    # Strings used for suggested filenames to save from the webview, for tasks,
    # trackers, and clinical text views. Substitutions will be made to determine
    # the filename to be used for each file. Possible substitutions:
    #
    #   {patient}   : Patient string. If the task is anonymous, this is
    #                 PATIENT_SPEC_IF_ANONYMOUS; otherwise, it is defined by
    #                 PATIENT_SPEC above.
    #   {created}   : Date/time of task creation.  Dates/times are of the format
    #                 "%Y-%m-%dT%H%M", e.g. 2013-07-24T2004. They are expressed in
    #                 the timezone of creation (but without the timezone
    #                 information for filename brevity).
    #   {now}       : Time of access/download (i.e. time now), in local timezone.
    #   {tasktype}  : Base table name of the task (e.g. "phq9"). May contain an
    #                 underscore. Blank for to trackers/CTVs.
    #   {serverpk}  : Server's primary key. (In combination with tasktype, this
    #                 uniquely identifies not just a task but a version of that
    #                 task.) Blank for trackers/CTVs.
    #   {filetype}  : e.g. "pdf", "html", "xml" (lower case)
    #   {anonymous} : evaluates to PATIENT_SPEC_IF_ANONYMOUS if anonymous,
    #                 otherwise ""
    #   ... plus all those substitutions applicable to PATIENT_SPEC
    #
    # After these substitutions have been made, the entire filename is then
    # processed to ensure that only characters generally acceptable to filenames
    # are used (see convert_string_for_filename() in the CamCOPS source code).
    # Specifically:
    #
    #   - Unicode converted to 7-bit ASCII (will mangle, e.g. removing accents)
    #   - spaces converted to underscores
    #   - characters are removed unless they are one of the following: all
    #     alphanumeric characters (0-9, A-Z, a-z); '-'; '_'; '.'; and the
    #     operating-system-specific directory separator (Python's os.sep, a forward
    #     slash '/' on UNIX or a backslash '' under Windows).

    TASK_FILENAME_SPEC = CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}
    TRACKER_FILENAME_SPEC = CamCOPS_{patient}_{now}_tracker.{filetype}
    CTV_FILENAME_SPEC = CamCOPS_{patient}_{now}_clinicaltextview.{filetype}

    # -----------------------------------------------------------------------------
    # Debugging options
    # -----------------------------------------------------------------------------
    # Possible log levels are (case-insensitive): "debug", "info", "warn"
    # (equivalent: "warning"), "error", and "critical" (equivalent: "fatal").

    # WEBVIEW_LOGLEVEL: Set the level of detail provided from the webview to the
    # Apache server log. (Loglevel option; see above.)

    WEBVIEW_LOGLEVEL = info

    # CLIENT_API_LOGLEVEL: Set the log level for the tablet client database access
    # script. (Loglevel option; see above.)

    CLIENT_API_LOGLEVEL = info

    # ALLOW_INSECURE_COOKIES: DANGEROUS option that removes the requirement that
    # cookies be HTTPS (SSL) only.

    ALLOW_INSECURE_COOKIES = false

    # =============================================================================
    # List of HL7/file recipients, and then details for each one
    # =============================================================================
    # This section defines a list of recipients to which Health Level Seven (HL7)
    # messages or raw files will be sent. Typically, you will send them by calling
    # "camcops -7 CONFIGFILE" regularly from the system's /etc/crontab or other
    # scheduling system. For example, a conventional /etc/crontab file has these
    # fields:
    #
    #   minutes, hours, day_of_month, month, day_of_week, user, command
    #
    # so you could add a line like this to /etc/crontab:
    #
    #   * * * * *  root  camcops -7 /etc/camcops/MYCONFIG.conf
    #
    # ... and CamCOPS would run its exports once per minute. See "man 5 crontab"
    # or http://en.wikipedia.org/wiki/Cron for more options.
    #
    # In this section, keys are ignored; values are section headings (one per
    # recipient).

    [recipients]

    # Examples (commented out):

    # recipient=recipient_A
    # recipient=recipient_B

    # =============================================================================
    # Individual HL7/file recipient configurations
    # =============================================================================
    # Dates are YYYY-MM-DD, e.g. 2013-12-31, or blank

    # Example (disabled because it's not in the list above)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # First example
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    [recipient_A]

    # TYPE: one of the following methods.
    #   hl7
    #       Sends HL7 messages across a TCP/IP network.
    #   file
    #       Writes files to a local filesystem.

    TYPE = hl7

    # -----------------------------------------------------------------------------
    # Options applicable to HL7 messages and file transfers
    # -----------------------------------------------------------------------------

    # GROUP_ID: CamCOPS group to export from.
    # HL7 messages are sent from one group at a time. Which group will this
    # recipient definition use? (Note that you can just duplicate a recipient
    # definition to export a second or subsequent group.)
    # This is an integer.

    GROUP_ID = 1

    # PRIMARY_IDNUM: which ID number (1-8) should be considered the "internal"
    # (primary) ID number? Must be specified for HL7 messages. May be blank for
    # file transmission.

    PRIMARY_IDNUM = 1

    # REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY: defines behaviour relating to the
    # primary ID number (as defined by PRIMARY_IDNUM).
    # - If true, no message sending will be attempted unless the PRIMARY_IDNUM is a
    #   mandatory part of the finalizing policy (and if FINALIZED_ONLY is false,
    #   also of the upload policy).
    # - If false, messages will be sent, but ONLY FROM TASKS FOR WHICH THE
    #   PRIMARY_IDNUM IS PRESENT; others will be ignored.
    # - For file sending only, this will be ignored if PRIMARY_IDNUM is blank.
    # - For file sending only, this setting does not apply to anonymous tasks,
    #   whose behaviour is controlled by INCLUDE_ANONYMOUS (see below).

    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = true

    # START_DATE: earliest date for which tasks will be sent. Assessed against the
    # task's "when_created" field, converted to Universal Coordinated Time (UTC) --
    # that is, this date is in UTC (beware if you are in a very different time
    # zone). Blank to apply no start date restriction.

    START_DATE =

    # END_DATE: latest date for which tasks will be sent. In UTC. Assessed against
    # the task's "when_created" field (converted to UTC). Blank to apply no end
    # date restriction.

    END_DATE =

    # FINALIZED_ONLY: if true, only send tasks that are finalized (moved off their
    # originating tablet and not susceptible to later modification). If false, also
    # send tasks that are uploaded but not yet finalized (they will then be sent
    # again if they are modified later).

    FINALIZED_ONLY = true

    # TASK_FORMAT: one of: pdf, html, xml

    TASK_FORMAT = pdf

    # XML_FIELD_COMMENTS: if TASK_FORMAT is xml, then XML_FIELD_COMMENTS determines
    # whether field comments are included. These describe the meaning of each field
    # so add to space requirements but provide more information for human readers.
    # (Default true.)

    XML_FIELD_COMMENTS = true

    # -----------------------------------------------------------------------------
    # Options applicable to HL7 only (TYPE = hl7)
    # -----------------------------------------------------------------------------

    # HOST: HL7 hostname or IP address

    HOST = myhl7server.mydomain

    # PORT: HL7 port (default 2575)

    PORT = 2575

    # PING_FIRST: if true, requires a successful ping to the server prior to
    # sending HL7 messages. (Note: this is a TCP/IP ping, and tests that the
    # machine is up, not that it is running an HL7 server.) Default: true.

    PING_FIRST = true

    # NETWORK_TIMEOUT_MS: network time (in milliseconds). Default: 10000.

    NETWORK_TIMEOUT_MS = 10000

    # KEEP_MESSAGE: keep a copy of the entire message in the databaase. Default is
    # false. WARNING: may consume significant space in the database.

    KEEP_MESSAGE = false

    # KEEP_REPLY: keep a copy of the reply (e.g. acknowledgement) message received
    # from the server. Default is false. WARNING: may consume significant space.

    KEEP_REPLY = false

    # DIVERT_TO_FILE: Override HOST/PORT options and send HL7 messages to this
    # (single) file instead. Each messages is appended to the file. Default is
    # blank (meaning network transmission will be used). This is a debugging
    # option, allowing you to redirect HL7 messages to a file and inspect them.

    DIVERT_TO_FILE =

    # TREAT_DIVERTED_AS_SENT: Any messages that are diverted to a file (using
    # DIVERT_TO_FILE) are treated as having been sent (thus allowing the file to
    # mimic an HL7-receiving server that's accepting messages happily). If set to
    # false (the default), a diversion will allow you to preview messages for
    # debugging purposes without "swallowing" them. BEWARE, though: if you have
    # an automatically scheduled job (for example, to send messages every minute)
    # and you divert with this flag set to false, you will end up with a great many
    # message attempts!

    TREAT_DIVERTED_AS_SENT = false

    # -----------------------------------------------------------------------------
    # Options applicable to file transfers only (TYPE = file)
    # -----------------------------------------------------------------------------

    # INCLUDE_ANONYMOUS: include anonymous tasks.
    # - Note that anonymous tasks cannot be sent via HL7; the HL7 specification is
    #   heavily tied to identification.
    # - Note also that this setting operates independently of the
    #   REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY setting.

    INCLUDE_ANONYMOUS = true

    # PATIENT_SPEC_IF_ANONYMOUS: for anonymous tasks, this string is used as the
    # patient descriptor (see also PATIENT_SPEC, FILENAME_SPEC below). Typically
    # "anonymous".

    PATIENT_SPEC_IF_ANONYMOUS = anonymous

    # PATIENT_SPEC: string, into which substitutions will be made, that defines the
    # {patient} element available for substitution into the FILENAME_SPEC (see
    # below). Possible substitutions: as for PATIENT_SPEC in the main
    # "[server]" section of the configuration file (see above).

    PATIENT_SPEC = {surname}_{forename}_{idshortdesc1}{idnum1}

    # FILENAME_SPEC: string into which substitutions will be made to determine the
    # filename to be used for each file. Possible substitutions: as for
    # PATIENT_SPEC in the main "[server]" section of the configuration
    # file (see above).

    FILENAME_SPEC = /my_nfs_mount/mypath/CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}

    # MAKE_DIRECTORY: make the directory if it doesn't already exist. Default is
    # false.

    MAKE_DIRECTORY = true

    # OVERWRITE_FILES: whether or not to attempt overwriting existing files of the
    # same name (default false). There is a DANGER of inadvertent data loss if you
    # set this to true. (Needing to overwrite a file suggests that your filenames
    # are not task-unique; try ensuring that both the {tasktype} and {serverpk}
    # attributes are used in the filename.)

    OVERWRITE_FILES = false

    # RIO_METADATA: whether or not to export a metadata file for Servelec's RiO
    # (default false).
    # Details of this file format are in cc_task.py / Task.get_rio_metadata().
    # The metadata filename is that of its associated file, but with the extension
    # replaced by ".metadata" (e.g. X.pdf is accompanied by X.metadata).
    # If RIO_METADATA is true, the following options also apply:
    #   RIO_IDNUM: which of the ID numbers (as above) is the RiO ID?
    #   RIO_UPLOADING_USER: username for the uploading user (maximum of 10
    #       characters)
    #   RIO_DOCUMENT_TYPE: document type as defined in the receiving RiO system.
    #       This is a code that maps to a human-readable document type; for
    #       example, the code "APT" might map to "Appointment Letter". Typically we
    #       might want a code that maps to "Clinical Correspondence", but the code
    #       will be defined within the local RiO system configuration.

    RIO_METADATA = false
    RIO_IDNUM = 2
    RIO_UPLOADING_USER = CamCOPS
    RIO_DOCUMENT_TYPE = CC

    # SCRIPT_AFTER_FILE_EXPORT: filename of a shell script or other executable to
    # run after file export is complete. You might use this script, for example, to
    # move the files to a different location (such as across a network). If the
    # parameter is blank, no script will be run. If no files are exported, the
    # script will not be run.
    # - Parameters passed to the script: a list of all the filenames exported.
    #   (This includes any RiO metadata filenames.)
    # - WARNING: the script will execute with the same permissions as the instance
    #   of CamCOPS that's doing the export (so, for example, if you run CamCOPS
    #   from your /etc/crontab as root, then this script will be run as root; that
    #   can pose a risk!).
    # - The script executes while the export lock is still held by CamCOPS (i.e.
    #   further HL7/file transfers won't be started until the script(s) is/are
    #   complete).
    # - If the script fails, an error message is recorded, but the file transfer is
    #   still considered to have been made (CamCOPS has done all it can and the
    #   responsibility now lies elsewhere).
    # - Example test script: suppose this is /usr/local/bin/print_arguments:
    #       #!/bin/bash
    #       for f in $$@
    #       do
    #           echo "CamCOPS has just exported this file: $$f"
    #       done
    #   ... then you could set:
    #       SCRIPT_AFTER_FILE_EXPORT = /usr/local/bin/print_arguments

    SCRIPT_AFTER_FILE_EXPORT =

