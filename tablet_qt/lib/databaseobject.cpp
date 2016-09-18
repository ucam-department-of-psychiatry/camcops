// #define DEBUG_SAVES

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

const QString NOT_NULL_ERROR = "Error: attempting to save NULL to a NOT NULL "
                               "field:";


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
        UiFunc::stopApp(
            QString("DatabaseObject::DatabaseObject: Missing pk_fieldname; "
                    "table=%1").arg(m_tablename));
    }
    addField(pk_fieldname, QVariant::Int, true, true, true);
    if (has_modification_timestamp) {
        addField(DbConst::MODIFICATION_TIMESTAMP_FIELDNAME,
                 QVariant::DateTime);
    }
    if (has_creation_timestamp) {
        addField(DbConst::CREATION_TIMESTAMP_FIELDNAME,
                 QVariant::DateTime);
        QDateTime now = QDateTime::currentDateTime();
        m_record[DbConst::CREATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
    }
}


DatabaseObject::~DatabaseObject()
{
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


bool DatabaseObject::anyDirty() const
{
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        if (i.value().isDirty()) {
            return true;
        }
    }
    return false;
}


void DatabaseObject::addField(const QString& fieldname, QVariant::Type type,
                              bool mandatory, bool unique, bool pk)
{
    Field field(fieldname, type, mandatory, unique, pk);
    m_record.insert(fieldname, field);
    m_ordered_fieldnames.append(fieldname);
}


void DatabaseObject::addField(const Field& field)
{
    m_record.insert(field.name(), field);
    m_ordered_fieldnames.append(field.name());
}


QStringList DatabaseObject::fieldnames() const
{
    return m_ordered_fieldnames;
}


QStringList DatabaseObject::fieldnamesMapOrder() const
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
        UiFunc::stopApp("DatabaseObject::requireField: Database object does "
                        "not contain field: " + fieldname);
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


QByteArray DatabaseObject::valueByteArray(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toByteArray();
}


void DatabaseObject::touch(bool only_if_unset)
{
    if (!m_has_modification_timestamp) {
        return;
    }
    if (only_if_unset &&
            !m_record[DbConst::MODIFICATION_TIMESTAMP_FIELDNAME].isNull()) {
        return;
    }
    // Don't set the timestamp value with setValue()! Infinite loop.
    QDateTime now = QDateTime::currentDateTime();
    m_record[DbConst::MODIFICATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
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
    return DbFunc::sqlCreateTable(m_tablename, fieldsOrdered());
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
    WhereConditions where;
    where[pkname()] = QVariant(pk);
    return load(where);
}


bool DatabaseObject::load(const QString& fieldname,
                          const QVariant& where_value)
{
    if (!m_record.contains(fieldname)) {
        qCritical() << Q_FUNC_INFO
                    << "Attempt to load with nonexistent fieldname:"
                    << fieldname;
        nullify();
        return false;
    }
    WhereConditions where;
    where[fieldname] = where_value;
    return load(where);
}


bool DatabaseObject::load(const WhereConditions& where)
{
    SqlArgs sqlargs = fetchQuerySql(where);
    QSqlQuery query(m_db);
    bool success = DbFunc::execQuery(query, sqlargs);
    bool found = false;
    if (success) {  // SQL didn't have errors
        found = query.next();
    }
    if (success && found) {
        setFromQuery(query, true);
    } else {
        nullify();
    }
    return success && found;
}


SqlArgs DatabaseObject::fetchQuerySql(const WhereConditions& where)
{
    QStringList fields = fieldnamesMapOrder();
    QStringList delimited_fieldnames;
    for (int i = 0; i < fields.size(); ++i) {
        delimited_fieldnames.append(DbFunc::delimit(fields.at(i)));
    }
    QString sql = (
        "SELECT " + delimited_fieldnames.join(", ") + " FROM " +
        DbFunc::delimit(tablename())
    );
    ArgList args;
    SqlArgs sqlargs(sql, args);
    DbFunc::addWhereClause(where, sqlargs);
    return sqlargs;
}


void DatabaseObject::setFromQuery(const QSqlQuery& query,
                                  bool order_matches_fetchquery)
{
    MutableMapIteratorType it(m_record);
    // Note: QMap iteration is ordered; http://doc.qt.io/qt-5/qmap.html
    if (order_matches_fetchquery) {  // faster
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
    if (!anyDirty()) {
        return true;  // nothing to do, so let's not bother the database
    }
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
        fieldnames.append(DbFunc::delimit(fieldname));
        args.append(field.databaseValue());  // not field.value()
        placeholders.append("?");
        if (field.isMandatory() && field.isNull()) {
            qWarning() << NOT_NULL_ERROR << fieldname;
        }
    }
    QString sql = (
        "INSERT OR REPLACE INTO " + DbFunc::delimit(m_tablename) +
        " (" +
        fieldnames.join(", ") +
        ") VALUES (" +
        placeholders.join(", ") +
        ")"
    );
    QSqlQuery query(m_db);
    bool success = DbFunc::execQuery(query, sql, args);
    if (!success) {
        qCritical() << Q_FUNC_INFO << "Failed to insert record into table"
                    << m_tablename;
        return success;
    }
    QVariant new_pk = query.lastInsertId();
    setValue(pkname(), new_pk);
#ifdef DEBUG_SAVES
    qDebug().nospace() << "Save/insert: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << new_pk;
#endif
    return success;
}


bool DatabaseObject::saveUpdate()
{
#ifdef DEBUG_SAVES
    qDebug().nospace() << "Save/update: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << pkvalue();
#endif
    ArgList args;
    QStringList fieldnames;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        QString fieldname = i.key();
        Field field = i.value();
        if (field.isDirty()) {
            fieldnames.append(DbFunc::delimit(fieldname) + "=?");
            args.append(field.databaseValue());  // not field.value()
            if (field.isMandatory() && field.isNull()) {
                qWarning() << NOT_NULL_ERROR << fieldname;
            }
        }
    }
    if (fieldnames.isEmpty()) {
#ifdef DEBUG_SAVES
        qDebug() << "... no dirty fields; nothing to do";
#endif
        return true;
    }
    QString sql = (
        "UPDATE " + DbFunc::delimit(m_tablename) + " SET " +
        fieldnames.join(", ") +
        " WHERE " + DbFunc::delimit(pkname()) + "=?"
    );
    args.append(pkvalue());
    return DbFunc::exec(m_db, sql, args);
}


QList<Field> DatabaseObject::fieldsOrdered() const
{
    QList<Field> ordered_fields;
    for (auto fieldname : m_ordered_fieldnames) {
        ordered_fields.append(m_record[fieldname]);
    }
    return ordered_fields;
}


void DatabaseObject::makeTable()
{
    DbFunc::createTable(m_db, m_tablename, fieldsOrdered());
}


FieldRefPtr DatabaseObject::fieldRef(const QString& fieldname, bool mandatory,
                                     bool autosave, bool blob)
{
    // If we ask for two fieldrefs to the same field, they need to be linked
    // (in terms of signals), and therefore the same underlying FieldRef
    // object. So we maintain a map.
    // If an existing FieldRef has been created for this field, that field
    // reference is re-used, regardless of the (subsequent) autosave setting.
    requireField(fieldname);
    if (!m_fieldrefs.contains(fieldname)) {
        m_fieldrefs[fieldname] = FieldRefPtr(
            new FieldRef(this, fieldname, mandatory, autosave, blob));
    }
    return m_fieldrefs[fieldname];
}


QString DatabaseObject::recordSummary() const
{
    QStringList list;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        const Field& field = i.value();
        list.append(QString("<b>%1 =</b> %2").arg(field.name(),
                                                  field.prettyValue()));
    }
    return list.join("<br>");
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
        "DELETE FROM " + DbFunc::delimit(m_tablename) +
        " WHERE " + DbFunc::delimit(pkname()) + "=?"
    );
    args.append(pk);
    bool success = DbFunc::exec(m_db, sql, args);
    if (success) {
        nullify();
    } else {
        qWarning() << "Failed to delete object with PK" << pk
                   << "from table" << m_tablename;
    }
}


const QSqlDatabase& DatabaseObject::database() const
{
    return m_db;
}
