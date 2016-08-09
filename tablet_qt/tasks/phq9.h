#pragma once
#include <QString>
#include "common/camcops_app.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskmainrecord.h"


class Phq9Record : public TaskMainRecord
{
public:
    Phq9Record(const QSqlDatabase& db);
};


class Phq9 : public Task
{
public:
    Phq9(const QSqlDatabase& db, int load_pk = NONEXISTENT_PK);
    virtual QString tablename() const;
    virtual QString shortname() const;
    virtual QString longname() const;
};

void initializePhq9(TaskFactory& factory);
