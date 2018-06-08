..  documentation/source/introduction/data_structure_design.rst

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

Internal data structure in CamCOPS
==================================

The basics
----------

- The CamCOPS client uses a simple, standard relational database design.

- The server tables mirror the client device tables closely.

- On top of this, a layer of complexity is grafted: (a) to allow devices to
  operate independently, (b) to allow an audit trail, and (c) to allow devices
  to wipe their data whilst preserving it on the server.

To overcome this complexity for most practical purposes, the server provides
methods of viewing or downloading task data that hides out-of-date versions and
so forth.

Audit trail and preserve-and-delete function
--------------------------------------------

The thought process behind the design runs as follows.

- Tablet devices (“clients”) must be able to operate offline, without internet
  connectivity. Therefore, they must store their data locally, at least for a
  time; and they must periodically communicate with their server.

- Patient details should not be retrievable from a central server to the tablet
  device, because that isn’t necessary (the web viewer offers an alternative
  route) and therefore represents an unnecessary security vulnerability.
  Additionally, requiring different tablets to be synchronized is potentially
  unreliable (e.g. if someone adds the same patient on two tablets, both
  currently disconnected from the network). Consequently, patient details on
  different tablet devices are not necessarily synchronized. Therefore, the
  server must maintain records for each of its client tablet devices and keep
  them independent.

  - All client tables have a primary key called id; this primary key is unique in
    that table on that device.

  - The server mirrors the tables found on the client device.

  - In addition, a `_device` field on the server discriminates records by the
    unique device ID of the uploading device.

  - The server maintains its own primary key in the `_pk` field; this field is
    unique in that table on the server (across all devices).

- If someone edits a record on the server, the server shouldn’t rewrite its own
  records; it should maintain an audit trail. Therefore, the server must keep
  “old” records and distinguish them from “current” records.

  - The server maintains a `_current` field, to mark current records.

  - Records that are not current have additional information. (Is the record
    not current because it was deleted or because it was modified? Who deleted
    or modified it? Which is its predecessor or successor record?)

  - Inclusion of fields for “when added” and “when removed” allows a historical
    snapshot for any moment in time to be created.

- It should be possible to wipe a tablet device, yet keep its data actively
  accessible on the server. Therefore, the server must keep “era” information
  for each device.

  - The server has an `_era` field for each table.

  - The `_era` field begins life with the value `'NOW'`, representing the
    “current” era. (The use of `'NOW'` rather than NULL allows string
    comparison at all times; see below regarding date/time storage.)

  - When a device “preserves” its data on the server and wipes its database,
    the _era field is set to the date/time of the preservation process, for all
    records in all tables for that device that were in the “current” era. A new
    era is therefore begun for that device.

  - The combination of the `_device`, `_era`, and `id` fields is unique for all
    `_current` fields.

Transactional upload
--------------------

The upload process is transactional: it either succeeds as a whole, or fails as
a whole. (This is necessary because there may be arbitrary relationships
between tables on the tablet, e.g. between the main table of a task and its
sub-tables.)

Date/time storage
-----------------

Databases like MySQL discard fractions of a second, and CamCOPS needs to store
millisecond-accuracy timing information. Moreover, it is often helpful to work
in local time zones. Few databases handle this well, and there are no
consistent standards for database timezone handling.

For consistency, therefore, all date and date/time fields are stored as TEXT
fields in ISO 8601 format [#iso8601]_, specifically
`YYYY-MM-DDTHH:mm:ss.SSS+ZZ:ZZ`. An example is `2013-04-22T14:35:07.381+01:00`
– this means 22 April 2013 at 7.381 seconds after 2:35pm in a time zone 1 hour
ahead of Coordinated Universal Time (UTC, GMT), such as British Summer Time
(+01:00). Greater (e.g. microsecond) accuracy is permitted but not generally
used.

There are a few fields that are an exception to this rule and use DATETIME
format, but these are only used by the server and are not generally accessible
to users.

Tables in the CamCOPS database
------------------------------

Full details are available via the server’s option to view device definition
language (DDL, a subset of SQL) for all tables. These are fully commented, for
DDL dialects that support comments (try MySQL).

Note in particular the following conventions

- Tables beginning with an underscore (`_`) are private to the server, i.e. data
  is not uploaded into them.

- Fields (columns) beginning with an underscore are added by the server.

- Columns with “(TASK)” in their comments are generic task fields.

- Columns with “(CLINICIAN)” in their comments are generic fields for tasks
  having a clinician whose details are recorded.

- Columns with “(RESPONDENT)” in their comments are generic fields for tasks
  having a respondent (i.e. someone answering the questions who’s not the
  patient/subject and who’s not the clinician -- such as a carer).

- Columns with “(SERVER)” in their comments are added by the server.

- Columns with “(GENERIC)” in their comments are generic summary fields.
  Summary fields are not present on the server, but are created dynamically.
  See :ref:`summary fields <summary_fields>`.


.. rubric:: Footnotes

.. [#iso8601]
    https://en.wikipedia.org/wiki/ISO_8601
