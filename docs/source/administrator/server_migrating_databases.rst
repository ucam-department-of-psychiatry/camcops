..  docs/source/administrator/server_migrating_databases.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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

.. _DataGrip: https://www.jetbrains.com/datagrip/
.. _DBeaver: https://dbeaver.io/
.. _JDBC: https://en.wikipedia.org/wiki/Java_Database_Connectivity
.. _MySQL: https://www.mysql.com/
.. _MySQL Workbench: https://www.mysql.com/products/workbench/
.. _Navicat: https://www.navicat.com/
.. _ODBC: https://en.wikipedia.org/wiki/Open_Database_Connectivity
.. _PostgreSQL: https://www.postgresql.org/
.. _SQLite: https://www.sqlite.org/
.. _SQLiteStudio: https://sqlitestudio.pl/
.. _SQL Server: https://www.microsoft.com/sql-server/
.. _SQL Server Integration Services: https://docs.microsoft.com/en-us/sql/integration-services/sql-server-integration-services
.. _SQL Server Management Studio: https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms
.. _SQL Server Migration Assistant: https://docs.microsoft.com/en-us/sql/ssma/sql-server-migration-assistant
.. _SQuirreL SQL: http://squirrel-sql.sourceforge.net/


Server: migrating and merging databases
=======================================

As always, **back up your data first!**. Here are some suggestions for useful
database tools and a summary of automatic migration tools in CamCOPS.

..  contents::
    :local:
    :depth: 3


Database-specific tools
-----------------------

MySQL

- MySQL_ provides `MySQL Workbench`_, which uses ODBC_ to migrate other
  databases to MySQL.

- The ``mysqldump`` tool produces database backups in SQL format.

- The :ref:`camcops_backup_mysql_database` tool simplifies the use of
  ``mysqldump`` a little.

SQL Server

- `SQL Server`_ provides the `SQL Server Migration Assistant`_ (SSMA), in
  addition to `SQL Server Management Studio`_ (SSMS) and `SQL Server
  Integration Services`_ (SSIS). For specimen use, see e.g.
  https://www.sqlshack.com/migrate-mysql-tables-sql-server-using-sql-server-migration-assistant-ssma-ssis/.

SQLite

- A good one is SQLiteStudio_.


Generic tools
-------------

See https://en.wikipedia.org/wiki/Comparison_of_database_tools.

These include:

- `DataGrip`_: SQL and some schema management tools. Didn't leap out as superb.

- `DBeaver`_: **I think this is good.** Includes export/import support. Uses
  JDBC_.

- `Navicat`_: commercial product to support many databases that includes data
  migration as well as an SQL client. The Premium version
  supports lots of databases simultaneously (but as of 2018-09-30, it's
  $1,299).

- `SQuirreL SQL`_: this tool uses JDBC_ to connect to databases. I remember it
  as being quite good, but as of 2018-09-30 it doesn't seem to work under
  Ubuntu 18.04:

  #. Download the ``.jar`` file and launch it with

     .. code-block:: bash

        java -jar squirrel-sql-3.8.1-standard.jar

  #. Then fix any resulting "Assistive Technology Not Found" error like this:
     https://askubuntu.com/questions/695560/assistive-technology-not-found-awterror,
     e.g. by running

     .. code-block:: bash

        sudo pico /etc/java-11-openjdk/accessibility.properties

     and commenting out the line

     .. code-block:: none

        assistive_technologies=org.GNOME.Accessibility.AtkWrapper

     Then re-run the installer.

  #. Then launch SQuirreL.

  #. Then, if it incorrectly complains about your Java JVM version, hack the
     launch script as per https://sourceforge.net/p/squirrel-sql/bugs/1019/.
     Note that its version detection (in ``JavaVersionChecker.java``) is
     extremely primitive, being based on string comparison. Just hack this line
     in ``squirrel-sql.sh`` (for Linux systems):

     .. code-block:: bash

        $JAVACMD -cp "$UNIX_STYLE_HOME/lib/versioncheck.jar" JavaVersionChecker 1.8 9

     so that your JVM version is mentioned (e.g. add ``10`` to support JVM
     10.0.2.

  #. Then launch SQuirreL.

  #. Still fails, silently, with SQuirreL 3.8.1 under Ubuntu 18.04.


Merging old CamCOPS databases
-----------------------------

If you have several old CamCOPS databases and you want to merge them, so that
each old database is represented by a distinct group (or groups) in the new
database, see the ``camcops_server merge_db`` command, described in
:ref:`CamCOPS command-line tools <camcops_cli>`.
