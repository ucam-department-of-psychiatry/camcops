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

// ============================================================================
// Numeric string representations
// ============================================================================

// INTERNAL FUNCTION.
// Does the string contain ONLY a leading sign and/or zeroes? Such a number
// could be extended to anything.
// - Assumes no leading/trailing whitespace.
// - Returns false for an empty string.
bool containsOnlySignOrZeros(const QString& number_string);


// ============================================================================
// Digit counting; first n digits
// ============================================================================

// INTERNAL FUNCTION.
// Counts the number of digits in an integer type (and optionally, the sign).
template<typename T>
int numDigitsInteger(const T& number, bool count_sign = false);


// ============================================================================
// For integer validation
// ============================================================================

// Validates an integer.
template<typename T>
QValidator::State validateInteger(
    const QString& s,
    const QLocale& locale,
    const T& bottom,
    const T& top,
    bool allow_empty
);

// Is number an integer that is a valid start to typing a number between
// min and max (inclusive)?
// - Does not consider "number" itself (un-extended).
template<typename T>
bool isValidStartToInteger(const T& number, const T& bottom, const T& top);

// INTERNAL FUNCTION
// How many digits can pos_number be extended by, for range boundaries
// [pos_bottom, pos_top]? All are positive.
template<typename T>
int maxExtraDigits(const T& pos_number, const T& pos_bottom, const T& pos_top);

// INTERNAL FUNCTION
// If you add extra digits to a positive number, can it enter a valid positive
// range [pos_bottom, pos_top]?
// - Does not consider "number" itself (un-extended).
template<typename T>
bool isValidStartToPositiveInt(
    const T& pos_number, const T& pos_bottom, const T& pos_top
);

// INTERNAL FUNCTION.
// If you add extra digits to the number, must it be less than "bottom"?
// - Does not consider "number" itself (un-extended).
template<typename T>
bool extendedPositiveIntMustBeLessThanBottom(
    const T& pos_number, const T& pos_bottom, const int n_extra_digits
);

// INTERNAL FUNCTION.
// If you add extra digits to the number, must it exceed the top value?
// - Does not consider "number" itself (un-extended).
template<typename T>
bool extendedPositiveIntMustExceedTop(
    const T& pos_number, const T& pos_top, const int n_extra_digits
);


// ============================================================================
// For double validation
// ============================================================================
// See StrictDoubleValidator::validate().

// INTERNAL FUNCTION.
// Gets the decimal point symbol in the default locale.
QString getDefaultDecimalPoint();

// Is "number" something you could validly type something more after, and
// potentially end up with a number in the range [bottom, top]?
// - Does not consider "number" itself (un-extended).
bool isValidStartToDouble(
    double number,
    double bottom,
    double top,
    int max_dp,
    const QString& decimal_point = getDefaultDecimalPoint()
);

// INTERNAL FUNCTION
// If you add extra digits to a positive number, can it enter a valid positive
// range [pos_bottom, pos_top]?
// - Does not consider "number" itself (un-extended).
bool isValidStartToPosDouble(
    double pos_number,
    double pos_bottom,
    double pos_top,
    int max_dp,
    const QString& decimal_point = getDefaultDecimalPoint()
);

// INTERNAL FUNCTION.
// Must any typed extension of "number" necessarily be less than "bottom"?
// - Does not consider "number" itself (un-extended).
bool extendedPosDoubleMustBeLessThanBottom(
    double pos_number,
    double pos_bottom,
    int n_extra_digits,
    bool add_dp,
    const QString& decimal_point = getDefaultDecimalPoint()
);

// INTERNAL FUNCTION.
// Must any typed extension of "number" necessarily exceed "top"?
// - Does not consider "number" itself (un-extended).
bool extendedPosDoubleMustExceedTop(
    double pos_number,
    double pos_top,
    int n_extra_digits,
    bool add_dp,
    const QString& decimal_point = getDefaultDecimalPoint()
);

// INTERNAL FUNCTION.
// Counts the number of characters in a floating-point number, specified to a
// certain number of decimal places.
// - includes decimal point
// - optionally includes the sign
int numCharsDouble(double number, int max_dp, bool count_sign = false);

// INTERNAL FUNCTION
// How many digits can pos_number be extended by, for range boundaries
// [pos_bottom, pos_top]? All are positive.
int maxExtraDigitsDouble(
    double pos_number, double pos_bottom, double pos_top, int max_dp
);

}  // namespace numeric

// ============================================================================
// Templated functions, first declared above
// ============================================================================

template<typename T>
int numeric::numDigitsInteger(const T& number, bool count_sign)
{
    // Counts the number of digits in an integer type.
    int digits = 0;
    if (number < 0 && count_sign) {
        digits = 1;
    }
    T working = number;
    while (working) {
        // don't use while (number); consider double number = 0.05...
        working /= 10;  // assumes base 10
        ++digits;
    }
    return digits;
}

template<typename T>
QValidator::State numeric::validateInteger(
    const QString& s,
    const QLocale& locale,
    const T& bottom,
    const T& top,
    bool allow_empty
)
{
    // 1. Empty string?
    if (s.isEmpty()) {
        if (allow_empty) {
#ifdef NUMERICFUNC_DEBUG_BASIC
            qDebug() << Q_FUNC_INFO << "empty -> Acceptable (as allow_empty)";
#endif
            return QValidator::Acceptable;
        }
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "empty -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // 2. Contains a decimal point?
    const QString decimalPoint = locale.decimalPoint();
    if (s.indexOf(decimalPoint) != -1) {
        // Containing a decimal point: not OK
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "decimal point -> Invalid";
#endif
        return QValidator::Invalid;
    }

    // 3. "-" by itself?
    if ((bottom < 0 || top < 0) && s == "-") {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "plain -, negatives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // 4. "+" by itself?
    if ((bottom > 0 || top > 0) && s == "+") {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "plain +, positives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // 5. Invalid as an integer?
    bool ok = true;
    const T type_dummy = 0;
    const T i = localeStrToNumber(s, ok, locale, type_dummy);
    // NB: ok modified
    if (!ok) {  // Not an integer.
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "not an integer -> Invalid";
#endif
        return QValidator::Invalid;
    }

    // 5. Already within range?
    if (i >= bottom && i <= top) {  // Perfect.
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "in range -> Acceptable";
#endif
        return QValidator::Acceptable;
    }

    // 6. Contains only leading zeroes?
    if (containsOnlySignOrZeros(s)) {
        if (s.startsWith("-") && bottom > 0) {
#ifdef NUMERICFUNC_DEBUG_BASIC
            qDebug() << Q_FUNC_INFO << "-0, bottom > 0 -> Invalid";
#endif
            return QValidator::Invalid;
        }
        if (s.startsWith("+") && top < 0) {
#ifdef NUMERICFUNC_DEBUG_BASIC
            qDebug() << Q_FUNC_INFO << "+0, top < 0 -> Invalid";
#endif
            return QValidator::Invalid;
        }
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO << "leading zeros only -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // 7. Is the number on its way to being something valid?
    if (numeric::isValidStartToInteger(i, bottom, top)) {
#ifdef NUMERICFUNC_DEBUG_BASIC
        qDebug() << Q_FUNC_INFO
                 << "within range for number of digits -> Intermediate;"
                 << "s" << s;
#endif
        return QValidator::Intermediate;
    }

    // 8. By elimination: it is invalid.
#ifdef NUMERICFUNC_DEBUG_BASIC
    qDebug() << Q_FUNC_INFO << "end of function -> Invalid;"
             << "s" << s;
#endif
    return QValidator::Invalid;
}

template<typename T>
bool numeric::isValidStartToInteger(
    const T& number, const T& bottom, const T& top
)
{
    // Is number an integer that is a valid start to typing a number between
    // min and max (inclusive)?

    /*
    Tricky! No proper way to do it just by looking at the first n digits of
    the boundaries:

    +- bottom   +_ bottom_start
    |           |   +- top_start
    |           |   |
    b   top     bs  ts  possibilities   description

    10  30      1   3   1-3 yes         >= bottom_start && <= top_start
                        4-9 no          > top_start (3)

    30  100     3   1   1 yes           >= bottom_start || <= top_start
                        2 no            < bottom_start (3) && > top_start (1)
                        3-9 yes         >= bottom_start || <= top_start

    20  30      2   3   1 no            < bottom_start (2)
                        2-3 yes         >= bottom_start && <= top_start
                        4-9 no          > top_start (3)

    30  100     30  10  3_: 0-9 yes     >= bs (30) || <= ts (10)
                        1_: 0 yes       >= bs (30) || <= ts (10)
                        1-9 no          > top_start

    But then:

    100 30000   10  30  5_: 0-9 OK (e.g. 500-599)

    70  300     7   3   0-3, 7-9 OK

    */

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
    const T typed_zero = 0;
    if (number >= 0) {
        // Number is already positive (or zero).
        // We already know that top > 0, and by definition bottom <= top.
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number << "passing on positive/zero number";
#endif
        return isValidStartToPositiveInt(
            number,  // already positive or zero
            std::max(typed_zero, bottom),  // makes it zero or positive
            top  // already known to be positive
        );
    } else {
        // Number is negative.
        // We already know that bottom < 0, and by definition bottom <= top;
        // therefore, -top <= -bottom.
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << number << "passing on negative number";
#endif
        return isValidStartToPositiveInt(
            // 0- here avoids C4146 compiler error on Windows:
            // "unary minus operator applied to unsigned type, result still
            // unsigned."
            // This code will never be reached for unsigned types!
            0 - number,  // now positive
            std::max(typed_zero, 0 - top),  // makes it zero or positive
            0 - bottom
        );
    }
}

template<typename T>
int numeric::maxExtraDigits(
    const T& pos_number, const T& pos_bottom, const T& pos_top
)
{
    // The maximum number of extra digits we might permit.
    int nd_number = numDigitsInteger(pos_number);  // minimum: 1
    if (pos_number == 0) {
        // If someone has typed "0", then they have a redundant digit, but it
        // can be valid.
        --nd_number;  // nd_number can still not be less than 0
    }
    // How many digits in our longest range boundary?
    const int max_nd_target
        = std::max(numDigitsInteger(pos_bottom), numDigitsInteger(pos_top));
    // We can extend up to that many:
    const int n_extra = std::max(0, max_nd_target - nd_number);
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << "(" << pos_number << ", "
                       << pos_bottom << ", " << pos_top
                       << "): nd_number = " << nd_number
                       << ": max_nd_target = " << max_nd_target << " -> "
                       << n_extra;
#endif
    return n_extra;
}

template<typename T>
bool numeric::isValidStartToPositiveInt(
    const T& pos_number, const T& pos_bottom, const T& pos_top
)
{
    // Is "number" an integer that, if extended (but not by itself), might
    // make it into the range [pos_bottom, pos_top]?
    // - All arguments must be positive, and pos_bottom <= pos_top.

    const int n_extra = maxExtraDigits(pos_number, pos_bottom, pos_top);

    if (extendedPositiveIntMustBeLessThanBottom(
            pos_number, pos_bottom, n_extra
        )) {
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << pos_number
                 << "when extended must be less than bottom value of"
                 << pos_bottom << "=> fail";
#endif
        return false;
    }

    if (extendedPositiveIntMustExceedTop(pos_number, pos_top, n_extra)) {
#ifdef NUMERICFUNC_DEBUG_DETAIL
        qDebug() << Q_FUNC_INFO << pos_number
                 << "when extended must be more than top value of" << pos_top
                 << "=> fail";
#endif
        return false;
    }

    // By implication, there is a way of extending it that produces a number
    // that's >= bottom, and a way of extending that produces a number that's
    // <= top. It is not guaranteed that the same way of extenting satisfies
    // BOTH criteria. The only way to check that is recursion, which is very
    // slow.
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug() << Q_FUNC_INFO << pos_number << "is potentially OK for bottom"
             << pos_bottom << "top" << pos_top;
#endif
    return true;
}

template<typename T>
bool numeric::extendedPositiveIntMustBeLessThanBottom(
    const T& pos_number, const T& pos_bottom, const int n_extra_digits
)
{
    // If you add extra digits to the number, must it be less than the bottom
    // value?
    // - All arguments are positive.

    // Try to extend, making the number as large as possible.
    const T type_dummy = 0;
    QString str_number;
    str_number.setNum(pos_number);
    const QString extension_digit = "9";  // make the largest possible number
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << "; pos_number = " << pos_number
                       << ", pos_bottom = " << pos_bottom
                       << ", n_extra = " << n_extra_digits;
#endif
    for (int i = 0; i < n_extra_digits; ++i) {
        str_number += extension_digit;
        if (strToNumber(str_number, type_dummy) >= pos_bottom) {
            return false;
        }
    }
    return true;
}

template<typename T>
bool numeric::extendedPositiveIntMustExceedTop(
    const T& pos_number, const T& pos_top, const int n_extra_digits
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
    const T type_dummy = 0;
    QString str_number;
    str_number.setNum(pos_number);
    const QString extension_digit = "0";  // make the smallest possible number
#ifdef NUMERICFUNC_DEBUG_DETAIL
    qDebug().nospace() << Q_FUNC_INFO << "; pos_number = " << pos_number
                       << ", pos_top = " << pos_top
                       << ", n_extra_digits = " << n_extra_digits;
#endif
    for (int i = 0; i < n_extra_digits; ++i) {
        str_number += extension_digit;
        if (strToNumber(str_number, type_dummy) <= pos_top) {
            return false;  // an extended number does not exceed top
        }
    }
    return true;  // all extended versions exceed top
}
