..  docs/source/user/client_uninstall_upgrade.rst

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

Client upgrades and uninstallation
==================================

..  contents::
    :local:
    :depth: 3


Upgrading the client
--------------------

Just install a newer version. For example:

- For Android, install a newer version from the Google Play Store.

- For Windows, download the newer version and run its installer.

This will replace the CamCOPS software but should find your old (client)
databases, upgrade them if necessary, and continue working with them.

.. note::

    It shouldn't be critical, but as a matter of good practice, move all your
    data to your CamCOPS server before upgrading the client.

.. note::

    If your client and your institution's server are upgraded to support new
    CamCOPS tasks, you should tell the client to check in with the server to
    retrieve any new strings (etc.) that it might need. :ref:`Re-register
    <configuring_client>` with the server.

.. todo::

    Implement a simpler way to do this, without the need to re-register (which
    requires elevated privilege),


.. _client_default_db_location:

Where does the client store my data?
------------------------------------

The CamCOPS client uses two encrypted databases called ``camcops_data.sqlite``
and ``camcops_sys.sqlite``, stored in the device’s user-specific private area,
as below. (Note that some operating systems, such as Android and iOS, are
designed for single-user use and don’t have the concept of a per-user private
area.) For more details, see :ref:`Client SQLCipher databases
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

On some operating systems, you can specify a non-standard location for the
client databases. See :ref:`Specifying a non-standard database location <client_nonstandard_db_location>`.


Uninstalling the client
-----------------------

Use your operating system's uninstallation process. For example, in Windows,
use "Add or remove programs". In Android, remove the app. But **see below!**


Could data be lost if I uninstall the CamCOPS client?
-----------------------------------------------------

- **Android.** Yes! All application data is typically deleted when an
  application is removed.

- **Windows, Linux.** It shouldn't be. The installer doesn't touch the data. If
  you uninstall CamCOPS, the data should be left behind. If you install a new
  version, it should pick up the old data.

.. warning::

    Ensure you've moved all your data to your CamCOPS server before you
    uninstall the client!


Could data be lost if I downgrade the CamCOPS client?
-----------------------------------------------------

Yes!

CamCOPS doesn't delete unexpected database tables, but it does reshape existing
tables. Suppose we have the following situation:

+----------------+-------------------------+-------------------------+
| Table, column  | Present in old version? | Present in new version? |
+----------------+-------------------------+-------------------------+
| table1.column1 | Y                       | Y                       |
+----------------+-------------------------+-------------------------+
| table1.column2 | N                       | Y                       |
+----------------+-------------------------+-------------------------+
| table2.*       | N                       | Y                       |
+----------------+-------------------------+-------------------------+

When you upgrade from the old version to the new version, the new version will
add column ``column2`` to table ``table1``, and it will create table
``table2``. You might add data to those tables/columns. If you then manage to
install the old version, the old version will ignore ``table2`` (and leave it
intact) but it will notice that ``column2`` doesn't belong in ``table1`` and
will delete it -- which might lose data.

.. warning::

    Avoid downgrading the CamCOPS client. If you must downgrade, be sure to
    move all your data to your server first!
