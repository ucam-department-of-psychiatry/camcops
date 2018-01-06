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

#include "allowedservertable.h"
#include "core/camcopsapp.h"
#include "db/databasemanager.h"
#include "lib/convert.h"

const QString ALLOWEDSERVERTABLES_TABLENAME("allowed_server_tables");
const QString AllowedServerTable::TABLENAME_FIELD("tablename");
const QString AllowedServerTable::VERSION_FIELD("min_client_version");


// Specimen constructor:
AllowedServerTable::AllowedServerTable(CamcopsApp& app, DatabaseManager& db) :
    DatabaseObject(app, db, ALLOWEDSERVERTABLES_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
}


// Loading constructor:
AllowedServerTable::AllowedServerTable(CamcopsApp& app,
                                       DatabaseManager& db,
                                       const QString& tablename) :
    DatabaseObject(app, db, ALLOWEDSERVERTABLES_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
    if (!tablename.isEmpty()) {
        // Not a specimen; load
        WhereConditions where;
        where.add(TABLENAME_FIELD, tablename);
        m_exists = load(where);
    }
}


// Saving constructor:
AllowedServerTable::AllowedServerTable(CamcopsApp& app,
                                       DatabaseManager& db,
                                       const QString& tablename,
                                       const Version& min_client_version) :
    DatabaseObject(app, db, ALLOWEDSERVERTABLES_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
    if (tablename.isEmpty()) {
        qWarning() << Q_FUNC_INFO << "Using the save-blindly constructor "
                                     "without a tablename!";
        return;
    }
    setValue(TABLENAME_FIELD, tablename);
    setValue(VERSION_FIELD, min_client_version.toVariant());
    save();
    m_exists = true;
}


void AllowedServerTable::commonConstructor()
{
    // Define fields
    addField(TABLENAME_FIELD, QVariant::String, true, true, false);  // unique
    addField(VERSION_FIELD, convert::TYPENAME_VERSION, true, false, false);

    m_exists = false;
}


AllowedServerTable::~AllowedServerTable()
{
}


QString AllowedServerTable::tablename() const
{
    return valueString(TABLENAME_FIELD);
}


Version AllowedServerTable::minClientVersion() const
{
    return Version::fromVariant(value(VERSION_FIELD));
}


bool AllowedServerTable::exists() const
{
    return m_exists;
}


void AllowedServerTable::deleteAllAllowedServerTables()
{
    m_db.deleteFrom(ALLOWEDSERVERTABLES_TABLENAME);
}


void AllowedServerTable::makeIndexes()
{
    m_db.createIndex("_idx_allowedtables_tablename",
                     ALLOWEDSERVERTABLES_TABLENAME,
                     {TABLENAME_FIELD});
}
