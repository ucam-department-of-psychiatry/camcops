#pragma once
#include <QString>
#include "common/camcopsapp.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


class Phq9 : public Task
{
public:
    Phq9(const QSqlDatabase& db, int load_pk = NONEXISTENT_PK);
    ~Phq9();
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    virtual QString shortname() const;
    virtual QString longname() const;
    virtual QString menutitle() const;
    virtual QString menusubtitle() const;
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const;
    virtual QString getSummary() const;
    virtual QString getDetail() const;
    virtual void edit();
};

void initializePhq9(TaskFactory& factory);
