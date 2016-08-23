#pragma once
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class TaskFactory;
class OpenableWidget;


class DemoQuestionnaire : public Task
{
public:
    DemoQuestionnaire(const QSqlDatabase& db,
                      int load_pk = DbConst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    virtual bool isAnonymous() const { return true; }
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QString summary() const override;
    virtual OpenableWidget* editor(CamcopsApp& app,
                                   bool read_only = false) override;
protected:
    void callback_hello();
    void callback_arg(const QString& arg);
};

void initializeDemoQuestionnaire(TaskFactory& factory);
