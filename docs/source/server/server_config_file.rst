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

.. _Apache: https://httpd.apache.org/
.. _CherryPy: https://cherrypy.org/
.. _Gunicorn: https://gunicorn.org/
.. _HTTPS: https://en.wikipedia.org/wiki/HTTPS
.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _Pyramid: https://trypyramid.com/
.. _RFC 5322: https://tools.ietf.org/html/rfc5322#section-3.6.2
.. _TCP: https://en.wikipedia.org/wiki/Transmission_Control_Protocol
.. _WSGI: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface

.. _server_config_file:

The CamCOPS server configuration file
=====================================

CamCOPS needs a configuration file. Under Linux, this is normally something
that you create at `/etc/camcops/camcops.conf`, from a template produced by
CamCOPS. It is the configuration file that points to your database.

..  contents::
    :local:
    :depth: 3


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
- **Name/value (key/value) pairs.** The parser used is `ConfigParser
  <https://docs.python.org/3/library/configparser.html>`_. It allows
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
  - **Date/time.** Date/time values are in the format ``YYYY-MM-DDTHH:MM`` or
    other `ISO 8601`_-compatible syntax, e.g. ``2013-12-31T09:00``, or blank
    for "no date/time".


Config file sections
--------------------

- The main CamCOPS site settings are in ``[site]``.
- Options for configuring the web server aspects are in ``[server]``.
- A list of export recipients is in the ``[recipients]`` section.
- Each export recipient is defined in a section named
  ``[recipient:RECIPIENT_NAME]`` where *RECIPIENT_NAME* is the user-defined
  name of that recipient.


Options for the "[site]" section
--------------------------------

Database connection
~~~~~~~~~~~~~~~~~~~

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

*Integer.* Default: 30.

Time (in minutes) after which a session will expire.

PASSWORD_CHANGE_FREQUENCY_DAYS
##############################

*Integer.*

Force password changes (at webview login) with this frequency (0 for never).
Note that password expiry will not prevent uploads from tablets, but when the
user next logs on, a password change will be forced before they can do anything
else.

LOCKOUT_THRESHOLD
#################

*Integer.* Default: 10.

Lock user accounts after every *n* login failures.

LOCKOUT_DURATION_INCREMENT_MINUTES
##################################

*Integer.* Default: 10.

Account lockout time increment.

Suppose ``LOCKOUT_THRESHOLD = 10`` and ``LOCKOUT_DURATION_INCREMENT_MINUTES =
20``. Then:

- After the first 10 failures, the account will be locked for 20 minutes.
- After the next 10 failures, the account will be locked for 40 minutes.
- After the next 10 failures, the account will be locked for 60 minutes, and so
  on. Time and administrators can unlock accounts.

DISABLE_PASSWORD_AUTOCOMPLETE
#############################

*Boolean.* Default: true.

If set to true, asks browsers not to autocomplete the password field on the
main login page. The correct setting for maximum security is debated (don't
cache passwords, versus allow a password manager so that users can use
better/unique passwords). Note that some browsers (e.g. Chrome v34 and up) may
ignore this.

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

Options for the "[server]" section
-------------------------------------

Common web server options
~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS incorporates a Python web server. You can choose which one to lanuch:

- CherryPy_: a "proper" one; multithreaded; works on Windows and Linux.
- Gunicorn_: a "proper" one; multiprocess; Linux/UNIX only.
- Pyramid_: a "toy" one for debugging. (CamCOPS is written using Pyramid as its
  web framework; Pyramid is excellent, but other software is generally better
  for use as the web server.)

You may also want to configure a CamCOPS server behind a "front-end" web server
such as Apache_. Further options to help with this are described below.

HOST
####

*String.* Default: ``127.0.0.1``.

TCP/IP hostname to listen on. (See also ``UNIX_DOMAIN_SOCKET``.)

Note some variations. For example, if your machine has an IP (v4) address of
``192.168.1.1``, then under Linux you will find the following:

- Using ``192.168.1.1`` will make the CamCOPS web server directly visible to
  the network.
- Using ``127.0.0.1`` will make it invisible to the network and visible only to
  other processes on the same computer.
- Using ``localhost`` will trigger a lookup from ``localhost`` to an IP
  address, typically ``127.0.0.1``.

PORT
####

*Integer.* Default: 8000.

TCP_ port number to listen on. (See also ``UNIX_DOMAIN_SOCKET``.)

UNIX_DOMAIN_SOCKET
##################

*String.* Default: none.

Filename of a UNIX domain socket (UDS) to listen on (rather than using TCP/IP).
UDS is typically faster than TCP. If specified, this overrides the TCP options,
``HOST`` and ``PORT``.

For example, ``/tmp/.camcops.sock``.

(Not applicable to the Pyramid test web server; CherryPy/Gunicorn only.)

SSL_CERTIFICATE
###############

*String.* Default: none.

SSL certificate file for HTTPS_ (e.g.
``/etc/ssl/certs/ssl-cert-snakeoil.pem``).

(Not applicable to the Pyramid test web server; CherryPy/Gunicorn only.)

If you host CamCOPS behind Apache, it's likely that you'll want Apache to
handle HTTPS and CamCOPS to operate unencrypted behind a reverse proxy, in
which case don't set this or ``SSL_PRIVATE_KEY``.

SSL_PRIVATE_KEY
###############

*String.* Default: none.

SSL private key file for HTTPS_ (e.g.
``/etc/ssl/private/ssl-cert-snakeoil.key``).

(Not applicable to the Pyramid test web server; CherryPy/Gunicorn only.)

WSGI options
~~~~~~~~~~~~

This section controls how CamCOPS creates its WSGI_ application. They apply to
all Python web servers provided (CherryPy, Gunicorn, Pyramid). These options
are particularly relevant if you are reverse-proxying CamCOPS behind a
front-end web server such as Apache_.

DEBUG_REVERSE_PROXY
###################

*Boolean.* Default: false.

If a reverse proxy configuration is in use, show debugging information for it
as WSGI variable are rewritten?

A reverse proxy configuration will be used if any of the following are set (see
:meth:`cardinal_pythonlib.wsgi.reverse_proxied_mw.ReverseProxiedConfig.necessary`):

.. code-block:: none

    PROXY_HTTP_HOST
    PROXY_REMOTE_ADDR
    PROXY_REWRITE_PATH_INFO
    PROXY_SCRIPT_NAME
    PROXY_SERVER_NAME
    PROXY_SERVER_PORT
    PROXY_URL_SCHEME
    TRUSTED_PROXY_HEADERS

DEBUG_TOOLBAR
#############

*Boolean.* Default: false.

Enable the Pyramid debug toolbar? **This should not be enabled for production
systems; it carries security risks.** It will not operate via Gunicorn_, which
has an incompatible process model.

PROXY_HTTP_HOST
###############

*String.* Default: none.

Option to set the WSGI HTTP host directly. This affects the WSGI variable
``HTTP_HOST``. If not specified, the variables ``HTTP_X_HOST,
HTTP_X_FORWARDED_HOST`` will be used, if trusted.

PROXY_REMOTE_ADDR
#################

*String.* Default: none.

Option to set the WSGI remote address directly. This affects the WSGI variable
``REMOTE_ADDR``. If not specified, the variables ``HTTP_X_FORWARDED_FOR,
HTTP_X_REAL_IP`` will be used, if trusted.

PROXY_REWRITE_PATH_INFO
#######################

*Boolean.* Default: false.

If ``SCRIPT_NAME`` is rewritten, this option causes ``PATH_INFO`` to be
rewritten, if it starts with ``SCRIPT_NAME``, to strip off ``SCRIPT_NAME``.
Appropriate for some front-end web browsers with limited reverse proxying
support (but do not use for Apache with ``ProxyPass``, because that rewrites
incoming URLs properly).

PROXY_SCRIPT_NAME
#################

*String.* Default: none.

Path at which this script is mounted. Set this if you are hosting this CamCOPS
instance at a non-root path, unless you set trusted WSGI headers instead.
            
For example, if you are running an Apache server and want this instance of
CamCOPS to appear at ``/somewhere/camcops``, then (a) configure your Apache
instance to proxy requests to ``/somewhere/camcops/...`` to this server (e.g.
via an internal TCP/IP port or UNIX socket) and (b) specify this option.

If this option is not set, then the OS environment variable ``SCRIPT_NAME``
will be checked as well. If that is not set, the variables within
``HTTP_X_SCRIPT_NAME, HTTP_X_FORWARDED_SCRIPT_NAME`` will be used, if they are
trusted.
            
This option affects the WSGI variables ``SCRIPT_NAME`` and ``PATH_INFO``.

PROXY_SERVER_NAME
#################

*String.* Default: none.

Option to set the WSGI server name directly. This affects the WSGI variable
``SERVER_NAME``. If not specified, the variable ``HTTP_X_FORWARDED_SERVER``
will be used, if trusted.

PROXY_SERVER_PORT
#################

*Integer.* Default: none.

Option to set the WSGI server port directly. This affects the WSGI variable
``SERVER_PORT``. If not specified, the variable ``HTTP_X_FORWARDED_PORT`` will
be used, if trusted.

PROXY_URL_SCHEME
################

*String.* Default: none.

Option to set the WSGI scheme (e.g. http, https) directly. This affects the
WSGI variable ``wsgi.url_scheme``. If not specified, a variable from the
following will be used, if trusted: ``HTTP_X_FORWARDED_PROTO,
HTTP_X_FORWARDED_PROTOCOL, HTTP_X_FORWARDED_SCHEME, HTTP_X_SCHEME`` (which can
specify a protocol) or ``HTTP_X_FORWARDED_HTTPS, HTTP_X_FORWARDED_SSL,
HTTP_X_HTTPS`` (which can contain Boolean information about which protocol is
in use).

TRUSTED_PROXY_HEADERS
#####################

*Multiline string.*

A multiline list of strings indicating WSGI environment variables that CamCOPS
should trust. Use these when CamCOPS is behind a reverse proxy (e.g. an Apache
front-end web server) and you can guarantee that these variables have been set
by Apache and can be trusted.

Possible values:

.. code-block:: none

    HTTP_X_FORWARDED_FOR
    HTTP_X_FORWARDED_HOST
    HTTP_X_FORWARDED_HTTPS
    HTTP_X_FORWARDED_PORT
    HTTP_X_FORWARDED_PROTO
    HTTP_X_FORWARDED_PROTOCOL
    HTTP_X_FORWARDED_SCHEME
    HTTP_X_FORWARDED_SCRIPT_NAME
    HTTP_X_FORWARDED_SERVER
    HTTP_X_FORWARDED_SSL
    HTTP_X_HOST
    HTTP_X_HTTPS
    HTTP_X_REAL_IP
    HTTP_X_SCHEME
    HTTP_X_SCRIPT_NAME

Variables that are not marked as trusted will not be used by the reverse-proxy
middleware.

CherryPy options
~~~~~~~~~~~~~~~~

Additional options for the CherryPy web server.

CHERRYPY_SERVER_NAME
####################

*String.* Default: ``localhost``.

CherryPy's ``SERVER_NAME`` environment entry.

CHERRYPY_THREADS_START
######################

*Integer.* Default: 10.

Number of threads for server to start with.

CHERRYPY_THREADS_MAX
####################

*Integer.* Default: 100.

Maximum number of threads for server to use (-1 for no limit).

**BEWARE exceeding the permitted number of database connections.**

CHERRYPY_LOG_SCREEN
###################

*Boolean.* Default: true.

Log access requests etc. to the terminal (stdout/stderr)?

CHERRYPY_ROOT_PATH
##################

*String.* Default: ``/``.

Root path to serve CRATE at, WITHIN this CherryPy web server instance.

There is unlikely to be a reason to use something other than ``/``; do not
confuse this with the mount point within a wider, e.g. Apache, configuration,
which is set instead by the WSGI variable ``SCRIPT_NAME``; see the
``TRUSTED_PROXY_HEADERS`` and ``PROXY_SCRIPT_NAME`` options.

Gunicorn options
~~~~~~~~~~~~~~~~

Additional options for the Gunicorn web server.

GUNICORN_NUM_WORKERS
####################

*Integer.* Default: twice the number of CPUs in your server.

Number of worker processes for the Gunicorn server to use.

GUNICORN_DEBUG_RELOAD
#####################

*Boolean.* Default: false.

Debugging option: reload Gunicorn upon code change?

GUNICORN_TIMEOUT_S
##################

*Integer.* Default: 30.

Gunicorn worker timeout (s).

DEBUG_SHOW_GUNICORN_OPTIONS
###########################

*Boolean.* Default: false.

Debugging option: show possible Gunicorn settings.


Options for the "[export]" section
----------------------------------

CamCOPS defines **export recipients**. Each export recipient defines what to
export, and how to export it. For example, you might create an export recipient
called ``perinatal_admin_team`` that e-mails PDFs of tasks from your perinatal
psychiatry group to your perinatal psychiatry administrative team (including
immediately on receipt), for manual export to a clinical records system that
doesn't support incoming electronic messages. You might create another called
``smith_neutrophil_study`` that sends XML data via HL7 message, and a third
called ``regular_database_dump`` that exports the entire CamCOPS database to
a database on disk.

Most export recipients will use **incremental export**. Once CamCOPS has sent
a task to a recipient, it won't send the same task again (unless you force it
to).

Exports can happen in several ways:

- You can trigger an export **manually,** e.g. via ``camcops_server export
  --recipients regular_database_dump``.

- You can mark a recipient as a **"push"** recipient. Whenever a relevant task
  is uploaded to CamCOPS, CamCOPS will export it immediately.

- You can **schedule** an export. Obviously, you can do this by putting the
  "manual" export call (as above) into an operating system schedule, such as
  *crontab(5)* (see http://en.wikipedia.org/wiki/Cron). However, CamCOPS also
  provides its own *crontab*-style scheduler, so you could have the
  ``smith_neutrophil_study`` export run every Tuesday at 2am.


Export control options
~~~~~~~~~~~~~~~~~~~~~~

CELERY_BEAT_SCHEDULE_DATABASE
#############################

*String.*

Filename used by CamCOPS as the Celery Beat scheduler database. Celery may
append ``.db`` (see ``celery beat --help``).

CELERY_BEAT_EXTRA_ARGS
######################

*Multiline string.*

Each line of this multiline string is an extra option to the ``celery beat``
command used by ``camcops_server launch_scheduler``, after ``celery worker
--app camcops_server --loglevel <LOGLEVEL>``.

CELERY_BROKER_URL
#################

*String.* Default: ``amqp://``.

Broker URL for Celery. See
http://docs.celeryproject.org/en/latest/userguide/configuration.html#conf-broker-settings.

CELERY_WORKER_EXTRA_ARGS
########################

*Multiline string.*

Each line of this multiline string is an extra option to the ``celery worker``
command used by ``camcops_server launch_workers``, after ``celery worker --app
camcops_server --loglevel <LOGLEVEL>``.

EXPORT_LOCKDIR
##############

*String.*

Directory name used for process locking for export functions.

File-based locks are held during export, so that only one export process runs
at once for mutually exclusive situations (e.g. exporting the same task to the
same recipient).

CamCOPS must have permissions to create files in this directory.

Under Linux, the CamCOPS installation script will create a lock directory for
you. The demonstration config file will show you where this is likely to be on
your system.


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

SCHEDULE_TIMEZONE
#################

*String.* Default: ``UTC``.

Timezone used by Celery for the *crontab(5)*-style ``SCHEDULE`` (see below), as
per
http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#time-zones.

SCHEDULE
########

*Multiline string.*

Each line is in the format of *crontab(5)*, with five time-related entries
(separated by whitespace) followed by a "what to run" entry -- in this case,
the name of a single export recipient. Thus:

.. code-block:: none

    minute hour day_of_week day_of_month month_of_year recipient

For example:

.. code-block:: none

    0 1 * * * perinatal_group_email_recipient

which will trigger the ``perinatal_group_email_recipient`` recipient at 01:00
every day. Lines beginning with ``#`` are ignored.

.. note::

    For scheduled exports, you must be running the CamCOPS scheduler (via
    ``camcops_server launch_scheduler``) and CamCOPS workers (via
    ``camcops_server launch_workers``).


Options for each export recipient section
-----------------------------------------

The following options are applicable to a recipient definition section of the
config file. Together, they define a single export recipient.

How to export
~~~~~~~~~~~~~

TRANSMISSION_METHOD
###################

*String.*

One of the following methods:

- ``db``: Exports tasks to a relationship database.
- ``email``: Sends tasks via e-mail.
- ``hl7``: Sends HL7 messages across a TCP/IP network.
- ``file``: Writes files to a local filesystem.

PUSH
####

*Boolean.*

Treat this as a "push" recipient?

All recipients can be exported to via a manual (or automated) ``camcops_server
export ...`` command. Push recipients support automatic incremental export when
a task is uploaded (i.e. as soon as it's uploaded, it's exported).

Not all transmission methods currently support push notifications: currently
database export is not supported.

.. note::

    For push exports to function, you must be running CamCOPS workers (via
    ``camcops_server launch_workers``).

.. note::

    For speed, the front end does not check all task criteria against the
    recipient. It sends some tasks to the back end that the back end will
    reject (e.g. anonymous, out of time range, freshly finalized but previously
    exported). This is normal. The back end double-checks all tasks that it's
    asked to export.

TASK_FORMAT
###########

*String.*

One of the following:

- ``pdf``
- ``html``
- ``xml``

XML_FIELD_COMMENTS
##################

*Boolean.* Default: true.

If ``TASK_FORMAT = xml``, then ``XML_FIELD_COMMENTS`` determines whether field
comments are included. These describe the meaning of each field, so they take
space but they provide more information for human readers.

What to export
~~~~~~~~~~~~~~

ALL_GROUPS
##########

*Boolean.* Default: false.

Export from all groups? If not, ``GROUPS`` will come into play (see below).

GROUPS
######

*Multiline string.*

Names of CamCOPS group(s) to export from.

Only applicable if ``ALL_GROUPS`` is false.

START_DATETIME_UTC
##################

*Date/time. May be blank.*

Earliest date/time (in UTC unless otherwise specified) for which tasks will be
sent. Assessed against the task's ``when_created`` field, converted to
Universal Coordinated Time (UTC). Blank to apply no start date restriction.

The parameter is named ``_UTC`` to remind you that it's UTC if you don't
specify it more precisely (and because it's stored as UTC in the database).
However, if you want a non-UTC timezone, specify the date/time in `ISO 8601`_
format and it will be autoconverted to UTC.

END_DATETIME_UTC
################

*Date/time. May be blank.*

Date/time (in UTC unless other specified) at/beyond which no tasks will be
sent. Assessed against the task's ``when_created`` field (converted to UTC).
Blank to apply no end date restriction.

The parameter is named ``_UTC`` to remind you that it's UTC if you don't
specify it more precisely (and because it's stored as UTC in the database).
However, if you want a non-UTC timezone, specify the date/time in `ISO 8601`_
format and it will be autoconverted to UTC.

FINALIZED_ONLY
##############

*Boolean.*

If true, only send tasks that are finalized (moved off their originating tablet
and not susceptible to later modification). If false, also send tasks that are
uploaded but not yet finalized (they will then be sent again if they are
modified later).

.. warning::

    It is unusual, and very likely undesirable, to set ``FINALIZED_ONLY`` to
    False. You may end up exporting multiple copies of tasks, all slightly
    different, if the user makes edits before finalizing.

INCLUDE_ANONYMOUS
#################

*Boolean.*

Include anonymous tasks?

- Note that anonymous tasks cannot be sent via HL7; the HL7 specification is
  heavily tied to identification.

- Note also that this setting operates independently of the
  ``REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY`` setting.

PRIMARY_IDNUM
#############

*Integer.*

Which ID number type should be considered the "internal" (primary) ID number?
If specified, only tasks with this ID number present will be exported.

- Must be specified for HL7 messages.
- May be blank for file and e-mail transmission.
- For (e.g.) file/e-mail transmission, this does not control the behaviour of
  anonymous tasks, which are instead controlled by ``INCLUDE_ANONYMOUS`` (see
  below).

REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY
#########################################

*Boolean.*

Defines behaviour relating to the primary ID number. Applies only if
``PRIMARY_IDNUM`` is set.

- If true, no message sending will be attempted unless the ``PRIMARY_IDNUM`` is
  a mandatory part of the finalizing policy (and if ``FINALIZED_ONLY`` is
  false, also of the upload policy).
- If false, messages will be sent, but ONLY FROM TASKS FOR WHICH THE
  ``PRIMARY_IDNUM`` IS PRESENT; others will be ignored.
- If you export from multiple groups simultaneously, setting this to true means
  that the primary ID number must be present (as above) for *all* groups.

Options applicable to database export only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At present, only full (not incremental) database export is supported.

DB_URL
######

*String.*

SQLAlchemy URL to the receiving database.

DB_ECHO
#######

*Boolean.* Default: false.

Echo SQL sent to the destination database.

DB_INCLUDE_BLOBS
################

*Boolean.* Default: true.

Include binary large objects (BLOBs) in the export?

DB_ADD_SUMMARIES
################

*Boolean.* Default: true.

Add summary information (including :ref:`SNOMED CT <snomed>` codes if
available)?

DB_PATIENT_ID_PER_ROW
#####################

*Boolean.* Default: false.

Add patient ID numbers to all patient rows? Used, for example, to export a
database in a more convenient format for subsequent anonymisation.

.. todo:: DB_PATIENT_ID_PER_ROW not currently implemented.

Options applicable to e-mail export only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Attachment filenames are based on ``FILE_FILENAME_SPEC``, but only the basename
of the path is used.

EMAIL_HOST
##########

*String.*

Hostname of e-mail (SMTP) server.

EMAIL_PORT
##########

*Integer.* Default: 25.

Port number of e-mail (SMTP) server. The default is 25, but consider something
more secure (see below).

EMAIL_USE_TLS
#############

*Boolean.* Default: false.

Use a TLS (secure) connection to talk to the SMTP server? The default is false,
but you should strongly consider using it!

This is used for explicit TLS connections, usually on port 587 (in which the
connection is opened and then a ``STARTTLS`` command is issued).

EMAIL_HOST_USERNAME
###################

*String.*

Username on e-mail server.

EMAIL_HOST_PASSWORD
###################

*String.*

Password on e-mail server. (Not stored in database.)

EMAIL_FROM
##########

*String.*

"From:" address used in e-mails. See `RFC 5322`_. Only one is permitted here.

EMAIL_SENDER
############

"Sender:" address used in e-mails. See `RFC 5322`_. Only one is permitted.

EMAIL_REPLY_TO
##############

*String.*

"Reply-To:" address used in e-mails. See `RFC 5322`_.

EMAIL_TO
########

*Multiline string.*

List of "To:" recipients.

EMAIL_CC
########

*Multiline string.*

List of "CC:" (carbon copy) recipients.

EMAIL_BCC
#########

*Multiline string.*

List of "BCC:" (blind carbon copy) recipients.

EMAIL_PATIENT_SPEC_IF_ANONYMOUS
###############################

*String.*

For anonymous tasks, this string is used as the patient descriptor (see
``EMAIL_SUBJECT_PATIENT_SPEC``, ``EMAIL_SUBJECT_SPEC`` below). Typically "anonymous".

(Thus: as for the main :ref:`PATIENT_SPEC_IF_ANONYMOUS
<serverconfig_server_patient_spec_if_anonymous>` option.)

EMAIL_PATIENT_SPEC
##################

*String.*

String, into which substitutions will be made, that defines the ``patient``
element available for substitution into the ``EMAIL_SUBJECT_SPEC`` (see below).

Options are as for the main :ref:`PATIENT_SPEC
<serverconfig_server_patient_spec>` option.

EMAIL_SUBJECT
#############

*String.*

Possible substitutions are as for the main :ref:`TASK_FILENAME_SPEC
<serverconfig_server_task_filename_spec>` option.

EMAIL_BODY_IS_HTML
##################

*Boolean.*

Is the body HTML, rather than plain text? Default false.

EMAIL_BODY
##########

*Multiline string.*

E-mail body contents. Possible substitutions are as for the main
:ref:`TASK_FILENAME_SPEC <serverconfig_server_task_filename_spec>` option.

Possible substitutions are as for the main :ref:`TASK_FILENAME_SPEC
<serverconfig_server_task_filename_spec>` option.

EMAIL_KEEP_MESSAGE
##################

*Boolean.* Default: false.

Keep the entire message (including attachments). Turning this option on
consumes lots of database space! Use only for debugging.

Options applicable to HL7 only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HL7_HOST
########

*String.*

HL7 hostname or IP address.

HL7_PORT
########

*Integer.* Default: 2575.

HL7 port.

HL7_PING_FIRST
##############

*Boolean.* Default: true.

If true, requires a successful ping to the server prior to sending HL7
messages. (Note: this is a TCP/IP ping, and tests that the machine is up, not
that it is running an HL7 server.)

HL7_NETWORK_TIMEOUT_MS
######################

*Integer.* Default: 10000.

Network timeout (in milliseconds).

HL7_KEEP_MESSAGE
################

*Boolean.* Default: false.

Keep a copy of the entire message in the databaase. *WARNING:** may consume
significant space in the database.

HL7_KEEP_REPLY
##############

*Boolean.* Default: false.

Keep a copy of the reply (e.g. acknowledgement) message received from the
server. **WARNING:** may consume significant space.

HL7_DEBUG_DIVERT_TO_FILE
########################

*Boolean.* Default: false.

Override ``HL7_HOST``/``HL7_PORT`` options and send HL7 messages to a
(single) file instead?

This is a **debugging option,** allowing you to redirect HL7 messages to a file
and inspect them. If chosen, the following options are used:

.. code-block:: none

    FILE_PATIENT_SPEC
    FILE_PATIENT_SPEC_IF_ANONYMOUS
    FILE_FILENAME_SPEC
    FILE_MAKE_DIRECTORY
    FILE_OVERWRITE_FILES

and the files are named accordingly, but with ``filetype`` set to ``hl7``.

HL7_DEBUG_TREAT_DIVERTED_AS_SENT
################################

*Boolean.* Default: false.

Any messages that are diverted to a file (using ``DIVERT_TO_FILE``) are treated
as having been sent (thus allowing the file to mimic an HL7-receiving server
that's accepting messages happily). If set to false, a diversion will allow you
to preview messages for debugging purposes without "swallowing" them. BEWARE,
though: if you have an automatically scheduled job (for example, to send
messages every minute) and you divert with this flag set to false, you will end
up with a great many message attempts!

Options applicable to file transfers and attachments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FILE_PATIENT_SPEC_IF_ANONYMOUS
##############################

*String.*

For anonymous tasks, this string is used as the patient descriptor (see
``PATIENT_SPEC``, ``FILENAME_SPEC`` below). Typically "anonymous".

(Thus: as for the main :ref:`PATIENT_SPEC_IF_ANONYMOUS
<serverconfig_server_patient_spec_if_anonymous>` option.)

FILE_PATIENT_SPEC
#################

*String.*

String, into which substitutions will be made, that defines the ``patient``
element available for substitution into the ``FILENAME_SPEC`` (see below).

Options are as for the main :ref:`PATIENT_SPEC
<serverconfig_server_patient_spec>` option.

FILE_FILENAME_SPEC
##################

*String.*

String into which substitutions will be made to determine the filename to be
used for each file. (Patient details are determined by ``FILE_PATIENT_SPEC``
and ``FILE_PATIENT_SPEC_IF_ANONYMOUS``.)

Possible substitutions are as for the main :ref:`TASK_FILENAME_SPEC
<serverconfig_server_task_filename_spec>` option.

FILE_MAKE_DIRECTORY
###################

*Boolean.* Default: false.

Make the directory if it doesn't already exist.

FILE_OVERWRITE_FILES
####################

*Boolean.* Default: false.

Whether or not to attempt overwriting existing files of the same name. There is
a **DANGER** of inadvertent data loss if you set this to true.

(Needing to overwrite a file suggests that your filenames are not task-unique;
try ensuring that both the ``tasktype`` and ``serverpk`` attributes are used in
the filename.)

FILE_EXPORT_RIO_METADATA
########################

*Boolean.* Default: false.

Whether or not to export a metadata file for Servelec's RiO
(https://www.servelechsc.com/servelec-hsc/products-services/rio/).

Details of this file format are in ``cc_task.py`` and
:meth:`camcops_server.cc_modules.cc_task.Task.get_rio_metadata`.

The metadata filename is that of its associated file, but with the extension
replaced by ``.metadata`` (e.g. ``X.pdf`` is accompanied by ``X.metadata``).

If ``RIO_METADATA`` is true, the following options also apply: ``RIO_IDNUM``,
``RIO_UPLOADING_USER``, ``RIO_DOCUMENT_TYPE``.

FILE_SCRIPT_AFTER_EXPORT
########################

*String.* Optional.

Optional filename of a shell script or other executable to run after file
export is complete. You might use this script, for example, to move the files
to a different location (such as across a network). If the parameter is blank,
no script will be run. If no files are exported, the script will not be run.

The parameters passed to the script are all the filenames exported for a given
task. (This includes any RiO metadata filenames.)

Note:

- **WARNING:** the script will execute with the same permissions as the
  instance of CamCOPS that's doing the export (so, for example, if you run
  CamCOPS from your ``/etc/crontab`` as root, then this script will be run as
  root; that can pose a risk!).

- The script executes while the export lock is still held by CamCOPS (i.e.
  further exports won't be started until the script is complete).

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

Extra options for RiO metadata for file-based export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Demonstration config file
-------------------------

Here’s a specimen configuration file, generated via the command

.. code-block:: bash

    camcops_server demo_camcops_config > demo_camcops_config.ini

.. The INI file below is the last thing in this file, so select/copy/paste.

.. code-block:: ini

    # Demonstration CamCOPS server configuration file.
    # Created by CamCOPS server version 2.3.1 at 2018-12-30T18:34:44.416963+00:00.
    # See help at https://camcops.readthedocs.io/.

    # =============================================================================
    # CamCOPS site
    # =============================================================================

    [site]

    # -----------------------------------------------------------------------------
    # Database connection
    # -----------------------------------------------------------------------------

    DB_URL = mysql+mysqldb://YYY_USERNAME_REPLACE_ME:ZZZ_PASSWORD_REPLACE_ME@localhost:3306/camcops?charset=utf8
    DB_ECHO = false

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

    SESSION_COOKIE_SECRET = camcops_autogenerated_secret_S8qfhAXzh-w0ED-35OIObFJz3Ctlg1DrlIWrE_2r0l4HDwWRq2hnHajbPfZsa2ymT8sBn4BPw2Wod1jSjNgQiw==
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
    # Web server options
    # =============================================================================

    [server]

    # -----------------------------------------------------------------------------
    # Common web server options
    # -----------------------------------------------------------------------------

    HOST = 127.0.0.1
    PORT = 8000
    UNIX_DOMAIN_SOCKET =
    SSL_CERTIFICATE =
    SSL_PRIVATE_KEY =

    # -----------------------------------------------------------------------------
    # WSGI options
    # -----------------------------------------------------------------------------

    DEBUG_REVERSE_PROXY = false
    DEBUG_TOOLBAR = false
    PROXY_HTTP_HOST =
    PROXY_REMOTE_ADDR =
    PROXY_REWRITE_PATH_INFO = false
    PROXY_SCRIPT_NAME =
    PROXY_SERVER_NAME =
    PROXY_SERVER_PORT =
    PROXY_URL_SCHEME =
    TRUSTED_PROXY_HEADERS =
        HTTP_X_FORWARDED_HOST
        HTTP_X_FORWARDED_SERVER
        HTTP_X_FORWARDED_PORT
        HTTP_X_FORWARDED_PROTO
        HTTP_X_SCRIPT_NAME

    # -----------------------------------------------------------------------------
    # CherryPy options
    # -----------------------------------------------------------------------------

    CHERRYPY_SERVER_NAME = localhost
    CHERRYPY_THREADS_START = 10
    CHERRYPY_THREADS_MAX = 100
    CHERRYPY_LOG_SCREEN = true
    CHERRYPY_ROOT_PATH = /

    # -----------------------------------------------------------------------------
    # Gunicorn options
    # -----------------------------------------------------------------------------

    GUNICORN_NUM_WORKERS = 16
    GUNICORN_DEBUG_RELOAD = False
    GUNICORN_TIMEOUT_S = 30
    DEBUG_SHOW_GUNICORN_OPTIONS = False

    # =============================================================================
    # Export options
    # =============================================================================

    [export]

    CELERY_BEAT_EXTRA_ARGS =
    CELERY_BEAT_SCHEDULE_DATABASE = /var/lock/camcops/camcops_celerybeat_schedule
    CELERY_BROKER_URL = amqp://
    CELERY_WORKER_EXTRA_ARGS =
    EXPORT_LOCKDIR = /var/lock/camcops

    RECIPIENTS =

    SCHEDULE_TIMEZONE = UTC
    SCHEDULE =

    # =============================================================================
    # Details for each export recipient
    # =============================================================================

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Example recipient
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Example (disabled because it's not in the RECIPIENTS list above)

    [recipient:recipient_A]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # How to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    TRANSMISSION_METHOD = hl7
    TASK_FORMAT = pdf
    XML_FIELD_COMMENTS = true

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # What to export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    ALL_GROUPS = false
    GROUPS =
        myfirstgroup
        mysecondgroup

    START_DATETIME_UTC =
    END_DATETIME_UTC =
    FINALIZED_ONLY = true
    INCLUDE_ANONYMOUS = true
    PRIMARY_IDNUM = 1
    REQUIRE_PRIMARY_IDNUM_MANDATORY_IN_POLICY = true

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to database exports
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    DB_URL = some_sqlalchemy_url
    DB_ECHO = false
    DB_INCLUDE_BLOBS = true
    DB_ADD_SUMMARIES = true
    DB_PATIENT_ID_PER_ROW = false

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to e-mail exports
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    EMAIL_HOST = mysmtpserver.mydomain
    EMAIL_PORT = 587
    EMAIL_USE_TLS = true
    EMAIL_HOST_USERNAME = myusername
    EMAIL_HOST_PASSWORD = mypassword
    EMAIL_FROM = CamCOPS computer <noreply@myinstitution.mydomain>
    EMAIL_SENDER =
    EMAIL_REPLY_TO = CamCOPS clinical administrator <admin@myinstitution.mydomain>
    EMAIL_TO =
        Perinatal Psychiatry Admin <perinatal@myinstitution.mydomain>

    EMAIL_CC =
        Dr Alice Bradford <alice.bradford@myinstitution.mydomain>
        Dr Charles Dogfoot <charles.dogfoot@myinstitution.mydomain>

    EMAIL_BCC =
        superuser <root@myinstitution.mydomain>

    EMAIL_PATIENT_SPEC_IF_ANONYMOUS = anonymous
    EMAIL_PATIENT_SPEC = {surname}, {forename}, {allidnums}
    EMAIL_SUBJECT = CamCOPS task for {patient}, created {created}: {tasktype}, PK {serverpk}
    EMAIL_BODY_IS_HTML = false
    EMAIL_BODY =
        Please find attached a new CamCOPS task for manual filing to the electronic
        patient record of

            {patient}

        Task type: {tasktype}
        Created: {created}
        CamCOPS server primary key: {serverpk}

        Yours faithfully,

        The CamCOPS computer.

    EMAIL_KEEP_MESSAGE = false

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to HL7
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HL7_HOST = myhl7server.mydomain
    HL7_PORT = 2575
    HL7_PING_FIRST = true
    HL7_NETWORK_TIMEOUT_MS = 10000
    HL7_KEEP_MESSAGE = false
    HL7_KEEP_REPLY = false
    HL7_DEBUG_DIVERT_TO_FILE =
    HL7_DEBUG_TREAT_DIVERTED_AS_SENT = false

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Options applicable to file transfers/attachments
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    FILE_PATIENT_SPEC = {surname}_{forename}_{idshortdesc1}{idnum1}
    FILE_PATIENT_SPEC_IF_ANONYMOUS = anonymous
    FILE_FILENAME_SPEC = /my_nfs_mount/mypath/CamCOPS_{patient}_{created}_{tasktype}-{serverpk}.{filetype}
    FILE_MAKE_DIRECTORY = true
    FILE_OVERWRITE_FILES = false
    FILE_EXPORT_RIO_METADATA = false
    FILE_SCRIPT_AFTER_EXPORT =

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Extra options for RiO metadata for file-based export
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    RIO_IDNUM = 2
    RIO_UPLOADING_USER = CamCOPS
    RIO_DOCUMENT_TYPE = CC
