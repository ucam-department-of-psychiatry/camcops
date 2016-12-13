/*
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

// #define DEBUG_SAVES

#include "databaseobject.h"
#include <iostream>
#include <QDateTime>
#include <QMapIterator>
#include <QSqlField>
#include <QSqlQuery>
#include <QStringList>
#include "db/dbfunc.h"
#include "db/fieldref.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"

const QString NOT_NULL_ERROR("Error: attempting to save NULL to a NOT NULL "
                             "field:");


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
    addField(DbConst::MOVE_OFF_TABLET_FIELDNAME, QVariant::Bool,
             false, false, false);
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


// ============================================================================
// Adding fields
// ============================================================================

void DatabaseObject::addField(const QString& fieldname, QVariant::Type type,
                              bool mandatory, bool unique, bool pk)
{
    if (type == QVariant::ULongLong) {
        qWarning() << "SQLite3 does not properly support unsigned 64-bit "
                      "integers; please use signed if possible";
    }
    Field field(fieldname, type, mandatory, unique, pk);
    m_record.insert(fieldname, field);
    m_ordered_fieldnames.append(fieldname);
}


void DatabaseObject::addFields(const QStringList& fieldnames,
                               QVariant::Type type, bool mandatory)
{
    for (auto fieldname : fieldnames) {
        addField(fieldname, type, mandatory);
    }
}


void DatabaseObject::addField(const Field& field)
{
    m_record.insert(field.name(), field);
    m_ordered_fieldnames.append(field.name());
}


bool DatabaseObject::hasField(const QString& fieldname) const
{
    return m_ordered_fieldnames.contains(fieldname);
}


QStringList DatabaseObject::fieldnames() const
{
    return m_ordered_fieldnames;
}


// ============================================================================
// Field access
// ============================================================================

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


qulonglong DatabaseObject::valueULongLong(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toULongLong();
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


QString DatabaseObject::valueString(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toString();
}


QList<QVariant> DatabaseObject::values(const QStringList& fieldnames) const
{
    QList<QVariant> values;
    for (auto fieldname : fieldnames) {
        values.append(value(fieldname));
    }
    return values;
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


// ============================================================================
// Manipulating multiple fields
// ============================================================================

int DatabaseObject::sumInt(const QStringList& fieldnames) const
{
    int total = 0;
    for (auto fieldname : fieldnames) {
        total += valueInt(fieldname);  // gives 0 if it is NULL
    }
    return total;
}


double DatabaseObject::sumDouble(const QStringList& fieldnames) const
{
    double total = 0;
    for (auto fieldname : fieldnames) {
        total += valueDouble(fieldname);  // gives 0 if it is NULL
    }
    return total;
}


QVariant DatabaseObject::mean(const QStringList& fieldnames) const
{
    double sum = 0;
    int n = 0;
    for (auto fieldname : fieldnames) {
        QVariant v = value(fieldname);
        if (!v.isNull()) {
            sum += v.toDouble();
            n += 1;
        }
    }
    if (n == 0) {
        return QVariant();  // undefined
    }
    return sum / n;
}


int DatabaseObject::countTrue(const QStringList& fieldnames) const
{
    int n = 0;
    for (auto fieldname : fieldnames) {
        if (valueBool(fieldname)) {
            n += 1;
        }
    }
    return n;
}


bool DatabaseObject::allTrue(const QStringList& fieldnames) const
{
    for (auto fieldname : fieldnames) {
        if (!valueBool(fieldname)) {
            return false;
        }
    }
    return true;
}


bool DatabaseObject::allFalseOrNull(const QStringList& fieldnames) const
{
    for (auto fieldname : fieldnames) {
        if (valueBool(fieldname)) {
            return false;
        }
    }
    return true;
}


bool DatabaseObject::anyNull(const QStringList& fieldnames) const
{
    for (auto fieldname: fieldnames) {
        if (value(fieldname).isNull()) {
            return true;
        }
    }
    return false;
}


int DatabaseObject::numNull(const QStringList& fieldnames) const
{
    int n = 0;
    for (auto fieldname: fieldnames) {
        if (value(fieldname).isNull()) {
            n += 1;
        }
    }
    return n;
}


int DatabaseObject::numNotNull(const QStringList& fieldnames) const
{
    int n = 0;
    for (auto fieldname: fieldnames) {
        if (!value(fieldname).isNull()) {
            n += 1;
        }
    }
    return n;
}


int DatabaseObject::countWhere(const QStringList& fieldnames,
                               const QList<QVariant>& values) const
{
    int n = 0;
    for (auto fieldname : fieldnames) {
        if (values.contains(value(fieldname))) {
            n += 1;
        }
    }
    return n;
}


int DatabaseObject::countWhereNot(const QStringList& fieldnames,
                                  const QList<QVariant>& values) const
{
    int n = 0;
    for (auto fieldname : fieldnames) {
        if (!values.contains(value(fieldname))) {
            n += 1;
        }
    }
    return n;
}


// ============================================================================
// Whole-object summary
// ============================================================================

QString DatabaseObject::fieldSummary(const QString& fieldname,
                                     const QString& altname) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return QString("<b>%1 =</b> %2").arg(name).arg(prettyValue(fieldname));
}


QStringList DatabaseObject::recordSummaryLines() const
{
    QStringList list;
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        const Field& field = i.value();
        list.append(QString("%1 = <b>%2</b>").arg(field.name(),
                                                  field.prettyValue()));
    }
    return list;
}


QString DatabaseObject::recordSummary() const
{
    return recordSummaryLines().join("<br>");
}


// ============================================================================
// Loading, saving
// ============================================================================

bool DatabaseObject::load(int pk)
{
    if (pk == DbConst::NONEXISTENT_PK) {
        qDebug() << "Ignoring DatabaseObject::load() call for explicitly "
                    "invalid PK";
        return false;
    }
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


void DatabaseObject::nullify()
{
    MapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        Field field = i.value();
        field.nullify();
    }
}


bool DatabaseObject::isPkNull() const
{
    QVariant v = pkvalue();
    return v.isNull();
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


void DatabaseObject::setAllDirty()
{
    MutableMapIteratorType i(m_record);
    while (i.hasNext()) {
        i.next();
        i.value().setDirty();
    }
}

// ============================================================================
// Batch operations
// ============================================================================

QList<int> DatabaseObject::getAllPKs() const
{
    return DbFunc::getPKs(m_db, m_tablename, m_pk_fieldname);
}


// ============================================================================
// Deleting
// ============================================================================

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


// ============================================================================
// Debugging
// ============================================================================

void DatabaseObject::requireField(const QString &fieldname) const
{
    if (!m_record.contains(fieldname)) {
        UiFunc::stopApp("DatabaseObject::requireField: Database object with "
                        "tablename '" + m_tablename + "' does not contain "
                        "field: " + fieldname);
    }
}


// ============================================================================
// Special field access
// ============================================================================

bool DatabaseObject::shouldMoveOffTablet() const
{
    return valueBool(DbConst::MOVE_OFF_TABLET_FIELDNAME);
}


void DatabaseObject::setMoveOffTablet(bool move_off)
{
    setValue(DbConst::MOVE_OFF_TABLET_FIELDNAME, move_off);
    save();
}

// ============================================================================
// DDL
// ============================================================================

QString DatabaseObject::sqlCreateTable() const
{
    return DbFunc::sqlCreateTable(m_tablename, fieldsOrdered());
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

void DatabaseObject::makeTable()
{
    DbFunc::createTable(m_db, m_tablename, fieldsOrdered());
}

const QSqlDatabase& DatabaseObject::database() const
{
    return m_db;
}


// ========================================================================
// Additional protected
// ========================================================================

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
        qCritical() << Q_FUNC_INFO << "Failed to INSERT record into table"
                    << m_tablename;
        return success;
    }
    QVariant new_pk = query.lastInsertId();
    setValue(pkname(), new_pk);
#ifdef DEBUG_SAVES
    qDebug().nospace() << "Save/insert: " << qUtf8Printable(m_tablename)
                       << ", " << pkname() << "=" << new_pk;
#endif
    /*
    success = DbFunc::commit(m_db);
    if (!success) {
        qCritical() << Q_FUNC_INFO << "Failed to commit" << m_tablename;
    }
    */
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
    bool success = DbFunc::exec(m_db, sql, args);
    if (!success) {
        qCritical() << Q_FUNC_INFO << "Failed to UPDATE record into table"
                    << m_tablename;
        return success;
    }
    /*
    success = DbFunc::commit(m_db);
    if (!success) {
        qCritical() << Q_FUNC_INFO << "Failed to commit" << m_tablename;
    }
    */
    return success;
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

QList<Field> DatabaseObject::fieldsOrdered() const
{
    QList<Field> ordered_fields;
    for (auto fieldname : m_ordered_fieldnames) {
        ordered_fields.append(m_record[fieldname]);
    }
    return ordered_fields;
}


// ========================================================================
// For friends
// ========================================================================

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
