#include "strictintvalidator.h"
#include "lib/numericfunc.h"


StrictIntValidator::StrictIntValidator(int bottom, int top, QObject* parent) :
    QIntValidator(bottom, top, parent)
{
    if (top < bottom) {  // user has supplied them backwards
        setRange(top, bottom);  // reverse the range
    }
}



QValidator::State StrictIntValidator::validate(QString& s, int&) const
{
    if (s.isEmpty()) {
        return QValidator::Intermediate;
    }

    QChar decimalPoint = locale().decimalPoint();
    if (s.indexOf(decimalPoint) != -1) {  // Containing a decimal point: not OK
        return QValidator::Invalid;
    }

    int b = bottom();
    int t = top();

    if ((b < 0 || t < 0) && s == "-") {
        return QValidator::Intermediate;
    }
    if ((b > 0 || t > 0) && s == "+") {
        return QValidator::Intermediate;
    }

    bool ok;
    int i = locale().toInt(s, &ok);
    if (!ok) {  // Not an integer.
        return QValidator::Invalid;
    }

    if (i >= b && i <= t) {  // Perfect.
        return QValidator::Acceptable;
    }

    // Is the number on its way to being something valid, or is it already
    // outside the permissible range?
    int nd = Numeric::numDigitsInteger(i);
    int bottom_nd = Numeric::firstDigitsInteger(b, nd);
    int top_nd = Numeric::firstDigitsInteger(t, nd);
    if (i >= bottom_nd && i <= top_nd) {
        return QValidator::Intermediate;
    }
    return QValidator::Invalid;
}
