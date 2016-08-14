#include "databaseobject.h"
#include <iostream>
#include <QDateTime>
#include <QMapIterator>
#include <QSqlField>
#include <QSqlQuery>
#include <QStringList>
#include "lib/dbfunc.h"
#include "lib/uifunc.h"
#include "fieldref.h"


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


QStringList DatabaseObject::getFieldnames() const
{
    QStringList fieldnames;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        fieldnames.append(i.key());
    }
    return fieldnames;
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
    m_record[MODIFICATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
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


bool DatabaseObject::load(int pk)
{
    ArgList args;
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
    bool success = execQuery(query, sql, args);
    if (success) {
        // Note: QMap iteration is ordered; http://doc.qt.io/qt-5/qmap.html
        // So we can re-iterate in the same way:
        query.next();
        setFromQuery(query, true);
    } else {
        nullify();
    }
    return success;
}


SqlArgs DatabaseObject::fetchQuerySql(const WhereConditions& where)
{
    QStringList fieldnames = getFieldnames();
    QStringList delimited_fieldnames;
    for (int i = 0; i < fieldnames.size(); ++i) {
        delimited_fieldnames.append(delimit(fieldnames.at(i)));
    }
    QString sql = (
        "SELECT " + delimited_fieldnames.join(", ") + " FROM " +
        delimit(tablename())
    );
    ArgList args;
    SqlArgs sqlargs(sql, args);
    addWhereClause(where, sqlargs);
    return sqlargs;
}


void DatabaseObject::setFromQuery(const QSqlQuery& query, bool correct_order)
{
    MutableMapIteratorType it(m_record);
    // Note: QMap iteration is ordered; http://doc.qt.io/qt-5/qmap.html
    if (correct_order) {  // faster
        int field_index = -1;
        while (it.hasNext()) {
            it.next();
            ++field_index;
            it.value().setFromDatabaseValue(query.value(field_index));
        }
    } else {
        while (it.hasNext()) {
            it.next();
            QString fieldname = it.key();
            it.value().setFromDatabaseValue(query.value(fieldname));
            // *** will names be right with field delimiters?
        }
    }
}


bool DatabaseObject::save()
{
    touch(true);  // set timestamp only if timestamp not set
    bool success;
    if (isPkNull()) {
        success = saveInsert();
    } else {
        success = saveUpdate();
    }
    clearAllDirty();
    return success;
}


bool DatabaseObject::saveInsert()
{
    ArgList args;
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
    qDebug().nospace() << "Save/update: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << pkvalue();
    ArgList args;
    QStringList fieldnames;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        if (field.isDirty()) {
            fieldnames.append(delimit(fieldname) + "=?");
            args.append(field.getDatabaseValue());  // not field.value()
        }
    }
    if (fieldnames.isEmpty()) {
        qDebug() << "... no dirty fields; nothing to do";
        return true;
    }
    QString sql = (
        "UPDATE " + delimit(m_tablename) + " SET " +
        fieldnames.join(", ") +
        " WHERE " + delimit(pkname()) + "=?"
    );
    args.append(pkvalue());
    return exec(m_db, sql, args);
}


void DatabaseObject::makeTable()
{
    createTable(m_db, m_tablename, m_record.values());
}


FieldRef DatabaseObject::fieldRef(const QString& fieldname)
{
    requireField(fieldname);
    Field* p_field = &m_record[fieldname];
    FieldRef fieldref(p_field);
    return fieldref;
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
