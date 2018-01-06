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
#include "db/queryresult.h"
#include "db/sqlargs.h"


struct ThreadedQueryRequest
{
public:
    ThreadedQueryRequest(const SqlArgs& sqlargs,
                         QueryResult::FetchMode fetch_mode,
                         bool store_column_names,
                         bool suppress_errors = false,
                         bool thread_abort_request_not_query = false);
    ThreadedQueryRequest();  // required to be in a QVector
public:
    SqlArgs sqlargs;
    QueryResult::FetchMode fetch_mode;
    bool store_column_names;
    bool suppress_errors;
    bool thread_abort_request_not_query;
protected:
    friend QDebug operator<<(QDebug debug, const ThreadedQueryRequest& r);
};
