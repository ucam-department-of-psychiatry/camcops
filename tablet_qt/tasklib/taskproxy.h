#pragma once
#include <QSqlDatabase>
#include "common/dbconstants.h"
#include "lib/dbfunc.h"
#include "task.h"

class TaskFactory;


// For TaskFactory:
// ===========================================================================
// Base "descriptor" class, so we can do more things with the class as an
// entity than just instantiate one.
// ===========================================================================

class TaskProxy
{
public:
    TaskProxy(TaskFactory& factory);  // Registers itself with the factory.
    // We do want to create instances...
    virtual TaskPtr create(CamcopsApp& app,
                           const QSqlDatabase& db,
                           int load_pk = DbConst::NONEXISTENT_PK) const = 0;
    virtual TaskPtrList fetch(CamcopsApp& app,
                              const QSqlDatabase& db,
                              int patient_id = DbConst::NONEXISTENT_PK) const = 0;
protected:
    virtual TaskPtrList fetchWhere(CamcopsApp& app,
                                   const QSqlDatabase& db,
                                   const WhereConditions& where) const = 0;
};
