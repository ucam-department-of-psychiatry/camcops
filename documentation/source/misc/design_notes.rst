..  misc/design_notes.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
    This file is part of CamCOPS.
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.


Design notes
============

A few design decisions are documented here.

Client SQLCipher databases
--------------------------

The CamCOPS client uses two databases (typically called `camcops_data.sqlite`
and `camcops_sys.sqlite`), stored in the device’s user-specific private area
(e.g. `~/local/share/camcops under Linux`). Note that some operating systems
(e.g. Android, iOS) are designed for single-user use and don’t have the concept
of a per-user private area. The ‘data’ database holds user data (patients,
patient data) and the ‘sys’ database contains configuration information, stored
strings, and the like. Both are encrypted with AES-256 via SQLCipher. They use
the same passphrase for user convenience, but different encryption keys [#f1]_.

The decision to use two databases rather than one is so that, in emergencies,
the ‘data’ database can be processed (viewed, rescued) without the need to
share the ‘sys’ database and its information. It also simplifies the upload
process a little (as the client can simply upload everything from the ‘data’
database and nothing from the ‘sys’ database).

Inline CSS
----------

The server currently provides CSS inline. It could refer to CSS as files, so
that browsers cache them better. However, inline CSS is still required for PDF
creation, and it’s not clear this is an important performance constraint.

SFTP export
-----------

Not necessary, as one can mount an SFTP directory via NFS, then just export as a
plain file.

Anonymisation
-------------

Proper anonymisation is Somebody Else’s Business; CamCOPS supports convenient
export for subsequent anonymisation (see, for example, CRATE;
https://github.com/RudolfCardinal/crate).


.. rubric:: Footnotes

.. [#f1] See https://www.zetetic.net/sqlcipher/design/
