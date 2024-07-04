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


int localeStrToNumber(const QString& str, bool& ok,
                      const QLocale& locale, const int type_dummy)
{
    Q_UNUSED(type_dummy)
    return locale.toInt(str, &ok);
}


qint64 localeStrToNumber(const QString& str, bool& ok,
                         const QLocale& locale, const qint64 type_dummy)
{
    Q_UNUSED(type_dummy)
    return locale.toLongLong(str, &ok);
}


quint64 localeStrToNumber(const QString& str, bool& ok,
                          const QLocale& locale,
                          const quint64 type_dummy)
{
    Q_UNUSED(type_dummy)
    return locale.toULongLong(str, &ok);
}


// ============================================================================
// For double validation
// ============================================================================

int numDigitsDouble(const double number, const int max_dp)
{
    const QString formatted = QString::number(number, 'f', max_dp);
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << number << "formatted to" << max_dp << "dp is" << formatted;
#endif
    const bool sign_present = number < 0;
    // Trim trailing zeros:
    int pos;
    for (pos = formatted.length() - 1; pos > 0; --pos) {
        if (formatted.at(pos) != '0') {
            break;
        }
    }
    int length = pos + 1;
    return sign_present ? length - 1 : length;
}


double firstDigitsDouble(const double number,
                         const int n_digits,
                         const int max_dp)
{
    const QString formatted = QString::number(number, 'f', max_dp);
    const bool sign_present = number < 0;
    const QString left = formatted.left(sign_present ? n_digits + 1 : n_digits);
    const double result = left.toDouble();
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "- formatted" << formatted
             << "n_digits" << n_digits
             << "left" << left
             << "result" << result;
#endif
    return result;
}


bool isValidStartToDouble(const double number,
                          const double bottom,
                          const double top,
                          const int max_dp)
{
    if (extendedDoubleMustBeLessThanBottom(number, bottom, top, max_dp)) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be less than bottom value of"
                 << bottom << "=> fail";
#endif
        return false;
    }
    if (extendedDoubleMustExceedTop(number, bottom, top, max_dp)) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be more than top value of"
                 << top << "=> fail";
#endif
        return false;
    }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << number << "is OK for bottom"
             << bottom << "top" << top;
#endif
    return true;
}


bool extendedDoubleMustExceedTop(const double number,
                                 const double bottom,
                                 const double top,
                                 const int max_dp)
{
    if (number < 0 && top > 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number << " < 0 and " << top << " > 0"
             << " return false";
#endif
        return false;
    }
    if (number > 0 && top < 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number << " > 0 and " << top << " < 0";
        qDebug() << "true EXIT POINT 4";
#endif
        return true;
    }
    const int nd_number = numDigitsDouble(number, max_dp);
    QString str_number;
    str_number.setNum(number);
    if (number > 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number << " > 0";
#endif
        // Both positive. Extend with zeros, to length of top
        const int nd_top = numDigitsDouble(top, max_dp);
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << "nd_number:" << nd_number << "nd_top:" << nd_top;
#endif
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "0";
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
            qDebug() << "str_number now:" << str_number;
#endif
            if (str_number.toDouble() <= top) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
                qDebug() << Q_FUNC_INFO << str_number.toDouble() << " <= "
                         << top << " return false";
#endif
                return false;
            }
        }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "Could not extend" << number << "with zeros"
                 << "to make it between" << bottom << "and" << "top";
        qDebug() << "true EXIT POINT 5";
#endif
        return true;
    }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << number << " <= 0";
#endif
    // Both negative. Extend with nines.
    const int nd_bottom = numDigitsDouble(bottom, max_dp);
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << "nd_number:" << nd_number << "nd_bottom:" << nd_bottom;
#endif
    for (int i = 0; i < nd_bottom - nd_number; ++i) {
        str_number += "9";
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << "str_number now:" << str_number;
#endif
        if (str_number.toDouble() <= top) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
            qDebug() << Q_FUNC_INFO << str_number.toDouble() << " <= "
                     << top << " return false";
#endif

            return false;
        }
    }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "Could not extend" << number << "with nines"
             << "to make it between" << bottom << "and" << top;
    qDebug() << "true EXIT POINT 6";
#endif

    return true;
}


bool extendedDoubleMustBeLessThanBottom(const double number,
                                        const double bottom,
                                        const double top,
                                        const int max_dp)
{
    if (number < 0 && bottom > 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << "EXIT POINT 1";
        qDebug() << Q_FUNC_INFO << number << " < 0 and " << bottom << " > 0"
             << " return true";
#endif
        return true;
    }
    if (number > 0 && bottom < 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number << " > 0 and " << bottom << " < 0"
             << " return false";
#endif
        return false;
    }
    const int nd_number = numDigitsDouble(number, max_dp);
    QString str_number;
    str_number.setNum(number);
    if (number > 0) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number << " > 0";
#endif
        // Both positive. Extend with nines, to length of top
        const int nd_top = numDigitsDouble(top, max_dp);
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << "nd_number:" << nd_number << "nd_top:" << nd_top;
#endif
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "9";
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
            qDebug() << "str_number now:" << str_number;
#endif
            if (str_number.toDouble() >= bottom) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
                qDebug() << Q_FUNC_INFO << str_number.toDouble() << " >= "
                         << bottom << " return false";
#endif
                return false;
            }
        }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "Could not extend" << number << "with nines"
                 << "to make it between" << bottom << "and" << top;
        qDebug() << "true EXIT POINT 2";
#endif
        return true;
    }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << number << " <= 0";
#endif
    // Both negative. Extend with zeros, to length of bottom
    const int nd_bottom = numDigitsDouble(bottom, max_dp);

#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << "nd_number:" << nd_number << "nd_bottom:" << nd_bottom;
#endif

    for (int i = 0; i < nd_bottom - nd_number; ++i) {
        str_number += "0";
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
        qDebug() << "str_number now:" << str_number;
#endif
        if (str_number.toDouble() >= bottom) {
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
            qDebug() << Q_FUNC_INFO << str_number.toDouble() << " >= "
                     << bottom << " return false";
#endif
            return false;
        }
    }
#ifdef NUMERICFUNC_DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "Could not extend" << number << "with zeros"
             << "to make it between" << bottom << "and" << top;
    qDebug() << "true EXIT POINT 3";
#endif
    return true;
}


}  // namespace numeric
