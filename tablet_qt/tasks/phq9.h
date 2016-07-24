#pragma once
#include <QString>
#include "common/camcops_app.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


class Phq9 : public Task
{
public:
    Phq9(const QSqlDatabase& db, int loadPk = NONEXISTENT_PK);
    virtual QString tablename() const { return "phq9"; }
    virtual QString shortname() const { return "PHQ-9"; }
    virtual QString longname() const { return "Patient Health Questionnaire-9"; }
    virtual DatabaseObject* makeDatabaseObject();
};

void InitializePhq9(TaskFactory& factory);
