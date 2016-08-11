#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class MainMenu : public MenuWindow
{
    Q_OBJECT

public:
    MainMenu(CamcopsApp& app);
    ~MainMenu();

    static MenuWindow* makeTestMenu(CamcopsApp& app);
};
