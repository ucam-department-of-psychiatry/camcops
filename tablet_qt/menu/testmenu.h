#pragma once
#include <QSharedPointer>
#include "common/camcopsapp.h"
#include "lib/netcore.h"
#include "menulib/menuwindow.h"


class TestMenu : public MenuWindow
{
    Q_OBJECT

public:
    TestMenu(CamcopsApp& app);
protected:
    void testPhq9Creation();
    void testDebugConsole();
    void testSound();
    void testHttp();
    void testHttps();
protected:
    QSharedPointer<NetworkManager> m_p_netmgr;
};
