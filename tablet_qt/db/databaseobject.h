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

#pragma once
#include <QDate>
#include <QDateTime>
#include <QMap>
#include <QSqlDatabase>
#include <QString>
#include "common/aliases_camcops.h"
#include "common/aliases_qt.h"
#include "common/dbconstants.h"
#include "db/field.h"
#include "db/sqlargs.h"

class CamcopsApp;


class DatabaseObject : public QObject
{
    // A database object supporting a single integer PK field, and a default
    // modification timestamp field, extensible to add other fields.
    Q_OBJECT  // so our derived classes can be too
public:
    DatabaseObject(CamcopsApp& m_app,
                   const QSqlDatabase& db,
                   const QString& tablename,
                   const QString& pk_fieldname = DbConst::PK_FIELDNAME,
                   bool has_modification_timestamp = true,
                   bool has_creation_timestamp = false,
                   bool has_move_off_tablet_field = true,
                   bool triggers_need_upload = true);
    virtual ~DatabaseObject();

    // ========================================================================
    // Adding fields
    // ========================================================================

    void addField(const QString& fieldname,
                  QVariant::Type type,
                  bool mandatory = false,
                  bool unique = false,
                  bool pk = false);
    void addField(const Field& field);
    void addFields(const QStringList& fieldnames, QVariant::Type type,
                   bool mandatory = false);
    bool hasField(const QString& fieldname) const;
    QStringList fieldnames() const;

    // ========================================================================
    // Field access
    // ========================================================================

    bool setValue(const QString& fieldname, const QVariant& value,
                  bool touch_record = true);  // returns: changed?

    QVariant value(const QString& fieldname) const;
    QString prettyValue(const QString& fieldname) const;
    bool valueBool(const QString& fieldname) const;
    int valueInt(const QString& fieldname) const;
    qlonglong valueLongLong(const QString& fieldname) const;
    qulonglong valueULongLong(const QString& fieldname) const;
    double valueDouble(const QString& fieldname) const;
    QDateTime valueDateTime(const QString& fieldname) const;
    QDate valueDate(const QString& fieldname) const;
    QByteArray valueByteArray(const QString& fieldname) const;
    QString valueString(const QString& fieldname) const;

    QList<QVariant> values(const QStringList& fieldnames) const;

    FieldRefPtr fieldRef(const QString& fieldname,
                         bool mandatory = true,
                         bool autosave = true,
                         bool blob = false);

    // ========================================================================
    // Manipulating multiple fields
    // ========================================================================

    int sumInt(const QStringList& fieldnames) const;
    double sumDouble(const QStringList& fieldnames) const;
    QVariant mean(const QStringList& fieldnames) const;

    int countTrue(const QStringList& fieldnames) const;
    bool allTrue(const QStringList& fieldnames) const;
    bool allFalseOrNull(const QStringList& fieldnames) const;

    bool anyNull(const QStringList& fieldnames) const;
    int numNull(const QStringList& fieldnames) const;
    int numNotNull(const QStringList& fieldnames) const;

    int countWhere(const QStringList& fieldnames,
                   const QList<QVariant>& values) const;
    int countWhereNot(const QStringList& fieldnames,
                      const QList<QVariant>& values) const;

    // ========================================================================
    // Whole-object summary
    // ========================================================================

    QString fieldSummary(const QString& fieldname,
                         const QString& altname = "") const;
    QStringList recordSummaryLines() const;
    QString recordSummary() const;

    // ========================================================================
    // Loading, saving
    // ========================================================================

    virtual bool load(int pk);
    virtual bool load(const QString& fieldname, const QVariant& where_value);
    virtual bool load(const WhereConditions& where);
    virtual SqlArgs fetchQuerySql(const WhereConditions& where = WhereConditions());
    virtual void setFromQuery(const QSqlQuery& query,
                              bool order_matches_fetchquery = false);
    virtual bool save();
    void nullify();  // set all fields to null values
    bool isPkNull() const;
    void touch(bool only_if_unset = false);
    void setAllDirty();

    // ========================================================================
    // Batch operations
    // ========================================================================

    QList<int> getAllPKs() const;

    // ========================================================================
    // Deleting
    // ========================================================================

    virtual void deleteFromDatabase();

    // ========================================================================
    // Debugging:
    // ========================================================================

    void requireField(const QString& fieldname) const;

    // ========================================================================
    // Special field access
    // ========================================================================

    bool shouldMoveOffTablet() const;
    void setMoveOffTablet(bool move_off);
    void toggleMoveOffTablet();

    // ========================================================================
    // DDL
    // ========================================================================

    QString sqlCreateTable() const;
    QString tablename() const;
    QString pkname() const;
    QVariant pkvalue() const;
    int pkvalueInt() const;
    void makeTable();

    // For making BLOBs share the same database:
    const QSqlDatabase& database() const;

protected:
    bool saveInsert();
    bool saveUpdate();
    void clearAllDirty();
    bool anyDirty() const;
    QStringList fieldnamesMapOrder() const;
    QList<Field> fieldsOrdered() const;

protected:
    CamcopsApp& m_app;
    QSqlDatabase m_db;
    QString m_tablename;  // also used as key for extra strings
    QString m_pk_fieldname;
    bool m_has_modification_timestamp;
    bool m_has_move_off_tablet_field;
    bool m_triggers_need_upload;
    using MapType = QMap<QString, Field>;
    using MapIteratorType = QMapIterator<QString, Field>;
    using MutableMapIteratorType = QMutableMapIterator<QString, Field>;
    MapType m_record;  // Note: no intrinsic ordering to fields from this. So:
    QStringList m_ordered_fieldnames;
    QMap<QString, FieldRefPtr> m_fieldrefs;

public:
    friend QDebug operator<<(QDebug debug, const DatabaseObject& d);
};

// The QSqlDatabase doesn't need to be passed by pointer; it copies itself
// safely. See qsqldatabase.cpp (and note also that pass-by-copy, rather than
// pointers or const references, is how QSqlQuery works in any case).
