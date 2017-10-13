/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "camcopsversion.h"

namespace camcopsversion {  // http://semver.org/

const Version CAMCOPS_VERSION(2, 0, 4);
const Version MINIMUM_SERVER_VERSION(2, 0, 0);

}  // namespace camcopsversion

/*

===============================================================================
VERSION HISTORY
===============================================================================
2.0.0
- Development of C++ version from scratch. Replaces Titanium version.
- Released as beta to Google Play on 2017-07-17.

2.0.1
- More const checking.
- Bugfix to stone/pound/ounce conversion.
- Bugfix to raw SQL dump.
- ID numbers generalized so you can have >8 (= table structure change).

2.0.2
- Cosmetic bug fixes, mainly for phones, including a re-layout of the ACE-III
  address learning for very small screens.
- Bugfix: deleting a patient didn't deselect that patient.
- Default software keyboard for date entry changed.
- Bugfix for canvas widget on Android (size was going wrong).
- Automatic adjustment for high-DPI screens as standard in
  QuBoolean (its image option), QuCanvas, QuImage, QuThermometer.

2.0.3
- 2018-08-07
- Trivial type fix to patient_wanted_copy_of_letter (String -> Bool) in the
  unused task CPFTLPSDischarge.

*/
