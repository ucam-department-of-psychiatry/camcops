..  documentation/source/client/client_troubleshooting.rst

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


Troubleshooting client problems
===============================

Tablet upload fails with error “Read timed out”
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Likely problem: slow network, large BLOB (binary large object – e.g. a big
photo). For example, in one of our tests a BLOB took more than 17 s to upload,
so the tablet needs to wait at least that long after starting to send it.
Increase the tablet’s network timeout (e.g. to 60000 ms or more) in Settings →
Server settings.

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
