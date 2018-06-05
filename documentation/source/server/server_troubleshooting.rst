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

MySQL: “Too many connections”
-----------------------------

This error occurs if programs collectively attempt to open more connections to
MySQL than the configured limit [#f1]_. The easiest way to make it happen in
CamCOPS is to launch a web server with a very high maximum number of threads,
in excess of the MySQL limit, and then work the web server hard.

Fix the problem by limiting the maximum number of threads/processes used by
CamCOPS or by increasing the MySQL connection limit.

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
same as ‘literal’), *filesystem*, *results*, *system* [#f2]_. (Some don’t
change: system, for storing identifiers, always UTF8 [#f3]_. Some we don’t need
to care about: filesystem, for referring to filenames. The client one is for
statements arriving from the client. The connection one is used for literals,
and I have no idea why you might want this to be different from the client
setting. The results one is the one that the server uses to return result sets
or error messages. You can inspect some of these settings with `SHOW VARIABLES
LIKE 'char%'`, and table-specific settings using `SHOW CREATE TABLE
tablename`.)

Collations are supported for the following (from greatest to least precedence):
*query*, *column*, *table*, *database*, *connection*, *server* [#f4]_. (The
connection collation is applicable for the comparison of literal strings. You
can inspect the database/connection/server collations using `SHOW VARIABLES LIKE
'collation%'`, and table-specific settings using `SHOW CREATE TABLE tablename`.)

How CamCOPS configures MySQL character sets and collations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS (via SQLAlchemy) creates all MySQL tables using the ‘utf8mb4’ character
set. This is MySQL’s “proper” 4-byte UTF8 character set. (The MySQL ‘utf8’
character set uses up to 3 bytes per character and can’t store all characters
[#f5]_.)

CamCOPS uses the ‘utf8mb4_unicode_ci’ collation, which uses the ‘utf8mb4’
character set and implements the Unicode standard for sorting [#f6]_. The ‘_ci’
suffix means “case insensitive”. CamCOPS sets the table collation when it
creates tables, and then ignores collations for queries/columns.

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
different collations and MySQL cannot resolve the conflict [#f7]_.

The CamCOPS reason: if you have a very old CamCOPS database, it might not have
the table collations set properly. Pick some tables and use syntax like `SHOW
CREATE TABLE phq9 \\G`. (The `\\G` is a special MySQL console suffix to show the
results in non-tabular format.) If you don’t see a `COLLATE` command at the end,
that’s probably the reason for the error.

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

So you have to go through all tables. To automate this [#f8]_, execute the
following command to generate all the necessary SQL:

.. code-block:: sql

    SELECT CONCAT(
            'ALTER TABLE ', table_schema, '.', table_name,
            ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
        ) AS ExecuteTheString
    FROM information_schema.tables
    WHERE table_schema = 'your_database_name'
    AND table_type = 'BASE TABLE';

Then a quick bit of copying/pasting and you should be there.


Web browser reports: “DevTools failed to parse SourceMap...”
------------------------------------------------------------

In full, the web browser reports:

::

    DevTools failed to parse SourceMap: https://wombat/camcops/deform_static/css/bootstrap.min.css.map

This file (`bootstrap.min.css.map`) should be shipped with Deform, but isn’t.
For now: don’t worry about it.


.. rubric:: Footnotes

.. [#f1] https://dev.mysql.com/doc/refman/5.7/en/too-many-connections.html

.. [#f2] https://dev.mysql.com/doc/refman/5.7/en/charset-connection.html

.. [#f3] https://dev.mysql.com/doc/refman/5.5/en/server-system-variables.html

.. [#f4] https://stackoverflow.com/questions/24356090/difference-between-database-table-column-collation

.. [#f5] https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-utf8mb4.html

.. [#f6] https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci

.. [#f7] https://stackoverflow.com/questions/3029321/troubleshooting-illegal-mix-of-collations-error-in-mysql

.. [#f8]
   https://stackoverflow.com/questions/10859966/how-to-convert-all-tables-in-database-to-one-collation;
   https://stackoverflow.com/questions/1294117/how-to-change-collation-of-database-table-column
