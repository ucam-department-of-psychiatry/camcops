#pragma once
#include <QString>
#include "menulib/menuwindow.h"
#include "tasklib/task.h"


class SingleTaskMenu : public MenuWindow
{
    Q_OBJECT
public:
    SingleTaskMenu(const QString& tablename, CamcopsApp& app);
    virtual void build() override;
signals:
    void offerAdd(bool offer_add);
public slots:  // http://stackoverflow.com/questions/19129133/qt-signals-and-slots-permissions
    void addTask();
    void selectedPatientChanged(bool selected, const QString& details);
    void taskFinished();
protected:
    QString m_tablename;
    bool m_anonymous;
    TaskPtr m_current_task;
};
