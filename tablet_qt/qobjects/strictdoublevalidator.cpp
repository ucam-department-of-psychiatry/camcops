// #define DEBUG_VALIDATOR

#include "strictdoublevalidator.h"
#ifdef DEBUG_VALIDATOR
#include <QDebug>
#endif
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
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "empty -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    QChar decimalPoint = locale().decimalPoint();
    int charsAfterPoint = -1;
    if (s.indexOf(decimalPoint) != -1) {
        charsAfterPoint = s.length() - s.indexOf(decimalPoint) - 1;
    }
    if (charsAfterPoint > decimals()) {  // Too many decimals
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO <<
                    "too many digits after decimal point -> Invalid";
#endif
        return QValidator::Invalid;
    }

    double b = bottom();
    double t = top();
    // Guaranteed that b < t

    if (s == "-") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain -";
#endif
        return b < 0 ? QValidator::Intermediate  : QValidator::Invalid;
    }
    if (s == "+") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain +";
#endif
        return t > 0 ? QValidator::Intermediate  : QValidator::Invalid;
    }

    bool ok;
    double d = locale().toDouble(s, &ok);
    if (!ok) {  // Not a double
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "not a double -> Invalid";
#endif
        return QValidator::Invalid;
    }

    if (d >= b && d <= t) {  // Perfect.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "perfect -> Acceptable";
#endif
        return QValidator::Acceptable;
    }

    // "Negative zero" is a special case -- a string starting with "-" that
    // evaluates to zero, like "-0" or "--0". The presence of the minus sign
    // can't be detected in the numeric version, so we have to handle it
    // specially.
    if (s.startsWith("-") && d == 0 && charsAfterPoint < decimals()) {
        // If we get here, we already know that negative numbers are OK.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "negative zero -> Intermediate; s"
                 << s << "charsAfterPoint" << charsAfterPoint;
#endif
        return QValidator::Intermediate;
    }

    // Is the number on its way to being something valid, or is it already
    // outside the permissible range?
    if (t < 0 && !s.startsWith("-")) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "top < 0 and number doesn't start with - -> Invalid";
#endif
        return QValidator::Invalid;
    }
    if (Numeric::isValidStartToDouble(d, b, t)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO
                 << "within range for number of digits -> Intermediate; s ="
                 << s;
#endif
        return QValidator::Intermediate;
    }
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "end of function -> Invalid; s =" << s;
#endif
    return QValidator::Invalid;
}
