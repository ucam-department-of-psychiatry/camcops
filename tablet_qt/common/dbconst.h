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

#pragma once
#include <QString>
#include "common/design_defines.h"

namespace dbconst {

extern const QString PK_FIELDNAME;
extern const QString MOVE_OFF_TABLET_FIELDNAME;
extern const QString MODIFICATION_TIMESTAMP_FIELDNAME;
extern const QString CREATION_TIMESTAMP_FIELDNAME;
extern const int NONEXISTENT_PK;

#ifdef LIMIT_TO_8_IDNUMS_AND_USE_PATIENT_TABLE
extern const int NUMBER_OF_IDNUMS;
extern const QString BAD_IDNUM_DESC;
extern const QString IDDESC_FIELD_FORMAT;
extern const QString IDSHORTDESC_FIELD_FORMAT;
#endif
extern const QString UNKNOWN_IDNUM_DESC;

bool isValidWhichIdnum(int which_idnum);

}  // namespace dbconst
