..  documentation/source/server/server_front_end_general.rst

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

.. _website_general:

Web site: general use
=====================

Log into CamCOPS via a web browser.

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
you can restrict to completed tasks. You can also specify text contents. For
example, type in “paracetamol” to find clerkings that mention paracetamol
anywhere.

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

The HTML view is fastest and has additional viewing options. However, you
should **not** print the HTML view in a clinical environment, because it won’t
have patient identifiers on each page. Use the PDF for that instead, or if you
want to save the task as a single human-readable file.

When you view a task in HTML mode, there are some additional hyperlinks at the
bottom:

- *View raw data as XML.* This shows you the raw structure as XML, including
  stored data and calculated fields such as summary scores. One useful feature
  is that all fields have an associated comment, and these comments are
  displayed in the XML.

- *View anonymised version (HTML, PDF).* This shows you a version with patient
  identification details hidden. It is not guaranteed to be free of identifying
  material, though; it makes no effort to remove patient details from free
  text, for example [#crate]_.

- *View PDF.* A link to the PDF version.

(Administrators have additional options; see :ref:`administrative options
<task_admin>`.)

PDF versions include patient identifiers on each page, to meet normal UK
clinical standards, and if the task involved recording a clinician’s views or
assessments, the PDF will include a template signature box for on-paper
authentication by the clinician.

Specimen tasks in PDF format:

- :download:`PHQ-9 <demotasks/dummy_task_1.pdf>`
- :download:`Psychiatric clerking <demotasks/dummy_task_2.pdf>` (albeit not a
  very good one!)

.. http://www.sphinx-doc.org/en/stable/markup/inline.html#referencing-downloadable-files

Trackers for numerical information
----------------------------------

Many tasks produce numerical information, like total scores. Trackers allow you
to view numerical information from these tasks, or a subset of them, over time.
The resulting graphs are time-aligned within the tracker, across all tasks
(i.e. all graphs have the same time axis).

Not all tasks offer trackers.

Some tasks offer more than one numerical value, and therefore provide more than
one graph.

To configure a tracker, choose a patient by an ID number. You can, optionally,
specify a start and/or end date, and you can restrict to specific tasks.

You can view trackers in HTML or PDF mode, or view the data used to generate
them in XML format.

Specimen tracker:

- :download:`Fictional tracker <demotasks/dummy_tracker.pdf>`

.. include:: include_consistency_warning.rst

Clinical text views
-------------------

Like a tracker, a clinical text view (CTV) collects information across many
tasks for one patient. Like a tracker, a CTV is configured for a patient, and
can be configured for a date range and/or a subset of tasks. Like a tracker
(and like a book), a CTV flows from older to newer information. Unlike a
tracker, a CTV produces text for each task, not numbers. The text is intended
to be clinically useful. For example, simple questionnaires produce their
summary information. The ACE-III produces its total but also its subscale
scores. Clinical clerkings produce their full text. All tasks appear in the
CTV, but some tasks simply indicate that they have been performed.

In the HTML view of a CTV, all tasks provide hyperlinks to the full
representation of each task, so you can delve into more detail for any task of
interest.

Specimen CTV:

- :download:`Fictional CTV <demotasks/dummy_clinicaltextview.pdf>`

.. include:: include_consistency_warning.rst

Research views
--------------

.. _summary_fields:

Basic research dump (fields and summaries)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic research dump generates a ZIP file. The ZIP file contains one TSV
(tab-separated value) file for every current task [#current]_, and includes raw
data and summary measures (e.g. total scores).

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

Dump table data as SQL
~~~~~~~~~~~~~~~~~~~~~~

This more sophisticated research dump generates a fully structured SQLite binary
database of the data you select (or, if you prefer, the SQL text to create it).
By default, BLOBs (binary large objects) are skipped, because they can be very
large, but if you want, you can choose to include them.

You can choose the information you want exactly as for the basic research dump.

Some user information will be provided (e.g. user names), but security
information (e.g. passwords) is removed prior to the download.

As for the basic research dump, summary information is added to tables as they
are created. For example: the internal :ref:`PHQ9 <phq9>` table contains scores
for individual questions, but not the total (which is calculated dynamically).
When you download the data, the total (amongst other things) is calculated and
added to the data that you download (within the SQLite table or CSV file).

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

.. _introspection:

Introspection
-------------

CamCOPS allows direct introspection of the server’s source code (the version
that it is running as you use it) and the tablet source code (the version that
was current when the server was built).

The server is primarily written in Python (.py files). The client is primarily
written in C++ (.h and .cpp files). Many tasks keep their string information in
XML (.xml) files.

For example, to see how the :ref:`PHQ-9 <phq9>` task works, look for `phq9.h`
and `phq9.cpp` (client), `phq9.py` (server), and `phq9.xml` (strings).

For the latest source code, see the CamCOPS GitHub repository [#github]_.

Help
----

Click “CamCOPS documentation” for this manual.

Log out
-------

Click “Log out” to end your CamCOPS session.


.. rubric:: Footnotes

.. [#current] “Current” means that this download will skip historical versions of
   tasks that have been edited, and just provide the latest version.

.. [#icd9cm] ICD-9-CM diagnostic codes:
   https://en.wikipedia.org/wiki/List_of_ICD-9_codes_290%E2%80%93319:_mental_disorders

.. [#sqlformat]
    e.g. https://sqlformat.org/;
    https://www.freeformatter.com/sql-formatter.html

.. [#github] https://github.com/RudolfCardinal/camcops

.. [#crate]
    For a software product that takes de-identification seriously, see e.g.
    CRATE, described in Cardinal RN (2017),
    https://doi.org/10.1186/s12911-017-0437-1, and available at
    https://github.com/RudolfCardinal/crate.

.. [#databasenormalization]
    https://en.wikipedia.org/wiki/Database_normalization
