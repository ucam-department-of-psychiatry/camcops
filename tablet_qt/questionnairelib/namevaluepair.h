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
#include <QList>
#include <QString>
#include <QVariant>


class NameValuePair
{
    // Encapsulates a single name/value pair.

public:
    NameValuePair() {}  // so it can live in a QVector
    NameValuePair(const QString& name, const QVariant& value);
    const QString& name() const;  // function access write-protects the members
    const QVariant& value() const;
protected:
    QString m_name;
    QVariant m_value;
};
