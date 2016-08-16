#include "phq9.h"
#include "tasklib/taskfactory.h"


Phq9::Phq9(const QSqlDatabase& db, int load_pk) :
    Task(db, "phq9", false, false, false)
{
    addField("q1", QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


QString Phq9::shortname() const
{
    return "PHQ-9";
}


QString Phq9::longname() const
{
    return "Patient Health Questionnaire-9";
}


QString Phq9::menusubtitle() const
{
    return "Self-scoring of the 9 depressive symptoms in DSM-IV.";
}


bool Phq9::isComplete() const
{
    return false;  // ***
}


QString Phq9::getSummary() const
{
    return "***";
}


QString Phq9::getDetail() const
{
    return "***";
}


void Phq9::edit(CamcopsApp& app)
{
    (void)app;
    // ***
}


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered(factory);
}
