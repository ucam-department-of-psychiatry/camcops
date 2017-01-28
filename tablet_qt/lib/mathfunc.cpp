/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "mathfunc.h"
#include <QObject>

namespace mathfunc {


QVariant mean(const QList<QVariant>& values, bool ignore_null)
{
    double total = 0;
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            if (ignore_null) {
                continue;
            } else {
                return QVariant();  // mean of something including null is null
            }
        }
        n += 1;
        total += v.toDouble();
    }
    if (n == 0) {
        return QVariant();
    }
    return total / n;
}


int sumInt(const QList<QVariant>& values)
{
    int total = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toInt();  // gives 0 if it is NULL
    }
    return total;
}


double sumDouble(const QList<QVariant>& values)
{
    double total = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toDouble();  // gives 0 if it is NULL
    }
    return total;
}


int countTrue(const QList<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            n += 1;
        }
    }
    return n;
}


bool allTrue(const QList<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.toBool()) {
            return false;
        }
    }
    return true;
}


bool allFalseOrNull(const QList<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            return false;
        }
    }
    return true;
}


bool anyNull(const QList<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            return true;
        }
    }
    return false;
}


bool noneNull(const QList<QVariant>& values)
{
    return !anyNull(values);
}


int numNull(const QList<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            n += 1;
        }
    }
    return n;
}


int numNotNull(const QList<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.isNull()) {
            n += 1;
        }
    }
    return n;
}


bool eq(const QVariant& x, int test)
{
    // SQL principle: NULL is not equal to anything
    return !x.isNull() && x.toInt() == test;
}


bool eq(const QVariant& x, bool test)
{
    return !x.isNull() && x.toBool() == test;
}


bool eqOrNull(const QVariant& x, int test)
{
    return x.isNull() || x.toInt() != test;
}


bool eqOrNull(const QVariant& x, bool test)
{
    return x.isNull() || x.toBool() != test;
}



int countWhere(const QList<QVariant>& test_values,
               const QList<QVariant>& where_values)
{
    int n = 0;
    int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (where_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


int countWhereNot(const QList<QVariant>& test_values,
                  const QList<QVariant>& where_not_values)
{
    int n = 0;
    int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (!where_not_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


QString percent(double numerator, double denominator, int dp)
{
    double pct = 100 * numerator / denominator;
    return QString("%1%").arg(pct, 0, 'f', dp);
}


QString scoreString(int numerator, int denominator, bool show_percent, int dp)
{
    QString result = QString("<b>%1</b>/%2").arg(numerator).arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator, denominator, dp) + ")";
    }
    return result;
}


QString scoreStringWithPercent(int numerator, int denominator, int dp)
{
    return scoreString(numerator, denominator, true, dp);
}


QString totalScorePhrase(int numerator, int denominator)
{
    return QString("%1: %2")
            .arg(QObject::tr("Total score"))
            .arg(scoreString(numerator, denominator, false));
}


}  // namespace mathfunc
