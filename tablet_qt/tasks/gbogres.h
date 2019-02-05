#pragma once
#include <QPointer>
#include <QString>
#include "questionnairelib/namevalueoptions.h"
#include "tasklib/task.h"

void initializeGboGReS(TaskFactory& factory);

class GboGReS : public Task
{
    Q_OBJECT
public:
    GboGReS(CamcopsApp& app, DatabaseManager& db,
         int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // -----------c-------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task specific
    // ------------------------------------------------------------------------
    void updateMandatory();
    QString completedBy() const;
    QString extraGoals() const;
    QString goalNumber() const;
public:
    static const QString GBOGRES_TABLENAME;
protected:
    NameValueOptions m_completed_by;
    QPointer<Questionnaire> m_questionnaire;
};
