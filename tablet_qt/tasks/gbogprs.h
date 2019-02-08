#pragma once
#include <QPointer>
#include <QString>
#include "questionnairelib/namevalueoptions.h"
#include "tasklib/task.h"

void initializeGboGPrS(TaskFactory& factory);

class GboGPrS : public Task
{
    Q_OBJECT
public:
    GboGPrS(CamcopsApp& app, DatabaseManager& db,
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
public:
    static const QString GBOGPRS_TABLENAME;
protected:
    QPointer<Questionnaire> m_questionnaire;
};
