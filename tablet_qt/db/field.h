/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once
#include <QDebug>
#include <QMetaType>
#include <QVariant>

// Represents a field (the intersection of a column and a row in a database).
//
// This object represents both a column (name, type, etc.; e.g. "mycol INT NOT
// NULL") and a specific value (e.g. 7).

class Field
{
public:
    // Default constructor
    Field();

    // Construct by QVariant type.
    // Args:
    //  name: field name
    //  type: data type to be represented
    //  mandatory: NOT NULL?
    //  unique: UNIQUE?
    //  pk: PRIMARY KEY?
    //  default_value: value if not otherwise set
    Field(
        const QString& name,
        QMetaType type,
        bool mandatory = false,
        bool unique = false,
        bool pk = false,
        const QVariant& cpp_default_value = QVariant(),
        const QVariant& db_default_value = QVariant()
    );

    // Sets whether this field is a primary key (PK) or not.
    Field& setPk(bool pk);

    // Sets whether this field has a UNIQUE constraint or not.
    Field& setUnique(bool unique);

    // Sets whether this field has a NOT NULL constraint or not.
    Field& setMandatory(bool pk);

    // Sets this field's C++ default value.
    Field& setCppDefaultValue(const QVariant& value);

    // Sets this field's database default value.
    Field& setDbDefaultValue(const QVariant& value);

    // Sets this field's C++ and database default value.
    Field& setDefaultValue(const QVariant& value);

    // Does this field have a non-NULL default database value?
    bool hasDbDefaultValue() const;

    // Returns the field's name.
    QString name() const;

    // Returns the field's data type.
    QMetaType type() const;

    // Is it a PK?
    bool isPk() const;

    // Is it subject to a UNIQUE constraint?
    bool isUnique() const;

    // Is it marked as NOT NULL?
    bool isMandatory() const;

    // Should it be NOT NULL? True if isMandatory() or isPk(); see code for
    // explanation (relates to an old SQLite bug).
    bool notNull() const;

    // Returns SQL text to define this column, e.g. "mycol INT NOT NULL".
    QString sqlColumnDef() const;

    // Returns the value stored in this field.
    QVariant value() const;

    // Returns a pretty-printed version of the value in this field, for
    // display purposes only.
    QString prettyValue(int dp = -1) const;

    // Sets the field's value. Returns: dirty?
    bool setValue(const QVariant& value);

    // Sets the field's value to NULL. Returns: dirty?
    bool nullify();

    // Is the field's value NULL?
    bool isNull() const;

    // Is the field dirty (marked as needing to be written to the database)?
    bool isDirty() const;

    // Sets the dirty flag.
    void setDirty();

    // Clears the dirty flag.
    void clearDirty();

    // Debugging representation.
    friend QDebug operator<<(QDebug debug, const Field& f);

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // To support new field types, modify these three:
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // Returns the SQLite column type (e.g. "INT", "TEXT").
    QString sqlColumnType() const;

    // SQLite -> C++
    // Sets the internal value from something read from the database.
    void setFromDatabaseValue(const QVariant& db_value);  // SQLite -> C++

    // C++ -> SQLite
    // Returns the value to be stored in the database.
    QVariant databaseValue() const;  // C++ -> SQLite

protected:
    // Field name
    QString m_name;

    // Data type
    QMetaType m_type;

    // PK?
    bool m_pk;

    // UNIQUE constraint?
    bool m_unique;

    // Mandatory (NOT NULL)?
    bool m_mandatory;

    // Has it been set, somehow?
    bool m_set;

    // Is it dirty (requiring writing to the database)?
    bool m_dirty;

    // Default C++ value (not database defai;t).
    QVariant m_cpp_default_value;

    // Default database value (not C++ default).
    QVariant m_db_default_value;

    // Stored value
    QVariant m_value;
};
