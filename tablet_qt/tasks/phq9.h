#pragma once
#include <QString>
#include "common/camcops_app.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


class Phq9 : public Task
{
public:
    Phq9(const QSqlDatabase& db, int load_pk = NONEXISTENT_PK);
    ~Phq9();
    virtual QString shortname() const;
    virtual QString longname() const;
    virtual QString menutitle() const;
    virtual QString menusubtitle() const;
};

void initializePhq9(TaskFactory& factory);
