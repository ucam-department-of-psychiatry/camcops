#pragma once
#include <QDebug>
#include <QList>
#include <QPair>
#include <QString>
#include <QStringList>
#include <QSqlDatabase>
#include <QVariant>
#include "lib/field.h"

const QString DATA_DATABASE_FILENAME = "camcops_data.sqlite";
const QString SYSTEM_DATABASE_FILENAME = "camcops_sys.sqlite";
const QString TABLE_TEMP_SUFFIX = "_temp";


class SqlitePragmaInfo {
public:
    int cid = -1;
    QString name;
    QString type;
    bool notnull = false;
    QVariant dflt_value;
    bool pk = false;
public:
    friend QDebug operator<<(QDebug debug, const SqlitePragmaInfo& info);
};


class FieldCreationPlan {
public:
    QString name;
    const Field* intended_field = nullptr;
    bool exists_in_db = false;
    QString existing_type;
    bool add = false;
    bool drop = false;
    bool change = false;
public:
    friend QDebug operator<<(QDebug debug, const FieldCreationPlan& plan);
};


// Database operations

void openDatabaseOrDie(QSqlDatabase& db, const QString& filename);

// SQL fragments

QString delimit(const QString& fieldname);

// Queries

void addArgs(QSqlQuery& query, const QList<QVariant>& args);
bool execQuery(QSqlQuery& query, const QString& sql,
                const QList<QVariant>& args);
bool execQuery(QSqlQuery& query, const QString& sql);
bool exec(const QSqlDatabase& db, const QString& sql);
bool exec(const QSqlDatabase& db,
          const QString& sql,
          const QList<QVariant>& args);
QVariant dbFetchFirstValue(QSqlDatabase& db, const QString& sql,
                              const QList<QVariant>& args);
QVariant dbFetchFirstValue(QSqlDatabase& db, const QString& sql);
int dbFetchInt(const QSqlDatabase& db,
               const QString& sql,
               const QList<QVariant>& args = QList<QVariant>(),
               int failureDefault = -1);
int dbFetchInt(const QSqlDatabase& db,
               const QString& sql,
               int failureDefault = -1);

// Database structure

bool tableExists(const QSqlDatabase& db, const QString& tablename);
QList<SqlitePragmaInfo> getPragmaInfo(const QSqlDatabase& db,
                                      const QString& tablename);
QStringList fieldNamesFromPragmaInfo(const QList<SqlitePragmaInfo>& infolist,
                                     bool delimited = false);
QStringList dbFieldNames(const QSqlDatabase& db, const QString& tablename);
QString makeCreationSqlFromPragmaInfo(const QString& tablename,
                                      const QList<SqlitePragmaInfo>& infolist);
QString dbTableDefinitionSql(const QSqlDatabase& db, const QString& tablename);
bool createIndex(const QSqlDatabase& db, const QString& indexname,
                 const QString& tablename, QStringList fieldnames);
void renameColumns(const QSqlDatabase& db, QString tablename,
                   const QList<QPair<QString, QString>>& from_to,
                   const QString& tempsuffix = TABLE_TEMP_SUFFIX);
void renameTable(const QSqlDatabase& db, const QString& from,
                 const QString& to);
void changeColumnTypes(const QSqlDatabase& db, const QString& tablename,
                       const QList<QPair<QString, QString>>& field_newtype,
                       const QString& tempsuffix = TABLE_TEMP_SUFFIX);
QString sqlCreateTable(const QString& tablename,
                       const QList<Field>& fieldlist);
void createTable(const QSqlDatabase& db, const QString& tablename,
                 const QList<Field>& fieldlist,
                 const QString& tempsuffix = TABLE_TEMP_SUFFIX);
