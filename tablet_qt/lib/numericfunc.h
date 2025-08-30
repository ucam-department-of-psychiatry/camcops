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

#pragma once

// #define NUMERICFUNC_DEBUG_BASIC
// #define NUMERICFUNC_DEBUG_DETAIL

#if defined NUMERICFUNC_DEBUG_BASIC || defined NUMERICFUNC_DEBUG_DETAIL
    #include <QDebug>
#endif
#include <QLocale>
#include <QString>
#include <QValidator>

namespace numeric {

// Since there are many integer types, we templatize these:

// ============================================================================
// Overloaded functions to convert to an integer type
// ============================================================================

// Converts a string containing a decimal integer to that integer.
// We offer this function for a variety of types, so our templatized functions
// can find what they want.
int strToNumber(const QString& str, int type_dummy);
qint64 strToNumber(const QString& str, qint64 type_dummy);
quint64 strToNumber(const QString& str, quint64 type_dummy);

// Similarly for locale-based strings containing integers, for different
// languages/conventions; see https://doc.qt.io/qt-6.5/qlocale.html
int localeStrToNumber(
    const QString& str, bool& ok, const QLocale& locale, int type_dummy
);
qint64 localeStrToNumber(
    const QString&, bool& ok, const QLocale& locale, qint64 type_dummy
);
quint64 localeStrToNumber(
    const QString&, bool& ok, const QLocale& locale, quint64 type_dummy
);
}
