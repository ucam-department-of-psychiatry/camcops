..  documentation/source/server/server_installation.rst

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

Installing and configuring the server
=====================================

Hardware and operating system requirements
------------------------------------------

The CamCOPS server is cross-platform software written in Python. It’s been
tested primarily under Linux with MySQL.

URLs for CamCOPS source code
----------------------------

- https://github.com/RudolfCardinal/camcops (for source)

.. TODO: https://pypi.io/project/XXX/ (for pip install XXX)

Ubuntu installation from Debian package
---------------------------------------

To install CRATE and all its dependencies, download the Debian package and use
gdebi:

.. code-block:: bash

    $ sudo gdebi camcops-VERSION.deb

where :code:`VERSION` is the CamCOPS version you're installing.
(If you don’t have gdebi, install it with :code:`sudo apt-get install gdebi`.)

Installation for any OS
-----------------------

.. TODO: WRITE XXX
