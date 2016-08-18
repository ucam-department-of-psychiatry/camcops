#pragma once
#include <QMap>
#include <QString>
#include <QVariant>
#include "common/camcopsapp.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


class DemoQuestionnaire : public Task
{
public:
    DemoQuestionnaire(const QSqlDatabase& db, int load_pk = NONEXISTENT_PK);
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
    virtual QString getSummary() const override;
    virtual QString getDetail() const override;
    virtual void edit(CamcopsApp& app) override;
protected:
    void callback_hello();
    void callback_arg(const QString& arg);
};

void initializeDemoQuestionnaire(TaskFactory& factory);
