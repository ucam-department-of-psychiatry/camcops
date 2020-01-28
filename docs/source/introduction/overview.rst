..  docs/source/overview/overview.rst

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


Overview
========

**Summary**

CamCOPS is:

- an application that runs on tablet devices including **iPads, Android
  tablets, and desktop computers (Linux, Windows, iOS)**.

- It offers many well-known questionnaires and more advanced tests relevant to
  **cognitive and psychiatric assessment**.

- It is intended for clinical research by qualified professionals.

- It offers structured and unstructured **clinical record-keeping** facilities.

- It operates **offline**, so it can be used in places with no network
  reception.

- It is compatible with UK NHS information security standards (though security
  is multifaceted and you will need to do extra things to meet these security
  requirements).

- It periodically sends its data to a server of yours, which you control.

- The server offers a web ‘front end’ (including printable task summaries,
  quantitative tracking information, and clinical summary views), a relational
  database ‘back end’ for powerful statistical analysis, and automatic export
  facilities including HL7- and file-based export of structured data or PDFs.

Additionally,

- it’s open-source, so you can download and modify the source code. If you’re
  a programmer, it’s very easy to add your own tasks.

Internally,

- the client app is written using C++ using Qt, an open-source cross-platform
  framework.

- The server is written in Python and will run on any suitably configured web
  server.

**Features for patients**

- Enter information electronically in a convenient format on a mobile or
  desktop device.

- See automatically calculated summary information.

**Features for clinicians**

- Enter information electronically in a convenient format on a mobile or
  desktop device.

- Lock a device so one patient can't see another's information.

- Have summary scores automatically calculated for you.

- Upload data to your institution when you have a network connection.

- Find and view tasks on the CamCOPS server.

- View tasks in a quick HTML format, or a printable PDF format.

- Track numerical changes graphically over time.

- View quick "clinical text view" summaries of pertinent information.

**Features for researchers**

- As for clinicians above.

- View tasks with automatically calculated summary information.

- Download detailed structured information in spreadsheet or database format.

- View and download reports, including patient-finding queries.

- A description of the database structure is built into the database itself
  (visible via XML or SQL comments).

**Features for system administrators**

- Group security and group administrators.

  - Create groups.
  - Define a group's preferred ID policy. (Fully identifiable for clinical use?
    Pseudonymised for a research study?)
  - Allow users to see groups, or groups to see other groups.
  - Create group administrators to manage groups independently.

- Export facilities

  - Export via files, e-mails, HL7.
  - Export tasks as PDF, HTML, XML, or as a database.
  - For database export, add summary information or denormalize for subsequent
    anonymisation.
  - Define export recipients: what's exported (e.g. by group, creation date),
    what task format you prefer, how the export should proceed. For a given
    export recipient, exports are typically incremental (i.e. only new stuff is
    sent).
  - Metadata support for Servelec's RiO.
  - Export manually, or via a schedule (either via the operating system, e.g.
    via `crontab`, or via CamCOPS's own scheduler).
  - "Push" export: when a task is uploaded, it's exported.

- Detailed audit trails.

- Coding via SNOMED-CT.
