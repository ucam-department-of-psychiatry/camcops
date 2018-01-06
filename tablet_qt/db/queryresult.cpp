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

#include "queryresult.h"
#include <QDebug>
#include <QSqlQuery>
#include <QSqlRecord>
#include "lib/convert.h"


QueryResult::QueryResult(QSqlQuery& query,
                         const bool success,
                         const FetchMode fetch_mode,
                         const bool store_column_names) :
    m_success(success)
{
    int ncols = 0;
    if (success) {
        m_last_insert_id = query.lastInsertId();  // in case it was an INSERT
        if (fetch_mode != FetchMode::NoFetch) {
            bool first = true;
            while (query.next()) {
                if (first) {
                    const QSqlRecord rec = query.record();
                    ncols = rec.count();
                    if (ncols == 0) {
                        break;
                    }
                    if (store_column_names) {
                        for (int i = 0; i < ncols; ++i) {
                            m_column_names.append(rec.fieldName(i));
                        }
                    }
                }

                QVector<QVariant> row;
                for (int i = 0; i < ncols; ++i) {
                    row.append(query.value(i));
                }
                m_data.append(row);

                if (first) {
                    if (fetch_mode == FetchMode::FetchFirst) {
                        // all done
                        break;
                    }
                    first = false;
                }
            }
        }
    }
    m_n_cols = ncols;
    m_n_rows = m_data.length();
}


QueryResult::QueryResult() :
    m_n_cols(0),
    m_n_rows(0)
{
}


bool QueryResult::succeeded() const
{
    return m_success;
}


int QueryResult::nCols() const
{
    return m_n_cols;
}


int QueryResult::nRows() const
{
    return m_n_rows;
}


bool QueryResult::isEmpty() const
{
    return m_n_rows == 0 || m_n_cols == 0;
}


QVector<QVariant> QueryResult::row(const int row) const
{
    Q_ASSERT(row >= 0 && row <= m_n_rows);
    return m_data.at(row);
}


QVector<QVariant> QueryResult::col(const int col) const
{
    Q_ASSERT(col >= 0 && col <= m_n_cols);
    QVector<QVariant> values;
    for (int row = 0; row < m_n_rows; ++row) {
        values.append(at(row, col));
    }
    return values;
}


QVariant QueryResult::at(const int row, const int col) const
{
    Q_ASSERT(row >= 0 && row <= m_n_rows);
    Q_ASSERT(col >= 0 && col <= m_n_cols);
    return m_data.at(row).at(col);
}


QVariant QueryResult::at(const int row, const QString& colname) const
{
    const int col = m_column_names.indexOf(colname);
    return at(row, col);
}


QVariant QueryResult::firstValue() const
{
    if (isEmpty()) {
        return QVariant();
    }
    return at(0, 0);
}


QVector<int> QueryResult::columnAsIntList(const int col) const
{
    Q_ASSERT(col >= 0 && col <= m_n_cols);
    QVector<int> values;
    for (int row = 0; row < m_n_rows; ++row) {
        values.append(at(row, col).toInt());
    }
    return values;
}


QVector<int> QueryResult::firstColumnAsIntList() const
{
    return columnAsIntList(0);
}


QStringList QueryResult::columnAsStringList(const int col) const
{
    QStringList values;
    for (int row = 0; row < m_n_rows; ++row) {
        values.append(at(row, col).toString());
    }
    return values;
}


QStringList QueryResult::firstColumnAsStringList() const
{
    return columnAsStringList(0);
}


QVariant QueryResult::lastInsertId() const
{
    return m_last_insert_id;
}


QString QueryResult::csvHeader(const char sep) const
{
    if (m_column_names.length() < nCols()) {
        qCritical("Column names were discarded from the QueryResult but are "
                  "now being requested for a CSV header!");
    }
    return m_column_names.join(sep);
}


QString QueryResult::csvRow(const int row, const char sep) const
{
    const int ncols = nCols();
    QStringList values;
    for (int col = 0; col < ncols; ++col) {
        values.append(convert::toSqlLiteral(at(row, col)));
    }
    return values.join(sep);
}


QString QueryResult::csv(const char sep, const char linesep) const
{
    QStringList rows;
    if (!m_column_names.isEmpty()) {
        rows.append(csvHeader(sep));
    }
    const int nrows = nRows();
    for (int row = 0; row < nrows; ++row) {
        rows.append(csvRow(row));
    }
    return rows.join(linesep);
}


QString QueryResult::fetchModeDescription(const FetchMode fetch_mode)
{
    switch (fetch_mode) {
    case FetchMode::NoAnswer:
        return "NoAnswer";
    case FetchMode::NoFetch:
        return "NoFetch";
    case FetchMode::FetchAll:
        return "FetchAll";
    case FetchMode::FetchFirst:
        return "FetchFirst";
    default:
        return "?";
    }
}


// ========================================================================
// For friends
// ========================================================================

QDebug operator<<(QDebug debug, const QueryResult& qr)
{
    debug.nospace().noquote()
            << "succeeded=" << qr.succeeded()
            << ", columns=" << qr.nCols()
            << ", rows=" << qr.nRows() << "\n"
            << qr.csv();
    return debug;
}
