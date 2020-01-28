..  docs/source/user/include_consistency_warning.rst

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

.. warning::

    Both trackers and CTVs collate information from multiple tasks. They
    therefore perform a **consistency check** to ensure that patient ID
    information is the same across all tasks. (Did someone mis-spell a name,
    for example -- or worse, mis-file information by entering the wrong ID
    number?) **Beware** if the consistency check fails; you will need to
    ensure yourself that all the data relates to the same patient.
