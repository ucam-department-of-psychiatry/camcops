// #define DEBUG_VALIDATOR

#include "numericfunc.h"
#ifdef DEBUG_VALIDATOR
#include <QDebug>
#endif
#include <QString>


int Numeric::numDigitsInteger(int number, bool count_sign)
{
    // Counts the number of digits in an integer.
    int digits = 0;
    if (number < 0 && count_sign) {
        digits = 1;
    }
    while (number) {  // don't use while (number); consider double number = 0.05...
        number /= 10;  // assumes base 10
        ++digits;
    }
    return digits;
}


int Numeric::firstDigitsInteger(int number, int n_digits)
{
    // Returns the first n_digits of an integer, as an integer.
    int result = number;
    int current_digits = numDigitsInteger(number);
    while (current_digits > n_digits) {
        result /= 10;  // assumes base 10
        --current_digits;
    }
#ifdef DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "- number" << number
             << "n_digits" << n_digits
             << "result" << result;
#endif
    return result;
}


bool Numeric::extendedIntegerMustExceed(int number, int top)
{
    // If you add extra digits to the number to make it as long as top,
    // must it exceed it?
    if (number < 0 && top > 0) {
        return false;
    }
    if (number > 0 && top < 0) {
        return true;
    }
    int nd_number = numDigitsInteger(number);
    int nd_top = numDigitsInteger(top);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with zeros.
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "0";
            if (str_number.toInt() <= top) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with nines.
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "9";
            if (str_number.toInt() <= top) {
                return false;
            }
        }
        return true;
    }
}


bool Numeric::extendedIntegerMustBeLessThan(int number, int bottom)
{
    // If you add extra digits to the number to make it as long as bottom,
    // must it be less than it?
    if (number < 0 && bottom > 0) {
        return true;
    }
    if (number > 0 && bottom < 0) {
        return false;
    }
    int nd_number = numDigitsInteger(number);
    int nd_bottom = numDigitsInteger(bottom);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with nines.
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "9";
            if (str_number.toInt() >= bottom) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with zeros.
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "0";
            if (str_number.toInt() >= bottom) {
                return false;
            }
        }
        return true;
    }
}


bool Numeric::isValidStartToInteger(int number, int bottom, int top)
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
    */

    if (extendedIntegerMustBeLessThan(number, bottom)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be less than bottom value of"
                 << bottom << "=> fail";
#endif
        return false;
    }
    if (extendedIntegerMustExceed(number, top)) {
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


int Numeric::numDigitsDouble(double number, int max_dp)
{
    // Counts the number of digits in a floating-point number.
    // - ignores sign
    // - includes decimal point

    QString formatted = QString::number(number, 'f', max_dp);
    bool sign_present = number < 0;
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


double Numeric::firstDigitsDouble(double number, int n_digits, int max_dp)
{
    // Returns the first n_digits of a floating point number, as a double.
    // - sign is ignored (can't compare numbers without dropping it)
    // - includes decimal point
    QString formatted = QString::number(number, 'f', max_dp);
    bool sign_present = number < 0;
    QString left = formatted.left(sign_present ? n_digits + 1 : n_digits);
    double result = left.toDouble();
#ifdef DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "- formatted" << formatted
             << "n_digits" << n_digits
             << "left" << left
             << "result" << result;
#endif
    return result;
}


bool Numeric::isValidStartToDouble(double number, double bottom, double top)
{
    if (extendedDoubleMustBeLessThan(number, bottom)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be less than bottom value of"
                 << bottom << "=> fail";
#endif
        return false;
    }
    if (extendedDoubleMustExceed(number, top)) {
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


bool Numeric::extendedDoubleMustExceed(double number, double top)
{
    if (number < 0 && top > 0) {
        return false;
    }
    if (number > 0 && top < 0) {
        return true;
    }
    int nd_number = numDigitsDouble(number);
    int nd_top = numDigitsDouble(top);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with zeros.
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "0";
            if (str_number.toDouble() <= top) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with nines.
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "9";
            if (str_number.toDouble() <= top) {
                return false;
            }
        }
        return true;
    }
}


bool Numeric::extendedDoubleMustBeLessThan(double number, double bottom)
{
    if (number < 0 && bottom > 0) {
        return true;
    }
    if (number > 0 && bottom < 0) {
        return false;
    }
    int nd_number = numDigitsDouble(number);
    int nd_bottom = numDigitsDouble(bottom);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with nines.
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "9";
            if (str_number.toDouble() >= bottom) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with zeros.
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "0";
            if (str_number.toDouble() >= bottom) {
                return false;
            }
        }
        return true;
    }
}
