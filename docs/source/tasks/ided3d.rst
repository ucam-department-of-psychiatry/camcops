..  docs/source/tasks/ided3d.rst

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

.. _ided3d:

Three-dimensional intradimensional/extradimensional set-shifting task (IDED3D)
------------------------------------------------------------------------------

Source
~~~~~~

From Rogers RD et al. (1999), Psychopharmacology 146: 482, PMID
https://www.pubmed.gov/10550499.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- De novo task code; part of the CamCOPS intellectual property.

- Some stimuli redrawn from original task (by RD Rogers, University of
  Cambridge, 1995-1999).


Settings
~~~~~~~~

When assigning this task to a patient as part of a :ref:`task schedule
<scheduling_tasks>`, the task may be configured with the following JSON
settings. For example:


.. code-block:: json

    {
        "ided3d": {
            "last_stage": 8,
            "max_trials_per_stage": 50,
            "progress_criterion_x": 6,
            "progress_criterion_y": 6,
            "min_number": 1,
            "max_number": 9,
            "pause_after_beep_ms": 500,
            "iti_ms": 500,
            "counterbalance_dimensions": 4,
            "volume": 0.5,
            "offer_abort": false
        }
    }

Here is a description of each setting:

.. glossary::

    last_stage
        Last stage to use (1 [SD] – 8 [EDR]). Default 8.

        The stages are:

        1. simple discrimination (SD)
        2. reversal of previous SD stage (SDr)
        3. compound discrimination (CD)
        4. reversal of previous CD stage (CDr)
        5. intradimensional shift (ID)
        6. reversal of previous ID stage (IDr)
        7. extradimensional shift (ED)
        8. reversal of previous ED stage (EDr)

    max_trials_per_stage
        Maximum number of trials per stage (abort if this reached without
        success). Default 50.

    progress_criterion_x
        Criterion to proceed to next stage: X correct out of the last Y trials,
        where this is X. Default 6.

    progress_criterion_y
        Criterion to proceed to next stage: X correct out of the last Y trials,
        where this is Y. Default 6.

    min_number
        Minimum number of stimuli [1–9]. Default 1.

    max_number
        Maximum number of stimuli [1–9]. Default 9.

    pause_after_beep_ms
        Time to continue visual feedback after auditory feedback finished (ms).
        Default 500.

    iti_ms
        Intertrial interval (ITI) (ms). Default 500.

    counterbalance_dimensions
        Dimension counterbalancing [0–5]. See :ref:`Counterbalancing
        <ided3d_counterbalancing>`. No default.

    volume
        Volume [0-1]. Default 0.5

    offer_abort
        Offer the user an abort button. Default false.


In clinician mode, the user may change these settings before starting the
task. In single-user mode, if all of the settings have valid values (as a
minimum `counterbalance_dimensions` must be set), the user will not be able to
change these settings and the task will start immediately.


.. _ided3d_counterbalancing:

Counterbalancing
################

The counterbalancing options are:

* Counterbalancing 0: dimensions shape, colour, number
* Counterbalancing 1: dimensions colour, number, shape
* Counterbalancing 2: dimensions number, shape, colour
* Counterbalancing 3: dimensions shape, number, colour
* Counterbalancing 4: dimensions colour, shape, number
* Counterbalancing 5: dimensions number, colour, shape

Python code equivalent to the actual code used in ``IDED3D::makeStages()``:

.. code-block:: python

    poss_dimensions = ["shape", "colour", "number"]
    # ... from Exemplars::possibleDimensions()
    n_dimensions = len(poss_dimensions)
    for cb_dim in range(0, 5 + 1):
        cb1max = n_dimensions
        cb2max = n_dimensions - 1
        cb1 = cb_dim % cb1max
        cb2 = (cb_dim // cb1max) % cb2max
        first_dim_index = cb1
        second_dim_index = (first_dim_index + 1 + cb2) % n_dimensions
        third_dim_index = (first_dim_index + 1 + (cb2max - 1 - cb2)) % n_dimensions
        print(
            f"Counterbalancing {cb_dim}: dimensions "
            f"{poss_dimensions[first_dim_index]}, "
            f"{poss_dimensions[second_dim_index]}, "
            f"{poss_dimensions[third_dim_index]}"
        )
