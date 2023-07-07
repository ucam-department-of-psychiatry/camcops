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


Counterbalancing
~~~~~~~~~~~~~~~~

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
