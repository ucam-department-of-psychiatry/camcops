..  documentation/source/introduction/registration.rst

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

.. _registration:

About device registration
=========================

Tablets must register with a server. This serves four purposes:

**The server doesn’t want unauthorized devices uploading to it.**

Consequently, the server will only accept uploads from registered devices, and
requires users to authenticate (with a username approved for device
registration) before accepting registration.

**Administrators don’t want their clinicians to upload data to unauthorized
servers.**

Consequently, registration is a privileged-mode function. (As a result, the
requirement to re-register a device should be minimized, since the day-to-day
user of the tablet may not be authorized to register a device.)

**The server and the tablet should share a set of ID descriptions.**

It is not envisaged that the server’s ID type labelling should change once set!
However, allowing for that possibility: the tablet should not overwrite its ID
descriptions without checking with the user (except at device registration),
because this may apply errors to existing patients’ ID descriptions (e.g.
something the tablet thought was an NHS number is re-labelled as
hospital-X-number). CamCOPS will (a) automatically accept ID descriptions when
you register a device; (b) allow you to manually accept ID descriptions at any
time [Settings → Accept ID descriptions from the server]; (b) check that the
descriptions match when you upload, and if they do not match, prevent upload
until you have manually accepted them. You are advised to check all patients’
ID number/descriptions carefully if this mismatch occurs.

**The tablet needs to know the server’s upload/finalize policies.**

Consequently, the tablet re-checks these policies before commencing an upload.
