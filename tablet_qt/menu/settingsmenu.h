#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class SettingsMenu : public MenuWindow
{
    Q_OBJECT
public:
    SettingsMenu(CamcopsApp& app);
};
