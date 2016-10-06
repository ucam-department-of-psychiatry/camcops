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
