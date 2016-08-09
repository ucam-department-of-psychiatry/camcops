#include "test_menu.h"
#include <QDebug>
#include <QMediaPlayer>


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app),
      m_p_netmgr(NULL)
{
    m_items = {
        MenuItem::makeFuncItem(
            "Test debug console",
            std::bind(&TestMenu::testDebugConsole, this)),
        MenuItem::makeFuncItem(
            "Test sound",
            std::bind(&TestMenu::testSound, this)),
        MenuItem::makeFuncItem(
            "Test network (HTTP)",
            std::bind(&TestMenu::testHttp, this)),
        MenuItem::makeFuncItem(
            "Test network (HTTPS/SSL)",
            std::bind(&TestMenu::testHttps, this)),
    };
    buildMenu();
}


TestMenu::~TestMenu()
{
}


void TestMenu::testDebugConsole()
{
    qDebug() << "Testing debug console. This is the entire test. Success.";
}


void TestMenu::testSound()
{
    QMediaPlayer* player = new QMediaPlayer;
    QUrl url("qrc:///sounds/camcops/portal_still_alive.mp3");
    qDebug() << "Trying to play:" << url;
    player->setMedia(url);
    player->setVolume(50);
    player->play();
}


void TestMenu::testHttps()
{
    delete m_p_netmgr;
    m_p_netmgr = new NetworkManager("https://egret.psychol.cam.ac.uk/index.html");
    m_p_netmgr->testHttps();
}


void TestMenu::testHttp()
{
    delete m_p_netmgr;
    m_p_netmgr = new NetworkManager("http://egret.psychol.cam.ac.uk/index.html");
    m_p_netmgr->testHttp();
}

