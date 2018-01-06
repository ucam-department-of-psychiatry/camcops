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

// #define DEBUG_VALIDATOR

#include <QString>
#ifdef DEBUG_VALIDATOR
#include <QDebug>
#endif
#include <QLocale>
#include <QValidator>

namespace numeric {

// Since there are many integer types, we templatize these:

// ============================================================================
// Overloaded functions to convert to an integer type
// ============================================================================

int strToNumber(const QString& str, int type_dummy);
int localeStrToNumber(const QString& str, bool& ok,
                      const QLocale& locale, int type_dummy);
qlonglong strToNumber(const QString& str, qlonglong type_dummy);
qlonglong localeStrToNumber(const QString&, bool& ok,
                            const QLocale& locale, qlonglong type_dummy);
qulonglong strToNumber(const QString& str, qulonglong type_dummy);
qulonglong localeStrToNumber(const QString&, bool& ok,
                             const QLocale& locale, qulonglong type_dummy);

// ============================================================================
// Digit counting; first n digits
// ============================================================================

template<typename T>
int numDigitsInteger(const T& number, bool count_sign = false);

template<typename T>
int firstDigitsInteger(const T& number, int n_digits);

template<typename T>
bool extendedIntegerMustExceedTop(const T& number, const T& bottom,
                                  const T& top);

template<typename T>
bool extendedIntegerMustBeLessThanBottom(const T& number, const T& bottom,
                                         const T& top);

// ============================================================================
// For integer validation
// ============================================================================

template<typename T>
bool isValidStartToInteger(const T& number, const T& bottom, const T& top);

template<typename T>
QValidator::State validateInteger(QString& s, const QLocale& locale,
                                  const T& bottom, const T& top,
                                  bool allow_empty);

// ============================================================================
// For double validation:
// ============================================================================

int numDigitsDouble(double number, int max_dp = 50);
double firstDigitsDouble(double number, int n_digits, int max_dp = 50);
bool isValidStartToDouble(double number, double bottom, double top);
bool extendedDoubleMustExceed(double number, double bottom, double top);
bool extendedDoubleMustBeLessThan(double number, double bottom, double top);

}  // namespace numeric


// ============================================================================
// Templated functions
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
int numeric::firstDigitsInteger(const T& number, int n_digits)
{
    // Returns the first n_digits of an integer, as an integer.
    int current_digits = numDigitsInteger(number);
    T working = number;
    while (current_digits > n_digits) {
        working /= 10;  // assumes base 10
        --current_digits;
    }
    return working;
}


template<typename T>
bool numeric::extendedIntegerMustExceedTop(const T& number,
                                           const T& bottom,
                                           const T& top)
{
    // If you add extra digits to the number to make it as long as it could be,
    // must it exceed it the top value?
    T type_dummy = 0;
    if (number < 0 && top > 0) {
        return false;
    }
    if (number > 0 && top < 0) {
        return true;
    }
    int nd_number = numDigitsInteger(number);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with zeros, to length of nd_top
        int nd_top = numDigitsInteger(top);
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "0";
            if (strToNumber(str_number, type_dummy) <= top) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with nines, to length of nd_bottom
        int nd_bottom = numDigitsInteger(bottom);
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "9";
            if (strToNumber(str_number, type_dummy) <= top) {
                return false;
            }
        }
        return true;
    }
}


template<typename T>
bool numeric::extendedIntegerMustBeLessThanBottom(const T& number,
                                                  const T& bottom,
                                                  const T& top)
{
    // If you add extra digits to the number to make it as long as it could be,
    // must it be less than bottom?
    T type_dummy = 0;
    if (number < 0 && bottom > 0) {
        return true;
    }
    if (number > 0 && bottom < 0) {
        return false;
    }
    int nd_number = numDigitsInteger(number);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with nines, to length of top
        int nd_top = numDigitsInteger(top);
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "9";
            if (strToNumber(str_number, type_dummy) >= bottom) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with zeros, to length of bottom
        int nd_bottom = numDigitsInteger(bottom);
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "0";
            if (strToNumber(str_number, type_dummy) >= bottom) {
                return false;
            }
        }
        return true;
    }
}


template<typename T>
bool numeric::isValidStartToInteger(const T& number, const T& bottom,
                                    const T& top)
{
    // Is number an integer that is a valid start to typing a number between
    // min and max (inclusive)?

    /*
    Tricky! No proper way to do it just by looking at the first n digits of
    the boundaries:

    bottom  top     bottom_start    top_start   possibilities   description

    10      30      1               3           1-3 yes         >= bottom_start && <= top_start
                                                4-9 no          > top_start (3)

    30      100     3               1           1 yes           >= bottom_start || <= top_start
                                                2 no            < bottom_start (3) && > top_start (1)
                                                3-9 yes         >= bottom_start || <= top_start

    20      30      2               3           1 no            < bottom_start (2)
                                                2-3 yes         >= bottom_start && <= top_start
                                                4-9 no          > top_start (3)

    30      100     30              10          3_: 0-9 yes     >= bottom_start (30) || <= top_start (10)
                                                1_: 0 yes       >= bottom_start (30) || <= top_start (10)
                                                    1-9 no      > top_start

    But then:

    100     30000   10              30          5_: 0-9 OK (e.g. 500-599)

    70      300     7               3           0-3, 7-9 OK
    */

    if (extendedIntegerMustBeLessThanBottom(number, bottom, top)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be less than bottom value of"
                 << bottom << "=> fail";
#endif
        return false;
    }
    if (extendedIntegerMustExceedTop(number, bottom, top)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be more than top value of"
                 << top << "=> fail";
#endif
        return false;
    }
#ifdef DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << number << "is OK for bottom"
             << bottom << "top" << top;
#endif
    return true;
}

template<typename T>
QValidator::State numeric::validateInteger(QString& s, const QLocale& locale,
                                           const T& bottom, const T& top,
                                           bool allow_empty)
{
    if (s.isEmpty()) {
        if (allow_empty) {
#ifdef DEBUG_VALIDATOR
            qDebug() << Q_FUNC_INFO << "empty -> Acceptable (as allow_empty)";
#endif
            return QValidator::Acceptable;
        }
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "empty -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    QChar decimalPoint = locale.decimalPoint();
    if (s.indexOf(decimalPoint) != -1) {
        // Containing a decimal point: not OK
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "decimal point -> Invalid";
#endif
        return QValidator::Invalid;
    }

    if ((bottom < 0 || top < 0) && s == "-") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain -, negatives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }
    if ((bottom > 0 || top > 0) && s == "+") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain +, positives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    bool ok = true;
    T type_dummy = 0;
    T i = localeStrToNumber(s, ok, locale, type_dummy);  // NB: ok modified
    if (!ok) {  // Not an integer.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "not an integer -> Invalid";
#endif
        return QValidator::Invalid;
    }

    if (i >= bottom && i <= top) {  // Perfect.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "in range -> Acceptable";
#endif
        return QValidator::Acceptable;
    }

    // "Negative zero" is a special case -- a string starting with "-" that
    // evaluates to zero, like "-0" or "--0". The presence of the minus sign
    // can't be detected in the numeric version, so we have to handle it
    // specially.
    if (s.startsWith("-") && i == 0) {
        // If we get here, we already know that negative numbers are OK.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "negative zero -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // Is the number on its way to being something valid, or is it already
    // outside the permissible range?
    if (numeric::isValidStartToInteger(i, bottom, top)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO
                 << "within range for number of digits -> Intermediate;"
                 << "s" << s;
#endif
        return QValidator::Intermediate;
    }
#ifdef DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "end of function -> Invalid;"
             << "s" << s;
#endif
    return QValidator::Invalid;
}
