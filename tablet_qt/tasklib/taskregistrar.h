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

#pragma once
#include <QSqlQuery>
#include "task.h"
#include "taskproxy.h"


// For TaskFactory:
// ===========================================================================
// Wrapper that makes a TaskProxy out of any Task-derived class
// ===========================================================================

template<class Derived> class TaskRegistrar : public TaskProxy
{
    static_assert(std::is_base_of<Task, Derived>::value,
                  "You can only use Task-derived classes here.");
public:
    TaskRegistrar(TaskFactory& factory) :
        TaskProxy(factory)  // registers proxy with factory (see TaskProxy::TaskProxy)
    {}

    TaskPtr create(CamcopsApp& app,
                   const QSqlDatabase& db,
                   int load_pk = DbConst::NONEXISTENT_PK) const override
    {
        // Create a single instance of a task (optionally, loading it)
        return TaskPtr(new Derived(app, db, load_pk));
    }

    TaskPtrList fetch(CamcopsApp& app,
                      const QSqlDatabase& db,
                      int patient_id = DbConst::NONEXISTENT_PK) const override
    {
        // Fetch multiple tasks, either matching a patient_id, or all for
        // the task type.
        Derived specimen(app, db, DbConst::NONEXISTENT_PK);
        bool anonymous = specimen.isAnonymous();
        if (patient_id != DbConst::NONEXISTENT_PK && anonymous) {
            // No anonymous tasks will match a specific patient.
            return TaskPtrList();
        }
        WhereConditions where;
        if (patient_id != DbConst::NONEXISTENT_PK) {
            where[PATIENT_FK_FIELDNAME] = QVariant(patient_id);
        }
        return fetchWhere(app, db, where);
    }

protected:
    TaskPtrList fetchWhere(CamcopsApp& app,
                           const QSqlDatabase& db,
                           const WhereConditions& where) const override
    {
        // Fetch multiple tasks according to the field/value "where" criteria
        TaskPtrList tasklist;
        Derived specimen(app, db, DbConst::NONEXISTENT_PK);
        SqlArgs sqlargs = specimen.fetchQuerySql(where);
        QSqlQuery query(db);
        bool success = DbFunc::execQuery(query, sqlargs);
        if (success) {  // success check may be redundant (cf. while clause)
            while (query.next()) {
                TaskPtr p_new_task(new Derived(app, db,
                                               DbConst::NONEXISTENT_PK));
                p_new_task->setFromQuery(query, true);
                tasklist.append(p_new_task);
            }
        }
        return tasklist;
    }
};
