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

// #define DEBUG_VALIDATOR

#include "strictdoublevalidator.h"
#ifdef DEBUG_VALIDATOR
    #include <QDebug>
#endif
#include "lib/numericfunc.h"

StrictDoubleValidator::StrictDoubleValidator(
    const double bottom,
    const double top,
    const int decimals,
    const bool allow_empty,
    QObject* parent
) :
    QDoubleValidator(bottom, top, decimals, parent),
    m_allow_empty(allow_empty)
{
    if (top < bottom) {  // user has supplied them backwards
        setRange(top, bottom, decimals);  // reverse the range
    }
}

QValidator::State StrictDoubleValidator::validate(QString& s, int&) const
{
    using numeric::containsOnlySignOrZeros;

    // 1. Empty string?
    if (s.isEmpty()) {
        if (m_allow_empty) {
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

    // 2. Too many digits after decimal point?
    const QString decimalPoint = locale().decimalPoint();
    int charsAfterPoint = -1;
    if (s.indexOf(decimalPoint) != -1) {
        charsAfterPoint = s.length() - s.indexOf(decimalPoint) - 1;
    }
    if (charsAfterPoint > decimals()) {  // Too many decimals
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO
                 << "too many digits after decimal point -> Invalid";
#endif
        return QValidator::Invalid;
    }

    const double b = bottom();
    const double t = top();
    // Guaranteed that b < t

    // 3. A sign (+, -) by itself?
    if (s == "-") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain -";
#endif
        return b < 0 ? QValidator::Intermediate : QValidator::Invalid;
    }
    if (s == "+") {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "plain +";
#endif
        return t > 0 ? QValidator::Intermediate : QValidator::Invalid;
    }

    // 4. Garbage that isn't a number?
    bool ok;
    const double d = locale().toDouble(s, &ok);
    if (!ok) {  // Not a double
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "not a double -> Invalid";
#endif
        return QValidator::Invalid;
    }

    // 5. Already within range?
    if (b <= d && d <= t) {  // Perfect.
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "perfect -> Acceptable";
#endif
        return QValidator::Acceptable;
    }

    // 6. Contains only leading zeroes?
    if (containsOnlySignOrZeros(s)) {
        if (s.startsWith("-") && b > 0) {
#ifdef DEBUG_VALIDATOR
            qDebug() << Q_FUNC_INFO << "-0, bottom > 0 -> Invalid";
#endif
            return QValidator::Invalid;
        }
        if (s.startsWith("+") && t < 0) {
#ifdef DEBUG_VALIDATOR
            qDebug() << Q_FUNC_INFO << "+0, top < 0 -> Invalid";
#endif
            return QValidator::Invalid;
        }
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO << "leading zeros only -> Intermediate";
#endif
        return QValidator::Intermediate;
    }

    // 7. Is the number on its way to being something valid?
    if (numeric::isValidStartToDouble(d, b, t, decimals(), decimalPoint)) {
#ifdef DEBUG_VALIDATOR
        qDebug() << Q_FUNC_INFO
                 << "within range for number of digits -> Intermediate; s ="
                 << s;
#endif
        return QValidator::Intermediate;
    }

    // 8. By elimination: it is invalid.
#ifdef DEBUG_VALIDATOR
    qDebug() << Q_FUNC_INFO << "end of function -> Invalid; s =" << s;
#endif
    return QValidator::Invalid;
}
