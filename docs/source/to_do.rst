..  docs/source/misc/to_do.rst

..  Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).
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

**Regression to fix**

- Regression: crash in creating SVG figures from
  ``cardinal_expdetthreshold.py`` and ``cardinal_expectationdetection.py``. Not
  helped by matplotlib upgrade from 3.0.2 to 3.1.1. However, no problem with
  ``ace3.py``, which also uses ``fontdict``. The error is:

  .. code-block:: none

      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/offsetbox.py", line 808, in get_extent
        "lp", self._text._fontproperties, ismath=False)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/backends/backend_agg.py", line 210, in get_text_width_height_descent
        font = self._get_agg_font(prop)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/backends/backend_agg.py", line 245, in _get_agg_font
        fname = findfont(prop)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1238, in findfont
        rc_params)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1270, in _findfont_cached
        + self.score_size(prop.get_size(), font.size))
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1076, in score_family
        family1 = family1.lower()
    AttributeError: 'dict' object has no attribute 'lower'

  or

  .. code-block:: none

      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/backends/backend_svg.py", line 1180, in get_text_width_height_descent
        return self._text2path.get_text_width_height_descent(s, prop, ismath)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/textpath.py", line 89, in get_text_width_height_descent
        font = self._get_font(prop)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/textpath.py", line 38, in _get_font
        fname = font_manager.findfont(prop)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1238, in findfont
        rc_params)
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1270, in _findfont_cached
        + self.score_size(prop.get_size(), font.size))
      File "/home/rudolf/dev/venvs/camcops/lib/python3.6/site-packages/matplotlib/font_manager.py", line 1076, in score_family
        family1 = family1.lower()
    AttributeError: 'dict' object has no attribute 'lower'


  Is also not specific to SVG, as it still happens (and the ACE-III is still
  OK) when setting ``USE_SVG_IN_HTML = False``.

  Not affecting self-testing (which probably skips those figures for a blank
  task).


**Priority: IAM**

- :ref:`Lynall M-E — 2 — IAM study — life events <lynall_2_iam_life>`

  .. todo:: IN PROGRESS +++ a/w permission clarification

- :ref:`Childhood Trauma Questionnaire, Short Form (CTQ-SF) <ctqsf>`

  .. todo:: IN PROGRESS +++ a/w permission clarification


**Priority: MOJO**

- :ref:`Khandaker GM — 2 — MOJO study <khandaker_2_mojo>`


**To be prioritized**

- Test Your Memory (TYM) task (Jerry M. Brown).
- Continuous performance task, as per RNC's similar previous task (Linda P
  and team). A/w ETB.


**Then**

- Lewy body dementia checklist -- need details from JO'B, as per 14 Jan 2018
  meeting.


**Not a priority**

- Cardinal_ExpDet* tasks: generate noise on the fly?

- PDSQ screener (see Clark talk 2018-09-20, MQ Data Science)


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

- Create 64-bit ARM build, then release to Google Play Store (deadline 1 Aug
  2019). Work in progress: ``build_qt.py --build_android_arm_v8_64``.

- Have facility to upload and/or automatically feed patient details into the
  server, then have clients restrict to these predefined patients. Since we are
  aiming to minimize PID on the client, this could be implemented by having the
  client validate its patients with the server, and refusing to upload if they
  don't match. This would be a per-group setting.

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

- Consider a “chain of tasks” concept again (see e.g. ResearchMenu.js;
  MenuTableRow.js; QuestionnaireHeader.js...)... or is that pointless relative
  to a “set of tasks” concept?

- Test task upload (and date filtering) under Windows/SQL Server.

**Medium priority**

- iOS build.

- Apple App Store.

**Not a priority**

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


Server
------

- **Re possibility of duplication ?due to network dropout:**

  - **Facility to delete individual tasks from the server**, via
    a safety check form and then
    :meth:`camcops_server.cc_modules.cc_task.Task.delete_entirely`.

  .. code-block:: none

    There is not a specific "delete task" function that's accessible to users.
    Duplicates sounded concerning but we can think this through. On the client:

        everything begins with NetworkManager::upload() and chugs through a
        series of steps via ::uploadNext() (e.g. checking the server knows
        about our device)

        If we're using one-step upload, then we end up at
        NetworkManager::uploadOneStep(), followed by NextUploadStage::Finished
        (which wipes local data) -- so if the upload succeeds, data is wiped,
        and if it doesn't, it's not. It is probably possible that if the server
        accepts the upload data (writing it to its database) but then the
        connection is dropped before the server can say "OK, received", that
        the client will not delete the data, leading to duplication. I presume
        that is what's happened. (Definitely better than the other option of
        deleting from the client without confirmation, though!)

        In a multi-step upload, there is a multi-stage conversation which ends
        up with the client say "OK, commit my changes", via ::endUpload(), and
        the server saying "OK". I imagine that a connection failure during that
        last phase might lead to the server saving/committing but the "done"
        message not getting back to the client. This is probably less likely
        than with the one-step upload, because it's a very brief process.

    What sort of failure messages were you seeing? Was it all explicable by
    dodgy wi-fi?

    If this looks the likely cause -- we should implement a privileged
    operation (with deliberately difficult validation steps as for some of the
    other unsafe operations) to call Task.delete_entirely(), which does the
    business. (At present that is only called when an entire patient is
    deleted.) I think that will be OK because I think there is very little
    chance of any "partial" uploads; the system should prevent those
    effectively.

    I think that sounds safer than any of the alternatives.

    Likewise, if this is the probable root cause, perhaps we should add a
    warning (+/- change the default upload method) to say that "if you have a
    dodgy network connection, the chance of duplicates is probably lower with
    the multi-step upload".


**Reports for perinatal**

- APEQ_CPFT_Perinatal reports:

  - summary of question and %people responding each possibility
  - plus "summary of comments"

- POEM: as per APEQ_CPFT_Perinatal

- Core-10 report:

  For those with >=2 scores, "start" mean and "finish" mean, where "start" is
  the first and "finish" is the latest.

- MAAS: as per Core-10, but also for subscales

- PBQ: as per Core-10, but also for subscales


**Priority**

- (SERVER + CLIENT) Concept of “tasks that need doing” in the context of a
  research study.

  - define patients on server (per group)

    - share main patient/patient_idnum tables

    - use the “server device” to create them, and always in era “NOW”

  - ScheduledTask -- "task needs doing"

    - patient (by ID number); group; task; due_from; due_by;
      skip_if_not_done_by; cancelled?

    - Example: "PHQ9 due for Mr X after 1 July; due by 7 July; must be
      completed by 1 Aug"

  - then for metacreation: “StudySchedule” or “TaskPanel”

    - ... a list of tasks, each with: task; due_from_relative_to_start_date;
      due_by_relative_to_start_date

    - example: “In our study, we want a PHQ9 and GAD7 at the start, a PHQ9 at
      3 months, and a PHQ9 and GAD7 at 6 months.”

  - PatientSchedule

    - instantiate a “StudySchedule”/“TaskPanel” with patient, group, start date

    - e.g. “Mr Jones starts today.... enrol!”

  - ALTERNATIVELY: do we need ScheduledTask if the main thing is a person/panel
    association?

  - Tablets should fetch “what needs doing” for any patients defined on the
    tablet, and display them nicely.
  - Tasks must be complete to satisfy the requirement.

  - Database field type: represent :class:`pendulum.Duration` in ISO-8601
    format, which is ``P[n]Y[n]M[n]DT[n]H[n]M[n]S``. The
    ``pendulum.Duration.min`` and ``pendulum.Duration.max`` values are
    ``Duration(weeks=-142857142, days=-5)`` and ``Duration(weeks=142857142,
    days=6)`` respectively. A possible database output standard is
    ``PT[x.y]S``, with floating-point seconds; this maps from the
    :func:`pendulum.Duration.total_seconds` function.

    - See new functions :func:`cardinal_pythonlib.datetimefunc.duration_to_iso`
      and :func:`cardinal_pythonlib.datetimefunc.duration_from_iso`.

    - New column type
      :class:`camcops_server.cc_modules.cc_sqla_coltypes.PendulumDurationAsIsoTextColType`.

- … Relating to that: consider, on the client, a “single-patient” mode
  (distinct from the current “researcher” mode), tied to a specific server.
  “This tablet client is attached to a specific patient and will operate in a
  patient-friendly, single-patient mode. Show me what needs completing.” The
  operating concept would be: if you would like someone geographically far away
  to be able to download CamCOPS and complete a set of tasks for you, how could
  you organize so that would be simplest for them? The minimum would that you’d
  create login details for them, and give them a URL, username, and password.

- What's the optimal packaging method for the server? Is it DEB/RPM for Linux,
  and PyInstaller + Inno Setup (or just Inno Setup) for Windows?

**Not a priority**

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

- FHIR support via ``fhirclient``.

  - https://en.wikipedia.org/wiki/Fast_Healthcare_Interoperability_Resources
  - https://www.hl7.org/fhir/overview.html
  - CamCOPS will be a FHIR server, not a client.

- More generic e-mails to administrators, via backend task. (E-mail framework
  now in place.)

- Move research export dumps to backend (via e-mail)? However, note that e-mail
  brings size limits (sometimes severe, for people with poor e-mail servers).


Documentation
-------------

- Finish manual esp. web site user guide.


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
