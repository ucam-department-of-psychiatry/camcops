// #define DEBUG_VALIDATOR

#include "strictintvalidator.h"
#ifdef DEBUG_VALIDATOR
#include <QDebug>
#endif
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
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "empty -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    QChar decimalPoint = locale().decimalPoint();
    if (s.indexOf(decimalPoint) != -1) {  // Containing a decimal point: not OK
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "decimal point -> Invalid";
#endif
        return QValidator::Invalid;
    }

    int b = bottom();
    int t = top();

    if ((b < 0 || t < 0) && s == "-") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain -, negatives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }
    if ((b > 0 || t > 0) && s == "+") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain +, positives OK -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    bool ok;
    int i = locale().toInt(s, &ok);
    if (!ok) {  // Not an integer.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "not an integer -> Invalid";
#endif
        return QValidator::Invalid;
    }

    if (i >= b && i <= t) {  // Perfect.
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
    if (Numeric::isValidStartToInteger(i, b, t)) {
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
