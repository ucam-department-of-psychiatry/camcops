#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class HelpMenu : public MenuWindow
{
    Q_OBJECT
public:
    HelpMenu(CamcopsApp& app);
};
