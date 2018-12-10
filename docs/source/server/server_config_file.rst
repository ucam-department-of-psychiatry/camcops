..  docs/source/server/server_config_file.rst

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
---------------------------------

In general, it is best to have a single CamCOPS database and a single CamCOPS
configuration file. This is simple. You can add :ref:`groups <groups>`
dynamically, and use :ref:`group security <groups>` to manage data access.
Groups can be entirely isolated from each other, which mimics having multiple
databases, but they can also overlap in useful ways.

It’s also possible, of course, to have multiple CamCOPS databases, each with
its own configuration file.

If you do operate with multiple databases/configuration files, you may want to
use the :ref:`camcops_server_meta <camcops_server_meta>` tool, which allows you
to run the same :ref:`camcops <camcops_cli>` command over multiple
configuration files in one go (for example, to upgrade the databases for a new
version of CamCOPS).

Format of the configuration file
--------------------------------

- The config file is in standard `INI file format
  <https://en.wikipedia.org/wiki/INI_file>`_.

- **UTF-8 encoding.** Use this! The file is explicitly opened in UTF-8 mode.
- **Comments.** Hashes (``#``) and semicolons (``;``) denote comments.
- **Sections.** Sections are indicated with: ``[section]``
- **Name/value (key/value) pairs.** The parser used is ConfigParser
  (https://docs.python.org/3/library/configparser.html). It allows
  ``name=value`` or ``name:value``.
- **Avoid indentation of parameters.** (Indentation is used to indicate
  the continuation of previous parameters.)
- **Parameter types,** referred to below, are:

  - **String.** Single-line strings are simple.
  - **Multiline string.** Here, a series of lines is read and split into a list
    of strings (one for each line). You should indent all lines except the
    first beyond the level of the parameter name, and then they will be treated
    as one parameter value.
  - **Integer.** Simple.
  - **Boolean.** For Boolean options, true values are any of: ``1, yes, true,
    on`` (case-insensitive). False values are any of: ``0, no, false, off``.
  - **Loglevel.** Possible log levels are (case-insensitive): ``debug``,
    ``info``, ``warning `` (equivalent: ``warn``), ``error``, and ``critical``
    (equivalent: ``fatal``).
  - **Date.** Dates are in the format ``YYYY-MM-DD``, e.g. ``2013-12-31``, or
    blank for "no date".


Config file sections
--------------------

- All server settings are in the main section, ``[server]``.
- A list of export recipients is in the ``[recipients]`` section.
- Each export recipient is defined in a section whose name is the user-defined
  name of that recipient.


Options for the "[server]" section
----------------------------------

Database connection/tools
~~~~~~~~~~~~~~~~~~~~~~~~~

DB_URL
######

*String.*

The SQLAlchemy connection URL for the CamCOPS database. See
http://docs.sqlalchemy.org/en/latest/core/engines.html. Examples:

- MySQL under Linux via mysqlclient

  .. code-block:: none

    $ pip install mysqlclient

    DB_URL = mysql+mysqldb://<username>:<password>@<host>:<port>/<database>?charset=utf8

  (The default MySQL port is 3306, and 'localhost' is often the right host.)

- SQL Server under Windows via ODBC and username/password authentication.

  .. code-block:: none

    C:\> pip install pyodbc

    DB_URL = mssql+pyodbc://<username>:<password>@<odbc_dsn_name>

- ... or via Windows authentication:

  .. code-block:: none

    DB_URL = mssql+pyodbc://@<odbc_dsn_name>

DB_ECHO
#######

*Boolean.*

Echo all SQL?

URLs and paths
~~~~~~~~~~~~~~

..
    outdated:
..
    First, a quick note on absolute and relative URLs, and how CamCOPS is
    mounted.
..
    Suppose your CamCOPS site is visible at
..
      .. code-block:: none
..
        https://www.somewhere.ac.uk/camcops_smith_lab/webview
        ^      ^^                 ^^                ^^      ^
        +------+|                 |+----------------+|      |
        |       +-----------------+|                 +------+
        |       |                  |                 |
        1       2                  3                 4
..
    Part 1 is the protocol, and part 2 the machine name. Part 3 is the mount
    point. The main server (e.g. Apache) knows where the CamCOPS script is
    mounted (in this case ``/camcops_smith_lab``). It does NOT tell the script
    via the script's WSGI environment. Therefore, if the script sends HTML
    including links, the script can operate only in relative mode. For it to
    operate in absolute mode, it would need to know (3). Part 4 is visible to
    the CamCOPS script (as the WSGI ``PATH_INFO`` variable).
..
    If CamCOPS emitted URLs starting with '/', it would need to be told at
    least part (3). To use absolute URLs, it would need to know all of (1),
    (2), (3). We will follow others (e.g.
    http://stackoverflow.com/questions/2005079) and use only relative URLs.


LOCAL_INSTITUTION_URL
#####################

*String.*

Clicking on your institution's logo in the CamCOPS menu will take you to this
URL. Edit this to point to your institution:

LOCAL_LOGO_FILE_ABSOLUTE
########################

*String.*

Specify the full path to your institution's logo file, e.g.
``/var/www/logo_local_myinstitution.png``. It's used for PDF generation; HTML
views use the fixed string ``static/logo_local.png``, aliased to your file via
the Apache configuration file). Edit this setting to point to your local
institution's logo file:

CAMCOPS_LOGO_FILE_ABSOLUTE
##########################

*String.*

As for ``LOCAL_LOGO_FILE_ABSOLUTE``, but for the CamCOPS logo. It's fine not to
specify this; a default will be used.

EXTRA_STRING_FILES
##################

*Multiline string.*

A multiline list of filenames (with absolute paths), read by the server, and
used as EXTRA STRING FILES. Should **as a minimum** point to the string file
``camcops.xml``. May use "glob" pattern-matching (see
https://docs.python.org/3.5/library/glob.html).

SNOMED_TASK_XML_FILENAME
########################

*String.*

Filename of special XML file containing SNOMED CT codes used by CamCOPS tasks.
This file is OK to use in the UK, but not necessarily elsewhere. See
:ref:`SNOMED CT <snomed>`.

SNOMED_ICD9_XML_FILENAME
########################

*String.*

Name of XML file mapping ICD-9-CM codes to SNOMED-CT.

Created by ``camcops_server convert_athena_icd_snomed_to_xml``; see
:ref:`SNOMED CT <snomed>`.

SNOMED_ICD10_XML_FILENAME
#########################

*String.*

Name of XML file mapping ICD-10[-CM] codes to SNOMED-CT.

Created by ``camcops_server convert_athena_icd_snomed_to_xml``; see
:ref:`SNOMED CT <snomed>`.

WKHTMLTOPDF_FILENAME
####################

*String.*

For the pdfkit PDF engine, specify a filename for wkhtmltopdf
(https://wkhtmltopdf.org/) that incorporates any need for an X Server (not the
default ``/usr/bin/wkhtmltopdf``). See
http://stackoverflow.com/questions/9604625/ . A suitable one is bundled with
CamCOPS, so you shouldn't have to alter this default. A blank parameter here
usually ends up calling ``/usr/bin/wkhtmltopdf``


Login and session configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SESSION_COOKIE_SECRET
#####################

*String.*

Secret used for HTTP cookie signing via Pyramid. Put something random in here
and keep it secret. (When you make a new CamCOPS demo config, the value shown
is fresh and random.)

SESSION_TIMEOUT_MINUTES
#######################

*Integer.*

Time after which a session will expire (default 30).

PASSWORD_CHANGE_FREQUENCY_DAYS
##############################

*Integer.*

Force password changes (at webview login) with this frequency (0 for never).
Note that password expiry will not prevent uploads from tablets, but when the
user next logs on, a password change will be forced before they can do anything
else.

LOCKOUT_THRESHOLD
#################

*Integer.*

Lock user accounts after every *n* login failures (default 10).

LOCKOUT_DURATION_INCREMENT_MINUTES
##################################

*Integer.*

Account lockout time increment (default 10).

Suppose ``LOCKOUT_THRESHOLD = 10`` and ``LOCKOUT_DURATION_INCREMENT_MINUTES =
20``. Then:

- After the first 10 failures, the account will be locked for 20 minutes.
- After the next 10 failures, the account will be locked for 40 minutes.
- After the next 10 failures, the account will be locked for 60 minutes, and so
  on. Time and administrators can unlock accounts.

DISABLE_PASSWORD_AUTOCOMPLETE
#############################

*Boolean.*

If set to true, asks browsers not to autocomplete the password field on the
main login page. The correct setting for maximum security is debated (don't
cache passwords, versus allow a password manager so that users can use
better/unique passwords). Default: true. Note that some browsers (e.g. Chrome
v34 and up) may ignore this.

Suggested filenames for saving PDFs from the web view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Try these with Chrome, Firefox. Internet Explorer may be less obliging.

.. _serverconfig_server_patient_spec_if_anonymous:

PATIENT_SPEC_IF_ANONYMOUS
#########################

*String.*

For anonymous tasks, this fixed string is used as the patient descriptor (see
also ``PATIENT_SPEC`` below). Typically "anonymous".

.. _serverconfig_server_patient_spec:

PATIENT_SPEC
############

*String.*

A string, into which substitutions will be made, that defines the ``patient``
element available for substitution into the ``*_FILENAME_SPEC`` variables (see
below). Possible substitutions:

+-------------------+---------------------------------------------------------+
| ``surname``       | Patient's surname in upper case                         |
+-------------------+---------------------------------------------------------+
| ``forename``      | Patient's forename in upper case                        |
+-------------------+---------------------------------------------------------+
| ``dob``           | Patient's date of birth (format ``%Y-%m-%d``, e.g.      |
|                   | ``2013-07-24``)                                         |
+-------------------+---------------------------------------------------------+
| ``sex``           | Patient's sex (F, M, X)                                 |
+-------------------+---------------------------------------------------------+
| ``idshortdesc1``, | Short description of the relevant ID number, if that ID |
| ``idshortdesc2``, | number is not blank; otherwise blank                    |
| ...               |                                                         |
+-------------------+---------------------------------------------------------+
| ``idnum1``,       | Actual patient ID numbers                               |
| ``idnum2``,       |                                                         |
| ...               |                                                         |
+-------------------+---------------------------------------------------------+
| ``allidnums``     | All available ID numbers in "shortdesc-value" pairs     |
|                   | joined by ``_``. For example, if ID numbers 1, 4, and 5 |
|                   | are non-blank, this would have the format               |
|                   | ``<idshortdesc1>-<idnum1>_<idshortdesc4>-<idnum4>_      |
|                   | <idshortdesc5>-<idnum5>``                               |
+-------------------+---------------------------------------------------------+

.. _serverconfig_server_task_filename_spec:

TASK_FILENAME_SPEC
##################

*String.*

Filename specification used for task downloads (e.g. PDFs).

Substitutions will be made to determine the filename to be used for each file.
Possible substitutions:

+---------------+-------------------------------------------------------------+
| ``patient``   | Patient string. If the task is anonymous, this is the       |
|               | config variable ``PATIENT_SPEC_IF_ANONYMOUS``; otherwise,   |
|               | it is defined by ``PATIENT_SPEC`` above.                    |
+---------------+-------------------------------------------------------------+
| ``created``   | Date/time of task creation.  Dates/times are in the format  |
|               | ``%Y-%m-%dT%H%M``, e.g. ``2013-07-24T2004``. They are       |
|               | expressed in the timezone of creation (but without the      |
|               | timezone information for filename brevity).                 |
+---------------+-------------------------------------------------------------+
| ``now``       | Time of access/download (i.e. time now), in local timezone. |
+---------------+-------------------------------------------------------------+
| ``tasktype``  | Base table name of the task (e.g. "phq9"). May contain an   |
|               | underscore. Blank for trackers/CTVs.                        |
+---------------+-------------------------------------------------------------+
| ``serverpk``  | Server's primary key. (In combination with tasktype, this   |
|               | uniquely identifies not just a task but a version of that   |
|               | task.) Blank for trackers/CTVs.                             |
+---------------+-------------------------------------------------------------+
| ``filetype``  | e.g. ``pdf``, ``html``, ``xml`` (lower case)                |
+---------------+-------------------------------------------------------------+
| ``anonymous`` | Evaluates to the config variable                            |
|               | ``PATIENT_SPEC_IF_ANONYMOUS`` if anonymous, otherwise to    |
|               | a blank string                                              |
+---------------+-------------------------------------------------------------+

... plus all those substitutions applicable to ``PATIENT_SPEC``.

After these substitutions have been made, the entire filename is then processed
to ensure that only characters generally acceptable to filenames are used (see
:func:`camcops_server.cc_modules.cc_filename.convert_string_for_filename` in
the CamCOPS source code). Specifically:

- Unicode is converted to 7-bit ASCII (will mangle, e.g. removing accents)
- spaces are converted to underscores
- characters are removed *unless* they are one of the following:

  - all alphanumeric characters (0-9, A-Z, a-z);
  - ``-``, ``_``, ``.``, and the operating-system-specific directory separator
    (Python's ``os.sep``, a forward slash ``/`` on UNIX or a backslash ``\``
    under Windows).

TRACKER_FILENAME_SPEC
#####################

*String.*

Filename specification used for tracker downloads; see ``TASK_FILENAME_SPEC``.

CTV_FILENAME_SPEC
#################

*String.*

Filename specification used for clinical text view downloads; see
``TASK_FILENAME_SPEC``.

Debugging options
~~~~~~~~~~~~~~~~~

WEBVIEW_LOGLEVEL
################

*Loglevel.*

Set the level of detail provided from the webview to ``stderr`` (e.g. to the
Apache server log).

CLIENT_API_LOGLEVEL
###################

*Loglevel.*

Set the log level for the tablet client database access script.

ALLOW_INSECURE_COOKIES
######################

*Boolean.*

**DANGEROUS** option that removes the requirement that cookies be HTTPS (SSL)
only.

Options for the "[export]" section
----------------------------------

CamCOPS supports **incremental export**. For example, when a new task is
uploaded, you may want it sent somewhere via a Health Level Seven (HL7)
message, or saved to a PDF somewhere for another program to notice it, or
e-mailed to a special location.

You might trigger the export by calling ``camcops incremental_export``
regularly from the system's ``/etc/crontab`` or other scheduling system. For
example, a conventional ``/etc/crontab`` file has these fields:

.. code-block:: none

    minutes, hours, day_of_month, month, day_of_week, user, command

so you could add a line like this to /etc/crontab:

.. code-block:: none

    * * * * *  root  camcops_server incremental_export --config /etc/camcops/MYCONFIG.conf

... and CamCOPS would run its exports once per minute. See ``man 5 crontab`` or
http://en.wikipedia.org/wiki/Cron for more options.

Export control options
~~~~~~~~~~~~~~~~~~~~~~

EXPORT_LOCKFILE
###############

*String.*

Filename stem used for process locking for export functions.

A file-based lock is held during export, so that only one export process runs
at once.

Under Linux, the CamCOPS installation script will create a lock directory, and
the filename used will be ``<lockdir>/<EXPORT_LOCKFILE>.lock``. The
demonstration config file will show you where this is likely to be on your
system.

List of export recipients
~~~~~~~~~~~~~~~~~~~~~~~~~

RECIPIENTS
##########

*Multiline string.*

This is a list of export recipients. Each recipient is defined in a config file
section of its own. For example, if you have

.. code-block:: none

    [export]

    recipients =
        recipient_A
        recipient_B

then CamCOPS expects to see, elsewhere in the config file:

.. code-block:: none

    [recipient_A]

    # options defining recipient_A

    [recipient_B]

    # options defining recipient_B


Options for each export recipient section
-----------------------------------------

The following options are applicable to a recipient definition section of the
config file. Together, they define a single export recipient.

Export type
~~~~~~~~~~~~

TYPE
####

*String.*

One of the following methods:

- ``hl7``: Sends HL7 messages across a TCP/IP network.
- ``file``: Writes files to a local filesystem.

Options applicable to all or most incremental export types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GROUP_ID
########

*Integer.*

.. todo::

    currently a single integer; change to a list of group names and call
    it ``GROUPS``

CamCOPS group(s) to export from.

PRIMARY_IDNUM
#############

*Integer.*

.. todo:: check/update

Which ID number type should be considered the "internal" (primary) ID number?
Must be specified for HL7 messages. May be blank for file transmission.

REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY
#########################################

*Boolean.*

Defines behaviour relating to the primary ID number (as defined by
``PRIMARY_IDNUM``).

- If true, no message sending will be attempted unless the ``PRIMARY_IDNUM`` is
  a mandatory part of the finalizing policy (and if ``FINALIZED_ONLY`` is
  false, also of the upload policy).
- If false, messages will be sent, but ONLY FROM TASKS FOR WHICH THE
  ``PRIMARY_IDNUM`` IS PRESENT; others will be ignored.
- For file sending only, this will be ignored if ``PRIMARY_IDNUM`` is blank.
- For file sending only, this setting does not apply to anonymous tasks,
  whose behaviour is controlled by ``INCLUDE_ANONYMOUS`` (see below).

START_DATE
##########

*Date. May be blank.*

Earliest date for which tasks will be sent. Assessed against the task's
``when_created`` field, converted to Universal Coordinated Time (UTC) -- that
is, this date is in UTC (beware if you are in a very different time zone).
Blank to apply no start date restriction.

END_DATE
########

*Date. May be blank.*

Latest date for which tasks will be sent. In UTC. Assessed against the task's
``when_created`` field (converted to UTC). Blank to apply no end date
restriction.

FINALIZED_ONLY
##############

*Boolean.*

If true, only send tasks that are finalized (moved off their originating tablet
and not susceptible to later modification). If false, also send tasks that are
uploaded but not yet finalized (they will then be sent again if they are
modified later).

TASK_FORMAT
###########

*String.*

One of the following:

- ``pdf``
- ``html``
- ``xml``

XML_FIELD_COMMENTS
##################

*Boolean.*

If ``TASK_FORMAT = xml``, then ``XML_FIELD_COMMENTS`` determines whether field
comments are included. These describe the meaning of each field, so they take
space but they provide more information for human readers. (Default is true.)

Options applicable to HL7 only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HL7_HOST
########

*String.*

HL7 hostname or IP address.

HL7_PORT
########

*Integer.*

HL7 port (default 2575).

PING_FIRST
##########

*Boolean.*

If true, requires a successful ping to the server prior to sending HL7
messages. (Note: this is a TCP/IP ping, and tests that the machine is up, not
that it is running an HL7 server.) Default: true.

NETWORK_TIMEOUT_MS
##################

*Integer.*

Network timeout (in milliseconds). Default: 10000.

KEEP_MESSAGE
############

*Boolean.*

Keep a copy of the entire message in the databaase. Default is false.
**WARNING:** may consume significant space in the database.

KEEP_REPLY
##########

*Boolean.*

Keep a copy of the reply (e.g. acknowledgement) message received from the
server. Default is false. **WARNING:** may consume significant space.

DIVERT_TO_FILE
##############

*Boolean.*

Override ``HL7_HOST``/``HL7_PORT`` options and send HL7 messages to this
(single) file instead. Each messages is appended to the file. Default is blank
(meaning network transmission will be used). This is a **debugging option,**
allowing you to redirect HL7 messages to a file and inspect them.

TREAT_DIVERTED_AS_SENT
######################

*Boolean.*

Any messages that are diverted to a file (using ``DIVERT_TO_FILE``) are treated
as having been sent (thus allowing the file to mimic an HL7-receiving server
that's accepting messages happily). If set to false (the default), a diversion
will allow you to preview messages for debugging purposes without "swallowing"
them. BEWARE, though: if you have an automatically scheduled job (for example,
to send messages every minute) and you divert with this flag set to false, you
will end up with a great many message attempts!

Options applicable to file transfers only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

INCLUDE_ANONYMOUS
#################

*Boolean.*

Include anonymous tasks?

- Note that anonymous tasks cannot be sent via HL7; the HL7 specification is
  heavily tied to identification.

- Note also that this setting operates independently of the
  ``REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY`` setting.

PATIENT_SPEC_IF_ANONYMOUS
#########################

*String.*

For anonymous tasks, this string is used as the patient descriptor (see
``PATIENT_SPEC``, ``FILENAME_SPEC`` below). Typically "anonymous".

(Thus: as for the main :ref:`PATIENT_SPEC_IF_ANONYMOUS
<serverconfig_server_patient_spec_if_anonymous>` option.)

PATIENT_SPEC
############

*String.*

String, into which substitutions will be made, that defines the ``patient``
element available for substitution into the ``FILENAME_SPEC`` (see below).

Options are as for the main :ref:`PATIENT_SPEC
<serverconfig_server_patient_spec>` option.

FILENAME_SPEC
#############

*String.*

String into which substitutions will be made to determine the filename to be
used for each file.

Possible substitutions are as for the main :ref:`TASK_FILENAME_SPEC
<serverconfig_server_task_filename_spec>` option.

MAKE_DIRECTORY
##############

*Boolean.*

Make the directory if it doesn't already exist. Default is false.

OVERWRITE_FILES
###############

*Boolean.*

Whether or not to attempt overwriting existing files of the same name (default
false). There is a **DANGER** of inadvertent data loss if you set this to true.

(Needing to overwrite a file suggests that your filenames are not task-unique;
try ensuring that both the ``tasktype`` and ``serverpk`` attributes are used in
the filename.)

RIO_METADATA
############

*Boolean.*

Whether or not to export a metadata file for Servelec's RiO
(https://www.servelechsc.com/servelec-hsc/products-services/rio/) (default
false).

Details of this file format are in ``cc_task.py`` and
:meth:`camcops_server.cc_modules.cc_task.Task.get_rio_metadata`.

The metadata filename is that of its associated file, but with the extension
replaced by ``.metadata`` (e.g. ``X.pdf`` is accompanied by ``X.metadata``).

If ``RIO_METADATA`` is true, the following options also apply: ``RIO_IDNUM``,
``RIO_UPLOADING_USER``, ``RIO_DOCUMENT_TYPE``.

RIO_IDNUM
#########

*Integer.* Applicable if ``RIO_METADATA`` is true.

Which of the ID numbers (as above) is the RiO ID?

RIO_UPLOADING_USER
##################

*String.* Applicable if ``RIO_METADATA`` is true.

RiO username for the uploading user (maximum of 10 characters).

RIO_DOCUMENT_TYPE
#################

*String.* Applicable if ``RIO_METADATA`` is true.

Document type as defined in the receiving RiO system. This is a code that maps
to a human-readable document type; for example, the code "APT" might map to
"Appointment Letter". Typically we might want a code that maps to "Clinical
Correspondence", but the code will be defined within the local RiO system
configuration.

SCRIPT_AFTER_FILE_EXPORT
########################

*String.* Optional.

Optional filename of a shell script or other executable to run after file
export is complete. You might use this script, for example, to move the files
to a different location (such as across a network). If the parameter is blank,
no script will be run. If no files are exported, the script will not be run.

The parameters passed to the script are all the filenames exported. (This
includes any RiO metadata filenames.)

Note:

- **WARNING:** the script will execute with the same permissions as the
  instance of CamCOPS that's doing the export (so, for example, if you run
  CamCOPS from your ``/etc/crontab`` as root, then this script will be run as
  root; that can pose a risk!).

- The script executes while the export lock is still held by CamCOPS (i.e.
  further HL7/file transfers won't be started until the script(s) is/are
  complete).

- If the script fails, an error message is recorded, but the file transfer is
  still considered to have been made (CamCOPS has done all it can and the
  responsibility now lies elsewhere).

- Example test script: suppose this is ``/usr/local/bin/print_arguments``:

  .. code-block:: bash

    #!/bin/bash
    for f in $$@
    do
       echo "CamCOPS has just exported this file: $$f"
    done

  ... then you could set:

  .. code-block:: none

    SCRIPT_AFTER_FILE_EXPORT = /usr/local/bin/print_arguments


Demonstration config file
-------------------------

Here’s a specimen configuration file, generated via the command

.. code-block:: bash

    camcops_server demo_camcops_config > demo_camcops_config.ini

.. The INI file below is the last thing in this file, so select/copy/paste.

.. code-block:: ini

    # Demonstration CamCOPS server configuration file.
    # Created by CamCOPS server version 2.3.1 at 2018-12-10T17:47:44.053084+00:00.
    # See help at https://camcops.readthedocs.io/.

    # =============================================================================
    # Main section: [server]
    # =============================================================================

    [server]

    # -----------------------------------------------------------------------------
    # Database connection/tools
    # -----------------------------------------------------------------------------

    DB_URL = mysql+mysqldb://YYY_USERNAME_REPLACE_ME:ZZZ_PASSWORD_REPLACE_ME@localhost:3306/camcops?charset=utf8

    DB_ECHO = False

    # -----------------------------------------------------------------------------
    # URLs and paths
    # -----------------------------------------------------------------------------

    LOCAL_INSTITUTION_URL = http://www.mydomain/
    LOCAL_LOGO_FILE_ABSOLUTE = /home/rudolf/Documents/code/camcops/server/camcops_server/static/logo_local.png
    # CAMCOPS_LOGO_FILE_ABSOLUTE = /home/rudolf/Documents/code/camcops/server/camcops_server/static/logo_camcops.png

    EXTRA_STRING_FILES = /home/rudolf/Documents/code/camcops/server/camcops_server/extra_strings/*

    SNOMED_TASK_XML_FILENAME =
    SNOMED_ICD9_XML_FILENAME =
    SNOMED_ICD10_XML_FILENAME =

    WKHTMLTOPDF_FILENAME =

    # -----------------------------------------------------------------------------
    # Login and session configuration
    # -----------------------------------------------------------------------------

    SESSION_COOKIE_SECRET = camcops_autogenerated_secret_lNqFk37CEpapg20TrUNpJcfe2VOEKY8Rx4eYgZjkNrkd1wKffabQ2I4RzpNMtYHEJRAYhVUHxnbfHYUlCiHMVQ==
    SESSION_TIMEOUT_MINUTES = 30
    PASSWORD_CHANGE_FREQUENCY_DAYS = 0
    LOCKOUT_THRESHOLD = 10
    LOCKOUT_DURATION_INCREMENT_MINUTES = 10
    DISABLE_PASSWORD_AUTOCOMPLETE = true

    # -----------------------------------------------------------------------------
    # Suggested filenames for saving PDFs from the web view
    # -----------------------------------------------------------------------------

    PATIENT_SPEC_IF_ANONYMOUS = anonymous
    PATIENT_SPEC = {surname}_{forename}_{allidnums}

    TASK_FILENAME_SPEC = CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}
    TRACKER_FILENAME_SPEC = CamCOPS_{patient}_{now}_tracker.{filetype}
    CTV_FILENAME_SPEC = CamCOPS_{patient}_{now}_clinicaltextview.{filetype}

    # -----------------------------------------------------------------------------
    # Debugging options
    # -----------------------------------------------------------------------------

    WEBVIEW_LOGLEVEL = info
    CLIENT_API_LOGLEVEL = info
    ALLOW_INSECURE_COOKIES = false


    # =============================================================================
    # Export options
    # =============================================================================

    [export]

    EXPORT_LOCKFILE = /var/lock/camcops/camcops.export

        # EXPORT_LOCKFILE:
        # Filename stem used for process locking for HL7 message transmission.
        # Default is /var/lock/camcops/camcops.export
        # The actual lockfile will, in this case, be called
        #     /var/lock/camcops/camcops.export.lock
        # and other process-specific files will be created in the same directory
        # (so the CamCOPS script must have permission from the operating system to
        # do so). The installation script will create the directory
        #     /var/lock/camcops

    RECIPIENTS =

    # =============================================================================
    # Details for each export recipient
    # =============================================================================

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # First example
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Example (disabled because it's not in the RECIPIENTS list above)

    [recipient_A]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Export type
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    TYPE = hl7

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to all or more incremental export types
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    GROUP_ID = 1

    PRIMARY_IDNUM = 1
    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = true

    START_DATE =
    END_DATE =

    FINALIZED_ONLY = true

    TASK_FORMAT = pdf
    XML_FIELD_COMMENTS = true

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to HL7 only (TYPE = hl7)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HL7_HOST = myhl7server.mydomain
    HL7_PORT = 2575

    PING_FIRST = true

    NETWORK_TIMEOUT_MS = 10000

    KEEP_MESSAGE = false
    KEEP_REPLY = false

    DIVERT_TO_FILE =
    TREAT_DIVERTED_AS_SENT = false

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to file transfers only (TYPE = file)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    INCLUDE_ANONYMOUS = true

    PATIENT_SPEC_IF_ANONYMOUS = anonymous
    PATIENT_SPEC = {surname}_{forename}_{idshortdesc1}{idnum1}
    FILENAME_SPEC = /my_nfs_mount/mypath/CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}

    MAKE_DIRECTORY = true
    OVERWRITE_FILES = false

    RIO_METADATA = false
    RIO_IDNUM = 2
    RIO_UPLOADING_USER = CamCOPS
    RIO_DOCUMENT_TYPE = CC

    SCRIPT_AFTER_FILE_EXPORT =
