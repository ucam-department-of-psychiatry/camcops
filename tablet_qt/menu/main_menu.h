#pragma once
#include "common/camcops_app.h"
#include "menulib/menu_window.h"


class MainMenu : public MenuWindow
{
    Q_OBJECT

public:
    MainMenu(CamcopsApp& app);
    ~MainMenu();

    static MenuWindow* makeTestMenu(CamcopsApp& app);
};
