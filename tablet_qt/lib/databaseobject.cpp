#include "databaseobject.h"
#include <iostream>
#include <QDateTime>
#include <QDebug>
#include <QMapIterator>
#include <QSqlField>
#include <QSqlQuery>
#include <QStringList>
#include "lib/dbfunc.h"
#include "lib/uifunc.h"

DatabaseObject::DatabaseObject(const QString& tablename,
                               const QSqlDatabase db,
                               bool hasDefaultPkField,
                               bool hasModificationTimestamp) :
    m_tablename(tablename),
    m_db(db),
    m_hasModificationTimestamp(hasModificationTimestamp)
{
    if (hasDefaultPkField) {
        addField(PK_FIELDNAME, QVariant::Int, true, true, true);
    }
    if (hasModificationTimestamp) {
        addField(MODIFICATION_TIMESTAMP_FIELDNAME, QVariant::DateTime);
    }
}

void DatabaseObject::setAllDirty()
{
    MutableMapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        i.value().setDirty();
    }
}

void DatabaseObject::addField(const QString& fieldname, QVariant::Type type,
                              bool mandatory, bool unique, bool pk)
{
    Field field(fieldname, type, mandatory, unique, pk);
    m_record.insert(fieldname, field);
}

void DatabaseObject::addField(const Field& field)
{
    m_record.insert(field.name(), field);
}

void DatabaseObject::requireField(const QString &fieldname)
{
    if (!m_record.contains(fieldname)) {
        stopApp("Database object does not contain field: " + fieldname);
    }
}

QVariant DatabaseObject::value(const QString& fieldname)
{
    requireField(fieldname);
    return m_record[fieldname].value();
}

bool DatabaseObject::setValue(const QString& fieldname, const QVariant& value)
{
    requireField(fieldname);
    bool dirty = m_record[fieldname].setValue(value);
    if (dirty) {
        touch();
    }
    return dirty;
}

void DatabaseObject::touch()
{
    if (!m_hasModificationTimestamp) {
        return;
    }
    QDateTime now = QDateTime::currentDateTime();
    setValue(MODIFICATION_TIMESTAMP_FIELDNAME, now);
}

QString DatabaseObject::tablename() const
{
    return m_tablename;
}

QString DatabaseObject::pkname() const
{
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        if (field.isPk()) {
            return fieldname;
        }
    }
    return "";
}

QString DatabaseObject::sqlCreateTable() const
{
    return ::sqlCreateTable(m_tablename, m_record.values());
}

bool DatabaseObject::loadByPk(int pk)
{
    qDebug() << "*** MISSING CODE: DatabaseObject::loadByPk ***";
}

void DatabaseObject::save()
{
    QString pkfieldname = pkname();
    QSqlQuery query(m_db);
    qDebug() << "*** MISSING CODE: DatabaseObject::save ***";
}

void DatabaseObject::makeTable()
{
    createTable(m_db, m_tablename, m_record.values());
}

QDebug operator<<(QDebug debug, const DatabaseObject& d)
{
    debug << d.m_tablename << " record: " << d.m_record << "\n";
    // use m_record.count() to get the number of fields
    // use m_record.field(i) to get the field at position i
    // use m_record.value(i) to get the value at position i
    // use m_record.value(fieldname) similarly
    // debug << "... Creation: " << qPrintable(d.sqlCreateTable());
    return debug;
}
