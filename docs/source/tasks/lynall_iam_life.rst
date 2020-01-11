..  docs/source/tasks/lynall_iam_life.rst

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

.. _lynall_iam_life:

Lynall M-E — IAM study — life events
------------------------------------

.. include:: include_data_collection_plus_local_upgrade.rst

Life events questionnaire for the Inflammation in Mind (IAM) study.

A bespoke scale that is a version of the Brugha life events questionnaire,
modified to include cumulative adult as well as recent stress.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Based on the List of Threatening Experiences (LTE) and modified from this.

  The LTE is owned and copyrighted jointly by Prof. Terry (Traolach) Brugha and
  the Medical Research Council (MRC).

    "I have no objection to you using the LTE in your research non
    commercially. There is no need to ask the MRC for this permission.

    In principle I favour the non commercial use of the LTE by other
    researchers and only ask that they cite it in any dissemination."

    [Commercial use may require a contract with the MRC, setup of which the MRC
    have subcontracted to an agency.]

  -- Personal communication, Prof. Terry (Traolach) Brugha (University of
  Leicester) to Mary-Ellen Lynall, 2019-09-12.

  Accordingly,

  - noncommercial restriction applied in CamCOPS;

  - skeleton task plus local upgrade for now.

- Modifications by Mary-Ellen Lynall, University of Cambridge, 2019.
  Any new material: copyright © 2019 Mary-Ellen Lynall. License: Creative
  Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0):
  https://creativecommons.org/licenses/by-sa/4.0/


History
~~~~~~~

- List of Threatening Experiences:

  - Brugha T, Bebbington P, Tennant C, Hurry J (1985).
    The List of Threatening Experiences: a subset of 12 life event categories
    with considerable long-term contextual threat.
    Psychological Medicine 15: 189-194.
    https://www.ncbi.nlm.nih.gov/pubmed/3991833

  - Brugha TS, Cragg D (1990).
    The List of Threatening Experiences: the reliability and validity of a
    brief life events questionnaire.
    *Acta Psychiatr Scand.* 82: 77-81.
    https://www.ncbi.nlm.nih.gov/pubmed/2399824

    Defines the LTE-Q, the questionnaire version of the life events instrument,
    consisting (as before) of 12 categories of common life events that are
    highly likely to be threatening. No definitive scoring system is described.

- See also:

  - Rosmalen JGM, Bos EH, de Jonge P (2012).
    Validation of the Long-Term Difficulties Inventory (LDI) and the List of
    Threatening Experiences (LTE) as measures of stress in epidemiological
    population-based cohort studies.
    Psychological Medicine 42: 2599–2608.
    https://www.ncbi.nlm.nih.gov/pubmed/22490940

    Uses a scoring system of "the total number of items endorsed" (out of 12).


Source
~~~~~~

- Mary-Ellen Lynall, personal communication to Rudolf Cardinal (e.g.
  2019-04-30).

- The IAM/Life Events version asks occurrence within the last 6 months; then
  about severity of index event and frequency (since age 18) for each category
  of event endorsed.

- The differences in categories from the LTE are:

  ================================================= =============================================================
  LTE-Q category                                    IAM/Life Events category
  ================================================= =============================================================
  1: Illness/injury/assault (self)                  [1: same]
  2: Illness/injury/assault (relative)              [2: same]
  3: Parent/child/spouse died                       [3: same except includes siblings]
  4: Close family friend/other relative died        [4: same, given 3]
  5: Marital separation                             5: marital separation or broke off relationship
  6: Broke off a steady relationship                [incorporated into 5]
  --                                                6: ended long-lasting friendship with close friend/relative
  7: Problems with close friend/neighbour/relative  [7: same]
  8: Unemployment or unsuccessful job-seeking 1mo+  8: unsuccessful job-seeking 1mo+
  9: Sacked                                         [9: same: sacked/made redundant]
  10: Financial crisis                              [10: same]
  11: Police with court appearance                  [11: same]
  12: Something lost/stolen                         [12: same]
  --                                                13: Self/partner gave birth
  --                                                14: Other
  ================================================= =============================================================

  *Note: in the draft IAM/Life (prior to 2019-09-15), 8 was "sacked" and 9 was
  "unsuccessful job-seeking"; transposed on 2019-09-15 for better consistency
  with original LTE-Q.*
