#include "databaseobject.h"
#include <iostream>
#include <QDateTime>
#include <QMapIterator>
#include <QSqlField>
#include <QSqlQuery>
#include <QStringList>
#include "lib/dbfunc.h"
#include "lib/uifunc.h"


DatabaseObject::DatabaseObject(const QString& tablename,
                               const QSqlDatabase db,
                               bool has_default_pk_field,
                               bool has_modification_timestamp) :
    m_tablename(tablename),
    m_db(db),
    m_has_modification_timestamp(has_modification_timestamp)
{
    if (has_default_pk_field) {
        addField(PK_FIELDNAME, QVariant::Int, true, true, true);
    }
    if (has_modification_timestamp) {
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


void DatabaseObject::clearAllDirty()
{
    MutableMapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        i.value().clearDirty();
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


void DatabaseObject::requireField(const QString &fieldname) const
{
    if (!m_record.contains(fieldname)) {
        stopApp("Database object does not contain field: " + fieldname);
    }
}


QVariant DatabaseObject::getValue(const QString& fieldname) const
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


void DatabaseObject::touch(bool only_if_unset)
{
    if (!m_has_modification_timestamp) {
        return;
    }
    if (only_if_unset &&
            !m_record[MODIFICATION_TIMESTAMP_FIELDNAME].isNull()) {
        return;
    }
    // Don't set the timestamp value with setValue()! Infinite loop.
    QDateTime now = QDateTime::currentDateTime();
    m_record[MODIFICATION_TIMESTAMP_FIELDNAME].setValue(now);
}


QString DatabaseObject::tablename() const
{
    return m_tablename;
}


QString DatabaseObject::pkname() const
{
    if (!m_cached_pkname.isEmpty()) {
        return m_cached_pkname;
    }
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        if (field.isPk()) {
            m_cached_pkname = fieldname;
            return m_cached_pkname;
        }
    }
    return "";
}


QVariant DatabaseObject::pkvalue() const
{
    return getValue(pkname());
}


bool DatabaseObject::isPkNull() const
{
    QVariant v = pkvalue();
    return v.isNull();
}


QString DatabaseObject::sqlCreateTable() const
{
    return ::sqlCreateTable(m_tablename, m_record.values());
}


void DatabaseObject::nullify()
{
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        Field field = i.value();
        field.nullify();
    }
}


bool DatabaseObject::loadByPk(int pk)
{
    QList<QVariant> args;
    QStringList fieldnames;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        fieldnames.append(delimit(fieldname));
    }
    QString sql = (
        "SELECT " + fieldnames.join(", ") + " FROM " + delimit(m_tablename) +
        " WHERE " + delimit(pkname()) + "=?"
    );
    args.append(pk);
    QSqlQuery query(m_db);
    bool success = exec(m_db, sql, args);
    if (success) {
        // Note: QMap iteration is ordered; http://doc.qt.io/qt-5/qmap.html
        // So we can re-iterate in the same way:
        MutableMapIteratorType it(m_record);
        int field_index = -1;
        while (it.hasNext()) {
            it.next();
            ++field_index;
            it.value().setFromDatabaseValue(query.value(field_index));
        }
    } else {
        nullify();
    }
    return success;
}


void DatabaseObject::save()
{
    touch(true);  // set timestamp only if timestamp not set
    if (isPkNull()) {
        saveInsert();
    } else {
        saveUpdate();
    }
    clearAllDirty();
}


bool DatabaseObject::saveInsert()
{
    QList<QVariant> args;
    QStringList fieldnames;
    QStringList placeholders;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        if (field.isPk()) {
            continue;
        }
        fieldnames.append(delimit(fieldname));
        args.append(field.getDatabaseValue());  // not field.value()
        placeholders.append("?");
    }
    QString sql = (
        "INSERT OR REPLACE INTO " + delimit(m_tablename) +
        " (" +
        fieldnames.join(", ") +
        ") VALUES (" +
        placeholders.join(", ") +
        ")"
    );
    QSqlQuery query(m_db);
    bool success = execQuery(query, sql, args);
    if (!success) {
        qCritical() << "Failed to insert record into table" << m_tablename;
        return success;
    }
    QVariant new_pk = query.lastInsertId();
    setValue(pkname(), new_pk);
    qDebug().nospace() << "Save/insert: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << new_pk;
    return success;
}


bool DatabaseObject::saveUpdate()
{
    QList<QVariant> args;
    QStringList fieldnames;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        fieldnames.append(delimit(fieldname) + "=?");
        args.append(field.getDatabaseValue());  // not field.value()
    }
    QString sql = (
        "UPDATE " + delimit(m_tablename) + " SET " +
        fieldnames.join(", ") +
        " WHERE " + delimit(pkname()) + "=?"
    );
    args.append(pkvalue());
    qDebug().nospace() << "Save/update: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << pkvalue();
    return exec(m_db, sql, args);
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
    // debug << "... Creation: " << qUtf8Printable(d.sqlCreateTable());
    return debug;
}
