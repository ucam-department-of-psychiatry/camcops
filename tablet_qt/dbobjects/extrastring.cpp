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

#include "extrastring.h"
#include "core/camcopsapp.h"
#include "db/databasemanager.h"

const QString EXTRASTRINGS_TABLENAME("extrastrings");
const QString ExtraString::TASK_FIELD("task");
const QString ExtraString::NAME_FIELD("name");
const QString ExtraString::VALUE_FIELD("value");


// Specimen constructor:
ExtraString::ExtraString(CamcopsApp& app, DatabaseManager& db) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
}


// String loading constructor:
ExtraString::ExtraString(CamcopsApp& app,
                         DatabaseManager& db,
                         const QString& task,
                         const QString& name) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
    if (!task.isEmpty() && !name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        WhereConditions where;
        where.add(TASK_FIELD, task);
        where.add(NAME_FIELD, name);
        m_exists = load(where);
    }
}


// String saving constructor:
ExtraString::ExtraString(CamcopsApp& app,
                         DatabaseManager& db,
                         const QString& task,
                         const QString& name,
                         const QString& value) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, dbconst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
    if (task.isEmpty() || name.isEmpty()) {
        qWarning() << Q_FUNC_INFO << "Using the save-blindly constructor "
                                     "without a name or task!";
        return;
    }
    setValue(TASK_FIELD, task);
    setValue(NAME_FIELD, name);
    setValue(VALUE_FIELD, value);
    save();
    m_exists = true;
}


void ExtraString::commonConstructor()
{
    // Define fields
    addField(TASK_FIELD, QVariant::String, true, false, false);
    addField(NAME_FIELD, QVariant::String, true, false, false);
    addField(VALUE_FIELD, QVariant::String, false, false, false);

    m_exists = false;
}


ExtraString::~ExtraString()
{
}


QString ExtraString::value() const
{
    return valueString(VALUE_FIELD);
}


bool ExtraString::exists() const
{
    return m_exists;
}


bool ExtraString::anyExist(const QString& task) const
{
    WhereConditions where;
    where.add(TASK_FIELD, task);
    return m_db.count(EXTRASTRINGS_TABLENAME, where) > 0;
}


void ExtraString::deleteAllExtraStrings()
{
    m_db.deleteFrom(EXTRASTRINGS_TABLENAME);
}


void ExtraString::makeIndexes()
{
    m_db.createIndex("_idx_extrastrings_task_name",
                     EXTRASTRINGS_TABLENAME,
                     {ExtraString::TASK_FIELD,
                      ExtraString::NAME_FIELD});
}
