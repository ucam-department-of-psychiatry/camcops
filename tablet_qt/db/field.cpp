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

#include "field.h"

#include "common/preprocessor_aid.h"  // IWYU pragma: keep
#include "lib/convert.h"
#include "lib/customtypes.h"
#include "lib/datetime.h"
#include "lib/errorfunc.h"
#include "lib/version.h"

const QString SQLITE_TYPE_BLOB("BLOB");
const QString SQLITE_TYPE_INTEGER("INTEGER");
const QString SQLITE_TYPE_REAL("REAL");
const QString SQLITE_TYPE_TEXT("TEXT");

Field::Field(
    const QString& name,
    const QMetaType type,
    const bool mandatory,
    const bool unique,
    const bool pk,
    const QVariant& cpp_default_value,
    const QVariant& db_default_value
) :
    m_name(name),
    m_type(type),
    m_pk(pk),
    m_unique(unique || pk),
    m_mandatory(mandatory || pk),
    m_set(false),
    m_dirty(true)
{
    setCppDefaultValue(cpp_default_value);
    // ... will also set m_value (because m_set is false)
    setDbDefaultValue(db_default_value);
}

Field::Field() :  // needed by QMap
    Field("", QMetaType::fromType<int>())  // delegating constructor (C++11)
{
}

Field& Field::setCppDefaultValue(const QVariant& value)
{
    m_cpp_default_value = value;
    m_cpp_default_value.convert(m_type);
    if (!m_set) {
        m_value = m_cpp_default_value;
    }
    return *this;
}

Field& Field::setDbDefaultValue(const QVariant& value)
{
    m_db_default_value = value;
    m_db_default_value.convert(m_type);
    return *this;
}

Field& Field::setDefaultValue(const QVariant& value)
{
    setCppDefaultValue(value);
    setDbDefaultValue(value);
    return *this;
}

bool Field::hasDbDefaultValue() const
{
    return !m_db_default_value.isNull();
}

Field& Field::setPk(const bool pk)
{
    m_pk = pk;
    return *this;
}

Field& Field::setUnique(const bool unique)
{
    m_unique = unique;
    return *this;
}

Field& Field::setMandatory(const bool mandatory)
{
    m_mandatory = mandatory;
    return *this;
}

QString Field::name() const
{
    return m_name;
}

QMetaType Field::type() const
{
    return m_type;
}

bool Field::isPk() const
{
    return m_pk;
}

bool Field::isUnique() const
{
    return m_unique;
}

bool Field::isMandatory() const
{
    return m_mandatory;
}

bool Field::notNull() const
{
    // SQLite allows NULL values in primary keys, but this is a legacy of
    // bugs in early SQLite versions.
    // http://www.sqlite.org/lang_createtable.html
    return m_mandatory || m_pk;
}

QString Field::sqlColumnDef() const
{
    QString type = sqlColumnType();
    if (m_pk) {
        type += " PRIMARY KEY";
    }
    // AUTOINCREMENT usually not required: https://www.sqlite.org/autoinc.html
    if (m_unique && !m_pk) {
        type += " UNIQUE";
    }
    if (notNull()) {
        type += " NOT NULL";
    }
    if (!m_db_default_value.isNull()) {
        // https://sqlite.org/syntax/column-constraint.html
        type += QString(" DEFAULT %1")
                    .arg(convert::toSqlLiteral(m_db_default_value));
    }
    return type;
}

QVariant Field::value() const
{
    return m_value;
}

QString Field::prettyValue(const int dp) const
{
    return convert::prettyValue(m_value, dp, m_type);
}

bool Field::setValue(const QVariant& value)
{
    const int type_id = m_type.id();

    if (!m_set || value != m_value) {
        m_dirty = true;
    }
    m_value = value;
    if (!m_value.isNull() && type_id < QMetaType::User) {
        // Don't try to convert NULL values; needless warning.
        // Don't try to convert user type; it'll go wrong.
        const bool converted = m_value.convert(m_type);
        if (!converted) {
            if (type_id == QMetaType::QChar) {
                // Deal with special oddities, e.g. failure to convert
                // a QVariant of type QString to one of type QChar.
                m_value = convert::toQCharVariant(value);
            } else {
                qWarning() << Q_FUNC_INFO << "Failed to convert" << value
                           << "to type" << type_id;
            }
        }
    }
    m_set = true;
    return m_dirty;
}

bool Field::nullify()
{
    if (!m_set || !isNull()) {
        m_dirty = true;
    }
    m_value = QVariant(m_type);
    m_set = true;
    return m_dirty;
}

bool Field::isNull() const
{
    return m_value.isNull();
}

bool Field::isDirty() const
{
    return m_dirty;
}

void Field::setDirty()
{
    m_dirty = true;
}

void Field::clearDirty()
{
    m_dirty = false;
}

QDebug operator<<(QDebug debug, const Field& f)
{
    if (f.m_value.isNull()) {
        debug.nospace() << "NULL (" << f.m_type.name() << ")";
    } else {
        debug.nospace() << f.m_value;
    }
    if (f.m_dirty) {
        debug.nospace() << " (*)";
    }
    return debug;
}

QString Field::sqlColumnType() const
{
    // SQLite types: https://www.sqlite.org/datatype3.html
    //      SQLite uses up to 8 bytes (depending on actual value) and
    //      integers are signed, so the maximum INTEGER
    //      is 2^63 - 1 = 9,223,372,036,854,775,807
    // C++ types:
    //      int -- typically 32-bit; not guaranteed on all C++ platforms,
    //             though 32-bit on all Qt platforms, I think
    // Qt types: https://doc.qt.io/qt-6.5/qtglobal.html
    //      - qint8, qint16, qint32, qint64...
    //      - standard int is int32
    //        32-bit signed: up to +2,147,483,647 = 2147483647
    //      - qlonglong is the same as qint64
    //        64-bit signed: up to +9,223,372,036,854,775,807
    //          = 9223372036854775807
    //      - qulonglong is the same as quint64
    //        64-bit unsigned: 0 to +18,446,744,073,709,551,615
    //          = 18446744073709551615
    // C++ type name: QVariant::typeToName(m_type);
    const int type_id = m_type.id();

    switch (type_id) {
        case QMetaType::Bool:
        case QMetaType::Int:  // normally 32-bit
        case QMetaType::LongLong:  // 64-bit
        case QMetaType::UInt:  // normally 32-bit
        case QMetaType::ULongLong:  // 64-bit
            return SQLITE_TYPE_INTEGER;

        case QMetaType::Double:
            return SQLITE_TYPE_REAL;

        case QMetaType::QChar:
        case QMetaType::QDate:
        case QMetaType::QDateTime:
        case QMetaType::QString:
        case QMetaType::QStringList:
        case QMetaType::QTime:
        case QMetaType::QUuid:
            return SQLITE_TYPE_TEXT;

        case QMetaType::QByteArray:
            return SQLITE_TYPE_BLOB;

        default:
            // Can't use further "case" statements here as the comparisons are
            // to a technically non-const expression (integers set by
            // convert::registerTypesForQVariant).
            if (type_id == customtypes::TYPE_ID_QVECTOR_INT) {
                return SQLITE_TYPE_TEXT;
            }

            if (type_id == customtypes::TYPE_ID_VERSION) {
                return SQLITE_TYPE_TEXT;
            }
            break;
    }
    errorfunc::fatalError(
        QString("Field::sqlColumnType: Unknown field type: %1").arg(type_id)
    );
#ifdef COMPILER_WANTS_RETURN_AFTER_NORETURN
    return "";
#endif
}

void Field::setFromDatabaseValue(const QVariant& db_value)
{
    const int type_id = m_type.id();
    // SQLite -> C++
    switch (m_type.id()) {
        case QMetaType::QChar:
            // If you just do "m_value = db_value", it will become an invalid
            // value when the convert() call is made below, so will appear as
            // NULL.
            m_value = convert::toQCharVariant(db_value);
            break;
        case QMetaType::QDate:
            m_value = QVariant(datetime::isoToDate(db_value.toString()));
            break;
        case QMetaType::QDateTime:
            m_value = QVariant(datetime::isoToDateTime(db_value.toString()));
            break;
        case QMetaType::QStringList:
            m_value
                = QVariant(convert::csvStringToQStringList(db_value.toString())
                );
            break;
        default:
            if (type_id == customtypes::TYPE_ID_QVECTOR_INT) {
                m_value.setValue(
                    convert::csvStringToIntVector(db_value.toString())
                );
            } else if (type_id == customtypes::TYPE_ID_VERSION) {
                m_value.setValue(Version::fromString(db_value.toString()));
            } else {
                m_value = db_value;
            }
            break;
    }
    if (type_id < QMetaType::User) {
        m_value.convert(m_type);
    }
    m_dirty = false;
}

QVariant Field::databaseValue() const
{
    const int type_id = m_type.id();

    // C++ -> SQLite
    if (m_value.isNull()) {
        return m_value;  // NULL
    }
    switch (type_id) {
        case QMetaType::QChar:
            return m_value.toString();
        case QMetaType::QDate:
            return QVariant(datetime::dateToIso(m_value.toDate()));
        case QMetaType::QDateTime:
            return QVariant(datetime::datetimeToIsoMs(m_value.toDateTime()));
        case QMetaType::QStringList:
            return convert::qStringListToCsvString(m_value.toStringList());
        case QMetaType::QUuid:
            return m_value.toString();
            // see https://doc.qt.io/qt-6.5/quuid.html#toString; e.g.
            // "{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}" where 'x' is a hex
            // digit
        default:
            if (type_id == customtypes::TYPE_ID_QVECTOR_INT) {
                return convert::numericVectorToCsvString(
                    convert::qVariantToIntVector(m_value)
                );
            }
            if (type_id == customtypes::TYPE_ID_VERSION) {
                return Version::fromVariant(m_value).toString();
            }
    }
    return m_value;
}
