#pragma once
#include "menulib/menuwindow.h"


class SettingsMenu : public MenuWindow
{
    Q_OBJECT
public:
    SettingsMenu(CamcopsApp& app);
protected:
    OpenableWidget* configureServerSettings(CamcopsApp& app);
    void setPrivilege();
    QString makeTitle(const QString& part1, const QString& part2) const;
    QString makeHint(const QString& part1, const QString& part2) const;
protected:
    CamcopsApp& m_app;
};
