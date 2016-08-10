#include "phq9.h"
#include "tasklib/taskfactory.h"

const QString phq9_tablename = "phq9";


// ============================================================================
// Phq9Record
// ============================================================================

Phq9Record::Phq9Record(const QSqlDatabase& db)
    : TaskMainRecord(phq9_tablename, db, false, false, false)
{
    addField("q1", QVariant::Int);
}


// ============================================================================
// Phq9
// ============================================================================

Phq9::Phq9(const QSqlDatabase& db, int load_pk) :
    Task(db)
{
    qDebug() << "Phq9::Phq9";
    m_p_dbobject = new Phq9Record(db);
    loadByPk(load_pk);  // MUST ALWAYS CALL from derived constructor.
}


QString Phq9::tablename() const
{
    return phq9_tablename;
}


QString Phq9::shortname() const
{
    return "PHQ-9";
}


QString Phq9::longname() const
{
    return "Patient Health Questionnaire-9";
}


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered_phq9(factory);
}
