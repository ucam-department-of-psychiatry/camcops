#include "phq9.h"
#include "tasklib/taskfactory.h"


Phq9::Phq9(const QSqlDatabase& db, int load_pk) :
    Task(db, "phq9", false, false, false)
{
    qDebug() << "Phq9::Phq9";

    addField("q1", QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


Phq9::~Phq9()
{
    qDebug() << "Phq9::~Phq9";
}


QString Phq9::shortname() const
{
    return "PHQ-9";
}


QString Phq9::longname() const
{
    return "Patient Health Questionnaire-9";
}


QString Phq9::menutitle() const
{
    return "Patient Health Questionnaire-9 (PHQ-9)";
}


QString Phq9::menusubtitle() const
{
    return "Self-scoring of the 9 depressive symptoms in DSM-IV.";
}


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered_phq9(factory);
}
