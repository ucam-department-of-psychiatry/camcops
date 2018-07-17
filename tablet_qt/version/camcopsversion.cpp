/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

// Increase this when the client is changed:
const Version CAMCOPS_VERSION(2, 2, 4);

// It is normal to have to increase this if you add a new task:
const Version MINIMUM_SERVER_VERSION(2, 2, 3);

}  // namespace camcopsversion

/*

===============================================================================
OTHER PLACE WHERE CLIENT VERSION NUMBER MUST BE UPDATED
===============================================================================

- tablet_qt/android/AndroidManifest.xml

===============================================================================
VERSION HISTORY
===============================================================================

See documentation/source/changelog.rst

Update that whenever changes are made.

*/
