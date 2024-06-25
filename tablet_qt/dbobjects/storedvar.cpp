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

// #define DEBUG_SET_VALUE

#include "storedvar.h"

#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "lib/uifunc.h"

const QString STOREDVAR_TABLENAME("storedvar");

const QString NAME_FIELDNAME("name");
const QString TYPE_FIELDNAME("type");
// - No need to keep to legacy fieldnames (valueInteger, valueReal, valueText)
//   as we'll no longer be uploading these.
const QString VALUE_BOOL_FIELDNAME("value_bool");
const QString VALUE_INTEGER_FIELDNAME("value_integer");
const QString VALUE_REAL_FIELDNAME("value_real");
const QString VALUE_TEXT_FIELDNAME("value_text");

// - Also, SQLite is typeless... could make use of that, and store all values
//   in the same column. But for generality:
const QMap<const int, QString> COLMAP{
    // Which database field shall we use to store each QVariant type?
    {QMetaType::Bool, VALUE_BOOL_FIELDNAME},
    {QMetaType::QDateTime, VALUE_TEXT_FIELDNAME},
    {QMetaType::Double, VALUE_REAL_FIELDNAME},
    {QMetaType::Int, VALUE_INTEGER_FIELDNAME},
    {QMetaType::LongLong, VALUE_INTEGER_FIELDNAME},
    {QMetaType::QString, VALUE_TEXT_FIELDNAME},
    {QMetaType::QUuid, VALUE_TEXT_FIELDNAME},
};
const QMap<const int, QString> TYPEMAP{
    // What value should we put in the 'type' database column to indicate
    // the QVariant type in use?
    // https://doc.qt.io/qt-6.5/qvariant-obsolete.html#Type-enum
    {QMetaType::Bool, "Bool"},
    {QMetaType::QDateTime, "DateTime"},
    {QMetaType::Double, "Double"},
    {QMetaType::Int, "Int"},
    {QMetaType::LongLong, "LongLong"},
    {QMetaType::QString, "String"},
    {QMetaType::QUuid, "Uuid"},
};

StoredVar::StoredVar(
    CamcopsApp& app,
    DatabaseManager& db,
    const QString& name,
    const QMetaType type,
    const QVariant& default_value
) :
    DatabaseObject(
        app,
        db,
        STOREDVAR_TABLENAME,
        dbconst::PK_FIELDNAME,
        true,
        false,
        false,
        false
    ),
    m_name(name),
    m_type(type),
    m_value_fieldname("")
{
    const int type_id = type.id();

    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(
        NAME_FIELDNAME, QMetaType::fromType<QString>(), true, true, false
    );
    addField(
        TYPE_FIELDNAME, QMetaType::fromType<QString>(), true, false, false
    );
    QMapIterator<const int, QString> i(COLMAP);
    while (i.hasNext()) {
        i.next();
        const int fieldtype = i.key();
        const QString fieldname = i.value();
        if (!hasField(fieldname)) {
            // We can have duplicate/overlapping fieldnames, and it will be
            // happy (if the types are appropriately interconvertible).
            // The Field will have the type of the FIRST one inserted.
            // However, it is dreadfully confusing if you put the Bool
            // definition before the Int one, and all your integers are
            // converted to 1 or 0. So use different ones!
            addField(fieldname, QMetaType(fieldtype), false, false, false);
        }
        if (fieldtype == type_id) {
            // Define our primary field
            m_value_fieldname = fieldname;
        }
    }
    if (m_value_fieldname.isEmpty()) {
        uifunc::stopApp(
            QString(
                "StoredVar::StoredVar: m_value_fieldname unknown to StoredVar "
                "with name=%1, type=%2; is the type missing from COLMAP "
                "(in storedvar.cpp)?"
            )
                .arg(name, QString::number(type_id))
        );
    }
    if (!TYPEMAP.contains(type_id)) {
        qCritical() << Q_FUNC_INFO << "QVariant type unknown:" << type_id;
        uifunc::stopApp(
            "StoredVar::StoredVar: type unknown to StoredVar; see debug "
            "console for details and check TYPEMAP (in storedvar.cpp)"
        );
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    if (!name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        const bool success = load(NAME_FIELDNAME, name);
        if (!success) {
            setValue(NAME_FIELDNAME, name);
            setValue(TYPE_FIELDNAME, TYPEMAP[type_id]);
            // qDebug() << "Setting type to:" << type;
            setValue(default_value);
            save();
        }
    }
}

bool StoredVar::setValue(const QVariant& value, const bool save_to_db)
{
#ifdef DEBUG_SET_VALUE
    qDebug() << Q_FUNC_INFO << "Setting" << m_name << "to" << value;
#endif
    const bool changed = setValue(m_value_fieldname, value);
    if (save_to_db) {
        save();
    }
    return changed;
}

QVariant StoredVar::value() const
{
    QVariant v = value(m_value_fieldname);
    v.convert(m_type);
    return v;
}

QString StoredVar::name() const
{
    return m_name;
}

void StoredVar::makeIndexes()
{
    m_db.createIndex(
        "_idx_storedvar_name", STOREDVAR_TABLENAME, {NAME_FIELDNAME}
    );
}
