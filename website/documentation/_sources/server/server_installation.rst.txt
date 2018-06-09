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

Installing CamCOPS on the server
================================

Hardware and operating system requirements
------------------------------------------

The CamCOPS server is cross-platform software written in Python. It’s been
tested primarily under Linux with MySQL.

URLs for CamCOPS source code
----------------------------

- https://github.com/RudolfCardinal/camcops (for source)

.. TODO: https://pypi.io/project/XXX/ (for pip install XXX)

Installing CamCOPS
------------------

See :ref:`Linux flavours <linux_flavours>` for a reminder of some common
differences between Linux operating systems.

Ubuntu installation from Debian package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install CRATE and all its dependencies, download the Debian package and use
gdebi:

.. code-block:: bash

    $ sudo gdebi camcops-VERSION.deb

where :code:`VERSION` is the CamCOPS version you're installing.
(If you don’t have gdebi, install it with :code:`sudo apt-get install gdebi`.)

CamCOPS will now be installed in `/usr/share/camcops`.

You should be able to type ``camcops`` and see something relevant.

CentOS installation from RPM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, to get Centos 6.5 to a basic standard, :ref:`see here
<centos65_prerequisites>`. Then:

.. code-block:: bash

    sudo yum install camcops_VERSION.noarch.rpm

    # Or, for more verbosity and to say yes to everything, use this command instead:
    # sudo yum --assumeyes --verbose --rpmverbosity=debug install camcops_VERSION.noarch.rpm
    # ... but, curiously, yum temporarily swallows the output from the post-install
    #     scripts and only spits it out at the end. This makes it look like the
    #     installation has got stuck (because packages like numpy are very slow
    #     to install); use "watch pstree" or "top" to reassure yourself
    #     that progress is indeed happening.

You should be able to type ``camcops`` and see something relevant.

Installation for any OS
~~~~~~~~~~~~~~~~~~~~~~~

.. todo:: upload to PyPI; write description of how to install via Pip

.. todo:: implement Windows service

Installing other prerequisites
------------------------------

For example, you might be running Ubuntu and want to use Apache as your
front-end web server and MySQL as your database:

.. code-block:: bash

    sudo apt-get install apache2 mysql-client mysql-server

See also the :ref:`more detailed MySQL configuration tips <linux_mysql_setup>`.
