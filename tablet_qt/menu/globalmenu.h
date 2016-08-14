#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class GlobalMenu : public MenuWindow
{
    Q_OBJECT
public:
    GlobalMenu(CamcopsApp& app);
};
