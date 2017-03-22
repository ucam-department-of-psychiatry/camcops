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
#include <QList>
#include <QVariant>


namespace mathfunc {

QVariant mean(const QList<QVariant>& values, bool ignore_null = false);
int sumInt(const QList<QVariant>& values);
double sumDouble(const QList<QVariant>& values);

int countTrue(const QList<QVariant>& values);
bool allTrue(const QList<QVariant>& values);
bool anyTrue(const QList<QVariant>& values);
bool allFalseOrNull(const QList<QVariant>& values);
bool anyNull(const QList<QVariant>& values);
bool noneNull(const QList<QVariant>& values);
int numNull(const QList<QVariant>& values);
int numNotNull(const QList<QVariant>& values);

bool eq(const QVariant& x, int test);
bool eq(const QVariant& x, bool test);
bool eqOrNull(const QVariant& x, int test);
bool eqOrNull(const QVariant& x, bool test);

int countWhere(const QList<QVariant>& test_values,
               const QList<QVariant>& where_values);
int countWhereNot(const QList<QVariant>& test_values,
                  const QList<QVariant>& where_not_values);

QString toDp(double x, int dp);
QString percent(double numerator, double denominator, int dp = 1);
QString scoreString(int numerator, int denominator,
                    bool show_percent = false, int dp = 1);
QString scoreStringWithPercent(int numerator, int denominator, int dp = 1);
QString totalScorePhrase(int numerator, int denominator);

}  // namespace mathfunc
