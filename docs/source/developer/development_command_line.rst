..  docs/source/developer/development_command_line.rst

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

.. _OpenSSL: https://www.openssl.org/
.. _Qt: https://www.qt.io/
.. _SQLCipher: https://www.zetetic.net/sqlcipher/
.. _SQLite: https://www.sqlite.org/
.. _WAV: https://en.wikipedia.org/wiki/WAV


.. _development_command_line_tools:

Development command-line tools
==============================

If you are developing tasks for CamCOPS, be aware of these additional
development tools.

..  contents::
    :local:
    :depth: 3


**In tablet_qt/tools:**


.. _build_qt:

build_qt.py
-----------

This program runs on a variety of platforms (including Linux, Windows, macOS)
and has the surprisingly tricky job of building the following libraries, from
source:

- OpenSSL_
- SQLCipher_
- Qt_

for the following platforms, using a variety of CPUs:

- Android (32-bit ARM, 64-bit x86 emulator) (compile under Linux)
- iOS (32-bit ARM, 64-bit ARM, 64-bit x86 simulator) (compile under macOS)
- Linux (64-bit x86)
- macOS (64-bit x86)
- Windows (32-bit x86, 64-bit x86)

It will fetch source code and do all the work. Once built, you should have a Qt
environment that you can point Qt Creator to, and you should be able to compile
CamCOPS with little extra work. (Though probably not none.)

The ``--build_all`` option is generally a good one; this builds for all
architectures supported on the host you're using.

Here's its help:

..  literalinclude:: build_qt_help.txt
    :language: none


chord.py
--------

This generates musical chords as WAV_ files. It's not very generic but it
generates specific sounds used by the CamCOPS client.


decrypt_sqlcipher.py
--------------------

This tool requires an installed copy of SQLCipher_. It creates a decrypted
SQLite_ database from an encrypted SQLCipher_ database, given the password.

Here's its help:

..  literalinclude:: decrypt_sqlcipher_help.txt
    :language: none


encrypt_sqlcipher.py
--------------------

This tool requires an installed copy of SQLCipher_. It creates an encrypted
SQLCipher_ database from a plain SQLite_ database.

Here's its help:

..  literalinclude:: encrypt_sqlcipher_help.txt
    :language: none


open_sqlcipher.py
------------------

This tool requires an installed copy of SQLCipher_. It opens an encrypted
SQLCipher_ database via the SQLite_ command line tool, given the password.
You can use this to view/edit CamCOPS databases.

Here's its help:

..  literalinclude:: open_sqlcipher_help.txt
    :language: none


**In server/tools:**


build_translations.py
---------------------

Builds translation files for the server. See :ref:`Internationalization
<dev_internationalization>`.


create_database_migration.py
----------------------------

Creates a new database migration for the server, in
``server/camcops_server/alembic/versions/``. Here's its help:

.. literalinclude:: create_database_migration_help.txt
    :language: none


make_xml_skeleton.py
--------------------

Takes a "secret" XML file (one containing task text that is restricted to a
particular site) and makes a generic "skeleton" XML file -- the same but with
strings replaced by placeholder text -- so that others can see the structure
required if they too have the permissions to create the full file.

Writes to stdout (so redirect it to save to a file). Here's its help:

.. literalinclude:: make_xml_skeleton_help.txt
    :language: none
