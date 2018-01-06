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
#include "db/databaseobject.h"
class CamcopsApp;


class StoredVar : public DatabaseObject
{
public:
    StoredVar(CamcopsApp& app,
              DatabaseManager& db,
              const QString& name = "",  // empty for a specimen
              QVariant::Type type = QVariant::Int,
              const QVariant& default_value = QVariant());
    virtual ~StoredVar();
    bool setValue(const QVariant& value, bool save_to_db = true);
    QVariant value() const;
    QString name() const;
    void makeIndexes();
protected:
    // http://stackoverflow.com/questions/411103/function-with-same-name-but-different-signature-in-derived-class
    // http://stackoverflow.com/questions/1628768/why-does-an-overridden-function-in-the-derived-class-hide-other-overloads-of-the
    using DatabaseObject::setValue;
    using DatabaseObject::value;
protected:
    QString m_name;  // only for name(), really
    QVariant::Type m_type;  // what QVariant type are we representing?
    QString m_value_fieldname;  // which field is in active use?
};
