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
class DatabaseManager;


class DbTransaction
{
    // In general, consider AVOIDING this and using DbNestableTransaction
    // instead. DbTransaction uses BEGIN TRANSACTION/COMMIT/ROLLBACK, and so
    // if you accidentally nest it, things go wrong.
    // DbNestableTransaction uses SAVEPOINT x/RELEASE x/ROLLBACK TO SAVEPOINT x
    // instead, which is safely nestable as long as x is transaction-specific,
    // and RELEASE behaves like COMMIT when it reaches the top level.
public:
    DbTransaction(DatabaseManager& db);
    ~DbTransaction();
    void fail();
    void succeed();
protected:
    DatabaseManager& m_db;
    bool m_fail;
};
