#pragma once
#include "menulib/menuwindow.h"


class HelpMenu : public MenuWindow
{
    Q_OBJECT
public:
    HelpMenu(CamcopsApp& app);
protected:
    void visitCamcopsDocumentation() const;
    void visitCamcopsWebsite() const;
    void softwareVersions() const;
    void aboutQt();
    void showDeviceId() const;
    void viewTermsConditions() const;
};
