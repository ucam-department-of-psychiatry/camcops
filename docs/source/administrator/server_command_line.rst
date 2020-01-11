..  docs/source/administrator/server_command_line.rst

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

.. _server_command_line_tools:

CamCOPS command-line tools
==========================

..  contents::
    :local:
    :depth: 3


.. _camcops_cli:

camcops_server
--------------

The ``camcops_server`` command is the main interface to the CamCOPS server.
Options (output from ``camcops_server --allhelp``):

..  literalinclude:: camcops_server_allhelp.txt
    :language: none


.. _camcops_server_meta:

camcops_server_meta
-------------------

The ``camcops_server_meta`` tool allows you to run CamCOPS over multiple
CamCOPS configuration files/databases. It’s less useful than it was, because
the dominant mode of “one database per research group” has been replaced by the
concept of “a single database with group-level security”.

Options:

..  literalinclude:: camcops_server_meta_help.txt
    :language: none


.. _camcops_fetch_snomed_codes:

camcops_fetch_snomed_codes
--------------------------

Subject to you having the necessary permissions, and access to a SNOMED CT REST
API server, this tool will help you find SNOMED CT codes relevant to CamCOPS.
See :ref:`SNOMED CT coding <snomed>` and :ref:`SNOMED CT licensing
<licence_snomed>`.

Options:

..  literalinclude:: camcops_fetch_snomed_codes_help.txt
    :language: none


.. _camcops_backup_mysql_database:

camcops_backup_mysql_database
-----------------------------

This simple tool uses MySQL to dump a MySQL database to a .SQL file (from which
you can restore it), and names the file according to the name of the database
plus a timestamp.

Options:

..  literalinclude:: camcops_backup_mysql_database_help.txt
    :language: none
