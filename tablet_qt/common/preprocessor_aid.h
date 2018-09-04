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

#if __GNUC__ >= 7  // gcc >= 7.0
    // https://www.gnu.org/software/gcc/gcc-7/changes.html
    #define GCC_AT_LEAST_7
    #define GCC_HAS_WARNING_INT_IN_BOOL_CONTEXT
#endif

// No need to test "#ifdef __GNUC__" first; an undefined preprocessor constant
// evalutes to 0 when tested with "#if";
// https://stackoverflow.com/questions/5085392/what-is-the-value-of-an-undefined-constant-used-in-if
