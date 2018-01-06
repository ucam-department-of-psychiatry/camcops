/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
extern const QString DATABASE_FILENAME_TEMP_SUFFIX;
extern const QString TABLE_TEMP_SUFFIX;

// SQL fragments

QString delimit(const QString& identifier);
QString selectColumns(const QStringList& columns, const QString& table);
SqlArgs updateColumns(const UpdateValues& updatevalues, const QString& table);

// Queries

void addOrderByClause(const OrderBy& order_by, SqlArgs& sqlargs_altered);
void addArgs(QSqlQuery& query, const ArgList& args);

bool execQuery(QSqlQuery& query, const SqlArgs& sqlargs,
               bool suppress_errors = false);
bool execQuery(QSqlQuery& query, const QString& sql, const ArgList& args,
               bool suppress_errors = false);

QString sqlParamHolders(int n);
ArgList argListFromIntList(const QVector<int>& intlist);

// Database structure

QStringList fieldNamesFromPragmaInfo(
        const QVector<SqlitePragmaInfoField>& infolist,
        bool delimited = false);
QString makeCreationSqlFromPragmaInfo(
        const QString& tablename,
        const QVector<SqlitePragmaInfoField>& infolist);

// Altering structure

QString sqlCreateTable(const QString& tablename,
                       const QVector<Field>& fieldlist);

// Encryption queries, via SQLCipher

bool encryptPlainDatabaseInPlace(const QString& filename,
                                 const QString& tempfilename,
                                 const QString& passphrase);

}  // namespace dbfunc
