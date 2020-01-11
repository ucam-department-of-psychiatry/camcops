..  docs/source/tasks/elixhauserci.rst

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


.. _elixhauserci:

Elixhauser Comorbidity Index (ElixhauserCI)
-------------------------------------------

A count (0-31) of the number of categories of comorbidity that someone has,
based on the :ref:`International Classification of Diseases <diagnosis_icd10>`.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The paper Quan et al. (2005), which develops the mapping from ICD-10 codes to
disease categories, is copyright © 2005 Lippincott Williams & Wilkins. The
comorbidity terms (e.g. "congestive heart failure") are themselves believed to
be in the public domain. The ICD-10 codes (which are owned by the WHO; see
:ref:`ICD-10 diagnostic coding <diagnosis_icd10>`) are not used in the CamCOPS
version of the task, which justs asks clinicians to score presence/absence.


History
~~~~~~~

- Elixhauser A, Steiner C, Harris DR, Coffey RM (1998).
  Comorbidity measures for use with administrative data.
  *Med Care.* 36: 8-27.
  https://www.ncbi.nlm.nih.gov/pubmed/9431328

  [Original 30-item version using ICD-9-CM codes.]

- Subsequent updates as per
  http://mchp-appserv.cpe.umanitoba.ca/viewConcept.php?printer=Y&conceptID=1436,
  including:

  - Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD,
    Beck CA, Feasby TE, Ghali WA (2005).
    Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10
    administrative data.
    *Med Care.* 43: 1130-9.
    https://www.ncbi.nlm.nih.gov/pubmed/16224307

    [This paper extends Elixhauser et al. (1998) to ICD-10 codes, developing an
    ICD-10 coding algorithm.]


Source
~~~~~~

- http://mchp-appserv.cpe.umanitoba.ca/viewConcept.php?printer=Y&conceptID=1436
