#pragma once
#include <QSharedPointer>
#include "lib/netcore.h"
#include "menulib/menuwindow.h"

class QMediaPlayer;


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
    void testIcd10CodeSetCreation();
    void testIcd9cmCodeSetCreation();
    void doneSeeConsole();
protected:
    QSharedPointer<NetworkManager> m_netmgr;
    QSharedPointer<QMediaPlayer> m_player;
};
