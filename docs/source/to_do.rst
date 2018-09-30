..  docs/source/misc/to_do.rst

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

Things to do
============

Client
------

Tasks
~~~~~

- Cardinal_ExpDet* tasks: generate noise on the fly?

- PDSQ screener (see Clark talk 2018-09-20, MQ Data Science)

Client core
~~~~~~~~~~~

- iOS build.

- Apple App Store.

- OS/X build.

- Consider a “chain of tasks” concept again (see e.g. ResearchMenu.js;
  MenuTableRow.js; QuestionnaireHeader.js...)... or is that pointless relative
  to a “set of tasks” concept?

- Desktop-style menu for desktop clients. (Faster to navigate around.)

- Search for ``“// ***”``

- Think about a web-based client, e.g. via VNC (but this is complex and loads
  servers/networks considerably). Potentially more promising is Qt for
  WebAssembly (in preview May 2018), which compiles to a variety of portable
  quasi-assembly language; the browser downloads and runs it. However, at
  present there is no threading or DNS lookup
  (http://blog.qt.io/blog/2018/05/22/qt-for-webassembly/).

- Validator options, e.g. the server says "ID type 72 uses the 'NHS number'
  validator", so checksums are checked. An NHS number validator is built.

  - needs ?text field addition to the ID number descriptor table (client +
    server), e.g. "nhs" for NHS number validator; only needs to be one option;
    default NULL or blank
  - (client + server) ID numbers should provide info as to whether they
    pass their validator?
  - plus changes to download code, maintaining backward compatibility
  - plus changes to (client) patient editor, using the NHS number validator
    if the validator is "NHS", etc.
  - on the server, HTML task view showing a warning if an ID number fails
    its validator?

- Current Android back button behaviour may not be optimal.

- Maybe implement pinch zoom for some subclasses of OpenableWidget, e.g.
  MenuWindow and Questionaire. See
  http://doc.qt.io/qt-5/qtwidgets-gestures-imagegestures-example.html

- QuAudioRecording: questionnaire element to record audio

- QuVideoRecording: questionnaire element to record video

- Qt have fixed bug https://bugreports.qt.io/browse/QTBUG-35545 as of Qt
  5.12.0 beta 1, so may be possible to improve dialogue boxes again on Android
  (but possibly our workaround sorted it; can't remember); check.

Server
------

- Superuser facility to list all users' e-mail addresses or provide ``mailto:``
  URL.

- Search for all ``‘***’`` and fix.

- Implement (from command line) “export to anonymisation staging database” =
  with patient info per table. (Extend cc_dump.)

- Test the HL7 backend. Think re HL7 implementation carefully; see
  hl7_design.txt. Also: ensure we can efficiently distinguish between
  “previously sent” and “needs to be sent” in the context of re-sending stuff
  that changes in important ways (if we continue to allow this).

- Ensure that the “system user” and “server device” are used everywhere they
  should be.

- Finish manual.

- Test SQL Server support. (Main work was the implementation of the ISO-8601
  field, 2018-05-22; the rest should be automatic.) Document that the minimum
  SQL Server version is 2008 (below that, there’s no time zone conversion
  support).

- (SERVER + CLIENT) Concept of “tasks that need doing” in the context of a
  research study.

  - define patients on server (per group)

    - share main patient/patient_idnum tables

    - use the “server device” to create them, and always in era “NOW”

  - ScheduledTask -- "task needs doing"

    - patient (by ID number); group; task; due_from; due_by; cancelled?

    - Example: "PHQ9 due for Mr X on 1 July; must be completed by 1 Aug"

  - then for metacreation: “StudySchedule” or “TaskPanel”

    - ... a list of tasks, each with: task; due_from_relative_to_start_date;
      due_by_relative_to_start_date

    - example: “In our study, we want a PHQ9 and GAD7 at the start, a PHQ9 at
      3 months, and a PHQ9 and GAD7 at 6 months.”

  - PatientSchedule

    - instantiate a “StudySchedule”/“TaskPanel” with patient, group, start date

    - e.g. “Mr Jones starts today.... enrol!”

  - Tablets should fetch “what needs doing” for any patients defined on the
     tablet, and display them nicely.
  - Tasks must be complete to satisfy the requirement.

- … Relating to that: consider, on the client, a “single-patient” mode
  (distinct from the current “researcher” mode), tied to a specific server.
  “This tablet client is attached to a specific patient and will operate in a
  patient-friendly, single-patient mode. Show me what needs completing.” The
  operating concept would be: if you would like someone geographically far away
  to be able to download CamCOPS and complete a set of tasks for you, how could
  you organize so that would be simplest for them? The minimum would that you’d
  create login details for them, and give them a URL, username, and password.

- Rename server master tool from camcops to camcops_server. Rename package,
  too. This is so we can use "camcops" for the client (on the basis that the
  client should be the simplest for users).

- What's the optimal packaging method for the server? Is it DEB/RPM for Linux,
  and PyInstaller + Inno Setup (or just Inno Setup) for Windows?

- fix problem with CherryPy

Documentation to-do list
------------------------

- Notes to readthedocs.org (when "source" links are working properly?).

- Consider autodocumentation for C++ code; see
  https://stackoverflow.com/questions/11246637/using-sphinx-apidoc-to-generate-documentation-from-c-code

.. todolist::
