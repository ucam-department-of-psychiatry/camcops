#pragma once
#include "common/camcopsapp.h"
#include "menulib/menuwindow.h"


class ExecutiveMenu : public MenuWindow
{
    Q_OBJECT
public:
    ExecutiveMenu(CamcopsApp& app);
};
