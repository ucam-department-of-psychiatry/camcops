/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DEBUG_SPECIMEN_CREATION
// #define DEBUG_SAVES

#include "databaseobject.h"
#include <iostream>
#include <QDateTime>
#include <QMapIterator>
#include <QSqlField>
#include <QSqlQuery>
#include <QStringList>
#include "common/camcopsapp.h"
#include "db/dbfunc.h"
#include "db/fieldref.h"
#include "dbobjects/blob.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"

const QString NOT_NULL_ERROR("Error: attempting to save NULL to a NOT NULL "
                             "field:");


DatabaseObject::DatabaseObject(CamcopsApp& app,
                               const QSqlDatabase& db,
                               const QString& tablename,
                               const QString& pk_fieldname,
                               bool has_modification_timestamp,
                               bool has_creation_timestamp,
                               bool has_move_off_tablet_field,
                               bool triggers_need_upload) :
    m_app(app),
    m_db(db),
    m_tablename(tablename),
    m_pk_fieldname(pk_fieldname),
    m_has_modification_timestamp(has_modification_timestamp),
    m_has_move_off_tablet_field(has_move_off_tablet_field),
    m_triggers_need_upload(triggers_need_upload)
{
    if (pk_fieldname.isEmpty()) {
        uifunc::stopApp(
            QString("DatabaseObject::DatabaseObject: Missing pk_fieldname; "
                    "table=%1").arg(m_tablename));
    }
    addField(pk_fieldname, QVariant::Int, true, true, true);
    if (has_move_off_tablet_field) {
        // Will be true for everything in data DB, but not system DB
        addField(dbconst::MOVE_OFF_TABLET_FIELDNAME, QVariant::Bool,
                 false, false, false);
    }
    if (has_modification_timestamp) {
        addField(dbconst::MODIFICATION_TIMESTAMP_FIELDNAME,
                 QVariant::DateTime);
    }
    if (has_creation_timestamp) {
        addField(dbconst::CREATION_TIMESTAMP_FIELDNAME,
                 QVariant::DateTime);
        QDateTime now = QDateTime::currentDateTime();
        m_record[dbconst::CREATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
    }
}


DatabaseObject::~DatabaseObject()
{
}


// ============================================================================
// Adding fields
// ============================================================================

void DatabaseObject::addField(const QString& fieldname, QVariant::Type type,
                              bool mandatory, bool unique, bool pk,
                              const QVariant& default_value)
{
    if (type == QVariant::ULongLong) {
        qWarning() << "SQLite3 does not properly support unsigned 64-bit "
                      "integers; please use signed if possible";
    }
    if (m_record.contains(fieldname)) {
        uifunc::stopApp("Attempt to insert duplicate fieldname: " + fieldname);
    }
    Field field(fieldname, type, mandatory, unique, pk, default_value);
    m_record.insert(fieldname, field);
    m_ordered_fieldnames.append(fieldname);
}


void DatabaseObject::addField(const QString& fieldname,
                              const QString& type_name,
                              bool mandatory, bool unique, bool pk,
                              const QVariant& default_value)
{
    if (m_record.contains(fieldname)) {
        uifunc::stopApp("Attempt to insert duplicate fieldname: " + fieldname);
    }
    Field field(fieldname, type_name, mandatory, unique, pk, default_value);
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

bool DatabaseObject::setValue(const QString& fieldname, const QVariant& value,
                              bool touch_record)
{
    requireField(fieldname);
    bool dirty = m_record[fieldname].setValue(value);
    if (dirty && touch_record) {
        touch();
        if (m_triggers_need_upload) {
            m_app.setNeedsUpload(true);
        }
    }
    return dirty;
}


bool DatabaseObject::setValue(const QString& fieldname,
                              const QVector<int>& value,
                              bool touch_record)
{
    return setValue(fieldname, QVariant::fromValue(value), touch_record);
}


bool DatabaseObject::setValue(const QString& fieldname,
                              const QStringList& value,
                              bool touch_record)
{
    return setValue(fieldname, QVariant::fromValue(value), touch_record);
}


void DatabaseObject::addToValueInt(const QString& fieldname, int increment)
{
    setValue(fieldname, valueInt(fieldname) + increment);
}


QVariant DatabaseObject::value(const QString& fieldname) const
{
    requireField(fieldname);
    return m_record[fieldname].value();
}


QString DatabaseObject::prettyValue(const QString &fieldname, int dp) const
{
    requireField(fieldname);
    return m_record[fieldname].prettyValue(dp);
}


bool DatabaseObject::valueIsNull(const QString &fieldname) const
{
    QVariant v = value(fieldname);
    return v.isNull();
}


bool DatabaseObject::valueIsFalseNotNull(const QString &fieldname) const
{
    QVariant v = value(fieldname);
    return !v.isNull() && !v.toBool();
}


bool DatabaseObject::valueIsNullOrEmpty(const QString &fieldname) const
{
    QVariant v = value(fieldname);
    return v.isNull() || v.toString() == "";
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


QStringList DatabaseObject::valueStringList(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toStringList();
}


QChar DatabaseObject::valueQChar(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.toChar();
}


char DatabaseObject::valueLatin1Char(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    QChar c = v.toChar();  // 16-bit char
    return c.toLatin1();  // 8-bit char
}


QVector<int> DatabaseObject::valueVectorInt(const QString& fieldname) const
{
    QVariant v = value(fieldname);
    return v.value<QVector<int>>();
}


QVector<QVariant> DatabaseObject::values(const QStringList& fieldnames) const
{
    QVector<QVariant> values;
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
        CamcopsApp* p_app = &m_app;
        m_fieldrefs[fieldname] = FieldRefPtr(
            new FieldRef(this, fieldname, mandatory, autosave, blob, p_app));
    }
    return m_fieldrefs[fieldname];
}


Field& DatabaseObject::getField(const QString& fieldname)
{
    // Dangerous in that it returns a reference.
    requireField(fieldname);
    return m_record[fieldname];
}


// ============================================================================
// Whole-object summary
// ============================================================================

QString DatabaseObject::fieldSummary(const QString& fieldname,
                                     const QString& altname,
                                     const QString& separator,
                                     const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return stringfunc::standardResult(name, prettyValue(fieldname),
                                      separator, suffix);
}


QString DatabaseObject::fieldSummaryYesNo(const QString& fieldname,
                                          const QString& altname,
                                          const QString& separator,
                                          const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return stringfunc::standardResult(name,
                                      uifunc::yesNo(valueBool(fieldname)),
                                      separator, suffix);
}


QString DatabaseObject::fieldSummaryYesNoNull(const QString& fieldname,
                                              const QString& altname,
                                              const QString& separator,
                                              const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return stringfunc::standardResult(name,
                                      uifunc::yesNoNull(value(fieldname)),
                                      separator, suffix);
}


QString DatabaseObject::fieldSummaryYesNoUnknown(const QString& fieldname,
                                                 const QString& altname,
                                                 const QString& separator,
                                                 const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return stringfunc::standardResult(name,
                                      uifunc::yesNoUnknown(value(fieldname)),
                                      separator, suffix);
}


QString DatabaseObject::fieldSummaryTrueFalseUnknown(
        const QString& fieldname,
        const QString& altname,
        const QString& separator,
        const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    return stringfunc::standardResult(name,
                                      uifunc::trueFalseUnknown(value(fieldname)),
                                      separator, suffix);
}


QString DatabaseObject::fieldSummaryNameValueOptions(
        const QString& fieldname,
        const NameValueOptions& options,
        const QString& altname,
        const QString& separator,
        const QString& suffix) const
{
    QString name = altname.isEmpty() ? fieldname : altname;
    QVariant v = value(fieldname);
    QString pretty_value = options.nameFromValue(v);
    return stringfunc::standardResult(name, pretty_value,
                                      separator, suffix);
}


QStringList DatabaseObject::recordSummaryLines(const QString& separator,
                                               const QString& suffix) const
{
    QStringList list;
    for (auto fieldname : m_ordered_fieldnames) {
        const Field& field = m_record[fieldname];
        list.append(stringfunc::standardResult(field.name(), field.prettyValue(),
                                               separator, suffix));
    }
    return list;
}


QString DatabaseObject::recordSummaryString(const QString& separator,
                                            const QString& suffix) const
{
    return recordSummaryLines(separator, suffix).join("<br>");
}


QString DatabaseObject::recordSummaryCSVString(
        const QString& equals_separator,
        const QString& comma_separator) const
{
    return recordSummaryLines(equals_separator, "").join(comma_separator);
}


// ============================================================================
// Loading, saving
// ============================================================================

bool DatabaseObject::load(int pk)
{
    if (pk == dbconst::NONEXISTENT_PK) {
#ifdef DEBUG_SPECIMEN_CREATION
        qDebug() << "Ignoring DatabaseObject::load() call for explicitly "
                    "invalid PK";
#endif
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
    bool success = dbfunc::execQuery(query, sqlargs);
    bool found = false;
    if (success) {  // SQL didn't have errors
        found = query.next();
    }
    if (success && found) {
        setFromQuery(query, true);
        loadAllAncillary(); // *** CHECK: two simultaneous queries? ***
    } else {
        nullify();
    }
    return success && found;
}


SqlArgs DatabaseObject::fetchQuerySql(const WhereConditions& where,
                                      const OrderBy& order_by)
{
    QStringList fields = fieldnamesMapOrder();
    QStringList delimited_fieldnames;
    for (int i = 0; i < fields.size(); ++i) {
        delimited_fieldnames.append(dbfunc::delimit(fields.at(i)));
    }
    QString sql = (
        "SELECT " + delimited_fieldnames.join(", ") + " FROM " +
        dbfunc::delimit(tablename())
    );
    ArgList args;
    SqlArgs sqlargs(sql, args);
    dbfunc::addWhereClause(where, sqlargs);
    dbfunc::addOrderByClause(order_by, sqlargs);
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

    // And also:
    loadAllAncillary(); // *** CHECK: two simultaneous queries? ***
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
            !m_record[dbconst::MODIFICATION_TIMESTAMP_FIELDNAME].isNull()) {
        return;
    }
    // Don't set the timestamp value with setValue()! Infinite loop.
    QDateTime now = QDateTime::currentDateTime();
    m_record[dbconst::MODIFICATION_TIMESTAMP_FIELDNAME].setValue(now);  // also: dirty
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

QVector<int> DatabaseObject::getAllPKs() const
{
    return dbfunc::getPKs(m_db, m_tablename, m_pk_fieldname);
}


// ============================================================================
// Deleting
// ============================================================================

void DatabaseObject::deleteFromDatabase()
{
    using dbfunc::delimit;
    QVariant pk = pkvalue();
    if (pk.isNull()) {
        qWarning() << "Attempting to delete a DatabaseObject with a "
                      "NULL PK; ignored";
        return;
    }

    // ------------------------------------------------------------------------
    // Delete any associated BLOBs
    // ------------------------------------------------------------------------
    // There is no automatic way of knowing if we possess a BLOB, since a
    // BLOB field is simply an integer FK to the BLOB table.
    // However, we can reliably do it the other way round, and, moreover,
    // delete all associated BLOBs in one DELETE command:
    WhereConditions where_blob;
    where_blob[Blob::SRC_TABLE_FIELDNAME] = tablename();
    where_blob[Blob::SRC_PK_FIELDNAME] = pk;
    if (!dbfunc::deleteFrom(m_db, Blob::TABLENAME, where_blob)) {
        qWarning() << "Failed to delete BLOB(s) where:" << where_blob;
    }

    // ------------------------------------------------------------------------
    // Delete associated ancillary objects
    // ------------------------------------------------------------------------
    // - How best to do this?
    //
    // - We could register table/fkname pairs. That allows us to delete
    //   ancillary objects without instantiating a C++ object. And it allows
    //   that deletion in SQL, so we can delete multiple ancillaries in one go,
    //   rather than via C++ per-object deletion. However, it doesn't let us
    //   create a hierarchy (an ancillary of an ancillary, in an arbitrary way;
    //   the best would be registration with a "top-level" C++ object that
    //   deletes all its ancillaries (but then the FK system would be more
    //   complex).
    //   To do automatic BLOB deletion... would need to
    //   (1) SELECT all the ancillary PKs based on FK to primary object PK
    //   (2) delete from the ancillary table
    //   ... again, this either supports only a single level of inheritance,
    //   or one would have to store the top-level PK within all levels (mind
    //   you, you'd probably have to do that anyway).
    //
    // - We could have a chain of C++ objects that register themselves with
    //   their parents. As long as they are all loaded, they could then
    //   delete themselves and their children (ad infinitum). This would
    //   handle BLOBs neatly. Might make menu loading a bit less efficient.
    //   They'd have to autoload when their owner does. Mind you, that's often
    //   what we want to do anyway...
    //
    // - We could look at SQLite's ON DELETE CASCADE.
    //   However, that would require us to rework the BLOB system (e.g. one
    //   BLOB table per task/ancillary), which could get less elegant.
    //   Plus, there are other ways to mess up FKs in SQLite.
    //
    // DECISION:
    // - The C++ object way.
    //
    // OTHER CONSIDERATION:
    // - If objects load their ancillaries as they are themselves loaded, can
    //   SQLite cope? The potential is for two simultaneous queries:
    //      - load tasks T1, T2, T3
    //      - during load of T1, T1 wishes to load A1a, A1b, A1c
    //          - will the ancillary query fail?
    //          - If not, will the top-level query proceed to T2?
    for (auto ancillary : getAllAncillary()) {
        ancillary->deleteFromDatabase();
    }

    // ------------------------------------------------------------------------
    // Delete ourself
    // ------------------------------------------------------------------------
    WhereConditions where_self;
    where_self[pkname()] = pk;
    bool success = dbfunc::deleteFrom(m_db, m_tablename, where_self);
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
        uifunc::stopApp("DatabaseObject::requireField: Database object with "
                        "tablename '" + m_tablename + "' does not contain "
                        "field: " + fieldname);
    }
}


// ============================================================================
// Special field access
// ============================================================================

bool DatabaseObject::shouldMoveOffTablet() const
{
    return valueBool(dbconst::MOVE_OFF_TABLET_FIELDNAME);
}


void DatabaseObject::setMoveOffTablet(bool move_off)
{
    if (!m_has_move_off_tablet_field) {
        qWarning() << Q_FUNC_INFO << "m_has_move_off_tablet_field is false";
        return;
    }
    setValue(dbconst::MOVE_OFF_TABLET_FIELDNAME, move_off, false);
    save();

    for (auto ancillary : getAllAncillary()) {
        ancillary->setMoveOffTablet(move_off);
    }
}


void DatabaseObject::toggleMoveOffTablet()
{
    setMoveOffTablet(!shouldMoveOffTablet());
}


// ============================================================================
// DDL
// ============================================================================

QString DatabaseObject::sqlCreateTable() const
{
    return dbfunc::sqlCreateTable(m_tablename, fieldsOrdered());
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


int DatabaseObject::pkvalueInt() const
{
    QVariant pk = pkvalue();
    return pk.isNull() ? dbconst::NONEXISTENT_PK : pk.toInt();
}


void DatabaseObject::makeTable()
{
    dbfunc::createTable(m_db, m_tablename, fieldsOrdered());
    for (auto specimen : getAncillarySpecimens()) {
        specimen->makeTable();
    }
}

const QSqlDatabase& DatabaseObject::database() const
{
    return m_db;
}


// ========================================================================
// Internals: ancillary management
// ========================================================================

void DatabaseObject::loadAllAncillary()
{
    int pk = pkvalueInt();
    loadAllAncillary(pk);
}


void DatabaseObject::loadAllAncillary(int pk)
{
    Q_UNUSED(pk);
}


QVector<DatabaseObjectPtr> DatabaseObject::getAllAncillary() const
{
    return QVector<DatabaseObjectPtr>();
}


QVector<DatabaseObjectPtr> DatabaseObject::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>();
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
        fieldnames.append(dbfunc::delimit(fieldname));
        args.append(field.databaseValue());  // not field.value()
        placeholders.append("?");
        if (field.isMandatory() && field.isNull()) {
            qWarning() << NOT_NULL_ERROR << fieldname;
        }
    }
    QString sql = (
        "INSERT OR REPLACE INTO " + dbfunc::delimit(m_tablename) +
        " (" +
        fieldnames.join(", ") +
        ") VALUES (" +
        placeholders.join(", ") +
        ")"
    );
    QSqlQuery query(m_db);
    bool success = dbfunc::execQuery(query, sql, args);
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
            fieldnames.append(dbfunc::delimit(fieldname) + "=?");
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
        "UPDATE " + dbfunc::delimit(m_tablename) + " SET " +
        fieldnames.join(", ") +
        " WHERE " + dbfunc::delimit(pkname()) + "=?"
    );
    args.append(pkvalue());
    bool success = dbfunc::exec(m_db, sql, args);
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

QVector<Field> DatabaseObject::fieldsOrdered() const
{
    QVector<Field> ordered_fields;
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
