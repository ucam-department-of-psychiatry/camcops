/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "customtypes.h"

#include "lib/version.h"

namespace customtypes {


int TYPE_ID_QVECTOR_INT;
int TYPE_ID_VERSION;

void registerTypesForQVariant()
{
    // http://stackoverflow.com/questions/6177906/is-there-a-reason-why-qvariant-accepts-only-qlist-and-not-qvector-nor-qlinkedlis
    TYPE_ID_QVECTOR_INT = qRegisterMetaType<QVector<int>>();
    TYPE_ID_VERSION = qRegisterMetaType<Version>();

    // See also the calls to Q_DECLARE_METATYPE().
    // https://doc.qt.io/qt-6.5/qtcore-tools-customtype-example.html
}

}  // namespace customtypes
