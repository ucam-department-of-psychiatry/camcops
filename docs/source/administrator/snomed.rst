..  docs/source/administrator/snomed.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
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

.. _Athena OHDSI: http://athena.ohdsi.org
.. _IHTSDO: https://en.wikipedia.org/wiki/International_Health_Terminology_Standards_Development_Organisation
.. _NHS: https://www.nhs.uk/
.. _SNOMED International: http://www.snomed.org/
.. _SNOMED CT: https://en.wikipedia.org/wiki/SNOMED_CT
.. _Systematized Nomenclature of Medicine: https://en.wikipedia.org/wiki/Systematized_Nomenclature_of_Medicine

.. _snomed:

SNOMED CT coding
================

..  contents::
    :local:
    :depth: 3


Overview
--------

`SNOMED CT`_ (`Systematized Nomenclature of Medicine`_ Clinical Terms) is a
structured computer-oriented vocabulary for medicine. It is owned by IHTSDO_,
who trade as `SNOMED International`_.

It is the standard computerized vocabulary for the UK NHS_.

CamCOPS supports SNOMED CT coding for:

- its tasks (where those tasks are supported by SNOMED CT)

- ICD-9-CM codes [recorded by the :ref:`Diagnostic coding (ICD-9-CM)
  <diagnosis_icd9cm>` task]

- ICD-10 codes [recorded by the :ref:`Diagnostic coding (ICD-10)
  <diagnosis_icd10>` task]

For example, the XML representation of a :ref:`PHQ-9 <phq9>` task might include
output like this:

.. code-block:: xml

    <snomed_ct_codes>
        <snomed_ct_expression xsi:type="string">
            715252007 |Depression screening using Patient Health Questionnaire Nine Item score (procedure)|
        </snomed_ct_expression>
        <snomed_ct_expression xsi:type="string">
            758711000000105 |Patient health questionnaire 9 (assessment scale)| : 720433000 |Patient Health Questionnaire Nine Item score (observable entity)| = #1
        </snomed_ct_expression>
        <snomed_ct_expression xsi:type="string">
            112011000119102 |Negative screening for depression on Patient Health Questionnaire 9 (finding)|
        </snomed_ct_expression>
    </snomed_ct_codes>


Licensing
---------

SNOMED CT is owned by the IHTSDO_ but is free to use within the UK, subject to
registration; see
https://digital.nhs.uk/services/terminology-and-classifications/snomed-ct. The
licensing agreement from https://termbrowser.nhs.uk/ is reproduced :ref:`here
<licence_snomed>` but the original should always be checked. It may not be free
elsewhere.

It is not permitted to distribute SNOMED CT generally; users must accept the
license terms and obtain the SNOMED CT identifiers separately. CamCOPS does not
contain SNOMED CT identifiers (it uses arbitrary strings to reference them).


Adding SNOMED CT support to CamCOPS
-----------------------------------

If you are permitted (see "Licensing" above), find a SNOMED CT REST API server
(e.g. from your national provider) and ask it for relevant SNOMED CT
identifiers using the :ref:`camcops_fetch_snomed_codes
<camcops_fetch_snomed_codes>` tool, creating ``camcops_tasks_snomed.xml``.

This file can then be plugged into the following parameter of the :ref:`server
configuration file <server_config_file>`:

.. code-block:: ini

    SNOMED_TASK_XML_FILENAME = /some_path/camcops_snomed_ct_codes/camcops_tasks_snomed.xml


Adding SNOMED CT support for ICD-9-CM and ICD-10 to CamCOPS
-----------------------------------------------------------

This requires additional data.

There are a few maps from ICD to SNOMED available, including:

- https://www.nlm.nih.gov/research/umls/mapping_projects/icd9cm_to_snomedct.html
- https://www.nlm.nih.gov/research/umls/mapping_projects/snomedct_to_icd10cm.html
- http://athena.ohdsi.org

CamCOPS supports the `Athena OHDSI`_ (pronounced "odyssey") datasets. Use it as
follows.

- Visit http://athena.ohdsi.org.
- Register and log in.
- "Download"
- Untick everything, then tick:

  - ICD9CM
  - ICD9Proc
  - ICD10

- "Download vocabularies"
- Unzip the result.

You will find files including ``CONCEPT.csv`` and ``CONCEPT_RELATIONSHIP.csv``.
(Despite their names, they are tab-separated-value [TSV] files, not
comma-separated-value [CSV] files.)

Since some of these files are quite large (e.g. ~10 million rows), CamCOPS
preprocesses them into smaller XML files covering the codes it cares about.
Convert with a script like this:

.. code-block:: bash

    #!/usr/bin/env bash

    ATHENA_ROOT=/some_path/Athena/unzipped
    CAMCOPS_SNOMED_DIR=/some_path/camcops_snomed_ct_codes

    camcops_server convert_athena_icd_snomed_to_xml \
        --athena_concept_tsv_filename ${ATHENA_ROOT}/CONCEPT.csv \
        --athena_concept_relationship_tsv_filename ${ATHENA_ROOT}/CONCEPT_RELATIONSHIP.csv \
        --icd9_xml_filename ${CAMCOPS_SNOMED_DIR}/icd9_snomed.xml \
        --icd10_xml_filename ${CAMCOPS_SNOMED_DIR}/icd10_snomed.xml

This will make two XML files. They can now be plugged into the following
parameters of the :ref:`server configuration file <server_config_file>`:

.. code-block:: ini

    SNOMED_ICD9_XML_FILENAME = /some_path/camcops_snomed_ct_codes/icd9_snomed.xml
    SNOMED_ICD10_XML_FILENAME = /some_path/camcops_snomed_ct_codes/icd10_snomed.xml


.. note::

    Not every ICD-9-CM or ICD-10 code has SNOMED CT equivalents (at least in
    the Athena OHDSI data of Dec 2018). Some have more than one code (of which
    CamCOPS will return all).
