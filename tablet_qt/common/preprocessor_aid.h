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

// Specific checks for compilation environments that need special workarounds.

#include <QtGlobal>  // for QT_VERSION

// ============================================================================
// Printing preprocessor variables
// ============================================================================
// https://stackoverflow.com/questions/1204202/is-it-possible-to-print-a-preprocessor-variable-in-c
#define PREPROCESSOR_STRING2(x) #x
#define PREPROCESSOR_STRING(x) PREPROCESSOR_STRING2(x)

// ============================================================================
// GCC_HAS_WARNING_INT_IN_BOOL_CONTEXT
// ============================================================================

#if __GNUC__ >= 7  // gcc >= 7.0
    // https://www.gnu.org/software/gcc/gcc-7/changes.html
    #define GCC_AT_LEAST_7
    #define GCC_HAS_WARNING_INT_IN_BOOL_CONTEXT
#endif

// No need to test "#ifdef __GNUC__" first; an undefined preprocessor constant
// evalutes to 0 when tested with "#if";
// https://stackoverflow.com/questions/5085392/what-is-the-value-of-an-undefined-constant-used-in-if

// ============================================================================
// QT_WORKAROUND_BUG_68889
// ============================================================================

#ifdef Q_OS_ANDROID
    // #pragma message "QT_VERSION = " PREPROCESSOR_STRING(QT_VERSION)
    #if QT_VERSION == ((5 << 16) | (12 << 8) | (0))
        // Qt version 5.12.0
        #define QT_WORKAROUND_BUG_68889
        // See https://bugreports.qt.io/browse/QTBUG-68889
        // Only seems to affect Android builds (Ubuntu, Arch Linux OK).
    #endif
#endif
