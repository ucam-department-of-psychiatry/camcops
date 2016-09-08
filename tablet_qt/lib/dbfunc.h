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
    // http://www.stroustrup.com/C++11FAQ.html#member-init
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


using ArgList = QList<QVariant>;
using WhereConditions = QMap<QString, QVariant>;


struct SqlArgs {
public:
    SqlArgs(const QString& sql, const ArgList& args) :
        sql(sql), args(args) {}
public:
    QString sql;
    ArgList args;
};


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
                   const QString& sql,
                   const ArgList& args = ArgList(),
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

}
