#include "test_menu.h"
#include <QMediaPlayer>


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app),
      m_p_netmgr(nullptr)
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
    qInfo() << "Testing debug console. This is the entire test. Success.";
    alert("Success! See the debug console for output.");
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
    // To find bad certificates, see
    // https://www.ssllabs.com/ssltest/analyze.html
    QString url = "https://egret.psychol.cam.ac.uk/index.html";  // good cert
    // QString url = "https://www.veltigroup.com/";  // bad cert (then Forbidden)

    delete m_p_netmgr;
    m_p_netmgr = new NetworkManager(url);
    m_p_netmgr->testHttps();
}


void TestMenu::testHttp()
{
    delete m_p_netmgr;
    m_p_netmgr = new NetworkManager("http://egret.psychol.cam.ac.uk/index.html");
    m_p_netmgr->testHttp();
}

