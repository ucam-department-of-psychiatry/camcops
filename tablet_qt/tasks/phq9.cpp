#include "phq9.h"
#include "tasklib/taskfactory.h"

Phq9::Phq9(const QSqlDatabase& db, int loadPk) :
    Task(db)
{
    initDatabaseObject(loadPk);  // MUST ALWAYS CALL from derived constructor.
}

DatabaseObject* Phq9::makeDatabaseObject()
{
    DatabaseObject* dbo = makeBaseDatabaseObject();
    dbo->addField("q1", QVariant::Int);
    return dbo;
}

void InitializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registeredPhq9(factory);
}
