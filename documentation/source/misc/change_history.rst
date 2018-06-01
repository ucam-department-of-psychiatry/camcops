..  misc/change_history.rst

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

Change history
==============

*Both client and server changes are described here.*

Client v2.0.0 beta

- Development of C++ version from scratch. Replaces Titanium version.

- Released as beta to Google Play on 2017-07-17.

Client v2.0.1 beta

- More const checking.

- Bugfix to stone/pound/ounce conversion.

- Bugfix to raw SQL dump.

- ID numbers generalized so you can have >8 (= table structure change).

Client v2.0.2 beta

- Cosmetic bug fixes, mainly for phones, including a re-layout of the ACE-III
  address learning for very small screens.

- Bugfix: deleting a patient didn't deselect that patient.

- Default software keyboard for date entry changed.

- Bugfix for canvas widget on Android (size was going wrong).

- Automatic adjustment for high-DPI screens as standard in `QuBoolean` (its
  image option), `QuCanvas`, `QuImage`, `QuThermometer`.

Client v2.0.3 beta, 2017-08-07

- Trivial type fix to patient_wanted_copy_of_letter (String → Bool) in the
  unused task CPFTLPSDischarge.

Client v2.0.4 beta, 2017-10-22

- Bugfix: BLOB FKs weren’t being set properly from `BlobFieldRef` helper
  functions.

Client v2.0.5 beta, 2017-10-23

- Bugfix: if the server’s ID number definitions were consecutively numbered, the
  client got confused and renumbered them from 1.

Server v2.1.1 beta, 2017-10-23

- Bugfix: WSAS “is complete?” flag failed to recognize the “retired or work
  irrelevant for other reasons” flag.

Client v2.2.0 beta, 2018-01-04 to 2018-02-03

- *To solve the problem of clients and servers being upgraded independently:*
  Reads tables from server during registration (see server v2.2.0). Implemented
  a “minimum server version” option internally for each task (see contemporary
  server changelog). Minimum server version increased from v2.0.0 to v2.2.0.

- Bugfix: adding a new patient from a task list didn’t wipe the task list until
  the patient was re-changed (failure to call `setSelectedPatient` from
  `ChoosePatientMenu::addPatient`; in fact, the patient name details changed
  without changing the underlying patient selection).

- Bugfix: don’t think the patient ID number table was being made routinely (!?).

- New CIS-R task.

- Internal fix to `DynamicQuestionnaire` to defer first-page creation until
  after constructor.

- Menu additions for CPFT Affective Disorders Research Database.

Server v2.2.0, 2018-01-04 to 2018-04-24

- *To solve the problem of clients and servers being upgraded independently:*
  Maintains a minimum client (tablet) version per task; during registration,
  offers the client the list of its tables and the minimum number. This allows a
  newer client to recognize that the server is older and has ‘missing’ tables,
  and act accordingly. See `ensure_valid_table_name()`. Minimum tablet version
  remains v1.14.0.

- An obvious question: with that mechanism in place, is there any merit to the
  client maintaining a list of minimum server versions for each task? The change
  to the client’s “minimum server version” to 2.2.0 (for client v2.2.0) means
  that future clients will always have the “supported versions” information from
  the server. So, might a client advance mean that it might want to refuse old
  versions of the server, even though the server might be happy to accept?
  (That’s the only situation when a client’s per-table minimum server version
  would come into play.) Well, perhaps it’s possible, even if it’s very unlikely
  (and would probably indicate bad backwards compatibility on the client’s part!
  Let’s implement it for symmetry. Actually, thinking further, it might be quite
  useful: if you upgrade a task and add extra fields, using this would
  potentially allow the client to work with older servers unless a specific task
  is used. Implemented; see client changelog above. The default for all tasks is
  the client-wide minimum server version.

- New report to find patients by ICD-10 or ICD-9-CM diagnosis (inclusion and
  exclusion diagnoses) and age.

- Bugfix where reports would only be produced in HTML format.

- New CIS-R task.

Server v2.2.1, 2018-04-24 [in progress]

- Username added to login audit.

- SQLAlchemy `Engine` scope fixed (was per-request; that was wrong and caused
  ‘Too many connections’ errors; now per URL across the application, as it
  should be; see `cc_config.py`).
