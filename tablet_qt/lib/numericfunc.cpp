#include "numericfunc.h"
#include <QString>
#include <QDebug>


int Numeric::numDigitsInteger(int number, bool count_sign)
{
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
    int current_digits = numDigitsInteger(number);
    while (current_digits > n_digits) {
        number /= 10;  // assumes base 10
        --current_digits;
    }
    return number;
}


int Numeric::numDigitsDouble(double number, int max_dp)
{
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
    // - sign is ignored (can't compare numbers without dropping it)
    // - includes decimal point
    QString formatted = QString::number(number, 'f', max_dp);
    bool sign_present = number < 0;
    QString left = formatted.left(sign_present ? n_digits + 1 : n_digits);
    double result = left.toDouble();
    qDebug() << "firstDigitsDouble: formatted" << formatted
             << "n_digits" << n_digits
             << "left" << left
             << "result" << result;
    return result;
}
