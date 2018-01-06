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
#include <QDebug>
#include <QVariant>


class Field
{
public:
    Field();
    Field(const QString& name, QVariant::Type type,
          bool mandatory = false, bool unique = false, bool pk = false,
          const QVariant& default_value = QVariant());
    Field(const QString& name, const QString& type_name,
          bool mandatory = false, bool unique = false, bool pk = false,
          const QVariant& default_value = QVariant());
    Field& setPk(bool pk);
    Field& setUnique(bool unique);
    Field& setMandatory(bool pk);
    Field& setDefaultValue(const QVariant& value);
    QString name() const;
    QVariant::Type type() const;
    bool isPk() const;
    bool isUnique() const;
    bool isMandatory() const;
    bool notNull() const;
    QString sqlColumnDef() const;
    QVariant value() const;
    QString prettyValue(int dp = -1) const;  // returns a QString representation
    bool setValue(const QVariant& value);  // returns: dirty?
    bool nullify();  // returns: dirty?
    bool isNull() const;
    bool isDirty() const;
    void setDirty();
    void clearDirty();
    friend QDebug operator<<(QDebug debug, const Field& f);

    // To support new field types, modify these three:
    QString sqlColumnType() const;
    void setFromDatabaseValue(const QVariant& db_value); // SQLite -> C++
    QVariant databaseValue() const; // C++ -> SQLite

protected:
    QString m_name;
    QVariant::Type m_type;
    QString m_type_name;
    bool m_pk;
    bool m_unique;
    bool m_mandatory;
    bool m_set;
    bool m_dirty;
    QVariant m_default_value;  // C++, not database
    QVariant m_value;
};
