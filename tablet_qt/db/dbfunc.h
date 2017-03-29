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

#pragma once
#include <QDebug>
#include <QPair>
#include <QString>
#include <QStringList>
#include <QSqlDatabase>
#include <QVariant>
#include "common/aliases_qt.h"
#include "db/field.h"
#include "sqlargs.h"

class SqlitePragmaInfoField;

namespace dbfunc {

// Constants

extern const QString DATA_DATABASE_FILENAME;
extern const QString SYSTEM_DATABASE_FILENAME;
extern const QString TABLE_TEMP_SUFFIX;

// Database operations

QString dbFullPath(const QString& filename);
void openDatabaseOrDie(QSqlDatabase& db, const QString& filename);

// SQL fragments

QString delimit(const QString& identifier);
QString selectColumns(const QStringList& columns, const QString& table);
SqlArgs updateColumns(const UpdateValues& updatevalues, const QString& table);

// Queries

void addWhereClause(const WhereConditions& where, SqlArgs& sqlargs_altered);
void addOrderByClause(const OrderBy& order_by, SqlArgs& sqlargs_altered);
void addArgs(QSqlQuery& query, const ArgList& args);
bool execQuery(QSqlQuery& query, const QString& sql,
                const ArgList& args);
bool execQuery(QSqlQuery& query, const QString& sql);
bool execQuery(QSqlQuery& query, const SqlArgs& sqlargs);
bool exec(const QSqlDatabase& db, const QString& sql);
bool exec(const QSqlDatabase& db, const QString& sql, const ArgList& args);
bool exec(const QSqlDatabase& db, const SqlArgs& sqlargs);
bool commit(const QSqlDatabase& db);
QVariant dbFetchFirstValue(const QSqlDatabase& db, const QString& sql,
                           const ArgList& args);
QVariant dbFetchFirstValue(const QSqlDatabase& db, const QString& sql);
int dbFetchInt(const QSqlDatabase& db,
               const SqlArgs& sqlargs,
               int failure_default = -1);
int dbFetchInt(const QSqlDatabase& db,
               const QString& sql,
               int failure_default = -1);

QString sqlParamHolders(int n);
ArgList argListFromIntList(const QVector<int>& intlist);

QString csvHeader(const QSqlQuery& query, const char sep = ',');
QString csvRow(const QSqlQuery& query, const char sep = ',');
QString csv(QSqlQuery& query, const char sep = ',',
            const char linesep = '\n');

int count(const QSqlDatabase& db,
          const QString& tablename,
          const WhereConditions& where = WhereConditions());

QVector<int> getSingleFieldAsIntList(const QSqlDatabase& db,
                                     const QString& tablename,
                                     const QString& fieldname,
                                     const WhereConditions& where);
QVector<int> getPKs(const QSqlDatabase& db,
                    const QString& tablename,
                    const QString& pkname,
                    const WhereConditions& where = WhereConditions());
bool existsByPk(const QSqlDatabase& db, const QString& tablename,
                const QString& pkname, int pkvalue);

// Modification queries

bool deleteFrom(const QSqlDatabase& db,
                const QString& tablename,
                const WhereConditions& where = WhereConditions());

// Database structure

QStringList getAllTables(const QSqlDatabase& db);
bool tableExists(const QSqlDatabase& db, const QString& tablename);
QVector<SqlitePragmaInfoField> getPragmaInfo(const QSqlDatabase& db,
                                             const QString& tablename);
QStringList fieldNamesFromPragmaInfo(
        const QVector<SqlitePragmaInfoField>& infolist,
        bool delimited = false);
QStringList getFieldNames(const QSqlDatabase& db, const QString& tablename);
QString makeCreationSqlFromPragmaInfo(
        const QString& tablename,
        const QVector<SqlitePragmaInfoField>& infolist);
QString dbTableDefinitionSql(const QSqlDatabase& db, const QString& tablename);

// Altering structure

bool createIndex(const QSqlDatabase& db, const QString& indexname,
                 const QString& tablename, QStringList fieldnames);
void renameColumns(const QSqlDatabase& db, QString tablename,
                   const QVector<QPair<QString, QString>>& from_to,
                   const QString& tempsuffix = TABLE_TEMP_SUFFIX);
void renameTable(const QSqlDatabase& db, const QString& from,
                 const QString& to);
void changeColumnTypes(const QSqlDatabase& db, const QString& tablename,
                       const QVector<QPair<QString, QString>>& field_newtype,
                       const QString& tempsuffix = TABLE_TEMP_SUFFIX);
QString sqlCreateTable(const QString& tablename,
                       const QVector<Field>& fieldlist);
void createTable(const QSqlDatabase& db, const QString& tablename,
                 const QVector<Field>& fieldlist,
                 const QString& tempsuffix = TABLE_TEMP_SUFFIX);

}  // namespace dbfunc
