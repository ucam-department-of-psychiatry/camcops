#include "testmenu.h"
#include <QMediaPlayer>
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"  // for TaskPtr


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app, tr("CamCOPS self-tests"), ""),
      m_p_netmgr(nullptr)
{
    m_items = {
        MenuItem(tr("User testing")).setLabelOnly(),
        MenuItem(
            "Test sound",
            std::bind(&TestMenu::testSound, this)
        ).setNotIfLocked(),
        MenuItem(tr("Developer testing")).setLabelOnly(),
        MenuItem(
            "Test debug console",
            std::bind(&TestMenu::testDebugConsole, this)
        ).setNotIfLocked(),
        MenuItem(
            "Test network (HTTP)",
            std::bind(&TestMenu::testHttp, this)
        ).setNotIfLocked(),
        MenuItem(
            "Test network (HTTPS/SSL)",
            std::bind(&TestMenu::testHttps, this)
        ).setNotIfLocked(),
        MenuItem(
            "Test PHQ9 creation",
            std::bind(&TestMenu::testPhq9Creation, this)
        ).setNotIfLocked(),
        MenuItem(tr("Test card 1 (black, white)")),  // ***
        MenuItem(tr("Test card 2 (scaling, scrolling)")),  // ***
    };
    buildMenu();
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

    m_p_netmgr = QSharedPointer<NetworkManager>(new NetworkManager(url));
    m_p_netmgr->testHttps();
}


void TestMenu::testHttp()
{
    QString url = "http://egret.psychol.cam.ac.uk/index.html";
    m_p_netmgr = QSharedPointer<NetworkManager>(new NetworkManager(url));
    m_p_netmgr->testHttp();
}


void TestMenu::testPhq9Creation()
{
    QString tablename = "phq9";
    TaskPtr p_task = m_app.m_p_task_factory->create(tablename);
    if (!p_task) {
        qCritical() << "Failed to create task: " << qUtf8Printable(tablename);
        return;
    }
    qDebug() << *p_task;
    m_app.setWhiskerConnected(true);
    alert("Done; see console");
    m_app.setWhiskerConnected(false);
}
