#include "strictdoublevalidator.h"
#include "lib/numericfunc.h"


StrictDoubleValidator::StrictDoubleValidator(double bottom, double top,
                                             int decimals,  QObject* parent) :
    QDoubleValidator(bottom, top, decimals, parent)
{
    if (top < bottom) {  // user has supplied them backwards
        setRange(top, bottom, decimals);  // reverse the range
    }
}


QValidator::State StrictDoubleValidator::validate(QString& s, int&) const
{
    if (s.isEmpty()) {
        return QValidator::Intermediate;
    }

    QChar decimalPoint = locale().decimalPoint();
    if (s.indexOf(decimalPoint) != -1) {
        int charsAfterPoint = s.length() - s.indexOf(decimalPoint) - 1;
        if (charsAfterPoint > decimals()) {  // Too many decimals
            return QValidator::Invalid;
        }
    }

    double b = bottom();
    double t = top();
    // Guaranteed that b < t

    if (s == "-") {
        return b < 0 ? QValidator::Intermediate  : QValidator::Invalid;
    }
    if (s == "+") {
        return t > 0 ? QValidator::Intermediate  : QValidator::Invalid;
    }

    bool ok;
    double d = locale().toDouble(s, &ok);
    if (!ok) {  // Not a double
        return QValidator::Invalid;
    }

    if (d >= b && d <= t) {  // Perfect.
        return QValidator::Acceptable;
    }

    // Is the number on its way to being something valid, or is it already
    // outside the permissible range?
    if (t < 0 && !s.startsWith("-")) {
        return QValidator::Invalid;
    }
    int nd = Numeric::numDigitsDouble(d);
    double bottom_nd = Numeric::firstDigitsDouble(b, nd);
    double top_nd = Numeric::firstDigitsDouble(t, nd);
    if (d >= bottom_nd && d <= top_nd) {
        return QValidator::Intermediate;
    }
    return QValidator::Invalid;
}
