..  docs/source/tasks/asdas.rst

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


.. _asdas:

Ankylosing Spondylitis Disease Activity Score (ASDAS)
-----------------------------------------------------

.. include:: include_data_collection_plus_local_upgrade.rst

Four numerical rating scales rated 0-10 and a measure of inflammation (either
C-reactive protein, CRP, or erythrocyte sedimentation rate, ESR).

Each question is weighted:

.. code-block:: none

  ASDAS-CRP =
                0.12 × back pain +
                0.06 × duration of morning stiffness +
                0.11 × patient global +
                0.07 × peripheral pain/swelling +
                0.58 × ln(CRP + 1)

    ... where CRP is measured in mg/L

  ASDAS-ESR =
                0.08 x back pain +
                0.07 x duration of morning stiffness +
                0.11 x patient global +
                0.09 x peripheral pain/swelling +
                0.29 x √(ESR)

    ... where ESR is measured in mm/h


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**TO BE ESTABLISHED.** Original paper (Lukas et al. 2009) is copyright 2009 BMJ
Publishing Group and European League Against Rheumatism, but status of task
itself less clear.


History
~~~~~~~

- Lukas C, Landewé R, Sieper J, Dougados M, Davis J, Braun J, van der Linden S,
  van der Heijde D (2009).
  Development of an ASAS-endorsed disease activity score (ASDAS) in patients
  with ankylosing spondylitis.
  *Ann Rheum Dis.* 68: 18-24.
  https://www.ncbi.nlm.nih.gov/pubmed/18625618


Source
~~~~~~

- https://www.asas-group.org/clinical-instruments/asdas-calculator/
- http://oml.eular.org/oml_search_results_details.cfm?id=31&action=All%20information
