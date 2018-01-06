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
#include "db/databaseobject.h"
#include "lib/version.h"
class CamcopsApp;


class AllowedServerTable : public DatabaseObject
{
public:
    // Specimen constructor:
    AllowedServerTable(CamcopsApp& app, DatabaseManager& db);
    // Loading constructor:
    AllowedServerTable(CamcopsApp& app, DatabaseManager& db,
                       const QString& tablename);
    // Saving constructor:
    AllowedServerTable(CamcopsApp& app, DatabaseManager& db,
                       const QString& tablename,
                       const Version& min_client_version);
    virtual ~AllowedServerTable();
    QString tablename() const;
    Version minClientVersion() const;
    bool exists() const;
    void deleteAllAllowedServerTables();  // sort-of static function
    void makeIndexes();  // sort-of static function

public:
    static const QString TABLENAME_FIELD;
    static const QString VERSION_FIELD;
protected:
    void commonConstructor();
    bool m_exists;
};
