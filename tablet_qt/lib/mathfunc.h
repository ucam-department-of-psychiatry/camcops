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

#pragma once
#include <QVariant>
#include <QVector>


namespace mathfunc {


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

bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1);
bool nearlyEqual(qreal x, qreal y);

QVariant mean(const QVector<QVariant>& values, bool ignore_null = false);
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

QVector<int> intseq(int first, int last, int step = 1);

}  // namespace mathfunc
