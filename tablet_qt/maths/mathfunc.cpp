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

#include "mathfunc.h"

#include <QtMath>  // for e.g. qSqrt()
#include <QObject>
#include "common/textconst.h"
#include "lib/convert.h"
#include "maths/eigenfunc.h"
#include "maths/floatingpoint.h"
#include "maths/mlpackfunc.h"
#include "maths/statsfunc.h"

namespace mathfunc {


// ============================================================================
// Basic sums
// ============================================================================

bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1)
{
    // There are two ranges: (a0, a1) and (b0, b1). Is there overlap?
    if (a0 > a1) {
        std::swap(a0, a1);
    }
    if (b0 > b1) {
        std::swap(b0, b1);
    }
    if (a1 < b0 || b1 < a0) {
        // A is entirely less than B, or B is entirely less than A.
        return false;
    }
    // Otherwise, there's overlap.
    return true;
}


bool nearlyEqual(const qreal x, const qreal y)
{
    // LESS GOOD: return qFuzzyIsNull(x - y);
    // BETTER:
    FloatingPoint<qreal> fx(x);
    FloatingPoint<qreal> fy(y);
    return fx.AlmostEquals(fy);
}


QVariant mean(const QVector<QVariant>& values, const bool ignore_null)
{
    // ignore_null true: return the mean of the values, ignoring any NULLs.
    // ignore_null false: return the mean, or NULL if any are NULL.
    double total = 0;
    int n = 0;
    const int length = values.length();
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


qreal mean(const qreal a, const qreal b)
{
    return (a + b) / 2;
}


int centile(const qreal x, const qreal minimum, const qreal maximum)
{
    const qreal fraction = (x - minimum) / (maximum - minimum);
    const qreal centile = 100 * fraction;
    if (!qIsFinite(centile)) {
        return -1;
    }
    return centile;  // truncates to int, which is what we want
}


double kahanSum(const QVector<double>& vec)
{
    // https://en.wikipedia.org/wiki/Kahan_summation_algorithm
    // https://codereview.stackexchange.com/questions/56532/kahan-summation
    double sum = 0.0;
    double c = 0.0;  // running compensation for lost low-order bits
    for (const double value : vec) {
        double y = value - c;
        double t = sum + y;
        c = (t - sum) - y;
        sum = t;
    }
    return sum;
}


// ============================================================================
// QVariant operations, and QVariant collections
// ============================================================================

int sumInt(const QVector<QVariant>& values)
{
    int total = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toInt();  // gives 0 if it is NULL
    }
    return total;
}


double sumDouble(const QVector<QVariant>& values)
{
    double total = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toDouble();  // gives 0 if it is NULL
    }
    return total;
}


bool falseNotNull(const QVariant& value)
{
    if (value.isNull() || value.toBool()) {  // null or true
        return false;
    }
    return true;
}


bool allTrue(const QVector<QVariant>& values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.toBool()) {
            return false;
        }
    }
    return true;
}


bool anyTrue(const QVector<QVariant>& values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            return true;
        }
    }
    return false;
}


bool allFalseOrNull(const QVector<QVariant>& values)
{
    return !anyTrue(values);
}


bool allFalse(const QVector<QVariant>& values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull() || v.toBool()) {  // null or true
            return false;
        }
    }
    return true;
}


bool anyFalse(const QVector<QVariant> &values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.isNull() && !v.toBool()) {  // not null and not true
            return true;
        }
    }
    return false;
}


bool anyNull(const QVector<QVariant>& values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            return true;
        }
    }
    return false;
}


bool noneNull(const QVector<QVariant>& values)
{
    return !anyNull(values);
}


bool anyNullOrEmpty(const QVector<QVariant>& values)
{
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull() || v.toString().isEmpty()) {
            return true;
        }
    }
    return false;
}


bool noneNullOrEmpty(const QVector<QVariant>& values)
{
    return !anyNullOrEmpty(values);
}


int countTrue(const QVector<QVariant>& values)
{
    int n = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            n += 1;
        }
    }
    return n;
}


int countFalse(const QVector<QVariant>& values)
{
    int n = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (falseNotNull(v)) {
            n += 1;
        }
    }
    return n;
}


int countNull(const QVector<QVariant>& values)
{
    int n = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            n += 1;
        }
    }
    return n;
}


int countNotNull(const QVector<QVariant>& values)
{
    int n = 0;
    const int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.isNull()) {
            n += 1;
        }
    }
    return n;
}


bool eq(const QVariant& x, const int test)
{
    // SQL principle: NULL is not equal to anything
    return !x.isNull() && x.toInt() == test;
}


bool eq(const QVariant& x, const bool test)
{
    return !x.isNull() && x.toBool() == test;
}


bool eqOrNull(const QVariant& x, const int test)
{
    return x.isNull() || x.toInt() != test;
}


bool eqOrNull(const QVariant& x, const bool test)
{
    return x.isNull() || x.toBool() != test;
}



int countWhere(const QVector<QVariant>& test_values,
               const QVector<QVariant>& where_values)
{
    int n = 0;
    const int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (where_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


int countWhereNot(const QVector<QVariant>& test_values,
                  const QVector<QVariant>& where_not_values)
{
    int n = 0;
    const int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (!where_not_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


// ============================================================================
// Functions for scoring
// ============================================================================

QString percent(const double numerator,
                const double denominator,
                const int dp)
{
    const double pct = 100 * numerator / denominator;
    return convert::toDp(pct, dp) + "%";
}


QString scoreString(const int numerator,
                    const int denominator,
                    const bool show_percent,
                    const int dp)
{
    QString result = QString("<b>%1</b>/%2").arg(numerator).arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator, denominator, dp) + ")";
    }
    return result;
}


QString scoreString(const double numerator,
                    const int denominator,
                    const bool show_percent,
                    const int dp)
{
    QString result = QString("<b>%1</b>/%2")
            .arg(convert::toDp(numerator, dp))
            .arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator, denominator, dp) + ")";
    }
    return result;
}


QString scoreStringVariant(const QVariant& numerator, const int denominator,
                           const bool show_percent, const int dp)
{
    QString result = QString("<b>%1</b>/%2")
            .arg(convert::prettyValue(numerator, dp))
            .arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator.toDouble(), denominator, dp) + ")";
    }
    return result;
}


QString scoreStringWithPercent(const int numerator,
                               const int denominator,
                               const int dp)
{
    return scoreString(numerator, denominator, true, dp);
}


QString scorePhrase(const QString& description,
                    const int numerator, const int denominator,
                    const QString& separator, const QString& suffix)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreString(numerator, denominator, false),
                 suffix);
}


QString scorePhrase(const QString& description,
                    const double numerator, const int denominator,
                    const QString& separator, const QString& suffix,
                    const int dp)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreString(numerator, denominator, false, dp),
                 suffix);
}


QString scorePhraseVariant(const QString& description,
                           const QVariant& numerator, const int denominator,
                           const QString& separator, const QString& suffix,
                           const int dp)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreStringVariant(numerator, denominator, false, dp),
                 suffix);
}


QString totalScorePhrase(const int numerator, const int denominator,
                         const QString& separator, const QString& suffix)
{
    return scorePhrase(textconst::TOTAL_SCORE, numerator, denominator,
                       separator, suffix);
}


QString totalScorePhrase(const double numerator, const int denominator,
                         const QString& separator, const QString& suffix,
                         const int dp)
{
    return scorePhrase(textconst::TOTAL_SCORE, numerator, denominator,
                       separator, suffix, dp);
}


// ============================================================================
// Sequence and range generation
// ============================================================================

QVector<int> range(const int start, const int end)
{
    return seq(start, end - 1, 1);
}


QVector<int> range(const int n)
{
    // returns 0 to n-1 inclusive
    return range(0, n);
}


// ============================================================================
// Spacing things out
// ============================================================================

QVector<qreal> distribute(const int n, qreal minimum, qreal maximum)
{
    // Fence/fence-post problem; return centre of fence segments.
    QVector<qreal> posts;
    if (n <= 0) {
        return posts;  // or we'll have division by zero shortly
    }
    if (maximum < minimum) {
        std::swap(minimum, maximum);
    }
    const qreal extent = maximum - minimum;
    const qreal each = extent / n;
    // ... (double / int) gives double
    // https://stackoverflow.com/questions/5563000/implicit-type-conversion-rules-in-c-operators
    const qreal centre_offset = each / 2;
    for (int i = 0; i < n; ++i) {
        posts.append(minimum + i * each + centre_offset);
    }
    return posts;
}


QPair<int, int> gridDimensions(const int n, const qreal aspect)
{
    // Solve the equations:
    //      x * y >= n
    //      aspect ~= x / y
    // ... for smallest x, y. Thus:
    //      x = aspect * y
    //      aspect * y * y >= n
    const int y = qCeil(qSqrt(n / aspect));
    const int x = qCeil(n / y);
    return QPair<int, int>(x, y);
}


// ============================================================================
// Numerical conversions
// ============================================================================

int proportionToByte(const qreal proportion)
{
    // convert 0.0-1.0 to 0-255
    const int a = qRound(qBound(0.0, proportion, 1.0) * 255);
    return qBound(0, a, 255);
}


qreal byteToProportion(const int byte)
{
    // convert 0-255 to 0.0-1.0
    return qBound(0, byte, 255) / 255.0;
}


int proportionToIntPercent(const qreal proportion)
{
    // convert 0.0-1.0 to 0-100
    const int a = qRound(qBound(0.0, proportion, 1.0) * 100);
    return qBound(0, a, 100);
}


qreal intPercentToProportion(const int percent)
{
    // convert 0-100 to 0.0-1.0
    return qBound(0, percent, 100) / 100.0;
}


}  // namespace mathfunc
