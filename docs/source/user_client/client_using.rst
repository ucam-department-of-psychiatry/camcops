..  docs/source/user_client/client_using.rst

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

.. include:: include_tabletdefs.rst

.. _client_using:

Using the client
================

..  contents::
    :local:
    :depth: 3


Menus
-----

CamCOPS begins at its main menu: :tabletmenu:`|camcops| CamCOPS: Cambridge
Cognitive and Psychiatric Assessment Kit`.

At any menu except the top menu, touch |back| (at the top left) to return to
the previous menu.


Locking
-------

The icon at the top right of the menus displays the **lock status**. Touch the
icon to change the lock status. When operating in Clinician Mode, the icon can
appear as:

- |locked| **Locked.** When CamCOPS has a patient selected, and is locked, you
  can give it to the patient, and the patient won’t be able to see details from
  any other patients. If no patient is selected, and CamCOPS is locked, no tasks
  or patients are visible except anonymous tasks (see below).

- |unlocked| **Unlocked.** When CamCOPS is unlocked, you can change the patient,
  and see tasks from all patients when no patient is selected.

- |privileged| **Privileged.** This mode is for administration, and allows full
  configuration of CamCOPS. You can enter privileged mode from the
  :tabletmenu:`|settings| Settings` menu.

When operating in :ref:`Single User Mode <single_user_mode>`, locking the app
will require the patient to enter their CAMCOPS APP PASSWORD before they can
continue using it.


Patients (Clinician Mode only)
------------------------------

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

- |stop_small| indicates that the patient’s details are insufficient to be
  uploaded (as determined by the server’s ID policy).

- |warning| indicates that the patient’s details are sufficient to be uploaded,
  but insufficient to be finalized and removed from the tablet (as determined
  by the server’s ID policy).

When editing a patient:

- The descriptions of the ID numbers (e.g. “NHS number”, “Hospital BlahBlah
  number”) are determined by your server.

- Touch |ok| to save.

- Touch |cancel| to cancel.


Tasks (Clinician Mode only)
------------------------------

From the main menu, you can go to the :tabletmenu:`|patient_summary| Patient
summary`. This shows all tasks on the tablet for the current patient. You can
also browse the menu to find specific tasks. If you have trouble finding one,
try :tabletmenu:`|alltasks_small| Search all tasks`.

At any task menu, task summaries are displayed.

- Choose :tabletmenu:`|info_small| Task information` for a page of background
  information about the task.

- Choose :tabletmenu:`|info_small| Task status` to view the task’s status within
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


Test subjects (Clinician Mode only)
-----------------------------------

You may want to experiment with the non-anonymous tasks. A suggested way is to
define a fake patient with an invalid ID number, or perhaps a few such patients
of different sexes. For example, you could tell everyone in your institution
that **FAKEPATIENT, JANE (mystudyid# 99999, female)** and **FAKEPATIENT, JOHN
(mystudyid# 99998, male)** are your test patients. Everyone can then feel free
to play with those identities, but not to create others. However, you may be
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

See the Demonstration questionnaire on the :tabletmenu:`|info_small| Help` menu
for a tutorial.

When viewing a read-only facsimile of a questionnaire-style task:

- The symbol |read_only| appears to indicate the read-only status.

- Touch |choose_page| to jump directly to a specific page. (This button will
  sometimes be available during editing, but will not then allow you to jump
  beyond the last seen or first incomplete page.)


Uploading
---------

Choose :tabletmenu:`|upload| Upload data to server` from the main menu.

In :ref:`Single User Mode <single_user_mode>` uploading should happen
automatically when you complete |finish| or abort |cancel| a task. If there was
a problem with the automatic upload (e.g. due to no internet connection) the app
will reattempt the upload when you return to the main menu from another screen,
provided 10 minutes has elapsed since the last attempt. You can also use this option
to reattempt the upload manually.

The rest of this section applies to Clinician Mode.

It will only work if:

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


Help (Clinician Mode only)
--------------------------

The :tabletmenu:`|info_small| Help` menu includes, amongst other things:

- links to this documentation;

- a demonstration task, to try out all the user interface elements;

- the CamCOPS app version number.


.. _single_user_mode:

Single user mode
----------------

Single User Mode is designed for a patient using the app at home on their own
tablet. It is used in conjunction with :ref:`task schedules <scheduling_tasks>`.

When you start the app for the first time, you will be prompted to enter the web
address of the CamCOPS server and the unique access key for your patient. These
should have been given to you by the clinician or researcher associated with the
study you are participating in. If you are using CamCOPS on a phone or tablet,
you may have been emailed a web address (beginning http://camcops.org/ or
camcops://camcops.org/) that you can use to register your patient with the
server without having to enter these details. You will need to have the email on
the same phone or tablet where the CamCOPS app is installed and open the link
from that email.

On the main menu you will see a list of tasks that you need to complete
and the date by which you need to complete them. You can start a task by
selecting it from the list. When you complete |finish| or abort |cancel| a task
and your tablet is connected to the internet, the app will upload your responses
automatically to the server. The app then marks the task as completed. If you
have completed all due tasks and there are tasks scheduled for future dates,
the app will display the date when the next task will be available.

If the app could not upload the tasks to the server, you can tell the app to try
again. Choose :tabletmenu:`|upload| Upload data to server` from the main menu.

You can select a number of other, less frequently used options by selecting
:menuselection:`More options`:

- :menuselection:`More options --> Get updates to my schedules` will fetch any
  updates to your task schedules from the server.

- :menuselection:`More options --> Choose language`

- :menuselection:`More options --> Online CamCOPS documentation`

- :menuselection:`More options --> Questionnaire font size`

- :menuselection:`More options --> Re-register me` will allow you to re-run the
  patient registration process. **WARNING:** any records not yet uploaded to the
  server will be lost.

Note that anonymous tasks are not associated with a patient when uploaded to the
server. If the database on the app is deleted and you re-register, we have no
way of knowing if the anonymous task has been completed or not so it will always
appear as incomplete.

There are a few other options from :menuselection:`More options --> Advanced options`.
These are intended to aid debugging so you should not need to use these in normal operation.

- :menuselection:`Advanced options --> Configure server settings`

- :menuselection:`Advanced options --> Enable network activity log`

- :menuselection:`Advanced options --> Change operating mode`

- :menuselection:`Advanced options --> Change user agent`
