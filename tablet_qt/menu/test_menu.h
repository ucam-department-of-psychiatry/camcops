#pragma once
#include "common/camcops_app.h"
#include "menulib/menu_item.h"
#include "menulib/menu_window.h"


class TestMenu : public MenuWindow
{
    Q_OBJECT

public:
    TestMenu(CamcopsApp& app);
    ~TestMenu();

};

MenuWindow* buildTestWindow(CamcopsApp& app);

