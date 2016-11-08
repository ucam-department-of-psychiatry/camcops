#include "numericfunc.h"
#include <QString>


// ============================================================================
// Overloaded functions to convert to an integer type
// ============================================================================

int Numeric::strToNumber(const QString& str, int type_dummy)
{
    Q_UNUSED(type_dummy);
    return str.toInt();
}


int Numeric::localeStrToNumber(const QString& str, bool& ok,
                               const QLocale& locale, int type_dummy)
{
    Q_UNUSED(type_dummy);
    return locale.toInt(str, &ok);
}


qlonglong Numeric::strToNumber(const QString& str, qlonglong type_dummy)
{
    Q_UNUSED(type_dummy);
    return str.toLongLong();
}


qlonglong Numeric::localeStrToNumber(const QString& str, bool& ok,
                                     const QLocale& locale,
                                     qlonglong type_dummy)
{
    Q_UNUSED(type_dummy);
    return locale.toLongLong(str, &ok);
}


qulonglong Numeric::strToNumber(const QString& str, qulonglong type_dummy)
{
    Q_UNUSED(type_dummy);
    return str.toULongLong();
}


qulonglong Numeric::localeStrToNumber(const QString& str, bool& ok,
                                      const QLocale& locale,
                                      qulonglong type_dummy)
{
    Q_UNUSED(type_dummy);
    return locale.toULongLong(str, &ok);
}


// ============================================================================
// For double validation
// ============================================================================

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
    if (extendedDoubleMustBeLessThan(number, bottom, top)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << number
                 << "when extended must be less than bottom value of"
                 << bottom << "=> fail";
#endif
        return false;
    }
    if (extendedDoubleMustExceed(number, bottom, top)) {
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


bool Numeric::extendedDoubleMustExceed(double number,
                                       double bottom, double top)
{
    if (number < 0 && top > 0) {
        return false;
    }
    if (number > 0 && top < 0) {
        return true;
    }
    int nd_number = numDigitsDouble(number);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with zeros, to length of top
        int nd_top = numDigitsDouble(top);
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "0";
            if (str_number.toDouble() <= top) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with nines.
        int nd_bottom = numDigitsDouble(bottom);
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "9";
            if (str_number.toDouble() <= top) {
                return false;
            }
        }
        return true;
    }
}


bool Numeric::extendedDoubleMustBeLessThan(double number,
                                           double bottom, double top)
{
    if (number < 0 && bottom > 0) {
        return true;
    }
    if (number > 0 && bottom < 0) {
        return false;
    }
    int nd_number = numDigitsDouble(number);
    QString str_number = QString("%1").arg(number);
    if (number > 0) {
        // Both positive. Extend with nines, to length of top
        int nd_top = numDigitsDouble(top);
        for (int i = 0; i < nd_top - nd_number; ++i) {
            str_number += "9";
            if (str_number.toDouble() >= bottom) {
                return false;
            }
        }
        return true;
    } else {
        // Both negative. Extend with zeros, to length of bottom
        int nd_bottom = numDigitsDouble(bottom);
        for (int i = 0; i < nd_bottom - nd_number; ++i) {
            str_number += "0";
            if (str_number.toDouble() >= bottom) {
                return false;
            }
        }
        return true;
    }
}
