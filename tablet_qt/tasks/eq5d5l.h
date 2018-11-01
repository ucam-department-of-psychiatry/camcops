#pragma once
#include <QPointer>
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class Questionnaire;
class TaskFactory;

void initializeEq5d5l(TaskFactory& factory);

class Eq5d5l : public Task
{
    Q_OBJECT
public:
    Eq5d5l(CamcopsApp& app, DatabaseManager& db,
         int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    virtual Version minimumServerVersion() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int getScore(QString field) const;
    QString getHealthStateCode() const;
protected slots:

public:
    static const QString EQ5D5L_TABLENAME;
protected:
    bool m_in_tickbox_change;
};
