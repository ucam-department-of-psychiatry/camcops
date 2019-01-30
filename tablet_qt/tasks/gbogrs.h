#ifndef GBOGRS_H
#define GBOGRS_H

#pragma once
#include <QPointer>
#include <QString>
#include "questionnairelib/namevalueoptions.h"
#include "tasklib/task.h"

void initializeGboGrs(TaskFactory& factory);

class GboGrs : public Task
{
    Q_OBJECT
public:
    GboGrs(CamcopsApp& app, DatabaseManager& db,
         int load_pk = dbconst::NONEXISTENT_PK);
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
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task specific
    // ------------------------------------------------------------------------
    void updateMandatory();
public:
    static const QString GBOGRS_TABLENAME;
protected:
    NameValueOptions m_completed_by;
    QPointer<Questionnaire> m_questionnaire;
};

#endif // GBOGRS_H
