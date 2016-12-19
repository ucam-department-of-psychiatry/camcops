/*
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
#include "common/camcopsapp.h"
#include "db/dbfunc.h"

const QString EXTRASTRINGS_TABLENAME("extrastrings");
const QString ExtraString::EXTRASTRINGS_TASK_FIELD("task");
const QString ExtraString::EXTRASTRINGS_NAME_FIELD("name");
const QString ExtraString::EXTRASTRINGS_VALUE_FIELD("value");


// Specimen constructor:
ExtraString::ExtraString(CamcopsApp& app, const QSqlDatabase& db) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, DbConst::PK_FIELDNAME,
                   true, false, false)
{
    commonConstructor();
}


// String loading constructor:
ExtraString::ExtraString(CamcopsApp& app,
                         const QSqlDatabase& db,
                         const QString& task,
                         const QString& name) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, DbConst::PK_FIELDNAME,
                   true, false, false, false)
{
    commonConstructor();
    if (!task.isEmpty() && !name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        WhereConditions where;
        where[EXTRASTRINGS_TASK_FIELD] = task;
        where[EXTRASTRINGS_NAME_FIELD] = name;
        m_exists = load(where);
    }
}


// String saving constructor:
ExtraString::ExtraString(CamcopsApp& app,
                         const QSqlDatabase& db,
                         const QString& task,
                         const QString& name,
                         const QString& value) :
    DatabaseObject(app, db, EXTRASTRINGS_TABLENAME, DbConst::PK_FIELDNAME,
                   true, false, false)
{
    commonConstructor();
    if (!task.isEmpty() && !name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        WhereConditions where;
        where[EXTRASTRINGS_TASK_FIELD] = task;
        where[EXTRASTRINGS_NAME_FIELD] = name;
        bool success = load(where);
        if (!success) {
            setValue(EXTRASTRINGS_TASK_FIELD, task);
            setValue(EXTRASTRINGS_NAME_FIELD, name);
            setValue(EXTRASTRINGS_VALUE_FIELD, value);
            save();
        }
        m_exists = true;
    }
}


void ExtraString::commonConstructor()
{
    // Define fields
    addField(EXTRASTRINGS_TASK_FIELD, QVariant::String, true, false, false);
    addField(EXTRASTRINGS_NAME_FIELD, QVariant::String, true, false, false);
    addField(EXTRASTRINGS_VALUE_FIELD, QVariant::String, false, false, false);

    m_exists = false;
}


ExtraString::~ExtraString()
{
}


QString ExtraString::value() const
{
    return valueString(EXTRASTRINGS_VALUE_FIELD);
}


bool ExtraString::exists() const
{
    return m_exists;
}


bool ExtraString::anyExist(const QString& task) const
{
    WhereConditions where;
    where[EXTRASTRINGS_TASK_FIELD] = task;
    return DbFunc::count(m_db, EXTRASTRINGS_TABLENAME, where) > 0;
}


void ExtraString::deleteAllExtraStrings()
{
    QString sql = QString("DELETE FROM %1").arg(EXTRASTRINGS_TABLENAME);
    DbFunc::exec(m_db, sql);
}
