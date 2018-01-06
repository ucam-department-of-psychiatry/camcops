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

#pragma once

#include <QVariant>
#include <QVector>


namespace mathfunc {

// ============================================================================
// Basic sums
// ============================================================================

template<typename T>
int sgn(T val)
{
    // Returns -1 if val is negative, 0 if zero, and +1 if positive.
    // http://stackoverflow.com/questions/1903954/is-there-a-standard-sign-function-signum-sgn-in-c-c
    return (T(0) < val) - (val < T(0));
}


template<typename T>
T mod(T x, T y)
{
    // Returns x mod y, coping with negatives.
    // http://stackoverflow.com/questions/11980292/how-to-wrap-around-a-range
    if (y == 0) {
        return 0;  // stupid caller
    }
    return x - y * std::floor(x / y);
}

// Implemented in GNU C++11 standard library but not available for Android
// (e.g. https://github.com/android-ndk/ndk/issues/82 ),
// and not offered by <QtGlobal>

template<typename T>
T trunc(const T& x)
{
    // http://en.cppreference.com/w/cpp/numeric/math/trunc
    // http://en.cppreference.com/w/cpp/numeric/math/floor
    // For x >= 0, floor and trunc are the same.
    // For x < 0, floor moves towards -Inf and trunc moves towards 0.
    // Example: floor(1.5) == trunc(1.5) == 1.0
    // Example: floor(-1.5) == -2.0; trunc(-1.5) == -1.0
    // The answer:
    // https://stackoverflow.com/questions/6709405/is-there-a-trunc-function-in-c

    return x > 0 ? std::floor(x) : std::ceil(x);
}


bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1);
bool nearlyEqual(qreal x, qreal y);
QVariant mean(const QVector<QVariant>& values, bool ignore_null = false);
qreal mean(qreal a, qreal b);
int centile(qreal x, qreal minimum, qreal maximum);
double kahanSum(const QVector<double>& vec);

// ============================================================================
// QVariant operations, and QVariant collections
// ============================================================================

int sumInt(const QVector<QVariant>& values);
double sumDouble(const QVector<QVariant>& values);

bool falseNotNull(const QVariant& value);

bool allTrue(const QVector<QVariant>& values);
bool anyTrue(const QVector<QVariant>& values);
bool allFalseOrNull(const QVector<QVariant>& values);
bool allFalse(const QVector<QVariant>& values);
bool anyFalse(const QVector<QVariant>& values);
bool anyNull(const QVector<QVariant>& values);
bool noneNull(const QVector<QVariant>& values);
bool anyNullOrEmpty(const QVector<QVariant>& values);
bool noneNullOrEmpty(const QVector<QVariant>& values);

int countTrue(const QVector<QVariant>& values);
int countFalse(const QVector<QVariant>& values);
int countNull(const QVector<QVariant>& values);
int countNotNull(const QVector<QVariant>& values);

bool eq(const QVariant& x, int test);
bool eq(const QVariant& x, bool test);
bool eqOrNull(const QVariant& x, int test);
bool eqOrNull(const QVariant& x, bool test);

int countWhere(const QVector<QVariant>& test_values,
               const QVector<QVariant>& where_values);
int countWhereNot(const QVector<QVariant>& test_values,
                  const QVector<QVariant>& where_not_values);

// ============================================================================
// Functions for scoring
// ============================================================================

QString percent(double numerator, double denominator, int dp = 1);
QString scoreString(int numerator, int denominator,
                    bool show_percent = false, int dp = 1);
QString scoreString(double numerator, int denominator,
                    bool show_percent = false, int dp = 1);
QString scoreStringVariant(const QVariant& numerator, int denominator,
                           bool show_percent = false, int dp = 1);
QString scoreStringWithPercent(int numerator, int denominator, int dp = 1);
QString scoreStringWithPercent(double numerator, int denominator, int dp = 1);
QString scorePhrase(const QString& description, int numerator, int denominator,
                    const QString& separator = ": ",
                    const QString& suffix = ".");
QString scorePhrase(const QString& description, double numerator, int denominator,
                    const QString& separator = ": ",
                    const QString& suffix = ".",
                    int dp = 1);
QString scorePhraseVariant(
        const QString& description, const QVariant& numerator, int denominator,
        const QString& separator = ": ",
        const QString& suffix = ".",
        int dp = 1);
QString totalScorePhrase(int numerator, int denominator,
                         const QString& separator = ": ",
                         const QString& suffix = ".");
QString totalScorePhrase(double numerator, int denominator,
                         const QString& separator = ": ",
                         const QString& suffix = ".",
                         int dp = 1);

// ============================================================================
// Sequence and range generation
// ============================================================================

template<typename T>
QVector<T> seq(T first, T last, T step = 1)
{
    QVector<T> v;
    if (step > 0) {
        for (T i = first; i <= last; i += step) {
            v.append(i);
        }
    } else if (step < 0) {
        for (T i = first; i >= last; i -= step) {
            v.append(i);
        }
    }
    return v;
}


QVector<int> range(int start, int end);  // start to (end - 1) inclusive
QVector<int> range(int n);  // 0 to (n - 1) inclusive


template<typename T>
QVector<T> rep(const T& x, int n)
{
    return QVector<T>(n, x);
}


template<typename T>
QVector<T> rep(const QVector<T>& values, int each, int times)
{
    QVector<T> result;
    for (int t = 0; t < times; ++t) {
        for (const T& x : values) {
            for (int e = 0; e < each; ++e) {
                result.append(x);
            }
        }
    }
    return result;
}


// ============================================================================
// Spacing things out
// ============================================================================

QVector<qreal> distribute(int n, qreal minimum, qreal maximum);
QPair<int, int> gridDimensions(int n, qreal aspect = 1.0);

// ============================================================================
// Numerical conversions
// ============================================================================

int proportionToByte(qreal proportion);  // 0.0-1.0 to 0-255
qreal byteToProportion(int byte);  // 0-255 to 0.0-1.0

int proportionToIntPercent(qreal proportion);  // 0.0-1.0 to 0-100
qreal intPercentToProportion(int percent);  // 0-100 to 0.0-1.0

}  // namespace mathfunc
