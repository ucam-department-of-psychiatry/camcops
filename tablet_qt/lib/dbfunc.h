#pragma once
#include <QDebug>
#include <QList>
#include <QPair>
#include <QString>
#include <QStringList>
#include <QSqlDatabase>
#include <QVariant>
#include "lib/field.h"
#include "sqlargs.h"

const QString DATA_DATABASE_FILENAME = "camcops_data.sqlite";
const QString SYSTEM_DATABASE_FILENAME = "camcops_sys.sqlite";
const QString TABLE_TEMP_SUFFIX = "_temp";

class SqlitePragmaInfoField;


using WhereConditions = QMap<QString, QVariant>;


namespace DbFunc {

    // Database operations

    void openDatabaseOrDie(QSqlDatabase& db, const QString& filename);

    // SQL fragments

    QString delimit(const QString& fieldname);
    void addWhereClause(const WhereConditions& where, SqlArgs& sqlargs_altered);

    // Queries

    void addArgs(QSqlQuery& query, const ArgList& args);
    bool execQuery(QSqlQuery& query, const QString& sql,
                    const ArgList& args);
    bool execQuery(QSqlQuery& query, const QString& sql);
    bool execQuery(QSqlQuery& query, const SqlArgs& sqlargs);
    bool exec(const QSqlDatabase& db, const QString& sql);
    bool exec(const QSqlDatabase& db, const QString& sql, const ArgList& args);
    bool exec(const QSqlDatabase& db, const SqlArgs& sqlargs);
    QVariant dbFetchFirstValue(const QSqlDatabase& db, const QString& sql,
                               const ArgList& args);
    QVariant dbFetchFirstValue(const QSqlDatabase& db, const QString& sql);
    int dbFetchInt(const QSqlDatabase& db,
                   const SqlArgs& sqlargs,
                   int failureDefault = -1);
    int dbFetchInt(const QSqlDatabase& db,
                   const QString& sql,
                   int failureDefault = -1);

    QString csvHeader(const QSqlQuery& query, const char sep = ',');
    QString csvRow(const QSqlQuery& query, const char sep = ',');
    QString csv(QSqlQuery& query, const char sep = ',',
                const char linesep = '\n');

    int count(const QSqlDatabase& db,
              const QString& tablename,
              const WhereConditions& where = WhereConditions());

    // Database structure

    bool tableExists(const QSqlDatabase& db, const QString& tablename);
    QList<SqlitePragmaInfoField> getPragmaInfo(const QSqlDatabase& db,
                                          const QString& tablename);
    QStringList fieldNamesFromPragmaInfo(const QList<SqlitePragmaInfoField>& infolist,
                                         bool delimited = false);
    QStringList dbFieldNames(const QSqlDatabase& db, const QString& tablename);
    QString makeCreationSqlFromPragmaInfo(const QString& tablename,
                                          const QList<SqlitePragmaInfoField>& infolist);
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
}
