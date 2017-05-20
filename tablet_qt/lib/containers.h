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


}  // namespace containers
