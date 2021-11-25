..  docs/source/misc/to_do.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
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

..  contents::
    :local:
    :depth: 3


Tasks
-----

- Bugfix: answer column in CISR main data table is double-escaping
  HTML, e.g. "I don&#x27;t enjoy anything".

- CISR: document current version (2013?) and examine changes required
  for 2020 version (very minor?) -- think about how best to handle this.

**Priority: IAM**

- :ref:`Childhood Trauma Questionnaire, Short Form (CTQ-SF) <ctqsf>`

  .. todo:: IN PROGRESS +++ a/w funding before proceeding


**To be prioritized**

- Mini-ACE (mACE).
- Free-Cog: https://pubmed.ncbi.nlm.nih.gov/33124050/
- Test Your Memory (TYM) task (Jerry M. Brown).
- Continuous performance task, as per RNC's similar previous task (Linda P
  and team). A/w ETB.


**Then**

- Lewy body dementia checklist -- need details from JO'B, as per 14 Jan 2018
  meeting.

- WHODAS 2.0 (12-item)
- RCADS-25
- Menu: Common Measures for Collecting Mental Health Data
  = WHODAS 2.0 (12-item), PHQ-9, GAD-7, RCADS-25
  as per https://wellcome.org/sites/default/files/CMB-and-CMA-July-2020-pdf.pdf

**Not a priority**

- Cardinal_ExpDet* tasks: generate noise on the fly?

- PDSQ screener (see Clark talk 2018-09-20, MQ Data Science)

- For computational fitting work, see https://lbfgspp.statr.me/


**Consider**

- review Guo 2015 "measurement-based care":

  - HADS/HDRS already
  - QIDS -- permissible?
  - Maudsley Treatment Inventory?
  - see notes on Cleare lecture 15/11/2018

- new task: ReQoL (https://www.reqol.org.uk/p/overview.html)
- new task: mini-ACE (subset of the ACE-III)
- new task: Andy Foster / eating disorders; e-mail of 24/5/16
- new task: AQ10 autistic spectrum screening
- discarded tasks - revitalize: ASRM
- discarded tasks - revitalize: BARS
- discarded tasks - revitalize: BFCRS
- discarded tasks - revitalize: CSI
- discarded tasks - revitalize: FAB
- discarded tasks - revitalize: GASS
- discarded tasks - revitalize: LSHSA
- discarded tasks - revitalize: LSHSLAROI2005
- discarded tasks - revitalize: LUNSERS
- discarded tasks - revitalize: MADRS
- discarded tasks - revitalize: SAS


Client core
-----------

**Priority**

- Test task upload (and date filtering) under Windows/SQL Server.

**Medium priority**

- Have facility to upload and/or automatically feed patient details into the
  server, then have clients restrict to these predefined patients. Since we are
  aiming to minimize PID on the client, this could be implemented by having the
  client validate its patients with the server, and refusing to upload if they
  don't match (**done**). This would be a per-group setting.

  - Client validation check implemented.
  - Just needs server-side extensions to
    :func:`camcops_server.cc_modules.cc_patient.is_candidate_patient_valid`,
    including a per-group setting for "should we validate", and a way of
    getting suitable data in.
  - Note that any patient unification should be external to CamCOPS (i.e.
    addressing the question of "are these two patients the same person").
  - Maybe implement as (1) a ``_known_patients`` table and (2) a
    ``_known_patient_idnums`` table?
  - Needs slightly more thought about what constitutes a "match" given a
    variable set of input and a variable set of known information.
    (Could have an ID policy for the known information too...)
  - Should "known" patients be across groups, or per-group?

**Not a priority**

- If user registration fails, automatically offer a "try again" option (in
  ``CamcopsApp::patientRegistrationFailed()``)?

- MacOS build.

- Think about a web-based client, e.g. via VNC (but this is complex and loads
  servers/networks considerably). Potentially more promising is Qt for
  WebAssembly (in preview May 2018), which compiles to a variety of portable
  quasi-assembly language; the browser downloads and runs it. However, at
  present there is no threading or DNS lookup
  (http://blog.qt.io/blog/2018/05/22/qt-for-webassembly/).

- Desktop-style menu for desktop clients. (Faster to navigate around.)

- Current Android back button behaviour may not be optimal.

- Maybe implement pinch zoom for some subclasses of OpenableWidget, e.g.
  MenuWindow and Questionaire. See
  http://doc.qt.io/qt-5/qtwidgets-gestures-imagegestures-example.html

- QuAudioRecording: questionnaire element to record audio

- QuVideoRecording: questionnaire element to record video

- Qt have fixed bug https://bugreports.qt.io/browse/QTBUG-35545 as of Qt
  5.12.0 beta 1, so may be possible to improve dialogue boxes again on Android
  (but possibly our workaround sorted it; can't remember); check.

- Via ``tablet_qt/tools/build_qt.py``, also build iOS "fat binary" with 32- and
  64-bit versions?


Server
------

**Priority**

- What's the optimal packaging method for the server? Is it DEB/RPM for Linux,
  and PyInstaller + Inno Setup (or just Inno Setup) for Windows?

- Improve installation ease and docs.

**Medium**

- At present the client calls ``op_validate_patients`` prior to an upload. This
  eliminates all realistic possibilities of uploading patient details not
  permitted to that user. However, it doesn't prevent the theoretical
  possibility of someone (a) obtaining a legitimate single-user account, (b)
  cracking its password, and (c) using a hacked version of the CamCOPS client
  to upload new "false" patient data from that user (into the group to which
  they are legitimately allowed to upload their own data). It'd be pretty
  traceable, and would not damage other data (just add potentially spurious
  data), but not theoretically impossible. The fix would be to have the server
  verify this too. (Slightly tricky as it involves validating not just the easy
  one-step JSON upload but also the table-by-table version, which requires
  tying patient records to ID numbers).

**Not a priority**

- Consider: see ``DEBUG_TEMPLATE_SOURCE`` -- would it improve performance to
  have a Mako template cache directory always set, via the config file? (There
  is still memory caching at present.)

- Fix Alembic migration autogeneration -- too much non-change junk.

- Tracker improvements.

  - In
    :meth:`camcops_server.cc_modules.cc_tracker.Tracker.get_all_plots_for_one_task_html`,
    consider improvements to allow tracker information to be associated with
    a user-specified date (see e.g. GBO), rather than the creation time (with
    fallback to the creation time if not specified).

  - Consider cross-task trackers, e.g. GBO-GPC and GBO-GRaS both contributing
    to a "goal 1 progress" tracker. Simplest way might be to collect specimen
    and x/y information from all tasks, keyed by tracker name, with some
    defaults for existing trackers?

- Implement (from command line) “export to anonymisation staging database” =
  with patient info per table. (Extend ``cc_dump.py``. See
  ``generate_anonymisation_staging_db()``, and it's also temporarily disabled
  in the master command-line handler.) Framework very partly done; search for
  ``db_patient_id_per_row``.

  - Best to implement by fixed column names for all ID numbers, e.g.
    ``_patient_idnum1``, ``_patient_idnum17``, etc.? NULL if absent.

- More generic e-mails to administrators, via backend task. (E-mail framework
  now in place.)

- There are still some of the more complex Deform widgets that aren't properly
  translated on a per-request basis, such as

  - TranslatableOptionalPendulumNode
  - TranslatableDateTimeSelectorNode
  - CheckedPasswordWidget

- When Deform bug https://github.com/Pylons/deform/issues/347 is fixed, turn
  off ``DEFORM_ACCORDION_BUG`` (in ``cc_forms.py``) to auto-hide advanced
  JSON task schedule settings by default.


Documentation
-------------

- Finish manual esp. web site user guide.


Developer convenience
---------------------


Wishlist and blue-sky thoughts
------------------------------

**Server-side “all tasks in full” view, like a clinical text view but for researchers?**

A “research multi-task view” would be an easy extension to the task collection
classes used for trackers and CTVs, if there is demand.

**Improvements to “camcops merge_db” facility**

The merge facility doesn’t yet allow you to say “ID#8 in database A means
something different to ID#8 in database B; don’t merge that”. Should it?
(Example: “research ID” that is group-specific, versus “NHS number” that
isn’t.) More generally: should some ID numbers be visible only to certain
groups?

**Server-side ability to edit existing (finalized) task instances?**

Would be done in a generic way, i.e. offer table with {fieldname, comment, old
value, new value}; constrain to min/max or permitted values where applicable;
at first “submit”, show differences and ask for confirmation; audit changes.
For BLOBs, allow option to upload file (or leave unchanged).

**Client-side index of tasks by patient ID, to speed up lookup on the tablet?**

Might be worthwhile on the client side as the number of tasks grows. (The
server already has indexing by patient ID.)

**MRI triggering on task side**

For example: CamCOPS tasks running on a desktop and communicating via TCP/IP
with a tool that talks to an MRI scanner for pulse synchronization and
response.


Considered but rejected
-----------------------

- Client-side task index, to speed up the client's patient summary view. (This
  is not a performance problem!)

- Tasks record the language operational on the client at the moment of their
  creation. (Would need the client to remove this field for older server
  versions at the moment of upload.) A reason not to: users can switch language
  mid-way, and we're not going to track all those potential changes.


Documentation to-do list
------------------------

Things to do collected from elsewhere in this documentation:

.. todolist::
