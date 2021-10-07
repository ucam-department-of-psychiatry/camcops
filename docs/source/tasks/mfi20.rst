..  docs/source/tasks/mfi20.rst

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


.. _mfi20:

Multidimensional Fatigue Inventory (MFI-20)
-------------------------------------------

.. include:: include_permission_contextual.rst

20 questions rated on a 5-point scale (1 = "yes, that is true" to 5 = "no, that
is not true").

Items are scored 1–5, with 10 [fatigue-]positively phrased items reverse scored
(items 2, 5, 9, 10, 13, 14, 16, 17, 18, 19). In the final score, high scores
represent more fatigue.

Total score calculated for 5 subscales:

- general fatigue (items 1, 5, 12, 16);
- physical fatigue (items 2, 8, 14, 20);
- reduced activity (items 3, 6, 10, 17);
- reduced motivation (items 4, 9, 15, 18);
- mental fatigue (items 7, 11, 13, 19).


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- "The MFI-20 is copyrighted on the names of the authors. The MFI is free for
  academic use, charges apply for commercial use. For further information, the
  developers can be contacted."
  [http://oml.eular.org/oml_search_results_details.cfm?id=119&action=All%20information,
  2020-02-07]

  - Thus, copyright 1995 Ellen Smets and colleagues.

- Permission given by the lead author, Prof. Smets, 3 Feb 2020 (personal
  communication, as below).

- Restricted to research and educational use as per the copyright holder's
  instructions (as below).


.. code-block:: none

    From: Smets, E.M.A. (Ellen) [...]
    Sent: 03 February 2020 17:01
    To: Joel Parkinson [...]
    Subject: RE: MFI-20 permission

    Dear Joel,

    Thank you for your interest in incorporating the MFI in CamCops. You
    herewith have my permission to do so. Although I realize it depends on the
    trustworthiness of the end-user, I would prefer tasks including the MFI to
    be restricted to researchers en educators.

    I hope you helps.

    Kind regards,

    Ellen Smets

    Prof. dr. Ellen Smets
    Department of Medical Psychology
    Location AMC | J3-220 | Meibergdreef 9, 1105 AZ Amsterdam
    [...]
    www.amsterdamumc.nl | www.vumc.nl / www.amc.nl


    Van: Joel Parkinson <[...]cam.ac.uk>
    Verzonden: woensdag 29 januari 2020 14:50
    Aan: Smets, E.M.A. (Ellen) [...]
    Onderwerp: MFI-20 permission


    Dear Professor Smets,

    We are very interested in incorporating the Multidimensional Fatigue
    Inventory into CamCOPS (https://camcops.readthedocs.io/), and wonder
    whether you might permit this.

    Our understanding of the copyright status of the MFI-20 is:

    · It is copyrighted on the names of the authors.
    · It is free for academic use.

    May we ask if that is correct?

    CamCOPS is free and open-source software for capturing structured data
    relevant to psychiatry directly from patients, clinicians, and researchers.
    It was developed in the University of Cambridge, UK, and is in use for
    clinical and research purposes. Data flow is entirely under the control of
    the hosting institution. CamCOPS implements both open/free tasks and
    closed/restricted tasks using one of the following methods:

    · Open/free tasks are embedded into CamCOPS directly; this is our preferred
      method.

    · Some tasks may be permitted to some institutions but not others. These
      can be implemented via a public “skeleton” in CamCOPS (with no task
      content) and a “plugin” containing the task content (e.g. text for a
      questionnaire) that licensed users can add to their CamCOPS installation,
      converting the skeleton into a fully working copy.

    · Some closed tasks do not permit electronic reproduction. Sometimes, these
      still benefit from an electronic data capture “skeleton” that never
      includes task content, but is still preferable to paper capture and
      manual (laborious and error-prone) transcription. The electronic skeleton
      can then be used in conjunction with a licensed paper copy of the task.

    In addition, all CamCOPS tasks can be restricted if necessary according to
    flags that the end user can set: clinical use? Research use? Educational
    use? Commercial use? For example, a task can be restricted to noncommercial
    use only (though this relies on end-user honesty and end-user liability).

    Would it be permissible for us to incorporate the MFI-20 into CamCOPS,
    using one of the above methods? We’d be most grateful.

    Thank you for your time in considering this. If you have any questions or
    if there is anything I can clarify, please just let me know.

    Yours sincerely,

    Joel Parkinson
    [...]


History
~~~~~~~

- Smets E, Garssen B, Bonke Bd, De Haes J (1995).
  The Multidimensional Fatigue Inventory (MFI): psychometric qualities of an
  instrument to assess fatigue.
  *Journal of Psychosomatic Research* 39: 315-25.
  https://www.ncbi.nlm.nih.gov/pubmed/7636775

- Smets EM, Garssen B, Cull A, de Haes JC (1996).
  Application of the multidimensional fatigue inventory (MFI-20) in cancer
  patients receiving radiotherapy.
  *Br J Cancer* 73: 241-5.
  https://www.ncbi.nlm.nih.gov/pubmed/8546913


Modifications
~~~~~~~~~~~~~

- Original scoring (from 2019-07-19) was as follows:

  "Items are scored 1–5, with 10 positively phrased items reverse scored (items
  2, 5, 9, 10, 13, 14, 16, 17, 18, 19). Total score calculated for 5 subscales:
  general fatigue (items 1, 5, 12, 16), physical fatigue (items 2, 8, 14, 20),
  reduced activity (items 7, 11, 13, 19), reduced motivation (items 3, 6, 10,
  17), and mental fatigue (items 4, 9, 15, 18)."

  Per https://github.com/RudolfCardinal/camcops/issues/199, from
  https://github.com/pjbulls, on 7 Sep 2021:

  The grouping of MFI-20 questions into categories (general, physical,
  motivation...) is not in line with literature, which almost invariably uses
  the following:

  - General [Fatigue] = items 1, 5, 12, 16 *[same as our original]*
  - Physical [Fatigue] = items 2, 8, 14, 20 *[same as our original]*
  - Reduced Activit[y] = items 3, 6, 10, 17 *[this list was "reduced motivation" previously]*
  - [Reduced] Motivation = items 4, 9, 15, 18 *[this list was "mental fatigue" previously]*
  - Mental [Fatigue] = items 7, 11, 13, 19 *[this list was "reduced activity" previously]*

  Example references include:

  - https://doi.org/10.1002/msc.124
    = Goodchild et al. (2008), https://pubmed.ncbi.nlm.nih.gov/18085596/,
    esp. Table 3;

  - https://doi.org/10.1016/j.parkreldis.2012.01.024
    = Elbers et al. (2012), https://pubmed.ncbi.nlm.nih.gov/22361576/,
    esp. Table 3;

  - https://doi.org/10.1007/s10597-014-9746-3
    = Hedlund et al. (2015), https://pubmed.ncbi.nlm.nih.gov/24972909/,
    esp. Table 1.

  The changes are clearly correct and our previous version clearly wrong.
  Changes implemented 2021-10-07. No changes are made to the underlying data;
  this merely alters its presentation in summary views.

  Also (simultaneously) fixed minor typo: "keep my thought on it" --> "keep my
  thoughts on it" in Q7.


Source
~~~~~~

- http://oml.eular.org/oml_search_results_details.cfm?id=119&action=All%20information
