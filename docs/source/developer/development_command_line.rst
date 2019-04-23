..  docs/source/developer/development_command_line.rst

..  Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).
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

Here's its help as of 2018-06-09:

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

Here's its help as of 2018-06-09:

..  literalinclude:: decrypt_sqlcipher_help.txt
    :language: none
