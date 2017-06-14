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
#include <QVector>


namespace containers
{


template<typename T>
void forceVectorSize(QVector<T>& vec,
                     int new_size,
                     const T& default_value = T())
{
    int old_size = vec.size();
    // Remove surplus
    for (int i = old_size; i > new_size; --i) {
        vec.pop_back();
    }
    // Add new
    for (int i = old_size; i < new_size; ++i) {
        vec.append(default_value);
    }
}


// first vector minus second vector
template<typename T>
QVector<T> subtract(const QVector<T>& first, const QVector<T>& second)
{
    QVector<T> difference;
    for (const T& first_item : first) {
        if (!second.contains(first_item)) {
            difference.append(first_item);
        }
    }
    return difference;
}


/*
generalization of "at" for multiple indices:

    QVector<QString> v{"zero", "one", "two", "three", "four"};
    QVector<QString> v2 = at(v, {1, 3});
    assert(v2 == QVector<QString>{"one", "three"});
*/
template<typename T>
QVector<T> at(const QVector<T>& vec, const QVector<int>& indices)
{
    const QVector<T>& subset;
    for (int index : indices) {
        subset.append(vec.at(index));
    }
    return vec;
}


template<typename ContainerType>
bool containsAll(const ContainerType& a, const ContainerType& b)
{
    // Does a contain all elements of b?
    for (auto b_element : b) {
        if (!a.contains(b_element)) {
            return false;
        }
    }
    return true;
}


template<typename ContainerType>
ContainerType rotateVector(const ContainerType& v, int n_rotate)
{
    int size = v.size();
    n_rotate = n_rotate % size;  // don't do unnecessary work
    if (n_rotate <= 0) {
        return v;
    }
    ContainerType newvec(size);
    int new_index;
    for (int old_index = 0; old_index < size; ++old_index) {
        new_index = (old_index + n_rotate) % size;
        newvec[new_index] = v.at(old_index);
    }
    return newvec;
}


template<typename ContainerType>
void rotateVectorInPlace(ContainerType& v, int n_rotate)
{
    v = rotateVector(v, n_rotate);
}


}  // namespace containers
