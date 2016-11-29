#pragma once
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class TaskFactory;
class OpenableWidget;

void initializePhq9(TaskFactory& factory);


class Phq9 : public Task
{
public:
    Phq9(CamcopsApp& app, const QSqlDatabase& db,
         int load_pk = DbConst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QString summary() const override;
    virtual QString detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int totalScore() const;
    int nCoreSymptoms() const;
    int nOtherSymptoms() const;
    static QString severity(int score);
};
