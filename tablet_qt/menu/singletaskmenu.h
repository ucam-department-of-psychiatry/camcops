#pragma once
#include <QString>
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class SingleTaskMenu : public MenuWindow
{
    Q_OBJECT
public:
    SingleTaskMenu(const QString& tablename, CamcopsApp& app);
    virtual void buildMenu() override;
signals:
    void offerAdd(bool offer_add);
public slots:  // http://stackoverflow.com/questions/19129133/qt-signals-and-slots-permissions
    void addTask();
    void selectedPatientChanged(bool selected, const QString& details);
protected:
    QString m_tablename;
    bool m_anonymous;
};
