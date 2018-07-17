..  documentation/source/server/server_troubleshooting.rst

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

Troubleshooting server problems
===============================

Web server errors from Apache
-----------------------------

- **Web server returns “permission denied”-type messages; Apache error log is
  full of file permission errors.** Ownerships, permissions, or SELinux
  security settings on files in the `DocumentRoot` tree are probably wrong. See
  :ref:`Server configuration <server_configuration>`; :ref:`Linux flavours
  <linux_flavours>`.

- **Operation (e.g. table upload) fails; Apache error log contains the message
  “client denied by server configuration”.** The Apache configuration file
  might be missing a section saying

  .. code-block:: apacheconf

    <Directory /usr/share/camcops/server>
        # ...
        <Files "database.py"> # CGI script for tablets to upload data
            Allow from all
        </Files>
        # ...
    </Directory>

  .. include:: include_old_bug_defunct.rst

- **SSL not working; Apache log contains “Invalid method in request
  \x16\x03\x01”.** Misconfigured server; it is speaking unencrypted HTTP on
  port 443. Do you have the VirtualHost section configured properly? Do you
  have `LoadModule ssl_module modules/mod_ssl.so`?

- **Other Apache errors.** See :ref:`front-end web server configuration
  <configure_apache>`, which has specimen Apache config sections.

Web server errors in general
----------------------------

- **Web server returns content but says <class 'ConfigParser.NoSectionError'>:
  No section: 'server'.** Unless the CamCOPS config files are broken, this
  probably means that the `/etc/camcops/*` configuration files have the wrong
  ownerships/permissions/SELinux security settings. See the ``chown`` and
  ``chcon`` commands [#linuxflavours]_. It’s also possible that the
  configuration files have been damaged, or that the Apache configuration file
  is pointing to a non-existing configuration file.

- **I can log in, but then seem to be logged out again immediately.**
  Is your browser correctly storing session cookies? Especially, are you trying
  to run CamCOPS over a non-encrypted (HTTP) link? The session cookies are set
  to secure and httponly for security reasons, and will not work without HTTPS.

Tablet upload errors
--------------------

MySQL server has gone away
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Tablet uploads fails with error including “(2006, 'MySQL server has gone
away')”. Apache log contains “OperationalError: (2006, 'MySQL server has gone
away')”.** CamCOPS takes care to ping the database connection, so it’s
unlikely that a connection has timed out. The probable cause is that the
relevant `max_allowed_packet` parameter is set too small; MySQL also generates
this error if the query is too big. You will need to edit the MySQL ``my.cnf``
configuration file; see :ref:`Setting up MySQL under Linux
<linux_mysql_setup>`. The most probable time to see this error is when
uploading the BLOB table (`blobs`).


Read timed out
~~~~~~~~~~~~~~


**Tablet BLOB upload fails with error “Read timed out”.** Likely problem: large
BLOB (big photo), slow network. For example, in one of our tests a BLOB took
more than 17 s to upload, so the tablet needs to wait at least that long after
starting to send it. Increase the tablet’s network timeout (e.g. try
increasing from 5000 to 60000 ms) in :menuselection:`Settings --> Server
settings.`


Row size too large (>8126)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: include_old_bug_defunct.rst

In full, the error was:

.. code-block:: none

    Uploading error: Operational error (1118). Row size too large (> 8126).
    Changing some columns to TEXT or BLOB may help. In current row format, BLOB
    prefix of 0 bytes is stored inline.

This is a problem with some TEXT-heavy tables, e.g. `psychiatricclerking`.

Best thing: change the table format.

#. Edit the MySQL config file, e.g. `/etc/my.cnf`. In the `[mysqld]` section,
   add the lines:

   .. code-block:: none

        innodb_file_per_table
        innodb_file_format = Barracuda

#. Restart MySQL.

#. At the MySQL command line:

   .. code-block:: sql

        ALTER TABLE psychiatricclerking
            ENGINE=InnoDB
            ROW_FORMAT=COMPRESSED
            KEY_BLOCK_SIZE=8;

Another method to consider for MySQL versions before 5.7.5: making the MySQL
log file bigger, e.g. 512 Mb.

#. At the MySQL console: ``SET GLOBAL innodb_fast_shutdown=0;``

#. Stop MySQL.

#. Edit the MySQL config file, e.g. `/etc/my.cnf`, and in the `[mysqld]`
   section, add the line:

   .. code-block:: none

        innodb_log_file_size = 512M

#. Delete the old log files, e.g. `/var/lib/mysql/ib_logfile0` and
   `/var/lib/mysql/ib_logfile1`.

#. Restart MySQL

From CamCOPS v1.32, the server autoconverts tables to Barracuda when using the
make-tables command, to avoid this problem.

MySQL: “Too many connections”
-----------------------------

This error occurs if programs collectively attempt to open more connections to
MySQL than the configured limit [#toomanyconnections]_. The easiest way to make
it happen in CamCOPS is to launch a web server with a very high maximum number
of threads, in excess of the MySQL limit, and then work the web server hard.

Fix the problem by limiting the maximum number of threads/processes used by
CamCOPS or by increasing the MySQL connection limit.

.. _mysql_illegal_mix_of_collations:

MySQL: “Illegal mix of collations...”
-------------------------------------

In full: MySQL reports: “Illegal mix of collations (utf8mb4_unicode_ci,IMPLICIT)
and (utf8mb4_general_ci,IMPLICIT) for operation '='”

In summary, part of your database is out of date, and this is probably because
you’ve upgraded from an old version of CamCOPS.

Background: character sets and collations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MySQL character sets and collations can be confusing.

A *character set* is the way in which the computer represents characters. We are
a long way beyond the basic ASCII 7-bit character set (which could represent 128
characters) and we should be supporting all Unicode characters (of which there
are >136,000, including accents like ä and symbols like ≈). There are several
ways to represent Unicode, but the most popular is UTF-8, which uses a variable
number of bytes (from 1 to 4) per character. This means that simple text using
only plain 7-bit ASCII characters still takes one byte per character, and more
bytes are added for non-ASCII characters. CamCOPS uses UTF-8.

A *collation* is a MySQL term for the way that characters are compared. For
example, if you are sorting in Swedish and you don’t care about case
sensitivity, you want the ordering A–Z then ÅÄÖ, and you want a to be considered
equal to A, å to be considered equal to Å, and so on.

Background: MySQL’s support for character sets and collations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now, to add to the difficulty, MySQL supports multiple different levels at which
you can define the character set and collation.

Character sets are supported for these things: *literal*, *column*, *table*,
*database*, *server* — plus *client*, *connection* (though I think that’s the
same as ‘literal’), *filesystem*, *results*, *system* [#charset]_. (Some don’t
change: system, for storing identifiers, always UTF8 [#sysvars]_. Some we don’t
need to care about: filesystem, for referring to filenames. The client one is
for statements arriving from the client. The connection one is used for
literals, and I have no idea why you might want this to be different from the
client setting. The results one is the one that the server uses to return
result sets or error messages. You can inspect some of these settings with
``SHOW VARIABLES LIKE 'char%'``, and table-specific settings using `SHOW CREATE
TABLE tablename`.)

Collations are supported for the following (from greatest to least precedence):
*query*, *column*, *table*, *database*, *connection*, *server* [#collations]_.
(The connection collation is applicable for the comparison of literal strings.)

.. note::

    You can inspect the database/connection/server collations using

    .. code-block:: sql

        SHOW VARIABLES LIKE 'collation%'

    and table-specific settings using

    .. code-block:: sql

        SHOW CREATE TABLE tablename

    Inspect all table collations for a given database with

    .. code-block:: sql

        SELECT table_catalog, table_schema, table_name, column_name, character_set_name, collation_name
        FROM information_schema.columns
        WHERE collation_name IS NOT NULL
        AND table_schema = 'camcops';  -- or whatever your database is named

How CamCOPS configures MySQL character sets and collations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS (via SQLAlchemy) creates all MySQL tables using the ‘utf8mb4’ character
set. This is MySQL’s “proper” 4-byte UTF8 character set. (The MySQL ‘utf8’
character set uses up to 3 bytes per character and can’t store all characters
[#utf8]_.)

CamCOPS uses the ‘utf8mb4_unicode_ci’ collation, which uses the ‘utf8mb4’
character set and implements the Unicode standard for sorting
[#utf8mb4unicodeci]_. The ‘_ci’ suffix means “case insensitive”. CamCOPS sets
the table collation when it creates tables, and then ignores collations for
queries/columns.

You can see what CamCOPS is doing easily from a running CamCOPS server, using
the “Inspect table definitions” view. You’ll see table definitions like:

.. code-block:: sql

    CREATE TABLE phq9 (
        q1 INTEGER COMMENT 'Q1 (anhedonia) (0 not at all - 3 nearly every day)',
        -- lots of other columns here
        -- lots of CONSTRAINT statements next
    ) CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC ENGINE=InnoDB;

The problem that creates this error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The underlying reason: a string comparison is occurring between columns with
different collations and MySQL cannot resolve the conflict [#mixofcollations]_.

The CamCOPS reason: if you have a very old CamCOPS database, it might not have
the table collations set properly. Pick some tables and use syntax like ``SHOW
CREATE TABLE phq9 \\G``. (The `\\G` is a special MySQL console suffix to show
the results in non-tabular format.) If you don’t see a `COLLATE` command at the
end, that’s probably the reason for the error.

How to generate the error
~~~~~~~~~~~~~~~~~~~~~~~~~

The error is typically triggered by viewing a clinical text view (CTV) that
joins across “old” and “new” tables. A textual comparison will happen on the
_era column. In the following example, `cisr` is a table with the collation set
correctly (`DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`), and `patient`
is an old one (`DEFAULT CHARSET=utf8mb4` only, with an implicit collation of
`utf8mb4_general_ci`). You can then generate an error by hand with the
following SQL:

.. code-block:: sql

    SELECT COUNT(*)
    FROM cisr c INNER JOIN patient p
        ON c.patient_id = p.id  -- integer; fine
        AND c._device_id = p._device_id  -- integer; fine
        AND c._era = p._era  -- string; collation mismatch; not fine
        -- COLLATE utf8mb4_unicode_ci  -- uncomment to fix the error for this query only
    ;

A quick solution
~~~~~~~~~~~~~~~~

Rather than applying the collation to each table, you’d think we could change
the database collation (and character set, while we’re at it) like this:

.. code-block:: sql

    ALTER DATABASE <dbname> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

However, that doesn’t work, because the old tables and columns both still have
‘hidden’ collation information:

.. code-block:: sql

    SHOW TABLE STATUS;
    SHOW FULL COLUMNS FROM patient;

So you have to go through all tables. To automate this [#changecollation]_,
execute the following command to generate all the necessary SQL:

.. code-block:: sql

    SELECT CONCAT(
            'ALTER TABLE ', table_schema, '.', table_name,
            ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
        ) AS ExecuteTheString
    FROM information_schema.tables
    WHERE table_schema = 'your_database_name'
    AND table_type = 'BASE TABLE';

Then a quick bit of copying/pasting and you should be there.

A CamCOPS table-creation bug, fixed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2018-07-02: this happened again on the CPFT machine. Most tables had a
collation of ``utf8mb4_general_ci`` except a new one
(``khandaker_1_medicalhistory``). There is no reference to
``utf8mb4_general_ci`` in the code except here in the help. The DDL report
looks right. Is there still a residual problem? Are upgrades messing with
the collations somehow? As of 2018-07-02 (CamCOPS server version 2.2.3),
all tables set back to ``CHARACTER SET utf8mb4 COLLATE
utf8mb4_unicode_ci``; let's see what happens.

In MySQL 5.7.22, this code:

.. code-block:: sql

    USE testdb;
    CREATE TABLE testtable (
        pk INTEGER PRIMARY KEY AUTO_INCREMENT,
        sometext VARCHAR(50)
    ) CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

successfully creates a table with the right collation. However, this
does not:

.. code-block:: sql

    USE testdb;
    CREATE TABLE testtable (
        pk INTEGER PRIMARY KEY AUTO_INCREMENT,
        sometext VARCHAR(50)
    ) COLLATE utf8mb4_unicode_ci CHARSET=utf8mb4;

The second produces fields with the default collation (e.g.
``uft8mb4_generai_ci``). So, the ``CHARSET`` command has to come before
the ``COLLATE`` command.

Now, in Alembic, these end up being passed as ``mysql_charset`` and
``mysql_collate`` parameters to the ``op.create_table()`` call. In
Alembic 0.9.9, the wrong order is generated. Ultimately, CamCOPS sets these
via ``Base.__table_args__``. SQLAlchemy finds that via
``ext/declarative/base.py`` and copies it to ``self.table_args``. Now, that
looks like it can be a dict or a tuple, so potentially ordered. However, in
Alembic, they are also passed as keyword arguments to
``alembic.operations.ops.CreateTableOp.create_table``, so go into an
unordered dict. The final result is typically ``COLLATE utf8mb4_unicode_ci
ROW_FORMAT=DYNAMIC ENGINE=InnoDB CHARSET=utf8mb4``, which doesn't get the
collation right.

So maybe one hacky option is to replace

.. code-block:: python

    Base.__table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_row_format': 'DYNAMIC',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

with

.. code-block:: python

    Base.__table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_row_format': 'DYNAMIC',
        'mysql_charset': 'utf8mb4 COLLATE utf8mb4_unicode_ci',
    }

since the COLLATE part is really an argument to CHARSET (or CHARACTER SET); see
https://dev.mysql.com/doc/refman/8.0/en/create-table.html.

(Of course, Python dictionaries are becoming ordered too; see
https://stackoverflow.com/questions/1867861/dictionaries-how-to-keep-keys-values-in-same-order-as-declared.)

Yes, that works. Therefore: fixed as of 2018-07-08, v2.2.4.


Web browser reports: “DevTools failed to parse SourceMap...”
------------------------------------------------------------

In full, the web browser reports:

::

    DevTools failed to parse SourceMap: https://wombat/camcops/deform_static/css/bootstrap.min.css.map

This file (`bootstrap.min.css.map`) should be shipped with Deform, but isn’t.
For now: don’t worry about it.


Logo PNG with transparency crashes PDF generator
------------------------------------------------

.. include:: include_old_bug_defunct.rst

*Problem*

If your institutional logo PNG file contains a transparency layer, it will
crash the xhtml2pdf PDF generator (as of 2015-02-05). The error looks like:

.. code-block:: none

     /usr/local/lib/python2.7/dist-packages/xhtml2pdf/xhtml2pdf_reportlab.py in getRGBData...
        426                     self.mode = 'RGB'
        427                 elif mode not in ('L', 'RGB', 'CMYK'):
    =>  428                     im = im.convert('RGB')
        429                     self.mode = 'RGB'
        430                 self._data = im.tostring()
    im = <PIL.PngImagePlugin.PngImageFile image mode=P size=590x118>, im.convert = <bound method PngImageFile.convert of <PIL.PngImagePlugin.PngImageFile image mode=P size=590x118>>

     /usr/local/lib/python2.7/dist-packages/PIL/Image.py in convert(self=<PIL.PngImagePlugin.PngImageFile image mode=P size=590x118>, mode='RGB', matrix=None, dither=3, palette=0, colors=256)
        808         if delete_trns:
        809             #crash fail if we leave a bytes transparency in an rgb/l mode.
    =>  810             del(new.info['transparency'])
        811         if trns is not None:
        812             if new_im.mode == 'P':
    global new = <function new>, new.info undefined

    <type 'exceptions.UnboundLocalError'>: local variable 'new' referenced before assignment
          args = ("local variable 'new' referenced before assignment",)
          message = "local variable 'new' referenced before assignment"

*Solution 1*

Remove the transparency layer. For example:

- Load the file in GIMP;
- :menuselection:`Layer --> Transparency --> Remove alpha channel`
- Resave, e.g. with :menuselection:`File --> Overwrite…`

*Solution 2*

Use a newer version of CamCOPS; from server version 1.40, it uses wkhtmltopdf
instead, which is also faster.

.. _mysql_row_size_too_large:


.. rubric:: Footnotes

.. [#toomanyconnections]
    https://dev.mysql.com/doc/refman/5.7/en/too-many-connections.html

.. [#charset]
    https://dev.mysql.com/doc/refman/5.7/en/charset-connection.html

.. [#sysvars]
    https://dev.mysql.com/doc/refman/5.5/en/server-system-variables.html

.. [#collations]
    https://stackoverflow.com/questions/24356090/difference-between-database-table-column-collation

.. [#utf8]
    https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-utf8mb4.html

.. [#utf8mb4unicodeci]
    https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci

.. [#mixofcollations]
    https://stackoverflow.com/questions/3029321/troubleshooting-illegal-mix-of-collations-error-in-mysql

.. [#changecollation]
   https://stackoverflow.com/questions/10859966/how-to-convert-all-tables-in-database-to-one-collation;
   https://stackoverflow.com/questions/1294117/how-to-change-collation-of-database-table-column

.. [#linuxflavours]
    See :ref:`Linux flavours <linux_flavours>`.
