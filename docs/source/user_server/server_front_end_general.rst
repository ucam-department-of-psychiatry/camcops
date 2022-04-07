..  docs/source/user_server/server_front_end_general.rst

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

.. _Google Authenticator: https://en.wikipedia.org/wiki/Google_Authenticator
.. _SMS: https://en.wikipedia.org/wiki/SMS
.. _Twilio Authy: https://authy.com/

.. include:: include_bootstrap_icons.rst

.. _website_general:

Using the web site
==================

..  contents::
    :local:
    :depth: 3


General navigation
------------------

First, |login| **log in** to CamCOPS via a web browser.

|camcops| Any time you see the CamCOPS logo (it’s at the top of most pages),
you can click it to get back to the |home| **main menu.**

You can also |logout| **log out** or return to the |home| **main menu** using
the navigation menu at the top of the page.


|home| Main menu
----------------

The main menu contains the following items. You may see only a subset,
depending on your permissions.


Patients
++++++++

.. _scheduling_tasks:

|patients| Manage patients and their task schedules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can schedule tasks for a patient to complete on their own tablet with the
CamCOPS app running in :ref:`Single User Mode <single_user_mode>`.

**OVERVIEW**

The key pieces of information your patient needs to know are:

- Where they can download CamCOPS for their tablet, phone, laptop etc (Google
  Play, Apple Store, GitHub)
- The location of the CamCOPS server
- Their unique access key

How you choose to communicate these to your patients is up to you. CamCOPS
supports a simple email workflow.

Your task schedules and patients will be associated with a :ref:`group
<groups>` that you administer. You must set the intellectual property (IP)
settings for this group to describe the contexts in which your group operates
(clinical, commercial, etc.). Any tasks you schedule for a patient need to be
permitted for these contexts.

- First, create a task schedule for your study (:menuselection:`Manage task
  schedules --> Add a task schedule`). Here you can specify the From, CC and
  BCC fields for your emails, along with an email template. The template can be
  customised to include the location of the server, the patient's name, their
  unique access key, and a unique URL that patients can use the first time they
  launch the app. This last option will register their patient automatically
  with the server, without the need to enter the server and access key (Android
  only).

- Next add items to your schedule (:menuselection:`Edit items` from the table
  of schedules):

  - Select the task from the drop-down

  - Enter the time from the start of the schedule when the patient may begin
    the task and the time the patient has to complete the task. These times can
    be expressed as a combination of months, weeks and days (defined here as 1
    month = 30 days, 1 week = 7 days).

From the Patient Task Schedules page you can add a new patient. The patient
must have enough identifiable information to match the :ref:`uploading and
finalizing ID policies <uploading_and_finalizing_policies>` of the group. Here
you can also assign one or more task schedules to the patient. You can specify
the start date of the schedule or leave it blank. If you leave it blank, the
start date will be the date the patient first downloads the schedule from the
server. You can assign the same schedule multiple times to a patient, though
you should only do this once the patient has completed the tasks for all
previous instances of the same schedule.

Advanced use: There is an optional form field to specify any patient-specific
settings for the tasks. This is a JSON object keyed on the task table name,
e.g.:

    .. code-block:: json

        {
            "task1": {
                "name1": "value1",
                "name2": "value2"
            },
            "task2": {
                "name1": "value1"
            }
        }

Refer to the relevant task documentation for any settings that can be applied
in this way.

If the patient has been successfully created, they should now appear in the
table along with the unique access key that they need for registration. The
address of the server is also displayed on this page for convenience. If you
have provided an email address for the patient and a "from" address for the
task schedule, :menuselection:`Send email...` will open a form with the email
body populated from the template associated with the schedule.

You can view a patient's progress through the schedule by following the link to
the named schedule from the table. From this table you can view the uploaded
task responses as HTML or PDF. Anonymous tasks will be listed in this table but
you will not see the responses. Here you can also view a list of emails sent to
the patient and view their details.

.. note::

    If you edit patient details after the patient has registered, the client
    will pick up the changes when it next picks up schedule updates.

    If you change the patient's ID numbers, though, the patient may have to
    redo tasks (completed tasks are sought by any current ID number).


**INTERFACE**

.. _view_patient_task_schedules:

|patients| **Patients and their task schedules**

This page manages patients and their associated schedules. It offers:

- |info_internal| **CamCOPS server location**

  - |info_external| Shows the URL for this server's API -- the URL that client
    devices should use to communicate with the CamCOPS server.

- |patients| **Patients (and their task schedules)**. For every patient set up
  for scheduling, this shows:

  - |patient| Their basic details (name, etc.);
  - identification numbers associated with them;
  - their access key;
  - |patient| |task_schedule| **task schedules** assigned to them (hyperlinked
    to :ref:`show their progress on this schedule
    <view_patient_task_schedule>`), along with a button to |email_send|
    **e-mail** them (using that schedule's template), if authorized;
  - a link to |patient_edit| **edit** the patient or assign schedules to them;
  - a link to |delete| **delete** the patient.

- A link to |patient_add| **add a patient**.

- A link to |task_schedules| :ref:`manage task schedules
  <view_task_schedules>`, if authorized.


.. _view_patient_task_schedule:

|patient| |task_schedule| **View a patient's progress on a schedule**

This page shows:

- Scheduled tasks for this patient on this schedule (including task type,
  "due from" date, "due by" date, whether the task has been created/uploaded to
  the server, and whether it is |complete| complete or |incomplete|
  incomplete).

  - If the task is due now and is not complete, a |due| due symbol will be
    displayed.

  - If the task is present on the server, you will be able to view it as
    |html_identifiable| HTML or |pdf_identifiable| PDF (see :ref:`View tasks
    <view_tasks>`).

  - If the task is anonymous, some of this information will be |unknown|
    unknown. CamCOPS treats anonymity seriously.

- Emails previously sent to the patient about this schedule. You can
  |email_view| **view** them, if authorized.

- A link to |email_send| **e-mail** the patient (using that schedule's
  template).

- A link back to |patients| :ref:`manage patients and their tasks
  <view_patient_task_schedules>`.


.. _view_task_schedules:

|task_schedules| **Task schedules**

This page manages task schedules themselves. It offers:

- |task_schedules| **Task schedules**. For every schedule configured, this
  shows:

  - the associated :ref:`group <groups>`;
  - the schedule's name;
  - links to |task_schedule| **edit** and |delete| **delete** the schedule;
  - the schedule's items and a link to |task_schedule_items| :ref:`edit items
    <view_task_schedule_items>`.

- A link to |task_schedule_add| **add a task schedule**.

- A link back to |patients| :ref:`manage patients and their tasks
  <view_patient_task_schedules>`.


.. _view_task_schedule_items:

|task_schedule_items| **Task schedule items (for a specific schedule)**

This page allows you to view and edit items for a specific schedule. It offers:

- |task_schedule_items| For every item associated with this schedule,

  - the task;
  - when the task is due from (relative to the start of the schedule);
  - how long the task is due within (once it falls due);
  - links to |edit| **edit** and |delete| **delete** the item.

- A link to |task_schedule_item_add| **add a task schedule item**.

- A link back to |task_schedules| :ref:`manage task schedules
  <view_task_schedules>`.


Task, trackers, and clinical text views
+++++++++++++++++++++++++++++++++++++++

Client devices upload **tasks**. You can view these individually in a variety
of formats. You can also view numeric information over time for a patient in a
**tracker**, and clinically relevant textual information for a patient in a
**clinical text view**.


.. _filter_tasks:

|filter| Filter tasks
~~~~~~~~~~~~~~~~~~~~~

You can configure your CamCOPS session to filter tasks according to *who*,
*what*, *when*, and *administrative criteria*. By default, no task filters are
set.

Under **who**, you can specify an optional patient forename, surname, date of
birth, sex, or any form of ID number in use on your server.

Under **what**, you can restrict to any subset of task types, and if you wish
you can restrict to completed tasks. You can also specify text contents. For
example, type in “paracetamol” to find clerkings that mention paracetamol
anywhere.

Under **when**, you can specify start and/or end dates, to find tasks in that
date range.

Under **administrative criteria**, you can restrict to specific uploading
devices or users, or the group to which a task belongs.

As well as a **set filters** button, there is a **clear** button to clear all
current filters.


.. _view_tasks:

|view_tasks| View tasks
~~~~~~~~~~~~~~~~~~~~~~~

This page shows all tasks meeting your current filter criteria. There are links
allowing you to |filter| :ref:`filter <filter_tasks>` the tasks.

Each task has hyperlinks to an |html_identifiable| HTML and a
|pdf_identifiable| PDF version. Sometimes tasks are colour-coded (there’s a key
at the bottom of the page).

The HTML task view is fastest and has additional viewing options. However, you
should not print the HTML view in a clinical environment, because it won’t have
patient identifiers on each page. Use the PDF for that instead, or if you want
to save the task as a single human-readable file.

When you view a task in HTML mode, there are some additional hyperlinks at the
bottom:

- |info_external| **Task help.** Shows you information about the task.

- **View raw data:** |xml| **XML** \| |json| **FHIR**. This shows you the raw
  structure as XML, or JSON-formatted FHIR format, including stored data and
  calculated fields such as summary scores.

  One useful feature is that all fields have an associated comment, and these
  comments are displayed in the XML.

  You can also view comments and other helpful details about the data structure
  of every task in the task details -- see :`Task list <task_list>`.

- **View anonymised version:** |html_anonymous| **HTML** \| |pdf_anonymous|
  **PDF**. This shows you a version with patient identification details hidden.
  It is not guaranteed to be free of identifying material, though; it makes no
  effort to remove patient details from free text, for example [#crate]_.

- (Administrators have additional options; see :ref:`administrative options
  <task_admin>`.)

- |pdf_identifiable| **View PDF**. A link to the PDF version.

PDF versions include patient identifiers on each page, to meet normal UK
clinical standards, and if the task involved recording a clinician’s views or
assessments, the PDF will include a template signature box for on-paper
authentication by the clinician.

Specimen tasks in PDF format:

- :download:`PHQ-9 <demotasks/dummy_task_1.pdf>`
- :download:`Psychiatric clerking <demotasks/dummy_task_2.pdf>` (albeit not a
  very good one!)

.. http://www.sphinx-doc.org/en/stable/markup/inline.html#referencing-downloadable-files


.. _trackers:

|trackers| Trackers for numerical information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many tasks produce numerical information, like total scores. Trackers allow you
to view numerical information from these tasks, or a subset of them, over time.
The resulting graphs are time-aligned within the tracker, across all tasks
(i.e. all graphs have the same time axis).

Not all tasks offer trackers.

Some tasks offer more than one numerical value, and therefore provide more than
one graph.

To configure a tracker, choose a patient by an ID number. You can, optionally,
specify a start and/or end date, and you can restrict to specific tasks.

You can view trackers in |html_identifiable| HTML or |pdf_identifiable| PDF
mode, or view the data used to generate them in |xml| XML format.

Specimen tracker:

- :download:`Fictional tracker <demotasks/dummy_tracker.pdf>`

.. include:: include_consistency_warning.rst


|ctv| Clinical text views
~~~~~~~~~~~~~~~~~~~~~~~~~

Like a tracker, a clinical text view (CTV) collects information across many
tasks for one patient. Like a tracker, a CTV is configured for a patient, and
can be configured for a date range and/or a subset of tasks. Like a tracker
(and like a book), a CTV flows from older to newer information. Unlike a
tracker, a CTV produces text for each task, not numbers. The text is intended
to be clinically useful. For example, simple questionnaires produce their
summary information. The ACE-III produces its total but also its subscale
scores. Clinical clerkings produce their full text. All tasks appear in the
CTV, but some tasks simply indicate that they have been performed.

You can view CTVs in |html_identifiable| HTML or |pdf_identifiable| PDF
mode, or view the data used to generate them in |xml| XML format.

In the HTML view of a CTV, all tasks provide hyperlinks to the full
representation of each task, so you can delve into more detail for any task of
interest.

Specimen CTV:

- :download:`Fictional CTV <demotasks/dummy_clinicaltextview.pdf>`

.. include:: include_consistency_warning.rst


Research views
++++++++++++++

.. _summary_fields:

|dump_basic| Basic research dump (fields and summaries)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option allows you to download a spreadsheet or similar file that contains
one worksheet for every type of task for which "current" data is present
[#current]_ (one row per task instance), and includes raw data and summary
measures (e.g. total scores).

.. note::

    For example, the :ref:`PHQ-9 <phq9>` stores the answers for 9 symptom
    questions in fields `q1` to `q9`, and one overall impact answer in the
    `q10` field; it also stores information to link the record to the patient
    in question, and some administrative information (relating to record
    history, editing time, etc.)

    However, it doesn’t store summary information on the server
    [#databasenormalization]_; rather, summary measures are calculated on
    demand. For this task, summary measures include:

    - `is_complete` (Boolean): is the task complete (no missing values)?
    - `total` (integer): total score
    - `n_core` (integer): number of core depressive symptoms reaching threshold
    - `n_other` (integer): number of other depressive symptoms reaching
      threshold
    - `n_total` (integer): total number of symptoms reaching threshold
    - `is_mds` (Boolean): does this patient meet the PHQ9 criteria for
      major depressive syndrome?
    - `is_ods` (Boolean): does this patient meet the PHQ9 criteria for
      other depressive syndrome?
    - `severity` (text): textual description of depressive severity by the
      standard PHQ9 scoring method.

    These summary measures are included in the research dumps.

You can choose to dump everything that you have permission for, or restrict to
the criteria you’ve set in your current session filter, or specify tasks and/or
groups manually.

**Formats**

The download formats include:

- An `R <https://www.r-project.org/>`_ script, which encapsulates the data and
  creates R objects for you. You can pull in the data from another script (or
  the command line) via th ``source`` command. It uses `data.table
  <https://cran.r-project.org/web/packages/data.table/vignettes/datatable-intro.html>`_.

- `OpenOffice <https://www.openoffice.org/>`_/`LibreOffice
  <https://www.libreoffice.org/>`_ spreadsheet (`ODS
  <https://en.wikipedia.org/wiki/OpenDocument>`_) format.

- XLSX (`Microsoft Excel <https://en.wikipedia.org/wiki/Office_Open_XML>`_).

- A ZIP file, containing multiple TSV files, one per worksheet. This is the
  least human-friendly format, but is OK for automatically importing into
  statistics packages.

  - For TSV, NULL values are represented by blank fields and are therefore
    indistinguishable from blank strings, and the Excel dialect of TSV is used.
    If you want to read TSV files into R, try:

    .. code-block:: R

        mydf = read.table("something.tsv", sep="\t", header=TRUE, na.strings="", comment.char="")

    Note that R will prepend ‘X’ to variable names starting with an underscore;
    see ``?make.names``.

    Inspect the results with e.g. ``colnames(mydf)`` or ``View(mydf)``.

There are also advanced data dumps in other formats (see below).

**Delivery method**

- Serve immediately.

  Depending on your administrator's preference, you may be permitted to
  download data with a single click. ("Immediate" downloads tie up part of the
  "front end" web server for a while as it builds the data file, which may be
  large, so it's often preferable to permit just e-mail and queued download
  options, as below.)

- E-mail.

  You can also choose to have the dump emailed to you, providing your user is
  set up with a valid email address. This is useful for large exports that may
  be time consuming.

- Queued download.

  You can ask the server to build a file for you. It will e-mail you when it's
  ready (assuming your e-mail address is configured) and you can then collect
  it from the |download| :ref:`Download area <download_area>`.

  Your administrator will set a time limit and a capacity limit for your
  download area. Files that get too old will be deleted, and you will not be
  allowed to create files that would exceed your capacity limit.


|dump_sql| Advanced research dump (SQL or database)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This more sophisticated research dump generates a fully structured SQLite
binary database of the data you select (or, if you prefer, the SQL text to
create it). By default, BLOBs (binary large objects) are skipped, because they
can be very large, but if you want, you can choose to include them.

You can choose the information you want exactly as for the basic research dump.

Some user information will be provided (e.g. user names), but security
information (e.g. passwords) is removed prior to the download.

As for the basic research dump, summary information is added to tables as they
are created. For example: the internal :ref:`PHQ9 <phq9>` table contains scores
for individual questions, but not the total (which is calculated dynamically).
When you download the data, the total (amongst other things) is calculated and
added to the data that you download (within the SQLite table or CSV file).

The delivery methods are as before.


.. _download_area:

|download| Download area
~~~~~~~~~~~~~~~~~~~~~~~~

This is where you can pick up data files that you have queued for downloading
(see above).


.. _task_list:

|info_internal| Task list
~~~~~~~~~~~~~~~~~~~~~~~~~

This provides information on all tasks in CamCOPS. For each task, you can view:

- |zoom_in| **Task code (internal table name) and details**, including:

  - Table definitions (data stored by CamCOPS in its database).
  - Summary elements (summary measures calculated by CamCOPS dynamically).
  - Tracker elements (see :ref:`trackers <trackers>` above).
  - FHIR structure.

- The task's **short name**.

- The task's long name, hyperlinked to its |info_external| **online help**.


|info_internal| Inspect table definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option allows you to view the database structure of the CamCOPS server
database, as data definition language (DDL), meaning the subset of SQL used to
create tables. In SQL dialects that support it (e.g. MySQL), the DDL contains
comments for every field, usually in considerable detail, so viewing the DDL
this is a good way of understanding how CamCOPS tasks store their data.


Reports
+++++++

|reports| Run reports
~~~~~~~~~~~~~~~~~~~~~

CamCOPS has a set of build-in reports; for example, to count tasks, or list
client devices, or find patients by diagnostic inclusion/exclusion criteria. You
can explore and run these from the Reports menu.

Reports are used in two stages: (1) |report_config| **configure**, (2)
|report_detail| **run**.

The configuration stage provides an interface to select options for the report.
This generally includes the output format (e.g. HTML, TSV), and sometimes much
more (e.g. for the reports to find patient by diagnosis). Once you’ve chosen the
options, click “View Report”. What the configuration stage actually does is to
generate a URL for the final report.

The HTML view of the report shows the configuration parameters, the results
(page by page), and the SQL used to generate the report.

The TSV option gives you the data in tab-separated values (TSV) format.

When you view the report in HTML format, you will see that the browser’s URL
contains your report configuration information. This means that you can save
this report for later.

For example, suppose you regularly want to find patients between the ages of 20
to 65 inclusive, with an ICD-9-CM inclusion diagnosis of depression (e.g. 311)
[#icd9cm]_, excluding bipolar affective disorder (e.g. anything starting 296)
or eating disorders (e.g. 307.1). You could create a report with these age
restrictions and inclusion and exclusion diagnoses, and view it. The URL would
look like this:

::

    https://my.camcops.site/report?diagnoses_inclusion=311%25&age_maximum=65&which_idnum=1&rows_per_page=&viewtype=html&diagnoses_exclusion=296%25&diagnoses_exclusion=307.1%25&age_minimum=20&report_id=diagnoses_finder_icd9cm&page=1

If you copy this URL, you can run the report again without having to configure
it manually. Here’s an approximate ICD-10 equivalent (same age range; include
F32% and F33%; exclude F30%, F31%, F50%):

::

    https://my.camcops.site/report?diagnoses_inclusion=F32%25&diagnoses_inclusion=F33%25&age_maximum=65&which_idnum=1&rows_per_page=&viewtype=html&diagnoses_exclusion=F30%25&diagnoses_exclusion=F31%25&diagnoses_exclusion=F50%25&age_minimum=20&report_id=diagnoses_finder_icd10&page=1

To view a report’s SQL in a formatted state, paste it into an online SQL
formatter [#sqlformat]_.


Group administrator options
+++++++++++++++++++++++++++

|user_management| User management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This page shows all users registered with the CamCOPS server. For existing
users, it shows:

- the username (marked to show |you| you in the list);
- their internal user ID number;
- flags, such as |superuser| superuser or |group_admin| group administrator
  status, or if the user is locked out, lockout status with an |unlock|
  **unlock** facility;
- full name;
- e-mail address, hyperlinked to |email_send| **e-mail** them;
- a link to |user_info| **view more details** about the user;
- a link to |edit| **edit** the user;
- groups they belong to, with links to set |user_permissions| **permissions**
  for the user within each group;
- their current upload group, with a button to |upload| **change** their upload
  group;
- links to set their authentication method, including

  - |password_other| **change password** for another user;
  - |password_own| **change password** for |you| yourself;
  - |mfa| **change multi-factor authentication method** for the user;

- a link to |delete| **delete** the user.

There is also a link to |user_add| **add a user**.

By default, autogenerated users (used by patients as part of :ref:`task
scheduling <scheduling_tasks>`) are not shown. They have names that look like
gibberish. However, you can show them if you wish; there's a tickbox to enable
this.


|email_configure| E-mail addresses of your users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This simple page shows all e-mail addresses of your users, along with users
whose e-mail addresses are missing.

You can e-mail an individual user by clicking their hyperlink (which will
launch your mail client via a ``mailto:`` URL).

To e-mail all users, copy/paste the list shown into your e-mail client. (There
is no universally accepted standard for multi-recipient ``mailto:`` URLs! See
https://stackoverflow.com/questions/13765286.)


|force_finalize| Forcibly finalize records for a device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here, you can force-finalize records for a device that has been lost or damaged
while it has outstanding business with the CamCOPS server.

This process marks all records from a particular device (e.g. tablet, or
desktop client) as final, so the device can no longer alter them. If you do
this and the client re-uploads records, they will be created as fresh tasks, so
only force-finalize devices that are no longer in use and to which you no
longer have access.


|delete_major| Delete patient entirely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This **irrevocable** operation permanently deletes a patient and all their
tasks from a specified group.


Superuser options
+++++++++++++++++

|groups| Group management
~~~~~~~~~~~~~~~~~~~~~~~~~

See :ref:`Groups <groups>` for background. Here, you can view and edit groups.

For existing groups, this shows

- the group's name;
- its internal ID number;
- its description;
- groups whose data this group is allowed to see (in addition to its own data);
- the upload ID policy;
- the principal (single necessary) ID number required by the upload policy, if
  applicable;
- the finalizing ID policy;
- the principal (single necessary) ID number required by the finalizing policy,
  if applicable;
- a list of group members;
- buttons to |group_edit| **edit** and |delete| **delete** the group.

There is also a link to |group_add| **add a new group**.


|audit_menu| Audit menu
~~~~~~~~~~~~~~~~~~~~~~~

Here you can

- |audit_options| **configure** then view the CamCOPS |audit_report| **audit
  trail** (with hyperlinks to |html_identifiable| **view a task** where
  relevant);

- |audit_options| **configure** then view the |audit_report| **exported task
  log** (with hyperlinks to the |exported_task| **task export attempt**, the
  |export_recipient| **export recipient**, and the |html_identifiable| **task**
  exported).

  The |exported_task| **task export attempt** may offer further details,
  depending on the export method, such as

  - |audit_item| e-mails sent;
  - |exported_task_entry_collection| FHIR task exports containing |audit_item|
    individual entries (e.g. Patients, Questionnaires, QuestionnaireResponses);
  - |audit_item| files created;
  - |audit_item| HL7 v2 messages sent;
  - |audit_item| REDCap exports.


|id_definitions| ID number definition management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :ref:`patient/subject identification <patient_identification>` for
background. Here, you can view and edit ID number definitions.

For existing ID number definitions, this shows

- the ID type number (e.g. 1, 2, 3...) *(note: this is the internal CamCOPS
  number representing this type, not a specific patient's ID)*;
- a description (e.g. "NHS number");
- a short description (e.g. "NHS");
- a validation method, if applicable (e.g. CamCOPS knows how to check UK NHS
  numbers for validity using their checksum method);
- for HL7 exports, the HL7 ID Type and HL7 Assigning Authority;
- for FHIR exports, the |info_internal| URL (hyperlinked) used to define this
  ID number (Patient identifier) system;
- buttons to |edit| **edit** and |delete| **delete** the ID number type.

There is also a link to |id_definition_add| **add a new ID number definition**.


|settings| Edit server settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here you can edit

- your CamCOPS server's database title.


|developer| Developer test pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows some test pages relevant to developers only.


Settings
++++++++

|upload| Choose group into which to upload data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS has a concept of "groups" (e.g. a clinical group or a research study).
Using this option, you can choose which group your CamCOPS client (tablet
device) will upload to next.


|info_internal| View your user settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Show information about your user, including:

- username
- e-mail address
- language
- group memberships (with associated permissions)


|info_internal| View server information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Show information about the server, including:

- patient identification number systems
- recent activity
- tasks available


|password_own| Change password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this option to change your password.


|mfa| Multi-factor authentication settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose your preferred multi-factor authentication (MFA) method. Your server
administrator may have enabled a subset of these, so some may be unavailable.
The full set of options is:

- Use an app such as `Google Authenticator`_ or `Twilio Authy`_.

- Send a code by e-mail.

- Send a code by SMS_ text message.

- Disable multi-factor authentication. (This is less secure!)


Help
++++

|info_external| CamCOPS documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Click “CamCOPS documentation” for this manual.



===============================================================================

.. rubric:: Footnotes

.. [#current] “Current” means that this download will skip historical versions
   of tasks that have been edited, and just provide the latest version.

.. [#icd9cm] ICD-9-CM diagnostic codes:
   https://en.wikipedia.org/wiki/List_of_ICD-9_codes_290%E2%80%93319:_mental_disorders

.. [#sqlformat]
    e.g. https://sqlformat.org/;
    https://www.freeformatter.com/sql-formatter.html

.. [#crate]
    For a software product that takes de-identification seriously, see e.g.
    CRATE, described in Cardinal RN (2017),
    https://doi.org/10.1186/s12911-017-0437-1, and available from
    https://crateanon.readthedocs.io/.

.. [#databasenormalization]
    https://en.wikipedia.org/wiki/Database_normalization
