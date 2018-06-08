..  documentation/source/client/client_using.rst

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

.. include:: include_tabletdefs.rst

.. _client_using:

Using the client
================

Menus
-----

CamCOPS begins at its main menu: :tabletmenu:`|camcops| CamCOPS: Cambridge
Cognitive and Psychiatric Assessment Kit`.

At any menu except the top menu, touch |back| (at the top left) to return to
the previous menu.

Locking
-------

The icon at the top right of the menus displays the **lock status**. Touch the
icon to change the lock status. The icon can appear as:

- |locked| **Locked.** When CamCOPS has a patient selected, and is locked, you
  can give it to the patient, and the patient won’t be able to see details from
  any other patients. If no patient is selected, and CamCOPS is locked, no tasks
  or patients are visible except anonymous tasks (see below).

- |unlocked| **Unlocked.** When CamCOPS is unlocked, you can change the patient,
  and see tasks from all patients when no patient is selected.

- |privileged| **Privileged.** This mode is for administration, and allows full
  configuration of CamCOPS. You can enter privileged mode from the
  :tabletmenu:`|settings| Settings` menu.

Patients
--------

When viewing a menu, near the top of the screen, you’ll always see the
:tabletcurrentpatient:`current patient’s details` or a message saying
:tabletnopatientselected:`No patient selected`.

Touch :tabletmenu:`|choose_patient| Choose patient` to choose (or add, or edit)
a patient. At the :tabletmenu:`|choose_patient| Choose patient` screen:

- Touch a patient row to select/deselect that patient.

- The currently selected patient, if any, will be :tabletcurrentpatient:`shown
  in blue`.

- Touch |add| to add a patient.

When a patient is selected, you can also:

- Touch |finishflag| to mark the patient as finished (see “Uploading” below).

- Touch |edit| to edit the patient’s details.

- Touch |delete| to delete the patient.

In the list of patients:

- |finishflag| indicates that the patient has been marked as finished (see
  “Uploading” below).

- |stop| indicates that the patient’s details are insufficient to be uploaded
  (as determined by the server’s ID policy).

- |warning| indicates that the patient’s details are sufficient to be uploaded,
  but insufficient to be finalized and removed from the tablet (as determined
  by the server’s ID policy).

When editing a patient:

- The descriptions of the ID numbers (e.g. “NHS number”, “Hospital BlahBlah
  number”) are determined by your server.

- Touch |ok| to save.

- Touch |cancel| to cancel.

Tasks
-----

From the main menu, you can go to the :tabletmenu:`|patient_summary| Patient
summary`. This shows all tasks on the tablet for the current patient. You can
also browse the menu to find specific tasks. If you have trouble finding one,
try :tabletmenu:`|alltasks| All tasks, listed alphabetically`.

At any task menu, task summaries are displayed.

- Choose :tabletmenu:`|info| Task information` for a page of background
  information about the task.

- Choose :tabletmenu:`|info| Task status` to view the task’s status within
  CamCOPS, such as whether your server is offering a fully functional copy or a
  skeleton task (according to institutional permissions).

- Touch |add| to create a new instance of the task, for the current patient.

- Touch a task row to select/deselect a task. (The currently selected task, if
  any, will be shown with a coloured background.)

- |finishflag| indicates (for an anonymous task only; see below) that the task
  has been marked as finished.

When a task is selected:

- Touch |zoom| to view the task, either as a quick summary, or as a proper
  facsimile.

- Touch |edit| to edit the task.

- Touch |delete| to delete the task.

- For anonymous tasks, touch |finishflag| to mark the task as finished.

Anonymous tasks
---------------

Some tasks are anonymous; they are not associated with any patient. (An example
is the anonymous GMC patient satisfaction questionnaire.)

Test subjects
-------------

You may want to experiment with the non-anonymous tasks. A suggested way is to
define a fake patient with an invalid ID number, or perhaps a couple of
different sexes. For example, an NHS number cannot be a single-digit number, but
CamCOPS doesn’t perform NHS number validation, so you could tell everyone in
your institution that **FAKEPATIENT, JANE (NHS# 1, female)** and **FAKEPATIENT,
JOHN (NHS# 2, male)** are your test patients. Everyone can then feel free to
play with those identities, but not to create others. However, you may be
prohibited from doing this in a clinical environment, in which case you could
set up a second training group in your database. (The disadvantage of that is
the need for users, or their administrator, to select the proper group after
training.)

Questionnaire-style tasks
-------------------------

Some tasks use an custom user interface, but many use a standard questionnaire
style with one or more pages.

The page colour tells you whom the page is primarily for:

- white for patients;

- pale yellow for clinicians;

- a pale yellow header with a white page where the clinician needs to show the
  patient the page and then mark the responses;

- lavender for configuration menus;

- … and grey for the CamCOPS main menus.

When entering information, **make the yellow disappear.** Information is
required if you see things in yellow, like this:
|radio_unselected_required| |check_unselected_required|
|field_incomplete_mandatory| :missingtext:`Enter some text`. You will not be
able to move on to the next page while required information is missing.

To navigate within a questionnaire, use the |back| (back) and |next| (next)
icons at the top right to navigate the pages. At the final page, touch |finish|
to finish. To abort, touch |cancel| (at the top left).

.. note::

    Aborting discards your changes when editing configuration information, but
    does not discard changes made to tasks. All changes made to task information
    are immediate and persistent.

Some widgets have special properties:

- Some widgets can’t display the lack of a value well (e.g. date/time pickers;
  sliders). They show the symbol |field_incomplete_mandatory| when information
  is missing but mandatory. If |field_incomplete_mandatory| appears, you need
  to set a value, even if it looks like one is already set! Widgets may show
  |field_incomplete_optional| when information is missing but optional.
  Occasionally, widgets may offer the delete button |delete| to wipe their
  contents.

- For date/time fields, touch |time_now| (if shown) to set the date/time to
  now.

- For sounds, touch |speaker| and |speaker_playing| to start and stop the
  sound, respectively. (The symbol indicates whether or not the sound is
  currently playing.) Some sound players offer a volume dial as well.

- For photos, touch |camera| to take a photo (using your device’s camera
  interface), and |rotate_anticlockwise| |rotate_clockwise| to rotate the photo.
  You can also delete the photo with |delete|.

- For sketches, touch |reload| to reset to the starting state.

- For countdowns, touch the :tabletmenu:`Start`, :tabletmenu:`Stop`, and
  :tabletmenu:`Reset` buttons as required. If your device’s volume is turned
  up, the device will go bong when the countdown elapses.

- For diagnostic codes, you can browse the tree (and touch ‘leaves’ and
  sometimes branches to select a diagnosis), or press |magnify| to switch to a
  search view, where you can type in a fragment of a diagnosis or its code.
  Press |treeview| to return to the tree view.

See the Demonstration questionnaire on the :tabletmenu:`|info| Help` menu for a
tutorial.

When viewing a read-only facsimile of a questionnaire-style task:

- The symbol |read_only| appears to indicate the read-only status.

- Touch |choose_page| to jump directly to a specific page. (This button will
  sometimes be available during editing, but will not then allow you to jump
  beyond the last seen or first incomplete page.)

Uploading
---------

Choose :tabletmenu:`|upload| Upload data to server` from the main menu. It will
only work if:

- You have chosen the server in :menuselection:`Settings --> Server settings`.

- You have set your username (and, optionally, password) in
  :menuselection:`Settings --> User settings`.

- The tablet has previously been registered with the server
  (:menuselection:`Settings --> Register...`).

There are three upload methods:

- **COPY.** This copies unfinished patients to the server. It moves finished
  patients (that is, the data for finished patients is copied to the server,
  then deleted from the tablet), and finished anonymous tasks.

- **MOVE.** This moves all patients and their data. (If some patients do not
  meet the server’s finalizing criteria, as above, then you can’t MOVE until you
  fix this.)

- **MOVE, KEEPING PATIENTS.** This moves all patients’ data, and erases all
  task data from the tablet, but it keeps the basic patient details, so you can
  add more tasks for these patients later.

Please MOVE whenever possible; this reduces the amount of patient-identifiable
information stored on this device.

You should see a message of success when the upload is complete.

Seeing what you’ve uploaded
---------------------------

Use any web browser (on a computer or tablet) to browse to your CamCOPS server.
See the :ref:`web interface instructions <website_general>` for more detail.

Help
----

The :tabletmenu:`|info| Help` menu includes, amongst other things:

- links to this documentation;

- a demonstration task, to try out all the user interface elements;

- the CamCOPS app version number.
