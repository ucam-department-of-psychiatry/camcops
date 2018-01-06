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
#include <QString>
#include <QVector>
#include <QVariant>
class QSqlQuery;


class QueryResult
{
public:
    enum class FetchMode {
        NoAnswer,  // do not store a reply
        NoFetch,  // store a reply with fact of success/failure, but no data
        FetchFirst,  // fetch first row
        FetchAll  // fetch everything
    };
public:
    QueryResult(QSqlQuery& query, bool success,
                FetchMode fetch_mode, bool store_column_names = false);
    QueryResult();  // required to be in a QVector
    bool succeeded() const;
    int nCols() const;
    int nRows() const;
    bool isEmpty() const;
    QVector<QVariant> row(int row) const;  // efficient
    QVector<QVariant> col(int col) const;  // inefficient
    QVariant at(int row, int col) const;
    QVariant at(int row, const QString& colname) const;
    QVariant firstValue() const;
    QVector<int> columnAsIntList(int col) const;
    QVector<int> firstColumnAsIntList() const;
    QStringList columnAsStringList(int col) const;
    QStringList firstColumnAsStringList() const;
    QVariant lastInsertId() const;
    QString csvHeader(const char sep = ',') const;
    QString csvRow(int row, const char sep = ',') const;
    QString csv(const char sep = ',', const char linesep = '\n') const;
    static QString fetchModeDescription(FetchMode fetch_mode);
protected:
    bool m_success;
    int m_n_cols;  // cached
    int m_n_rows;  // cached
    QStringList m_column_names;
    QVector<QVector<QVariant>> m_data;
    QVariant m_last_insert_id;

public:
    friend QDebug operator<<(QDebug debug, const QueryResult& qr);
};
