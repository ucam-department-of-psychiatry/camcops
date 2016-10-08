#include "phq9.h"
#include "tasklib/taskfactory.h"


Phq9::Phq9(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, "phq9", false, false, false)
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


QString Phq9::summary() const
{
    return "***";
}


OpenableWidget* Phq9::editor(bool read_only)
{
    Q_UNUSED(read_only)
    return nullptr; // ***
}


void initializePhq9(TaskFactory& factory)
{
    static TaskRegistrar<Phq9> registered(factory);
}
