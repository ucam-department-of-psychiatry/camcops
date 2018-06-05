..  documentation/source/server/server_front_end.rst

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

.. _serverfrontend:

Using the server’s web front end
================================

General navigation
------------------

Any time you see the CamCOPS logo (it’s at the top of most pages), you can
click it to get back to the main menu.

Task, trackers, and clinical text views
---------------------------------------

Client devices upload *tasks*. You can view these individually in a variety of
formats. You can also view numeric information over time for a patient in a
tracker, and clinically relevant textual information for a patient in a
*clinical text view*.

Set task filters
----------------

You can configure your CamCOPS session to filter tasks according to *who*,
*what*, *when*, and *administrative criteria*. By default, no task filters are
set.

Under *who*, you can specify an optional patient forename, surname, date of
birth, sex, or any form of ID number in use on your server.

Under *what*, you can restrict to any subset of task types, and if you wish
restrict to completed tasks.

Under *when*, you can specify start and/or end dates, to find tasks in that
date range.

Under *administrative criteria*, you can restrict to specific uploading devices
or users, or the group to which a task belongs.

As well as a “set filters” button, there is a “clear” button to clear all
current filters.

View tasks
----------

This page shows all tasks meeting your current filter criteria. Each task has
hyperlinks to an HTML and a PDF version. Sometimes tasks are colour-coded
(there’s a key at the bottom of the page).

When you view a task in HTML mode, there are some additional hyperlinks at the
bottom:

- *View raw data as XML*. This shows you the raw structure as XML, including
  stored data and calculated fields such as summary scores. One useful feature
  is that all fields have an associated comment, and these comments are
  displayed in the XML.

- *View PDF*. PDF versions include patient identifiers on each page, to meet
  normal UK clinical standards, and if the task involved recording a clinician’s
  views or assessments, the PDF will include a template signature box for
  on-paper authentication by the clinician.

*Hidden feature*: if you add “:code:`&anonymise=True`” to the URL, patient
details will be obscured.
.. TODO: ... Offer this explicitly?

Some users will have some of these additional options:

- *Apply special note*. This allows you to apply a textual note to a task,
  which will be displayed alongside it in the future. (For example, you could
  use this feature to mark a task’s content as disputed, if you are prohibited
  by policy from deleting data.)

- *Edit patient details*. This allows you to edit the patient record for this
  task, and others created alongside it on the same client device (e.g. if
  someone has misspelled a name).

- *Erase task instance*. This deletes the task’s data (leaving the empty task
  structure as a placeholder).

Trackers for numerical information
----------------------------------

Many tasks produce numerical information, like total scores. Trackers allow you
to view numerical information from these tasks, or a subset of them, over time.
The resulting graphs are time-aligned within the tracker, across all tasks (i.e.
all graphs have the same time axis).

Not all tasks offer trackers.

Some tasks offer more than one numerical value, and therefore provide more than
one graph.

To configure a tracker, choose a patient by an ID number. You can, optionally,
specify a start and/or end date, and you can restrict to specific tasks.

You can view trackers in HTML or PDF mode, or view the data used to generate
them in XML format.

Clinical text views
-------------------

Like a tracker, a clinical text view (CTV) collects information across many
tasks for one patient. Like a tracker, a CTV is configured for a patient, and
can be configured for a date range and/or a subset of tasks. Like a tracker (and
like a book), a CTV flows from older to newer information. Unlike a tracker, a
CTV produces text for each task, not numbers. The text is intended to be
clinically useful. For example, simple questionnaires produce their summary
information. The ACE-III produces its total but also its subscale scores.
Clinical clerkings produce their full text. Some tasks simply indicate that they
have been performed.

In the HTML view of a CTV, all tasks provide hyperlinks to the full
representation of each task, so you can delve into more detail for any task of
interest.

Research views
--------------

Basic research dump (fields and summaries)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic research dump generates a ZIP file. The ZIP file contains one TSV
(tab-separated value) file for every current task [#f1]_, and includes raw data
and summary measures (e.g. total scores).

You can choose to dump everything that you have permission for, or restrict to
the criteria you’ve set in your current session filter, or specify tasks and/or
groups manually.

Dump table data as SQL
~~~~~~~~~~~~~~~~~~~~~~

This more sophisticated research dump generates a fully structured SQLite binary
database of the data you select (or, if you prefer, the SQL text to create it).
By default, BLOBs (binary large objects) are skipped, because they can be very
large, but if you want, you can choose to include them.

You can choose the information you want exactly as for the basic research dump.

Some user information will be provided (e.g. user names), but security
information (e.g. passwords) is removed prior to the download.

Inspect table definitions
~~~~~~~~~~~~~~~~~~~~~~~~~

This option allows you to view the database structure of the CamCOPS server
database, as data definition language (DDL), meaning the subset of SQL used to
create tables. In SQL dialects that support it (e.g. MySQL), the DDL contains
comments for every field, usually in considerable detail, so viewing the DDL
this is a good way of understanding how CamCOPS tasks store their data.

Reports
-------

CamCOPS has a set of build-in reports; for example, to count tasks, or list
client devices, or find patients by diagnostic inclusion/exclusion criteria. You
can explore and run these from the Reports menu.

Reports are used in two stages: (1) configure, (2) run.

The configuration stage provides an interface to select options for the report.
This generally includes the output format (e.g. HTML, TSV), and sometimes much
more (e.g. for the reports to find patient by diagnosis). Once you’ve chosen the
options, click “View Report”. What the configuration stage actually does is to
generate a URL for the final report.

The HTML view of the report shows the configuration parameters, the results
(page by page), and the SQL used to generate the report.

The TSV option gives you the data in tab-separate values (TSV) format.

When you view the report in HTML format, you will see that the browser’s URL
contains your report configuration information. This means that you can save
this report for later.

For example, suppose you regularly want to find patients between the ages of 20
to 65 inclusive, with an ICD-9-CM inclusion diagnosis of depression (e.g. 311)
[#f2]_, excluding bipolar affective disorder (e.g. anything starting 296) or
eating disorders (e.g. 307.1). You could create a report with these age
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
formatter [#f3]_.

Group administrator options
---------------------------

These options are only available to users who are marked as administrators for
one or more groups.

View/manage users
~~~~~~~~~~~~~~~~~

Superusers can add, edit, and delete all users.

Group administrators can add users to their group, and edit/delete users who are
in a group that they administer.

The following are *user* attributes:

- username
- password, and whether this must be changed at next login
- full name
- email
- group membership(s)

The following are attributes of the *user—group association*, i.e. apply
separately to each group the user is in:

- permission to upload from tablets and other client devices
- permission to register tablet/client devices
- permission to log in to the server’s web front end
- permission to browse records from all patients when no patient filter is set (if disabled, no records appear in this circumstance)
- permission to perform bulk research data dumps
- permission to run reports
- permission to add special notes to tasks

When adding a user, make sure you give them permission to log in, for at least
one group, if you want them to be able to use the web front end! (You don’t have
to do this, though – for example, some users may have permission only to upload
from tablets, not use the server web interface.)

.. note::

    Groupadmins can’t currently change passwords for their users, but the
    editing screen makes it look like they should. And they should, probably; that
    would be tedious for the superuser otherwise. TODO: Fix this.

Delete patient entirely
~~~~~~~~~~~~~~~~~~~~~~~

This allows you to delete a patient (as identified by an ID number of your
choosing) from a specified group. This operation is IRREVERSIBLE, so a number of
confirmation steps are required.

Forcibly preserve/finalize records for a device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Client devices (tablets, or desktop clients) should finalize their own records.
“Finalizing” means saying to the server “I have finished editing these; they’re
all yours.” Tablets erase tasks locally when they finalize them (to minimize the
amount of information stored on mobile devices), though they sometimes keep a
copy of patient/subject identifiers to save typing later if the same patients
will be re-assessed.

If a device is somehow disrupted – broken, CamCOPS uninstalled, device lost
[#f4]_ – then you might need to tell the server that the client will no longer
be editing these data. That’s what “forcibly finalizing” is.

Superuser options
-----------------

These options are only available to users with the superuser flag set.

.. _view_manage_groups:

View/manage groups
~~~~~~~~~~~~~~~~~~

This option allows you to define ID policies for groups, and to configure which
groups have intrinsic permission to see which other groups (if any). See
:ref:`Groups <groups>`.

View audit trail
~~~~~~~~~~~~~~~~

View the CamCOPS audit trail (optionally, filtering it according to a range of
criteria).

View HL7 message log
~~~~~~~~~~~~~~~~~~~~

View a log of outbound HL7 messages that CamCOPS has sent (along with their
success/failure status).

View HL7 run log
~~~~~~~~~~~~~~~~

View a log of HL7 runs. A run is when CamCOPS checks to see if any HL7 messages
should be sent. Each message belongs to a run. An individual run may cause zero,
one, or many messages to be sent.

View/edit ID number definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamCOPS supports multiple simultaneous ID numbers. For example:

=============== =========================== =================
ID type number  Description                 Short description
=============== =========================== =================
1               NHS number                  NHS
2               CPFT RiO number             CPFT
3               CUH MRN                     CUH
4               Smith group research ID     RIDSmith
99              Jones group research ID     RIDJones
=============== =========================== =================

You can create and edit these definitions here. When you edit them, there are a
few additional options for HL7 messaging.

Edit server settings
~~~~~~~~~~~~~~~~~~~~

You can set the server’s master database title here. The title is displayed to
all users using the database.

Developer test page
~~~~~~~~~~~~~~~~~~~

This is a page offering server test options; it’s not for general use.

Settings
--------

Show database/server settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows the server’s ID number definitions, which extra string families are
present, and which tasks the server knows about.

Change password
~~~~~~~~~~~~~~~

This should be self-explanatory!

Choose group into which to upload data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When one of your tablets or other client devices (i.e. a client device using
your username) uploads data to this CamCOPS server, it will store its patient
and task details in a group. Which group should this be? You get to choose here,
from the groups that you are a member of (and have permission to upload into).

Show your user settings
~~~~~~~~~~~~~~~~~~~~~~~

This shows details about your user (including group memberships).

Introspection
-------------

CamCOPS allows direct introspection of the server’s source code (the version
that it is running as you use it) and the tablet source code (the version that
was current when the server was built).

The server is primarily written in Python (.py files). The client is primarily
written in C++ (.h and .cpp files).

For the latest source code, see the CamCOPS GitHub repository [#f5]_.

Help
----

Click “CamCOPS manual” for a PDF version of this manual.

Log out
-------

Click “Log out” to end your CamCOPS session.


.. rubric:: Footnotes

.. [#f1] “Current” means that this download will skip historical versions of
   tasks that have been edited, and just provide the latest version.

.. [#f2] ICD-9-CM diagnostic codes:
   https://en.wikipedia.org/wiki/List_of_ICD-9_codes_290%E2%80%93319:_mental_disorders

.. [#f3] e.g.
    https://sqlformat.org/;
    https://www.freeformatter.com/sql-formatter.html

.. [#f4] A disaster; you should hope that the device was encrypted and be
   slightly relieved that CamCOPS data itself is.

.. [#f5] https://github.com/RudolfCardinal/camcops
