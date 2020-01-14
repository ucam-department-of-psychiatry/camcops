..  docs/source/user/client_troubleshooting.rst

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


.. _client_troubleshooting:

Troubleshooting client problems
===============================

..  contents::
    :local:
    :depth: 3


I've lost the password for my CamCOPS client app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whoops! Any data that had not been uploaded to your server is lost, unless you
can remember the password. The databases are encrypted and the password to
unlock them is not stored anywhere by CamCOPS.

Make a copy of the databases anyway, just in case you remember the password.
See :ref:`Where does the client store my data? <client_default_db_location>`

Then you can delete them, and when you start CamCOPS it will make fresh
databases, but you'll have to reconfigure CamCOPS from scratch and you won't
get your data back.

Any data that was uploaded to the server should be fine.


Windows client fails to start under Windows Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Windows Server is not a supported operating system for the CamCOPS client. It's
not the same as normal Windows, which is supported! Windows Server is intended
for large-scale server use and doesn't have multimedia components that are a
standard part of normal Windows. See :ref:`CamCOPS client won't run under
Windows Server <client_windows_server>`.


Tablet upload fails with error “Read timed out”
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Likely problem: slow network, large BLOB (binary large object – e.g. a big
photo). For example, in one of our tests a BLOB took more than 17 s to upload,
so the tablet needs to wait at least that long after starting to send it.
Increase the tablet’s network timeout (e.g. to 60000 ms or more) in Settings →
Server settings.


A photo-based task says "No camera"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS asks Qt for available cameras. This message indicates that none were
found. This is usually a hardware configuration problem.

- Under Linux, run ``cheese``; does this find a camera?

- If you're using a laptop, does it have a special function key combination to
  enable/disable the camera?


What if it crashes?
~~~~~~~~~~~~~~~~~~~

This shouldn’t happen; please note down any error details and let us know! To
forcibly stop and restart the app:

*Android 4.3*

- Settings → More → Application Manager → CamCOPS → Force stop

- Then start the app again as usual.

*iOS 7*

- Double-click the Home button

- Swipe left/right until you find the CamCOPS app’s preview

- Swipe the app preview up to close it

- Then start the app again as usual

*Windows*

- Close it as usual; if it refuses to close, kill it via the Task Manager.


Rescuing data from very old CamCOPS clients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have an old Titanium version (version 1.x), then before you attempt an
upload to a modern CamCOPS server, follow these steps.

- Ensure you have a computer with the Android SDK installed, and an appropriate
  USB cable.

- Ensure the tablet device has USB debugging enabled.

- In CamCOPS, choose :menuselection:`Settings --> Dump local database to SQL
  file (Android only)`.

- It should say that it's saved to ``appdata:///camcops_db.txt``; this means
  ``/sdcard/org.camcops.camcops/camcops_db.txt`` on the filesystem.

- On the big computer, try ``adb devices`` to list devices, and ``adb shell``
  to run an SSH-type shell into the tablet.

- On the big computer, fetch the file via

  .. code-block:: bash

    adb pull /sdcard/org.camcops.camcops/camcops_db.txt rescued_camcops_db.txt

- If you want to create a binary SQLite database, then do

  .. code-block:: bash

    sqlite3 rescued_camcops_db.sqlite < rescued_camcops_db.txt
