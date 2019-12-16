..  docs/source/administrator/redcap.rst

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

.. _asteval: http://newville.github.io/asteval/index.html

.. _redcap:

REDCap export
=============

..  contents::
    :local:
    :depth: 3


Overview
--------

REDCap is a secure web application for building and managing online surveys and
databases. For general information about REDCap, see
https://www.project-redcap.org/.

Prerequisites for exporting CamCOPS tasks to REDCap records
-----------------------------------------------------------
- There must be a REDCap user (with API key) with the following privileges:

  - API Import/Update
  - API Export

- The CamCOPS configuration file needs to have an export recipient with
  ``TRANSMISSION_METHOD = redcap`` (see :ref:`the configuration file
  <server_config_file>`) and REDCap specific settings.
- Any instruments in a REDCap record that CamCOPS exports to must be
  set up as "repeating" within the REDCap interface (under "Project Setup").

- One of the instruments must have a field to store the patient identifier.

- There must be a fieldmap XML file that tells CamCOPS how the task fields
  correspond to the REDCap instrument form fields.

Example fieldmap XML file
-------------------------

The fieldmap below describes how three CamCOPS tasks are exported to a REDCap
record for a patient. The REDCap record has three instruments: ``bmi``,
``patient_health_questionnaire_9`` and ``medication_table``, which correspond to
CamCOPS tasks :ref:`bmi <bmi>`, :ref:`phq9 <phq9>` and
:ref:`khandaker_mojo_medicationtherapy <khandaker_mojo_medicationtherapy>`
respectively. In addition there is a fourth instrument called ``patient_record``
(defined in the ``identifier`` tag), which tells CamCOPS where in REDCap to find
or store the patient identifier.

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <fieldmap>
        <identifier instrument="patient_record" redcap_field="patient_id" />
        <instruments>
            <instrument task="phq9" name="patient_health_questionnaire_9">
                <fields>
                    <field name="phq9_1" formula="task.q1" />
                    <field name="phq9_2" formula="task.q2" />
                    <field name="phq9_3" formula="task.q3" />
                    <field name="phq9_4" formula="task.q4" />
                    <field name="phq9_5" formula="task.q5" />
                    <field name="phq9_6" formula="task.q6" />
                    <field name="phq9_7" formula="task.q7" />
                    <field name="phq9_8" formula="task.q8" />
                    <field name="phq9_9" formula="task.q9" />
                    <field name="phq9_how_difficult" formula="task.q10 + 1" />
                    <field name="phq9_total_score" formula="task.total_score()" />
                    <field name="phq9_first_name" formula="task.patient.forename" />
                    <field name="phq9_last_name" formula="task.patient.surname" />
                    <field name="phq9_date_enrolled" formula="format_datetime(task.when_created,DateFormat.ISO8601_DATE_ONLY)" />
                </fields>
            </instrument>
            <instrument task="bmi" name="bmi">
                <fields>
                    <field name="pa_height" formula="format(task.height_m * 100.0, '.1f')" />
                    <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
                    <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
                </fields>
            </instrument>
            <instrument task="khandaker_mojo_medicationtherapy" name="medication_table">
                <files>
                <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
                </files>
            </instrument>
        </instruments>
    </fieldmap>

Each ``field`` tag describes how the answer for a question will be stored in
REDCap. The ``name`` attribute is the column in the database table for the task. The
``formula`` attribute is python code to process the value before it is exported.

For the formula we use the library `asteval`_, a safer version of python
``eval()``.  Whilst asteval tries hard to prevent the python interpreter from
crashing, it is still possible to write potentially destructive code so use this
with care and at your own risk!

See the `asteval`_ documentation for supported operations (`numpy
<https://numpy.org/>`_ is available).  In addition we provide access to the
following symbols:

- ``task`` (the row in the database that contains the answers)
- ``format_datetime`` (:func:`cardinal_pythonlib.datetimefunc.format_datetime`, a function for date formatting)
- ``DateFormat`` (:func:`camcops_server.cc_modules.cc_constants.DateFormat`)
- ``request`` (the CamCOPS request object, required by a number of functions)

PHQ9 example
~~~~~~~~~~~~

In the PHQ9 example, the nine main questions are simply copied over to
REDCap with no processing.

.. code-block:: xml

            <instrument task="phq9" name="patient_health_questionnaire_9">
                <fields>
                    <field name="phq9_1" formula="task.q1" />
                    <field name="phq9_2" formula="task.q2" />
                    <field name="phq9_3" formula="task.q3" />
                    <field name="phq9_4" formula="task.q4" />
                    <field name="phq9_5" formula="task.q5" />
                    <field name="phq9_6" formula="task.q6" />
                    <field name="phq9_7" formula="task.q7" />
                    <field name="phq9_8" formula="task.q8" />
                    <field name="phq9_9" formula="task.q9" />
                    <field name="phq9_how_difficult" formula="task.q10 + 1" />
                    <field name="phq9_total_score" formula="task.total_score()" />
                    <field name="phq9_first_name" formula="task.patient.forename" />
                    <field name="phq9_last_name" formula="task.patient.surname" />
                    <field name="phq9_date_enrolled" formula="format_datetime(task.when_created,DateFormat.ISO8601_DATE_ONLY)" />
                </fields>
            </instrument>

The possible answers for the tenth question (known as ``phq9_how_difficult`` on
the REDCap side) have been coded differently in REDCap (1-4 instead of 0-3) so
we need to add one to the answer.

The total score in REDCap is stored rather than calculated so to fill in this
field we call the method :meth:`camcops_server.tasks.phq9.total_score()`.

The REDCap PHQ9 instrument also stores the first and last names of the
patient. We can retrieve these from the patient table associated with the task.

Finally the REDCap PHQ9 instrument has a date field (``phq9_date_enrolled``), which
needs to be in a certain format.

BMI example
~~~~~~~~~~~

In the BMI example, the height and weight fields need to be specified to
one decimal place in REDCap so we use the python built-in ``format()`` function. In
addition, the REDCap instrument has the height in centimetres rather than metres
so we need to multiply by 100.

.. code-block:: xml

            <instrument task="bmi" name="bmi">
                <fields>
                    <field name="pa_height" formula="format(task.height_m * 100.0, '.1f')" />
                    <field name="pa_weight" formula="format(task.mass_kg, '.1f')" />
                    <field name="bmi_date" formula="format_datetime(task.when_created, DateFormat.ISO8601_DATE_ONLY)" />
                </fields>
            </instrument>

Related table / file upload example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The final instrument in the fieldmap shows one way that a task with a
one-to-many related table can be uploaded to REDCap. The
:ref:`khandaker_mojo_medicationtherapy <khandaker_mojo_medicationtherapy>` task
has a table of medications (name, dose, frequency etc) with multiple entries for
each medication. REDCap does not have direct support for this kind of
one-to-many relationship. One workaround is simply to upload a PDF of the task
contents. We achieve this by creating a file upload field in REDCap and
populating this with the output of the method ``task.get_pdf()``.

.. code-block:: xml

            <instrument task="khandaker_mojo_medicationtherapy" name="medication_table">
                <files>
                <field name="medtbl_medication_items" formula="task.get_pdf(request)" />
                </files>
            </instrument>
