#pragma once
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class TaskFactory;
class OpenableWidget;
class QuBoolean;


class DemoQuestionnaire : public Task
{
public:
    DemoQuestionnaire(CamcopsApp& app, const QSqlDatabase& db,
                      int load_pk = DbConst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    virtual bool isAnonymous() const { return true; }
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QString summary() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Extra
    // ------------------------------------------------------------------------
protected:
    void callbackHello();
    void callbackArg(const QString& arg);
    QuBoolean* aceBoolean(const QString& stringname, const QString& fieldname);
};

void initializeDemoQuestionnaire(TaskFactory& factory);
