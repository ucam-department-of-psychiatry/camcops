#pragma once
#include <QDate>
#include <QDateTime>
#include <QMap>
#include <QSqlDatabase>
#include <QString>
#include "common/dbconstants.h"
#include "lib/dbfunc.h"
#include "lib/field.h"

class FieldRef;
using FieldRefPtr = QSharedPointer<FieldRef>;


class DatabaseObject
{
    // A database object supporting a single integer PK field, and a default
    // modification timestamp field, extensible to add other fields.
public:
    DatabaseObject(const QSqlDatabase& db,
                   const QString& tablename,
                   const QString& pk_fieldname = DbConst::PK_FIELDNAME,
                   bool has_modification_timestamp = true,
                   bool has_creation_timestamp = false);
    ~DatabaseObject();

    // Adding fields

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

    // Field access:

    bool setValue(const QString& fieldname, const QVariant& value);  // returns: changed?

    QVariant value(const QString& fieldname) const;
    QString prettyValue(const QString& fieldname) const;
    bool valueBool(const QString& fieldname) const;
    int valueInt(const QString& fieldname) const;
    qlonglong valueLongLong(const QString& fieldname) const;
    double valueDouble(const QString& fieldname) const;
    QDateTime valueDateTime(const QString& fieldname) const;
    QDate valueDate(const QString& fieldname) const;
    QByteArray valueByteArray(const QString& fieldname) const;

    FieldRefPtr fieldRef(const QString& fieldname,
                         bool mandatory = true,
                         bool autosave = true,
                         bool blob = false);

    // Whole-object summary:

    QString recordSummary() const;

    // Loading, saving:

    virtual bool load(int pk);
    virtual SqlArgs fetchQuerySql(const WhereConditions& where);
    virtual void setFromQuery(const QSqlQuery& query,
                              bool order_matches_fetchquery = false);
    virtual bool save();
    void nullify();  // set all fields to null values
    bool isPkNull() const;
    void touch(bool only_if_unset = false);
    void setAllDirty();

    // Deleting

    void deleteFromDatabase();

    // Debugging:

    void requireField(const QString& fieldname) const;

    // DDL

    QString sqlCreateTable() const;
    QString tablename() const;
    QString pkname() const;
    QVariant pkvalue() const;
    void makeTable();

    // For making BLOBs share the same database:
    const QSqlDatabase& database() const;

protected:
    virtual bool load(const QString& fieldname, const QVariant& where_value);
    virtual bool load(const WhereConditions& where);
    bool saveInsert();
    bool saveUpdate();
    void clearAllDirty();
    bool anyDirty() const;
    QStringList fieldnamesMapOrder() const;
    QList<Field> fieldsOrdered() const;

protected:
    QSqlDatabase m_db;
    QString m_tablename;  // also used as key for extra strings
    QString m_pk_fieldname;
    bool m_has_modification_timestamp;
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
