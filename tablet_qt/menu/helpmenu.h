#pragma once
#include "menulib/menuwindow.h"


class HelpMenu : public MenuWindow
{
    Q_OBJECT
public:
    HelpMenu(CamcopsApp& app);
protected:
    void visitCamcopsDocumentation();
    void visitCamcopsWebsite();
    void softwareVersions();
    void aboutQt();
};
