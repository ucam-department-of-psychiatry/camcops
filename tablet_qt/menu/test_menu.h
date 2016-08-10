#pragma once
#include "common/camcops_app.h"
#include "lib/netcore.h"
#include "menulib/menuitem.h"
#include "menulib/menuwindow.h"


class TestMenu : public MenuWindow
{
    Q_OBJECT

public:
    TestMenu(CamcopsApp& app);
    ~TestMenu();
protected:
    void testDebugConsole();
    void testSound();
    void testHttp();
    void testHttps();
protected:
    NetworkManager* m_p_netmgr;
};
