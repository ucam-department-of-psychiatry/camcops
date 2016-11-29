/*
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
#include "namevaluepair.h"


class NameValueOptions
{
    // Encapsulates a list of name/value pairs.

public:
    NameValueOptions();
    NameValueOptions(std::initializer_list<NameValuePair> options);
    void addItem(const NameValuePair& nvp);
    int size() const;
    const NameValuePair& at(int index) const;
    int indexFromName(const QString& name) const;
    int indexFromValue(const QVariant& value) const;
    void validateOrDie();
    bool validIndex(int index) const;
    void shuffle();
    QString name(int index) const;
    QVariant value(int index) const;
protected:
    QList<NameValuePair> m_options;
};
