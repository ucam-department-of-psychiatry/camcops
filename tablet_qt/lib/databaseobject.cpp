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


DatabaseObject::DatabaseObject(const QSqlDatabase& db,
                               const QString& tablename,
                               const QString& pk_fieldname,
                               bool has_modification_timestamp,
                               bool has_creation_timestamp) :
    m_db(db),
    m_tablename(tablename),
    m_pk_fieldname(pk_fieldname),
    m_has_modification_timestamp(has_modification_timestamp)
{
    if (pk_fieldname.isEmpty()) {
        stopApp(QString("Missing pk_fieldname; table=%1").arg(m_tablename));
    }
    addField(pk_fieldname, QVariant::Int, true, true, true);
    if (has_modification_timestamp) {
        addField(MODIFICATION_TIMESTAMP_FIELDNAME, QVariant::DateTime);
    }
    if (has_creation_timestamp) {
        addField(CREATION_TIMESTAMP_FIELDNAME, QVariant::DateTime);
        QDateTime now = QDateTime::currentDateTime();
        m_record[CREATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
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


QStringList DatabaseObject::fieldnames() const
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


bool DatabaseObject::setValue(const QString& fieldname, const QVariant& value)
{
    requireField(fieldname);
    bool dirty = m_record[fieldname].setValue(value);
    if (dirty) {
        touch();
    }
    return dirty;
}


QVariant DatabaseObject::value(const QString& fieldname) const
{
    requireField(fieldname);
    return m_record[fieldname].value();
}


QString DatabaseObject::prettyValue(const QString &fieldname) const
{
    requireField(fieldname);
    return m_record[fieldname].prettyValue();
}


bool DatabaseObject::valueBool(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toBool();
}


int DatabaseObject::valueInt(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toInt();
}


qlonglong DatabaseObject::valueLongLong(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toLongLong();
}


double DatabaseObject::valueDouble(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toDouble();
}


QDateTime DatabaseObject::valueDateTime(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toDateTime();
}


QDate DatabaseObject::valueDate(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toDate();
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
    return m_pk_fieldname;
}


QVariant DatabaseObject::pkvalue() const
{
    return value(pkname());
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
    QStringList fields = fieldnames();
    QStringList delimited_fieldnames;
    for (int i = 0; i < fields.size(); ++i) {
        delimited_fieldnames.append(delimit(fields.at(i)));
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
            // Empirically, these fieldnames are fine: no delimiting quotes,
            // despite use of delimiters in the SELECT SQL.
            // qDebug().noquote() << "fieldname:" << fieldname;
            it.value().setFromDatabaseValue(query.value(fieldname));
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
        args.append(field.databaseValue());  // not field.value()
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
            args.append(field.databaseValue());  // not field.value()
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


FieldRef DatabaseObject::fieldRef(const QString& fieldname, bool autosave)
{
    requireField(fieldname);
    if (autosave) {
        return FieldRef(this, fieldname, true);
    } else {
        Field* p_field = &m_record[fieldname];
        return FieldRef(p_field);
    }
}


QString DatabaseObject::recordSummary() const
{
    QStringList list;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        const Field& field = i.value();
        list.append(QString("%1 = %2").arg(field.name(), field.prettyValue()));
    }
    return list.join("\n");
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


void DatabaseObject::deleteFromDatabase()
{
    QVariant pk = pkvalue();
    if (pk.isNull()) {
        qWarning() << "Attempting to delete a DatabaseObject with a "
                      "NULL PK; ignored";
        return;
    }
    ArgList args;
    QString sql = (
        "DELETE FROM " + delimit(m_tablename) +
        " WHERE " + delimit(pkname()) + "=?"
    );
    args.append(pk);
    bool success = exec(m_db, sql, args);
    if (success) {
        nullify();
    } else {
        qWarning() << "Failed to delete object with PK" << pk
                   << "from table" << m_tablename;
    }
}
