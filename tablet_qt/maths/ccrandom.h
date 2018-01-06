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
#include <algorithm>
#include <random>
#include <QtGlobal>
#include <QStringList>
#include <QVector>


namespace ccrandom {  // not "random"; conflicts

extern std::random_device rd;
extern std::mt19937 rng;

bool coin(qreal p = 0.5);
int randomInt(int minimum, int maximum);
double randomRealExcUpper(double minimum, double maximum);
float nextFloatAbove(float x);
double nextDoubleAboveManual(double x);
double nextDoubleAbove(double x);
double randomRealIncUpper(double minimum, double maximum);


template<typename T>
int randomIndex(const QVector<T>& vec)
{
    if (vec.isEmpty()) {
        return -1;
    }
    return randomInt(0, vec.size() - 1);
}


// Draw without replacement
template<typename T>
T dwor(QVector<T>& bucket)
{
    if (bucket.isEmpty()) {
        return T();
    }
    int index = randomIndex(bucket);
    return bucket.takeAt(index);
}


// Draw with replacement
template<typename T>
T drawreplace(const QVector<T>& bucket)
{
    if (bucket.isEmpty()) {
        return T();
    }
    int index = randomIndex(bucket);
    return bucket.at(index);
}


template<typename T>
void shuffle(QVector<T>& vec)
{
    std::shuffle(vec.begin(), vec.end(), rng);
}


QStringList testRandom();


}  // namespace ccrandom
