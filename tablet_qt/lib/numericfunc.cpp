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

#include "numericfunc.h"

#include <QString>

namespace numeric {


// ============================================================================
// Overloaded functions to convert to an integer type
// ============================================================================

int strToNumber(const QString& str, const int type_dummy)
{
    Q_UNUSED(type_dummy)
    return str.toInt();
}

qint64 strToNumber(const QString& str, const qint64 type_dummy)
{
    Q_UNUSED(type_dummy)
    return str.toLongLong();
}

quint64 strToNumber(const QString& str, const quint64 type_dummy)
{
    Q_UNUSED(type_dummy)
    return str.toULongLong();
}

int localeStrToNumber(
    const QString& str, bool& ok, const QLocale& locale, const int type_dummy
)
{
    Q_UNUSED(type_dummy)
    return locale.toInt(str, &ok);
}

qint64 localeStrToNumber(
    const QString& str,
    bool& ok,
    const QLocale& locale,
    const qint64 type_dummy
)
{
    Q_UNUSED(type_dummy)
    return locale.toLongLong(str, &ok);
}

quint64 localeStrToNumber(
    const QString& str,
    bool& ok,
    const QLocale& locale,
    const quint64 type_dummy
)
{
    Q_UNUSED(type_dummy)
    return locale.toULongLong(str, &ok);
}

}  // namespace numeric
