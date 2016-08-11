#pragma once
#include <QSharedPointer>
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
    void testPhq9Creation();
    void testDebugConsole();
    void testSound();
    void testHttp();
    void testHttps();
protected:
    CamcopsApp& m_app;
    QSharedPointer<NetworkManager> m_p_netmgr;
};
