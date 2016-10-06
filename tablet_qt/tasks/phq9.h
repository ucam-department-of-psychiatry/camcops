#pragma once
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class TaskFactory;
class OpenableWidget;


class Phq9 : public Task
{
public:
    Phq9(CamcopsApp& app, const QSqlDatabase& db,
         int load_pk = DbConst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QString summary() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
};

void initializePhq9(TaskFactory& factory);
