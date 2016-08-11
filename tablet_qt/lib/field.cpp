#include "field.h"
#include "lib/uifunc.h"
#include "lib/datetimefunc.h"


Field::Field(const QString& name, QVariant::Type type,
             bool mandatory, bool unique, bool pk) :
    m_name(name),
    m_type(type),
    m_pk(pk),
    m_unique(unique),
    m_mandatory(mandatory),
    m_set(false),
    m_dirty(true)
{
    if (pk) {
        m_unique = true;
        m_mandatory = true;
    }
//    if (type == QVariant::String || type == QVariant::Char) {
//        m_default_value = "";  // empty string, not NULL (as per Django)
//    } else {
//        m_default_value = QVariant(type);  // NULL
//    }
    m_default_value = QVariant(type);  // NULL
    m_value = m_default_value;
}


Field::Field() :  // needed by QMap
    Field("", QVariant::Int)
{
    // delegating constructor (C++11)
}


void Field::setPk(bool pk)
{
    m_pk = pk;
}


void Field::setUnique(bool unique)
{
    m_unique = unique;
}


void Field::setMandatory(bool mandatory)
{
    m_mandatory = mandatory;
}


void Field::setDefaultValue(QVariant value)
{
    m_default_value = value;
    m_default_value.convert(m_type);
    if (!m_set) {
        m_value = m_default_value;
    }
}


QString Field::name() const
{
    return m_name;
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


void Field::setFromDatabaseValue(const QVariant& db_value)
{
    switch (m_type) {
        case QVariant::DateTime:
            m_value = QVariant(isoToDateTime(db_value.toString()));
            break;
        default:
            m_value = db_value;
            break;
    }
    m_value.convert(m_type);
    m_dirty = false;
}


QVariant Field::getDatabaseValue() const
{
    switch (m_type) {
        case QVariant::DateTime:
            if (m_value.isNull()) {
                return QVariant(QString());  // NULL string
            }
            return QVariant(datetimeToIsoMs(m_value.toDateTime()));
        default:
            return m_value;
    }
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
    if (m_mandatory && !m_pk) {
        type += " NOT NULL";
    }
    return type;
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
    // Qt types: http://doc.qt.io/qt-5/qtglobal.html
    //      - qint8, qint16, qint32, qint64...
    //      - qlonglong is the same as qint64
    // C++ type name: QVariant::typeToName(m_type);
    switch (m_type) {
        case QVariant::Int:  // normally 32-bit
        case QVariant::UInt:  // normally 32-bit
        case QVariant::Bool:
        case QVariant::LongLong:  // 64-bit
        case QVariant::ULongLong:  // 64-bit
            return "INTEGER";
        case QVariant::Double:
            return "REAL";
        case QVariant::String:
        case QVariant::Char:
        case QVariant::Date:
        case QVariant::Time:
        case QVariant::DateTime:
            return "TEXT";
        case QVariant::ByteArray:
            return "BLOB";
        default:
            stopApp("Unknown field type: " + m_type);
    }
    return "";
}


QVariant Field::value() const
{
    return m_value;
}


bool Field::setValue(const QVariant& value)
{
    if (!m_set || value != m_value) {
        m_dirty = true;
    }
    m_value = value;
    m_value.convert(m_type);
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
        debug.nospace() << "NULL (" << QVariant::typeToName(f.m_type) << ")";
    } else {
        debug.nospace() << f.m_value;
    }
    if (f.m_dirty) {
        debug.nospace() << " (*)";
    }
    return debug;
}
