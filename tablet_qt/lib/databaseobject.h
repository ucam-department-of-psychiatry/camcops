#pragma once
#include <QMap>
#include <QSqlDatabase>
#include <QString>
#include "common/dbconstants.h"
#include "lib/dbfunc.h"
#include "lib/field.h"

class FieldRef;


class DatabaseObject
{
    // A database object supporting a single PK field, and a default
    // modification timestamp field, extensible to add other fields.
public:
    DatabaseObject(const QString& tablename,
                   const QSqlDatabase db,
                   bool has_default_pk_field = true,
                   bool has_modification_timestamp = true,
                   bool has_creation_timestamp = false);
    // Adding fields
    void addField(const QString& fieldname,
                  QVariant::Type type,
                  bool mandatory = false,
                  bool unique = false,
                  bool pk = false);
    void addField(const Field& field);
    QStringList getFieldnames() const;
    // Field access:
    QVariant getValue(const QString& fieldname) const;
    bool setValue(const QString& fieldname, const QVariant& value);  // returns: changed?
    FieldRef fieldRef(const QString& fieldname);
    // Loading, saving:
    virtual bool load(int pk);
    virtual SqlArgs fetchQuerySql(const WhereConditions& where);
    virtual void setFromQuery(const QSqlQuery& query,
                              bool correct_order = false);
    virtual bool save();
    void nullify();  // set all fields to null values
    bool isPkNull() const;
    void touch(bool only_if_unset = false);
    void setAllDirty();
    // Debugging:
    void requireField(const QString& fieldname) const;
    // DDL
    QString sqlCreateTable() const;
    QString tablename() const;
    QString pkname() const;
    QVariant pkvalue() const;
    void makeTable();

protected:
    bool saveInsert();
    bool saveUpdate();
    void clearAllDirty();

protected:
    QString m_tablename;  // also used as key for extra strings
    QSqlDatabase m_db;
    bool m_has_modification_timestamp;
    typedef QMap<QString, Field> MapType;
    typedef QMapIterator<QString, Field> MapIteratorType;
    typedef QMutableMapIterator<QString, Field> MutableMapIteratorType;
    MapType m_record;
    mutable QString m_cached_pkname;

public:
    friend QDebug operator<<(QDebug debug, const DatabaseObject& d);
};

// The QSqlDatabase doesn't need to be passed by pointer; it copies itself
// safely. See qsqldatabase.cpp (and note also that pass-by-copy, rather than
// pointers or const references, is how QSqlQuery works in any case).
