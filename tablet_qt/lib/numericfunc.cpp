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

// ============================================================================
// Numeric string representations
// ============================================================================

bool containsOnlySignOrZeros(const QString& number_string)
{
    if (number_string.isEmpty()) {
        return false;
    }
    const qsizetype length = number_string.length();
    for (qsizetype pos = 0; pos < length; ++pos) {
        const QChar c = number_string.at(pos);
        if (c != '0' && !(pos == 0 && (c == '-' || c == '+'))) {
            // Not a zero; not a leading sign.
            return false;
        }
    }
    return true;
}

bool containsOnlySignZerosOrPoint(const QString& number_string)
{
    if (number_string.isEmpty()) {
        return false;
    }
    const qsizetype length = number_string.length();
    for (qsizetype pos = 0; pos < length; ++pos) {
        const QChar c = number_string.at(pos);
        if (c != '0' && c != '.' && !(pos == 0 && (c == '-' || c == '+'))) {
            // Not a zero or decimal point; not a leading sign.
            return false;
        }
    }
    return true;
}

// ============================================================================
// For double validation
// ============================================================================

QString getDefaultDecimalPoint()
{
    // https://doc.qt.io/qt-5/qlocale.html#QLocale
    // https://doc.qt.io/qt-5/qlocale.html#decimalPoint
    // ... changes from QChar to QString in Qt6
    return QLocale().decimalPoint();
}

bool isValidStartToDouble(
    const double number,
    const double bottom,
    const double top,
    const int max_dp,
    const QString& decimal_point
)
{
    // If you type more after "number", could you end up with a legitimate
    // value, in the range [bottom, top]?

    // 1. If "number" is negative and "bottom" is zero or positive, then
    //    "extended number" must always negative (because there must already be
    //    a minus sign at the start), and therefore always less than "bottom".
    if (number < 0 && bottom >= 0) {
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number
                 << "invalid (negative and bottom >= 0)";
#endif
        return false;  // invalid
    }

    // 2. If "number" is positive and "top" is negative or zero, then "extended
    //    number" must always be positive (because there is no minus sign) and
    //    therefore always more than "top".
    if (number > 0 && top <= 0) {
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number << "invalid (positive and top <= 0)";
#endif
        return false;  // invalid
    }

    // 3. Move into the positive domain to save brain ache.
    if (number >= 0) {
        // Number is already positive (or zero).
        // We already know that top > 0, and by definition bottom <= top.
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number << "passing on positive/zero number";
#endif
        return isValidStartToPosDouble(
            number,  // already positive or zero
            std::max(0.0, bottom),  // makes it zero or positive
            top,  // already known to be positive
            max_dp,
            decimal_point
        );
    } else {
        // Number is negative.
        // We already know that bottom < 0, and by definition bottom <= top;
        // therefore, -top <= -bottom.
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number << "passing on negative number";
#endif
        return isValidStartToPosDouble(
            -number,  // now positive
            std::max(0.0, -top),  // makes it zero or positive
            -bottom,
            max_dp,
            decimal_point
        );
    }
}

bool isValidStartToPosDouble(
    const double pos_number,
    const double pos_bottom,
    const double pos_top,
    const int max_dp,
    const QString& decimal_point
)
{
    // If you type more after "number", could you end up with a legitimate
    // value, in the range [bottom, top]?

    const int n_extra
        = maxExtraDigitsDouble(pos_number, pos_bottom, pos_top, max_dp);
    const QString str_number = QString("%1").arg(pos_number);
    const bool contains_dp = str_number.contains(decimal_point);

    // 1. If any extended version must be less than "bottom", it is invalid.
    // Check without adding a decimal point.
    const bool must_be_lt_bottom_noextradp
        = extendedPosDoubleMustBeLessThanBottom(
            pos_number, pos_bottom, n_extra, false, decimal_point
        );
    // Or with an extra decimal point, if applicable.
    const bool must_be_lt_bottom_extradp = contains_dp
        ? must_be_lt_bottom_noextradp
        : extendedPosDoubleMustBeLessThanBottom(
            pos_number, pos_bottom, n_extra, true, decimal_point
        );
    const bool must_be_lt_bottom
        = must_be_lt_bottom_noextradp && must_be_lt_bottom_noextradp;

    if (must_be_lt_bottom) {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << ": " << pos_number
                 << "when extended must be less than bottom value of"
                 << pos_bottom << "=> fail";
#endif
        return false;
    }

    // 2. If any extended version must be more than "top", it is invalid.
    // Check without adding a decimal point.
    const bool must_be_gt_top_noextradp = extendedPosDoubleMustExceedTop(
        pos_number, pos_top, n_extra, false, decimal_point
    );
    // Or with an extra decimal point, if applicable.
    const bool must_be_gt_top_extradp = contains_dp
        ? must_be_gt_top_noextradp
        : extendedPosDoubleMustExceedTop(
            pos_number, pos_top, n_extra, true, decimal_point
        );
    const bool must_be_gt_top
        = must_be_gt_top_noextradp && must_be_gt_top_extradp;

    if (must_be_gt_top) {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << ":" << pos_number
                 << "when extended must be more than top value of" << pos_top
                 << "=> fail";
#endif
        return false;
    }

    // 3. Check that we haven't allowed through obvious exclusionary
    // conditions.
    const bool no_extra_dp_ok
        = !must_be_lt_bottom_noextradp && !must_be_gt_top_noextradp;
    const bool extra_dp_ok
        = !must_be_lt_bottom_extradp && !must_be_gt_top_extradp;
    if (!no_extra_dp_ok && !extra_dp_ok) {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug().nospace() << Q_FUNC_INFO << ": " << pos_number
                           << "when extended must out of range [" << pos_bottom
                           << ", " << pos_top << "] => fail";
#endif
        return false;
    }

    // 4. By implication, there is a way of extending it that produces a number
    // that's >= bottom, and a way of extending that produces a number that's
    // <= top. It is not guaranteed that the same way of extenting satisfies
    // BOTH criteria. The only way to check that is recursion, which is very
    // slow.
#ifdef NUMERICFUNC_DEBUG_BASIC
    qDebug().nospace() << Q_FUNC_INFO << ": " << pos_number
                       << " is potentially OK for bottom " << pos_bottom
                       << ", top " << pos_top;
#endif
    return true;
}

bool extendedPosDoubleMustBeLessThanBottom(
    const double pos_number,
    const double pos_bottom,
    const int n_extra_digits,
    const bool add_dp,
    const QString& decimal_point
)
{
    // If you add extra digits to the number, must it be less than the bottom
    // value?
    // - All arguments are positive.

    // Try to extend, making the number as large as possible.
    // - Add a decimal point if our caller wants.
    //   That doesn't help us make it as large as possible, but our caller
    //   may have their reasons.
    QString str_number = QString("%1").arg(pos_number);
    if (add_dp && !str_number.contains(decimal_point)) {
        str_number += decimal_point;
    }
    const QString extension_digit = "9";  // make the largest possible number
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << "; pos_number = " << pos_number
                       << ", pos_bottom = " << pos_bottom
                       << ", n_extra = " << n_extra_digits;
#endif
    for (int i = 0; i < n_extra_digits; ++i) {
        str_number += extension_digit;
        if (str_number.toDouble() >= pos_bottom) {
            return false;
        }
    }
    return true;
}

bool extendedPosDoubleMustExceedTop(
    const double pos_number,
    const double pos_top,
    const int n_extra_digits,
    const bool add_dp,
    const QString& decimal_point
)
{
    // If you add extra digits to the number, must it exceed the top value?
    // - All arguments are positive.

    // 1. Adding digits to a positive integer can only make it larger.
    //    If "number" already exceeds "top", it will always do so.
    if (pos_number > pos_top) {
        return true;
    }

    // 2. Try to extend, making the number as small as possible.
    // - Add a decimal point if our caller wants.
    //   That helps us keep things as small as possible.
    QString str_number = QString("%1").arg(pos_number);
    if (add_dp && !str_number.contains(decimal_point)) {
        str_number += decimal_point;
    }
    const QString extension_digit = "0";  // make the smallest possible number
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << "; pos_number = " << pos_number
                       << ", pos_top = " << pos_top
                       << ", n_extra_digits = " << n_extra_digits;
#endif
    for (int i = 0; i < n_extra_digits; ++i) {
        str_number += extension_digit;
        if (str_number.toDouble() <= pos_top) {
            return false;  // an extended number does not exceed top
        }
    }
    return true;  // all extended versions exceed top
}

int numCharsDouble(const double number, const int max_dp, bool count_sign)
{
    const QString formatted = QString::number(number, 'f', max_dp);
    const bool sign_present = number < 0;
    const int length = formatted.length();
    const int nchars = (sign_present && !count_sign) ? length - 1 : length;
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << ": " << number << " formatted to "
                       << max_dp << " dp is " << formatted << "; nchars "
                       << nchars
                       << (count_sign ? " (inc. sign)" : " (exc. sign)");
#endif
    return nchars;
}

int maxExtraDigitsDouble(
    const double pos_number,
    const double pos_bottom,
    const double pos_top,
    const int max_dp
)
{
    // Follows logic of maxExtraDigits().
    int nd_number = numCharsDouble(pos_number, max_dp);
    if (pos_number == 0) {
        --nd_number;
    }
    const int max_nd_target = std::max(
        numCharsDouble(pos_bottom, max_dp), numCharsDouble(pos_top, max_dp)
    );
    return std::max(0, max_nd_target - nd_number);
}


}  // namespace numeric
