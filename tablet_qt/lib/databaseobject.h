#pragma once
#include <QMap>
#include <QSqlDatabase>
#include <QSqlRecord>
#include <QString>
#include "common/db_constants.h"
#include "lib/field.h"


class DatabaseObject
{
    // A database object supporting a single PK field, and a default
    // modification timestamp field.
public:
    DatabaseObject(const QString& tablename,
                   const QSqlDatabase db,
                   bool hasDefaultPkField = true,
                   bool hasModificationTimestamp = true);
    void addField(const QString& fieldname,
                  QVariant::Type type,
                  bool mandatory = false,
                  bool unique = false,
                  bool pk = false);
    void addField(const Field& field);
    void setAllDirty();
    // Field access:
    QVariant value(const QString& fieldname);
    bool setValue(const QString& fieldname, const QVariant& value);  // returns: changed?
    // Loading, saving:
    bool loadByPk(int pk);
    // Debugging:
    void requireField(const QString& fieldname);
    QString sqlCreateTable() const;
    QString tablename() const;
    QString pkname() const;
    void touch();
    void save();
    void makeTable();

protected:
    QString m_tablename;  // also used as key for extra strings
    QSqlDatabase m_db;
    bool m_hasModificationTimestamp;
    typedef QMap<QString, Field> MapType;
    typedef QMapIterator<QString, Field> MapIteratorType;
    typedef QMutableMapIterator<QString, Field> MutableMapIteratorType;
    MapType m_record;

public:
    friend QDebug operator<<(QDebug debug, const DatabaseObject& d);
};

// The QSqlDatabase doesn't need to be passed by pointer; it copies itself
// safely. See qsqldatabase.cpp (and note also that pass-by-copy, rather than
// pointers or const references, is how QSqlQuery works in any case).
