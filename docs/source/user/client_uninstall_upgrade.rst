..  docs/source/user/client_uninstall_upgrade.rst

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

Client upgrades and uninstallation
==================================

..  contents::
    :local:
    :depth: 3

Uninstalling the client
-----------------------

Use your operating system's uninstallation process. For example, in Windows,
use "Add or remove programs".

Where is my data stored?
------------------------

The CamCOPS client uses two encrypted databases called `camcops_data.sqlite`
and `camcops_sys.sqlite`, stored in the device’s user-specific private area, as
below. (Note that some operating systems, such as Android and iOS, are designed
for single-user use and don’t have the concept of a per-user private area.) For
more details, see :ref:`Client SQLCipher databases
<client_sqlcipher_databases>`.

+------------------+----------------------------------------------------------+
| Operating system | Typical location                                         |
+------------------+----------------------------------------------------------+
| Windows 10       | ``C:\Users\MYUSER\AppData\Roaming\camcops\``             |
+------------------+----------------------------------------------------------+
| Linux            | ``/home/MYUSER/.local/share/camcops/``                   |
+------------------+----------------------------------------------------------+
| Android          | ``/data/user/0/org.camcops.camcops/files/``              |
+------------------+----------------------------------------------------------+

The client will tell you the location itself; see :menuselection:`Help --> View
device ID and database details`.

Will data be lost if I uninstall CamCOPS
----------------------------------------

It shouldn't be! The installer doesn't touch the data. If you uninstall
CamCOPS, the data should be left behind. If you install a new version, it
should pick up the old data.
