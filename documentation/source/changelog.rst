..  documentation/source/changelog.rst

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

Change log/history
==================

*Both client and server changes are described here.*

Quick links:

- :ref:`2013 <changelog_2013>`
- :ref:`2014 <changelog_2014>`
- :ref:`2015 <changelog_2015>`
- :ref:`2016 <changelog_2016>`
- :ref:`2017 <changelog_2017>`
- :ref:`2018 <changelog_2018>`

Original Titanium/Javascript client, Python server with custom MySQL interface (defunct)
----------------------------------------------------------------------------------------

.. _changelog_2013:

2013
~~~~

**Server v1.0, 2013-08-14**

- First version (1.0).

**Client v1.0, 2013-11-13**

- first version
- requires server version 1.0

**Client v1.01, 2013-11-13**

- test of version number increment
- Bugfix: Executive menu had a duff entry in and crashed.

**Server v1.01, 2013-11-20**

- Test of version number increment (1.01).
- Trivial change: ensure empty "\*_SUMMARY_TEMP_current\*" views
  aren't created for anonymous tasks.

**Client 1.02, 2013-11-22 onwards**

- A couple of cosmetic changes.
- Analytics yes/no option.
- Changed app "domain" to org.camcops.\*, so app is org.camcops.camcops
- Signed APK file.
- QuestionTypedVariables improved in a few respects.
- QuestionDiagnosticCode bugfix (didn't appear read-only in read-only mode).
- android:allowBackup explicitly set to false
- ID description/policy check on upload.
- Titanium API now 3.2.0.GA
- Page jump in questionnaires when read-only.
- Two CECAQ3 fields used the wrong keyboard/type.
- Text field/cursor colours improved for iOS/Android.
- Bugfix to QuestionCanvas_webview.

**Server v1.02, 2013-11-28**

- Mostly changes on the app side (q.v.).
- Change to DemoQuestionnaire fields.
- DOB task filter.
- Server analytics with yes/no option.
- Fixed layout on old versions of Internet Explorer.
- get_id_info command in the database interface.
- QoL\* tasks remain in beta; data structure may change.
- Changes for CentOS, including Python version check and altered shebang.
  Using "#!/usr/bin/env python2.7" is perhaps desirable, but Lintian requires
  e.g. "#!/usr/bin/python2.7":
  http://lintian.debian.org/tags/python-script-but-no-python-dep.html
- Clinical text view.

.. _changelog_2014:

2014
~~~~

**Client v1.03, 2014-01-10**

- Requires server version 1.03.
- Fixed Titanium 3.2.0 multiline TextArea regression.
- CGI-SCH task, pending permissions.
- androidtipaint/QuestionCanvas_tipaint improved/fixed for Titanium 3.2.0.
- Questionnaire scrollview made full height (Titanium now capable of it).
- Single-tap/double-tap methods in diagnostic coding, now Titanium bug
  https://jira.appcelerator.org/browse/TIMOB-15540 fixed.
- Photo rotation bug fixed.
- ListView for diagnostic code search.
- QoL-SG phrasing improved.
- Tested on iOS 7.0.3/7.0.4, Android 4.1.1.

**Server v1.03, 2014-01-10**

- CGI-SCH task.

**Client v1.04, 2014-01-14**

- First beta version.
- Bugfix to Patient.js (re address display crash).
- Changes to SetMenu_Deakin_1.js
- Confirmation of CGI-SCH permissions.

**Client v1.05, 2014-01-14**

- Password entry windows improved: return key now accepts data entry.

**Client v1.06, 2014-01-16**

- Requires server version 1.06.
- CPFT_LPS_Referral, CPFT_LPS_Discharge, CPFT_LPS_ResetStartClock tasks.
  This are IN BETA.
- Batch upload empty tables for speed (big improvement).
- NULL-but-optional indicator in widgets:

  - QuestionDateTime, QuestionPickerInline, QuestionPickerPopup,
    QuestionSlider, ImageGroupVertical.

- offerNullButton option in QuestionDateTime, QuestionDiagnosticCode
- Variable column widths in ContainerTable, plus populateVertically option.
- Bugfix in QuestionTypedVariables layout for colWidthPrompt.
- (2014-01-18) Minor layour change in CPFT_LPS_Referral.

**Server v1.06, 2014-01-16**

- REQUIRES DATABASE CHANGE BEFORE INSTALLATION: 
  DROP TABLE _dirty_tables;
- CPFT_LPS_Referral, CPFT_LPS_Discharge, CPFT_LPS_ResetStartClock tasks.
  IN BETA; MAY CHANGE.
- QoL\* tasks remain in beta; data structure may change.
- Options in man page.
- cc_patient.py / get_id_generic and similar: bugfix to use Unicode
- Clinical text provided by Photo/PhotoSequence.
- Batch upload empty tables.
- rnc_db: skips creation of tables that exist already (removes a warning).
- Joint PK for _dirty_tables, and change from TEXT to VARCHAR(255)
  for the tablenamefield.
- Bugfix to database.pl / flag_deleted_where_clientpk_not: wasn't
  device-specific! Was used by blob upload on the tablet, i.e.
  dbupload.sendTableRecordwise()

**Server v1.07, 2014-02-14**

- REQUIRES DATABASE CHANGE BEFORE INSTALLATION: 
  DROP TABLE _security_webviewer_sessions;
- CPFT\* tasks remain in beta; data structure may change.
- QoL\* tasks remain in beta; data structure may change.
- Additional content for clinical text views.
- Python virtualenv.
- Dumping/reporting options for suitably privileged users.
  Additional user permissions: may_dump_data, may_run_reports.
- Bugfix to Session class to prevent the (incredibly unlikely)
  event of an IP address hop with an identical session token.
- Security improvement to Session class: change token upon login.
- Speedup to Session design (inc. integer PK).
- Typo in CAPS text, Q24.
- Speedup to LSTRING XML processor.
- Speedup via transaction-based database handling in the Python handler.
- Redirect to destination URL after re-authentication.

**Server v1.08, 2014-07-22**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE: 
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- Automatic version-based database structure upgrade via the --maketables
  command. (Similarly on the tablet side.)
- Distinct patient reports.
- CPFT\* tasks remain in beta; data structure may change.
- QoL\* tasks remain in beta; data structure may change.
- Remote IP addresses stored in audit log (additional field: remote_addr).
- Auditing of clinical text views.
- Some string constant code cleanup.
- Some Perl code cleanup and upload audit simplification.
- perltidy for Perl code.
- Trackers/CTVs clearer in their errors when no data found.
- Ability to apply multiple filters simultaneously.
- Option to force password changes periodically/ad hoc.
- PEP8 compliance for core Python code.
- PEP8 compliance for task code.
- Proper multiple inheritance handling for diagnosis.py, pcl.py.
- Disclaimer/acknowledgement recording.
- Audit all login attempts, plus user addition/deletion.
- OptionParser to ArgumentParser.
- Internal URLs for tasks altered slightly.
- Better internal timezone handling.
- Commit during menu-driven administration to prevent database locking.
- Lock user accounts after multiple login failures.
- HL7 message framework. (Validated internally and against HL7 Inspector.)
- File export message framework, with post-export script option.
- Database title, ID descriptions, and policies now have their primary home
  in the configuration file. Copied to database purely for researcher lookup.
- File locking for the regeneration of summary tables.
- XML export (tasks, trackers, CTVs).
- Unit testing framework (and a couple of bugs fixed).
- Shift to unsigned ints for PKs.
- Option to introspect source code.
- Option to view table definitions from webview.
- Basic non-modifying anonymisation system.
- Bugfix: added vignette to ICD10-PD display.
- Bugfix: HAMD-7 maximum is 26, not 23.
- Bugfix: CECAQ3 failed to calculate some summary scores with no siblings,
  and paternal psychological abuse score was sometimes inappropriately blank.
- Bugfix: filter for incomplete tasks only wasn't working.
- Bugfix: logic bugfix in ICD-10 manic, mixed, schizophrenia.
- Bugfix: categorization text in BMI.
- Bugfix: clinical text for SLUMS reported incorrect maximum.
- BMI thresholds refined in the underweight zone and referenced properly.
- All field comments.
- Manual erasure of individual tasks.
- Manual deletion of entire patients/associated tasks.
- Manual application of special notes.
- CTV is clearer when tasks are incomplete.
- More consistent formatting of null values in HTML. (Note that the quick
  way to view null handling is to specify a nonexistent server PK.) The aim is
  that all user answers should be proceesed via the answer() function, to apply
  typographic indications that the field is null.
- camcopswebview.py renamed to camcops.py.
- Optimization on compile.
- Ensure commit/rollback always occurs, even after exceptions.
- "crash" action to induce a deliberate exception, for testing.
- Configurable save-as filenames for tasks, trackers, and CTVs.
- Server-side validation of fields (field_contents_valid).
- Unit tests prohibit tasks from having summary fields with the same name as
  a main task field.
- Option to disable password autocompletion on the login page.
- Server version number in "office" details.
- Generator function for task list.
- Drop-down lists for filters remember state.
- Basic research dump (likely to be the most useful in practice).

**Client v1.08, 2014-07-23**

- Requires server version 1.08.
- Field renaming within Icd10Schizophrenia to avoid misnomers:
  - tpah_commentary TO hv_commentary
  - tpah_discussing TO hv_discussing
  - tpah_from_body TO hv_from_body
- CPFT\* tasks remain in beta.
- Chaining of tasks.
- Page jump within live questionnaires (allowPageJumpDuringEditing).
- Radio buttons allow double-clicks/taps to unset them (particularly applicable
  for potentially loaded questions).
- Bugfix to HAMD-7: Q4 value 4 and Q5 values 3/4 were not offered, and maximum
  is 26, not 23.
- Bugfix to SLUMS: Q9a, Q9b were scored as 1 point each; should be 2.
- Bugfix calling bad afterwardsFunc() after "move" upload.
- BMI thresholds refined in the underweight zone and referenced properly.
- Textual annotation to ICD-10 F90.0, as the actual text gives you no clue that
  it's a division of hyperkinetic disorders.
- dbcore.js changed to reflect Titanium bugfix.
- Android theme changed to light (with consequent changes to questionnaire
  font size editing screen, etc.).

**Client v1.09, 2014-08-02**

- Requires server version 1.09.
- Sends BLOBs in ways that cannot be confused with (even very bizarre)
  strings.
- PANSS stripped down to data collection tool only, for copyright reasons.
- Not distributed yet.

**Server v1.09, 2014-08-02**

- REQUIRES TABLET CLIENT V1.09.
- Full rewrite of the database upload script to Python.
- Fix MySQL "morning bug" ("MySQL server has gone away") from the Perl upload
  script.
- Logic change to flag_all_records_deleted(), which was not restricted to
  _current/era='NOW' records, but should have been.
- Also rolls back preservation flag changes as part of general rollback.
- BLOB transfer encoding improved; fixes design flaw that was due to the use
  of the Perl CSV module. (Requires tablet client v1.09 as a result.)
- Internal code changes: explicit modules in all cases, removing
  cc_shared.py.
- PANSS stripped down to data collection tool only, for copyright reasons.

**Client v1.10, 2014-08-08**

- Default network timeout changed from 5 s (5000 ms) to 60 s (60000 ms), as
  shorter timeouts were causing large BLOB uploads to fail.
- Minor fix to newline decoding for the mobileweb client.
- Ability to null out dates of birth (for anonymised research use).
- NULL dates now show in the widget as 01 Jan 1900, not the current date (it's
  impossible to show an actual NULL, and the current date is confusing when you
  have neonates).
- QuestionDateTime widget wouldn't successfully NULL itself on Android. (So
  now it NULLs itself but doesn't update its pseudo-date; it just displays the
  NULL icon.)
- First jshint compliance (except for included third-party libraries)...
- ... then jslint compliance.
- Unit testing framework.
- Not distributed yet.

**Client v1.12, 2014-09-11**

- Renamed ExpDetThreshold/ExpectationDetection tasks (and tables) to add
  a "[C/c]ardinal_" prefix, as the names were too vague. THEREFORE requires
  server version 1.12 as well.
- Session-based authentication for tablets to improve speed (i.e. no need for
  bcrypt reauthentication within the same session, as for the web front end).
- Whisker interface.

**Client v1.14, 2014-10-15**

- Requires server version 1.14.
- Server can enforce a minimum tablet version, and tablet can specify a minimum
  server version. Version numbers are in common/VERSION.js for the tablet.
- Bugfix: tablet registration crashed if the Patient table hadn't been created.
  And similar subsequent bug when uploading with no tables.
- CAPE-42 task.

**Server v1.10, 2014-08-16**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- Database upload script could fail to insert but not complain to the tablet.
- Stopped database handler (rnc_db.py) masking any exceptions.
- Improved exception handling in database.py.
- Bug: patient table incorrectly had forename/surname/DOB fields as NOT NULL.
  Sex column also now has that constraint removed (enforced elsewhere but one
  could envisage not enforcing it).
- Tablet-side (webclient) minor fix to newline escaping.
- Removed Unicode from error messages in make_summary_tables(), since they
  also go to the Apache log.
- Bugfix: login failures were redirecting to the page for acknowledging terms
  and conditions. Bug was in login().
- Bugfix: effective deadlock between the process of a mandatory password
  change for new users and acknowledging terms/conditions.
- Make database/username more prominent (bold) in menus. Was easy to ignore.
- pyflakes compliance.

**Server v1.11, 2014-09-06**

- Future necessity to discriminate field types that all use VARCHAR; e.g.
  (and esp.) ISO-8601 dates versus others. So change sqltype to cctype
  internally; see cc_db.add_sqltype().
- Significant simplification of work done in tasks with ancillary tables.
  New cc_task.Ancillary class; q.v.
- Export to CRIS staging database and autocreate draft data dictionary.

**Server v1.12, 2014-09-11**

- REQUIRES TABLET CLIENT V1.12.
- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- Renamed ExpDetThreshold/ExpectationDetection tasks (and tables) to add
  a "[C/c]ardinal_" prefix, as the names were too vague. THEREFORE requires
  tablet version 1.12 as well.
- Session-based authentication for tablets to improve speed (i.e. no need for
  bcrypt reauthentication within the same session, as for the web front end).

**Server v1.13, 2014-10-02**

- Trivial code changes.

**Server v1.14, 2014-10-15**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- REQUIRES TABLET CLIENT V1.14.
- Server can enforce a minimum tablet version, and tablet can specify a
  minimum server version. Version numbers are in cc_version.py on the server.
- CAPE-42 task.

**Client v1.15, 2014-10-18**

- Requires server version 1.15.
- NHS numbers were being corrupted, i.e. very long (10-digit) numbers.
  - Critical error. Stored correctly in database.
  - SQLite maximum integer is 2^63 - 1 = 9,223,372,036,854,775,807.
  - Javascript safe max is 9,007,199,254,740,991.
  - A valid database was read incorrectly by dbsqlite.js / getAllRows().
  - Ah. Titanium bug: https://jira.appcelerator.org/browse/TIMOB-3050

  - Workaround is either
    (a) float, which won't be quoted by the SQLite quote() function, and
    which MySQL will happily accept (rounding); and all numbers are floats
    anyway in Javascript;
    or
    (b) text, with parseInt() when reading from SQLite to Javascript.
    This will send integer values quoted, but MySQL will convert even e.g.
    '9876543209.999' (with the quotes) to 9876543210 when inserted into a
    BIGINT field, so that's OK. The parseInt() function will truncate, which
    is also fine.
    I guess float is slightly more logical. Let's be quite clear: in
    Javascript, all numbers are floats; they are 64-bit floating point
    values, the largest safe exact integer is Number.MAX_SAFE_INTEGER, or
    9007199254740991.

  - So:

- QuestionTypedVariables applies +/- Number.MAX_SAFE_INTEGER when no other
  limits are specified (in getValidatedInt).
- No negative ID numbers (in Patient.js).
- Changed columnDefSQL() in dbsqlite.js to use REAL for
  DBCONSTANTS.TYPE_INTEGER and DBCONSTANTS.TYPE_BLOBID. No value conversion
  is required.
- Equivalent change in fieldTypeMatches().
- Removed AUTOINCREMENT tag from PKs (SQLite behaviour doesn't require this).
- Added changeColumnTypes() function.
- Database upgrade changes type of patient ID numbers in patient table.
- On the server (MySQL) side, the fields were
  - INT: -2,147,483,648 to 2,147,483,647 or 4,294,967,295 unsigned (4-byte)
  - and need to be

  - BIGINT: -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807
    or 18,446,744,073,709,551,615 unsigned (8-byte)

**Server v1.15, 2014-10-20**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- ID number fields become unsigned BIGINT, not unsigned INT.
  Fixes critical error (inability to represent NHS numbers.)
  See VERSION_TRACKER.txt for the tablet software.

**Client v1.16, 2014-10-26**

- Text-as-button widgets:
  - QuestionBooleanText / props.asTextButton
  - QuestionMultipleResponse / props.asTextButton
  - QuestionMCQ / props.asTextButton

- Reworking of corresponding underlying widget code.
- QuestionDateTime supports text entry (including by default).
- Updated moment.js to 2.8.3
- Minor other code changes and improvement of demo questionnaire.

**Server v1.17, 2014-11-12**

- HAM-D: complained inappropriately about '3' codes (meaning 'not measured')
  for weight questions; maximum score adjusted accordingly from 53 to 52;
  comment for Q16B was erroneously labelled Q16A.

**Client v1.17, 2014-11-13**

- HAM-D scoring was wrong for "weight - not measured" option. Fixed. Maximum
  changed from 53 to 52 accordingly.

**Client v1.2, 2014-11-27**

- Requires server version 1.2.
- WEMWBS/SWEMWBS scales.
- QuestionMCQGrid wasn't centring its buttons properly, because McqGroup wasn't
  copying its incoming tipropsArray through properly.
- Bugfix to webclient database handling, in:
  - dbwebclient.js / convertResponseToRecordList()
  - netcore.js / parseServerReply()
- Some improvements to MobileWeb, though Titanium bugs remain, e.g.:
  - https://jira.appcelerator.org/browse/TC-5065
  - https://jira.appcelerator.org/browse/TC-5071
- GAF: applies 0-100 input constraint.
- GAF: interprets raw score of zero as "unknown" for total-score purposes.

**Server v1.2, 2014-11-28**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- WEMWBS/SWEMWBS tasks.
- GAF: interprets raw score of zero as "unknown" for total-score purposes.
- CGI: requires full completion for a valid total score.
- BPRS total score was erroneously including Q19/Q20.
- Scoring clarity expanded (e.g. BPRS, BPRS-E, CGI).
- Exclude manually erased tasks from list (unless "include old versions" is
  selected). See
  - cc_task.get_session_candidate_task_pks_whencreated()
  - cc_task.get_all_current_pks()
- Bugfix to cc_task.make_extra_summary_tables().

**Server v1.21, 2014-12-04**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- Draft support for RiO metadata export (for RiO's batch document upload
  facility). Some information pending, e.g. whether UTF-8 is supported in
  metadata.

**Client v1.21, 2014-12-26**

- Fixes bug found in v1.17.
  Symptom: crash after adding new patient in some circumstances (?when ID check
  failed). Error of "'undefined' is not an object (evaluating
  'this.props.pages[this.currentPage].pageTag') at Questionnaire.js (line 1)"
  Added getPageTag() function to check for invalid index effects.
- Note in passing: to view iPad-based SQLite files, copy them elsewhere with
  e.g. http://www.macroplant.com/iexplorer/
- Curious crash on loading on an iPad whereas fine under the iOS simulator.
  Occurring in
  - dbinit.js
  - storedvars.databaseVersion.setValue(...)
  - this.dbstore()
  - dbcommon.storeRow()
  - dbsqlite.updateByPK()
  - dbsqlite.getFieldValueArgs()
  Segmentation fault (view console with Xcore > Window > Devices > click the
  tiny up-arrow at the bottom left of the right-hand pane for the device).
  Titanium SDK: 3.5.0.Alpha
  http://builds.appcelerator.com.s3.amazonaws.com/index.html
  ... upgraded to 3.5.0.RC (install SDK + change tiapp.xml)
  ... fixed. So a Titanium bug.

.. _changelog_2015:

2015
~~~~

**Server v1.22, 2015-01-07**

- Improved audit search.

**Client v1.30, 2015-01-30**

- Requires server version 1.3.
- IDED3D task.
- Bug related to serialization of moment() objects from webviews.
  Probably introduced in v1.16.
  The moment.js library now includes a moment.toJSON() function, which
  overrides custom work in my json_encoder_replacer() function. However,
  moment.js's version loses information (specifically, time zone, not to
  mention that it's hard as the recipient to detect whether the object should
  be reconverted to a moment() object.) Therefore:
  preprocess_moments_for_json_stringify()
  ... in conversion.js and taskhtmlcommon.jsx.
- Alerts with large content no longer scroll under iOS 8.
  Apparently this is an Apple bug:
  https://jira.appcelerator.org/browse/TIMOB-17745
- Raphael.js upgraded from 2.1.0 to 2.1.3.
- Bugfix: if endUpload() failed, the failure wasn't processed properly.

**Server v1.30, 2015-01-30**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- IDED3D task.
- Cardinal_ExpectationDetection and Cardinal_ExpDetThreshold: ISO-8601 fields
  changed from TEXT to (internal) ISO8601 (i.e. SQL VARCHAR).
- Prohibit manual erasure of non-finalized (live-on-tablet) tasks (for one
  thing, the tablet might re-upload and surprise the erasing user).
- Manually erased records become non-current.
- Fix latent bug by finalizing special notes along with their tasks.
- Forcible finalization/preservation, with _forcibly_preserved flag.
- Option to drop superfluous columns when remaking tables.
- Bugfix: other filters failed if non-current tasks shown
  (get_session_candidate_task_pks_whencreated).

**Client v1.31, 2015-02-10**

- Requires server version 1.31.
- dbsqlite.renameColumns() and dbsqlite.changeColumnTypes() fail more politely
  with non-existing columns (remember that not all tables may exist, even if
  the app has been launched before, so don't throw an error).
- IDED3D: Minor config text bugfix.
- IDED3D: Save stimulus shapes to database as SVG.
- IDED3D: Occasional missing sounds.
  Reaches "playsound: filename =" message.
  I suspect this is a Titanium bug, but am not certain.
- IDED3D: Correct/incorrect sounds changed to more distinctive chords with
  more similar subjective volumes.
- IDED3D: Change colours for the colour-blind? A/w Annette.

**Server v1.31, 2015-02-10**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- IDED3D task: extra field to store shapes (ided3d.shape_definitions_svg).
- Patient deletion reports tasks that will be deleted.
- Ability to edit patient details, for finalized records.
- HL7 resending triggered by cancelling, not deleting, existing messages
  (in cc_task.Task.delete_from_hl7_message_log(), etc.)

**Server v1.32, 2015-02-15**

- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- Enforces sensible MySQL engine settings.
- Switches tables to Barracuda format to avoid uploading bug when rows too
  large.

**Server v1.33, 2015-02-19**

- Tweaks to RiO metadata export, based on feedback from Servelec.

**Server v1.34, 2015-03-01**

- Long text (e.g. ProgressNote) crashed PDF generator when in a table.
  Tasks prone to this (ProgressNote, PsychiatricClerking) reworked to avoid
  tables.
- Bug in RecipientDefinition.report_error() fixed.

**Client v1.32, 2015-03-10 to 2015-04-22**

- setRemoteBackup(false) call, to disable back to Apple iCloud; see dbinit.js
- Intermittent crash on Android 4.4.4 (build 23.0.1.A.4.30).
  Relates to database access?

  - Always create all tables at task start. (A crash due to a missing table was
    still possible, and the kind of thing it's easy to miss on a development
    machine that tends to have everything precreated. Mind you, not sure that
    was the actual bug; see next point.) See ensure_database_ok().
  - Explicitly close all recordsets (cursors) opened on all db.execute()
    operations.
  - Did not relate to database access in 10k soak test, and crash occurred
    outside updateByPK function. Maybe relating to visual display. Key error:

    - E/BufferQueue(  292): [org.camcops.camcops/org.appcelerator.titanium.TiActivity] dequeueBuffer: can't dequeue multiple buffers without setting the buffer count

  - This? https://code.google.com/p/android/issues/detail?id=63738
    Android source is:
    https://android.googlesource.com/platform/frameworks/native/+/jb-dev/libs/gui/BufferQueue.cpp
    But crash also occurred inside updateByPK function (unless from a different
    thread).

  - No... relates to setBackgroundImage() calls.
    - https://jira.appcelerator.org/browse/TC-5369
  - Attempt at change:

    - Get rid of all setBackgroundImage() calls for situations calling for
      multiple alternative images (e.g. radio buttons). Also
      setBackgroundSelectedImage().
    - Replace with method of loading all alternative images at the start, and
      using hide()/show() calls.
    - Affects ValidityIndicator; StateRadio; StateCheck.
    - setImage() calls also removed from ImageGroupVertical.
    - Residual setImage() calls, which may also be suspect if the Android file
      system is duff:

      - QuestionCanvas\_\*
      - QuestionImage
      - QuestionPhoto

    - NOT successful. If anything, crashes more frequent.
      Therefore, most likely a memory problem? E.g. ACE-III "learning address"
      page: 26 x QuestionBooleanText, each with up to 4 potential images loaded,
      each ~3k on disk, would give 312k (when image caching would reduce that
      to 12k); might be larger in memory, and if the "imageref_ashmem create
      failed" message is showing the size -- which it is; see
      https://code.google.com/p/skia/source/browse/trunk/src/images/SkImageRef_ashmem.cpp?spec=svn11558&r=11558
      ... then it's about 36k per image, i.e. we were using 3.7 Mb for that page.
      That's then perhaps less surprising.

  - Reverted.
  - New technique

    - imagecache.js
    - Cache cleared from questionnaire.js
    - Applied to ValidityIndicator, StateRadio, StateCheck
      ... except you can't pass Blobs to Titanium.UI.createButton, only to
      createImageView
      ... so ImageView used instead of button for now (which loses the "currently
      being touched" facility). See AS_BUTTONS flag in qcommon.js.
    - However, ImageVerticalGroup goes to preloading method for performance
      reasons.

- Allow user to specify the number of lines used for fixed-height multiline
  text entry: multilineDefaultNLines.

**Client v1.33, 2015-04-26**

- Bugfix: CGI didn't offer all options for Question 3 (drug effects)!

**Client v1.34, 2015-04-26**

- Probable bugfix: IDED3D performed its stage failure check before its stage
  success check at the end of trials (should be the other way round).

**Client v1.40, 2015-05-27**

- Requires server version 1.40.
- FROM-LP framework set menu
- O'Brien group set menu 1
- Brief COPE
- CBI-R
- ZBI (data collection tool only with option for institution to supply text)
- HADS (data collection tool only with option for institution to supply text)
- AUDIT-C
- CGI-I
- Patient Satisfaction Scale
- Referrer Satisfaction Scale (generic + specific)
- Friends and Family Test
- IRAC
- MDS-UPDRS (data collection tool only)
- GDS-15
- AUDIT and AUDIT-C corrected to be clinician-colour pages, and instruction
  page added.
- extrastrings framework - at registration, the tablet downloads sets of extra
  strings from its server. This allows the conversion of crippled tasks to
  fully-functional ones, subject to the hosting institution's right to offer
  the strings up to its tablets (which is a matter for the institution, the
  strings not being distributed with CamCOPS).
- clinician_service field as part of clinician block (and used for service
  feedback); corresponding storedvars.defaultClinicianService variable.
- boldPrompt option to QuestionTypedVariables
- editing_time_s field as standard on all tasks

.. _changelog_2016:

2016
~~~~

**Server v1.40, 2016-01-28**

- From May 2015 to 28 Jan 2016.
- REQUIRES COMMAND TO UPGRADE EACH DATABASE:
  camcops --maketables /etc/camcops/MYCONFIGNAME.conf
- NOTE THAT THE camcops_meta command is now available, e.g.
  `camcops_meta --filespecs /etc/camcops/camcops_*.conf --ccargs maketables`
- Brief COPE Inventory.
- CBI-R.
- ZBI (data collection tool only with option for institution to supply text).
- HADS (data collection tool only with option for institution to supply
  text).
- AUDIT-C
- CGI-I
- Patient Satisfaction Scale
- Referrer Satisfaction Scale (generic + specific)
- Friends and Family Test
- IRAC
- MDS-UPDRS (data collection tool only)
- GDS-15
- DEMQOL
- DEMQOL-Proxy
- Default "respondent" framework, for DEMQOL-Proxy.
- Bugfix to ProgressNote: get_task_html() crashed because "answer" was not
  imported.
- EXTRA_STRING_FILES system, with "get_extra_strings" command to database
  API.
- PHQ-9 database comment fixed for Q10.
- comment_fmt for HADS fields. Note MySQL: SHOW FULL COLUMNS FROM table.
- IES-R (skeleton only).
- WSAS (skeleton only).
- PDSS (skeleton only).
- PSWQ.
- Y-BOCS, Y-BOCS-SC (skeleton only).
- DAD (skeleton only).
- BADLS (skeleton only).
- NPI-Q (skeleton only).
- FRS.
- INECO Frontal Screening (IFS) (skeleton only).
- Add clinician to GAF.
- Diagnosis reports.
- Device report.
- update_multiple_databases.py script
- Unit tests to ensure no overlap for task longnames/shortnames/tables; see
  cc_task.unit_tests().
- clinician_service field as part of clinician block
- xhtml2pdf @page size changed from "a4" to "A4" in cc_html.py to remove
  "WARNING:xhtml2pdf:Unknown size value for @page"; see
  https://github.com/chrisglass/xhtml2pdf/issues/71 ... however, no effect.
- Switch from xhtml2pdf, bypassing Weasyprint, to wkhtmltopdf (via pdfkit) as
  the (default and now only) PDF renderer.
- Abstract base class for PCL tasks wasn't inheriting from object; now is.
- editing_time_s field for all tasks.
- Indexing of ID number fields in patient table.
- Python package format internally.
- Did not implement SVG logos for PDF generation; made files larger not
  smaller. Stick with PNG.
- Remove delayed imports; bug-prone.
  http://stackoverflow.com/questions/744373
  Except in cc_hl7, which imports phq9 for testing (which imports specific
  things from cc_task, which imports cc_hl7).
  ... subsequently revisited; delayed imports now remain only for unit tests,
  where they are more convenient.
- Refresh button for tasks (because browsers keep asking you twice if you hit
  F5).
- EXTRA_STRING_FILES can use globs (in cc_string.py).
- Support MPLCONFIGDIR (default: /var/cache/camcops/matplotlib) to speed up
  matplotlib/pyplot loading.
- Updated to current pythonlib.
- Python build toolchain.
- Moved to Python 3.

  - Of note: comparison of None to int now fails.

- Supplied with Gunicorn, to enable front-end web servers like Apache to
  talk to CamCOPS, and have CamCOPS upgrade/restart, without having to (a)
  restart Apache, or (b) integrate a specific Python version into Apache
  with mod_wsgi. The new system runs in a virtual environment, entirely
  separated (in terms of code) from the front-end web server, communicating
  with it via a private port or Unix socket.
- Disable HTTP client-side caching for added security.
  See also http://codebutler.github.io/firesheep
- Change to relative URL addressing to make that work simply (without having
  to tell CamCOPS where it's mounted).
- ALLOW_INSECURE_COOKIES debugging option.
- Fix nasty bug in rnc_web using "extraheaders=[]" in function signature,
  allowing headers (e.g. cookies) to accumulate over multiple calls (and leak
  across clients). 2016-01-09.
  (But note what is NOT a bug: multiple Chrome "incognito" tabs share each
  other's cookies: https://code.google.com/p/chromium/issues/detail?id=24690)
- Removed the "Tablet device" filter option for tasks (it generates long
  complex-looking lists of IDs and isn't helpful for end users). Removal
  done simply by taking the option out of the form, in
  cc_session.get_current_filter_html().
- New server environment variable options (see instructions.txt):
  - MPLCONFIGDIR
  - CAMCOPS_DEBUG_TO_HTTP_CLIENT
  - CAMCOPS_PROFILE
  - CAMCOPS_SERVE_STATIC_FILES
- Changes to config variables:
  - RESOURCES_DIRECTORY -- removed
  - INTROSPECTION_DIRECTORY -- removed
  - CAMCOPS_LOGO_FILE_ABSOLUTE -- added (optional)
  - MAIN_STRING_FILE -- added (optional)
  - EXTRA_STRING_FILES -- added (optional)
- Added process ID to log output.
- Task counting report.
- Restructure Task/Ancillary classes to be more concise.
- Better unit testing inc. checking for __dict__/fieldname conflicts.
- camcops_meta.py script for e.g. upgrading multiple databases.
- PyMySQL==0.7.1 (upgraded from PyMySQL==0.6.7) to eliminate error on
  inserting BLOBs ("TypeError: can't use a string pattern on a bytes-like
  object").

**Server v1.41, 2016-01-29**

- Bugfix to large research data dumps (were timing out due to inefficient
  SQL). Changed cc_task.get_ancillary_items(), with some back-end functions
  in rnc_db too (changed fetch_all_objects_from_db_where(); added
  create_object_from_list() ).

**Server v1.50, 2016-07-29**

- Change _device VARCHAR(255) fields to _device_id INT.
- Change \*_user VARCHAR(255) fields to \*_user_id INT.
- Note that this leaves only a few "odd" things from the point of standard
  RDBMSs:

  - multiple keys on server side (adding _device_id and _era) to reflect
    multiple devices with write-only access;
  - history on server side (adding _current, and forward/backward PK chain)
  - the "_era" field is textual (ISO-8601), because
    (a) no database seems to store DATETIME values with milli-/microsecond
    accuracy and proper timezone information (in the sense that you can
    recreate the timezone of origin);
    (b) we can use a non-NULL special value, in our case "NOW", as it makes
    things simpler for end users to use "a = b" consistently and not have
    to do "a = b OR a IS NULL AND b IS NULL".
  - patient IDs are unchecked and are allowed to be incomplete (to reflect
    our need to operate with incomplete information, and in anonymous as well
    as fully-identified environments), and duplicate patient records are
    allowed (across, but not within, device/era combinations).
- Static type checking for server Python code.

**Known problems and bugs at the end of the Titanium client**

- visually disabled elements not yet implemented (starting point only in
  qcommon.js)
- wait class imperfect and may leak
- ti.imagefactory module does not support x86 architecture, just arm
- Titanium iOS re-layout is very slow. Visible e.g. when changing questionnaire
  font sizes, but more important for multiline multiline text areas.
  Bug report: https://jira.appcelerator.org/browse/TC-3560
- mobileweb edition not yet working
- Alerts with large content no longer scroll under iOS 8.
  Apparently this is an Apple bug:
  https://jira.appcelerator.org/browse/TIMOB-17745

**Where were version numbers stored in the Titanium client?**

1. App version number is stored in tiapp.xml

2. Tablet's minimum server version requirement is in
   Resources/common/VERSION.js

3. Server version number is stored in server/cc_modules/cc_version.py
   (as is the server's minimum tablet version requirement).

4. Server changelog is stored in server/changelog.debian

5. The web page also has a record of the most recent version, in
   download/index.html

Indirectly:

- Tablet app: Resources/common/VERSION.js reads the app version using
  Titanium.App.version, which is determined by tiapp.xml. In turn,
  it exports this as CAMCOPS_VERSION.
- Tablet build: SHIP_ANDROID reads VERSION.js
- Server build: MAKE_PACKAGE reads cc_constants.py

Human-readable details are shown in this file.

.. _changelog_2017:

Current C++/SQLite client, Python/SQLAlchemy server
---------------------------------------------------

2017
~~~~

**Client v2.0.0 beta**

- Development of C++ version from scratch. Replaces Titanium version.
- Released as beta to Google Play on 2017-07-17.

**Client v2.0.1 beta**

- More const checking.
- Bugfix to stone/pound/ounce conversion.
- Bugfix to raw SQL dump.
- ID numbers generalized so you can have >8 (= table structure change).

**Client v2.0.2 beta**

- Cosmetic bug fixes, mainly for phones, including a re-layout of the ACE-III
  address learning for very small screens.
- Bugfix: deleting a patient didn't deselect that patient.
- Default software keyboard for date entry changed.
- Bugfix for canvas widget on Android (size was going wrong).
- Automatic adjustment for high-DPI screens as standard in `QuBoolean` (its
  image option), `QuCanvas`, `QuImage`, `QuThermometer`.

**Client v2.0.3 beta, 2017-08-07**

- Trivial type fix to patient_wanted_copy_of_letter (String → Bool) in the
  unused task CPFTLPSDischarge.

**Server v2.1.0 beta, 2017-10-17**

- Major changes, including...
- SQLAlchemy for database work
- Group concept
- HOWEVER, HL7 EXPORT AND ANONYMOUS STAGING DATABASE SUPPORT DISABLED;
  further release pending.

**Client v2.0.4 beta, 2017-10-22**

- Bugfix: BLOB FKs weren’t being set properly from `BlobFieldRef` helper
  functions.

**Client v2.0.5 beta, 2017-10-23**

- Bugfix: if the server’s ID number definitions were consecutively numbered,
  the client got confused and renumbered them from 1.

**Server v2.1.1 beta, 2017-10-23**

- Bugfix: WSAS “is complete?” flag failed to recognize the “retired or work
  irrelevant for other reasons” flag.

.. _changelog_2018:

2018
~~~~

**Client v2.2.0 beta, 2018-01-04 to 2018-02-03**

- *To solve the problem of clients and servers being upgraded independently:*
  Reads tables from server during registration (see server v2.2.0). Implemented
  a “minimum server version” option internally for each task (see contemporary
  server changelog). Minimum server version increased from v2.0.0 to v2.2.0.

- Bugfix: adding a new patient from a task list didn’t wipe the task list until
  the patient was re-changed (failure to call `setSelectedPatient` from
  `ChoosePatientMenu::addPatient`; in fact, the patient name details changed
  without changing the underlying patient selection).

- Bugfix: don’t think the patient ID number table was being made routinely
  (!?).

- New CIS-R task.

- Internal fix to `DynamicQuestionnaire` to defer first-page creation until
  after constructor.

- Menu additions for CPFT Affective Disorders Research Database.

**Server v2.2.0, 2018-01-04 to 2018-04-24**

- *To solve the problem of clients and servers being upgraded independently:*
  Maintains a minimum client (tablet) version per task; during registration,
  offers the client the list of its tables and the minimum number. This allows
  a newer client to recognize that the server is older and has ‘missing’
  tables, and act accordingly. See `ensure_valid_table_name()`. Minimum tablet
  version remains v1.14.0.

- An obvious question: with that mechanism in place, is there any merit to the
  client maintaining a list of minimum server versions for each task? The
  change to the client’s “minimum server version” to 2.2.0 (for client v2.2.0)
  means that future clients will always have the “supported versions”
  information from the server. So, might a client advance mean that it might
  want to refuse old versions of the server, even though the server might be
  happy to accept? (That’s the only situation when a client’s per-table minimum
  server version would come into play.) Well, perhaps it’s possible, even if
  it’s very unlikely (and would probably indicate bad backwards compatibility
  on the client’s part! Let’s implement it for symmetry. Actually, thinking
  further, it might be quite useful: if you upgrade a task and add extra
  fields, using this would potentially allow the client to work with older
  servers unless a specific task is used. Implemented; see client changelog
  above. The default for all tasks is the client-wide minimum server version.

- New report to find patients by ICD-10 or ICD-9-CM diagnosis (inclusion and
  exclusion diagnoses) and age.

- Bugfix where reports would only be produced in HTML format.

- New CIS-R task.

**Server v2.2.1, 2018-04-24 to 2018-06-11**

- Username added to login audit.

- SQLAlchemy `Engine` scope fixed (was per-request; that was wrong and caused
  ‘Too many connections’ errors; now per URL across the application, as it
  should be; see `cc_config.py`).

- Links to de-identified versions of tasks.

- Group administrators can now change passwords for other users in their group,
  as long as the other user isn't a groupadmin or superuser.

- A released (CPFT) version of 2.2.0 raised a "The resource could not be found"
  error when using the ``/view_groups`` URL, heading to ``groups_view.mako``.

  - Initially: not sure why; development version works fine. No files obviously
    missing. Only that page not working, of all the main menu pages. This was
    as the superuser. The problem was an exception being raised from the
    ``template.render_unicode()`` call in
    ``CamcopsMakoLookupTemplateRenderer.__call__``. Aha -- problem may have
    been a completely full disk. No; disk was completely full, but that wasn't
    the problem.

  - v2.2.1 released just in case I'd missed something.

  - No, it was a problem manifesting in groups_table.mako, which used
    ``u.username for u in group.users`` giving ``AttributeError: 'NoneType'
    object has no attribute 'username'``. Now, that is defined in `Group` as
    ``users = association_proxy("user_group_memberships", "user")``.

  - The problems looks to be in the data: there was an entry in the
    ``_security_user_group`` table with user_id = NULL (and group_id = 3).

  - *Not yet sure where that duff value came from.* Template updated to cope
    with the problem, regardless. (Perhaps the value came from an earlier
    version of ``merge_db.py``?)

**Server v2.2.2, 2018-06-19**

- Fixed bug in Diagnosis report for non-superusers (see
  :meth:`camcops_server.tasks.diagnosis.get_diagnosis_inc_exc_report_query`);
  the exclusion "where" restriction was being applied wrongly and joining the
  exclusion query to the main query, giving far too many rows.

**Client v2.2.1 beta, 2018-08-06**

- Background striping for the `QuMcqGrid*` classes.

- Bugfix: `android:allowBackup="false"` added back to AndroidManifest.xml

**Client v2.2.3, server v2.2.3, 2018-06-23**

- :ref:`Khandaker/Insight medical history <khandaker_1>` task.

- Client requires server v2.2.3.

**Client v2.2.4, 2018-07-18**

- Bugfix to Android client for older Android versions.

  - On startup, CamCOPS was crashing with "Unfortunately, CamCOPS has stopped."
    on older Android versions (e.g. 4.4.x).

  - The USB debugging stream showed: ``java.lang.UnsatisfiedLinkError: dlopen
    failed: could not load library "libcrypto.so.1.1" needed by
    "libcamcops.so"; caused by library "libcrypto.so.1.1" not found``.

  - Thoughts: see comments in ``changelog.rst``.

    .. Thoughts:
      - We were adding ``libcrypto.so`` and ``libssl.so`` (as part of the Qt
        Creator Build Settings). This used to work but now doesn't, presumably due
        to a change in Qt Creator. (The files were being packaged; try copying the
        ``.apk`` file and unzipping it.) The original files are symlinks to
        ``libcrypto.so.1.1`` and ``libssl.so.1.1``. Adding the ``*.1.1`` files via
        ``ANDROID_EXTRA_LIBS`` in ``camcops.pro`` is prohibited (the packaging
        process complains about files that are not ``lib*.so``). In
        ``libcamcops.so`` there are references to ``libcrypto.so.1.1``, but that
        file is missing.
    ..
      - Others have noticed this or a similar problem:
    ..
        - https://forum.qt.io/topic/35847/qt5-2-androiddeployqt-openssl-library-versioning (2013)
        - https://bugreports.qt.io/browse/QTCREATORBUG-11237
        - https://bugreports.qt.io/browse/QTCREATORBUG-11062
        - https://bugreports.qt.io/browse/QTBUG-47065
    ..
      - No change after manually deleting the build directory (not just cleaning)
        and rebuilding.
    ..
      - So, another way round: why is ``libcamcops.so`` asking for a versioned
        library? It turns out that the problem is that OpenSSL was built with
        versioned libraries.
    ..
        Instructions at http://doc.qt.io/qt-5/opensslsupport.html suggest using
        ``make CALC_VERSIONS="SHLIB_COMPAT=; SHLIB_SOVER=" build_libs`` when
        building OpenSSL for Android, also as per
        https://stackoverflow.com/questions/24204366/how-to-build-openssl-as-unversioned-shared-lib-for-android,
        but that is for an older version of OpenSSL (e.g. 1.0.2d). Lots of things
        failed, but I succeeded by automatically editing the Makefile in a hacky
        way. See changes in ``build_qt.py``. We now have unversioned libraries for
        Android.
    ..
      - I'm less clear what changed as it was working well beforehand!
    ..
        - In retrospect: may have been changing the Android API level from 23 to
          28.
    ..
      - Then we got this crash: ``java.lang.UnsatisfiedLinkError: dlopen failed:
        cannot locate symbol "EVP_MD_CTX_new" referenced by "libcamcops.so"...``.
        Deleted ``qmake`` and rebuilt via
        ``build_qt.py --build_android_arm_v7_32``. Didn't build for Android
        (``undefined reference to WebPInitAlphaProcessingNEON``). Upgraded Qt to
        5.11.1. Built fine (Linux, Android). Same crash. But as before,
        libcrypto.so and libssl.so are being loaded.
    ..
      - We are using android-ndk-r11c (March 2016); Qt's preference is 10e (May
        2015) (as per http://doc.qt.io/qt-5/androidgs.html). The current version
        (as of 2018-07-04) is r17b (June 2018); see
        https://developer.android.com/ndk/downloads/. Still, 11c has worked
        throughout.
    ..
      - I suspect the root cause is approximately as follows.
    ..
        - At present, the Qt build uses dynamic linking to OpenSSL. (That's why
          the Linux version needs to find libcrypto.so and libssl.so.)
    ..
        - In the Linux build of CamCOPS, OpenSSL is included statically. (That's
          why direct calls from cryptofunc.cpp to EVP* calls work.)
          (Certainly,
          ``objdump -t build-camcops-CustomLinux-Debug/camcops | grep EVP`` shows a
          bunch of stuff, and ``EVP_MD_CTX_new`` is present for ``objdump -T`` as
          well as ``objdump -t``, as a real function.)
    ..
        - In the Android build, CamCOPS is built to a library, libcamcops.so.
          Presumably that's why it can build without OpenSSL EVP* functions in it,
          without complaining. But then it needs OpenSSL functions via DLL?
          Certainly, ``objdump -t
          build-camcops-Android_ARM-Release/android-build/libs/armeabi-v7a/libcamcops.so``
          shows no symbols. However, ``strings`` shows EVP stuff, and ``objdump
          -T`` shows ``EVP_MD_CTX_new`` as ``DF *UND* ... OPENSSL_1_1_0
          EVP_MD_CTX_new``.
    ..
        - See also
          https://stackoverflow.com/questions/32737355/elf-dynamic-symbol-table.
    ..
        - OK, so we need to deal with the DLL zone. Dealt with. Runs on Linux with
          DLL mode and without; see OPENSSL_VIA_QLIBRARY.
    ..
      - No, perhaps I was wrong, because:
    ..
        - Now we get ``java.lang.UnsatisfiedLinkError: dlopen failed: cannot locate
          symbol "HMAC_CTX_new" referenced by "libcamcops.so"``. So that's
          progress. But ``HMAC_CTX_new`` isn't in my source code. If we do
          ``objdump -T libcamcops.so | grep OPENSSL_1_1_0``, we get
    ..
          .. code-block::
    ..
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 OBJ_nid2sn
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_CTX_new
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_iv_length
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_CTX_free
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CipherInit_ex
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_key_length
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_sha512
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 RAND_bytes
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_aes_256_cbc
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_nid
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_block_size
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CipherFinal_ex
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 HMAC_CTX_new
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 HMAC_Update
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 PKCS5_PBKDF2_HMAC_SHA1
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 HMAC_Final
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 HMAC_CTX_free
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 HMAC_Init_ex
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_get_cipherbyname
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 RAND_add
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_sha1
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CIPHER_CTX_set_padding
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_CipherUpdate
            00000000      DF *UND*	00000000  OPENSSL_1_1_0 EVP_MD_size
    ..
          So possibilities include that I'm calling some of these inadvertently by
          using types within cryptofunc.cpp; but more likely that sqlcipher is
          calling them. We're not going to get far this way; the explicit DLL
          approach was probably silly. Instead, see
          https://stackoverflow.com/questions/25147714/qt-openssl-android and note
          that we may need to insert into ``AndroidManifest.xml`` the following:
    ..
          .. code-block:: xml
    ..
            <meta-data android:name="android.app.load_local_libs" android:value="-- %%INSERT_LOCAL_LIBS%% --:lib/libssl.so:lib/libcrypto.so"/>
            Note this bit:                                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ..
          No, that didn't work. We ended up with two copies of the libraries, in
          "...camcops" and "...camcops-1", but it didn't fix the problem. Perhaps
          we need both static linkage (for CamCOPS internal calls to OpenSSL,
          including SQLCipher) and dynamic linkage (for the parts of Qt that use
          OpenSSL). Changes made to ``camcops.pro``. No, that didn't work either;
          doesn't link (missing e.g. ``signal``). See
          https://stackoverflow.com/questions/37122126/whats-the-exact-significance-of-android-ndk-platform-version-compared-to-api-le;
          perhaps this is all down to a change in the Qt setting for Android NDK
          level, from 23 to 26, without a change in the OpenSSL Android NDK build
          level.
    ..
          Not yet explored:
    ..
          - https://github.com/openssl/openssl/issues/3826
          - Note that SQLCipher may be moving from OpenSSL to mbedTLS:
            https://github.com/praeclarum/sqlite-net/issues/597
          - https://stackoverflow.com/questions/25049603/dlopen-failed-cannot-locate-symbol-signal?rq=1
    ..
          Trying NDK 10e (rather than 11c):
    ..
          - Download and unzip to ~/dev/
          - Change ``build_qt.py`` default.
          - In Qt Creator, change :menuselection:`Tools --> Options --> Devices --> Android --> Android Settings --> Android NDK location."
          - ABANDONDED/REVERTED; see below.
    ..
          Aha. It's this, perhaps:
    ..
          - https://android-developers.googleblog.com/2016/06/android-changes-for-ndk-developers.html
          - So, must be API 23 or lower, or dlopen() calls will fail, which is
            exactly what we're seeing.
    ..
          The Sony tablet is Android 4.4.2 (API level 19), and fails; my Samsung
          phone is Android 6.0.1 (API level 23) and works fine. So it is something
          about the Android API. So, checking
          https://wiki.qt.io/Qt_for_Android_known_issues: nothing obvious. But
          upgrading the Sony Xperia Z2 tablet (to 6.0.1, the next available) made
          the same binaries work.

  - Upshot: Android API 19 (Android 4.4.x) no longer works. API level 23
    (Android 6.0.1) is fine; intermediates untested. It's a little unclear
    what's changed (unless I was just behind on testing for old versions of
    Android and the problem had been there for a while). One possibility was
    that the shared OpenSSL libraries were being compiled for ``android-23``
    (as per ``build_qt.py``) and that was not the same as ``minSdkVersion`` in
    ``AndroidManifest.xml``. The problems are explained well at
    https://stackoverflow.com/questions/21888052/what-is-the-relation-between-app-platform-androidminsdkversion-and-androidtar/41079462#41079462,
    where APP_PLATFORM is equivalent to the API version used by ``build_qt.py``
    to compile OpenSSL etc.

  - The upshot from that article is that libraries compiled with the Android
    NDK (like OpenSSL in our case) must be compiled with for the same SDK
    version (``APP_PLATFORM``) as ``minSdkVersion``.

  - We were using ``minSdkVersion="16"``, so I tried setting
    ``DEFAULT_ANDROID_API_NUM = 16`` in ``build_qt.py``, and recompiling for
    Android using ``build_qt.py --build_android_arm_v7_32``, continuing to use
    NDK r11c. I moved ``targetSdkVersion`` back to 26 (soon to be the Google
    Play minimum). This works on Android 6.0.1 (API 23, using debug mode).
    However, it still crashes (as above) with Android 4.4.x (API 18).
    As of Feb 2018, about 58% of Android in the wild is API 23 or higher
    (https://en.wikipedia.org/wiki/Android_version_history), and about 82% is
    API 21 and higher. It is certainly better to fail to run than to crash, so
    let's say that we will set API 23 (Android 6.0) as the minimum for now.


**Server v2.2.4, 2018-06-29**

- Update to libraries:

  - alembic from 0.9.6 to 0.9.9
  - cardinal_pythonlib from 1.0.16 to 1.0.18
  - colorlog from 3.1.0 to 3.1.4
  - CherryPy from 11.0.0 to 16.0.2
  - deform from 2.0.4 to 2.0.5
  - distro from 1.0.4 to 1.3.0
  - dogpile.cache from 0.6.4 to 0.6.6
  - gunicorn from 19.7.1 to 19.8.1
  - matplotlib from 2.1.0 to 2.2.0
  - mysqlclient from 1.3.12 to 1.3.13
  - numpy from 1.13.3 to 1.14.5
  - pendulum from 1.3.0 to 2.0.2
  - pyramid from 1.9.1 to 1.9.2
  - pyramid_debugtoolbar from 4.3 to 4.4
  - python-dateutil from 2.6.1 to 2.7.3
  - pytz from 2017.2 to 2018.5
  - scipy from 1.0.0rc1 to 1.1.0
  - sqlalchemy from 1.2.0b2 to 1.2.8
  - typing from 3.6.2 to 3.6.4

- Bugfix to SQLAlchemy/Alembic handling, such that tables are always created
  with ``CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci`` rather than the erroneous
  ``COLLATE utf8mb4_unicode_ci CHARSET utf8mb4``. See :ref:`MySQL: Illegal mix
  of collations <mysql_illegal_mix_of_collations>`.

**Server v2.2.5, 2018-07-23**

- Python package: ``camcops-server``.
