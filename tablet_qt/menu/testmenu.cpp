#include "testmenu.h"
#include <QMediaPlayer>
#include "common/platform.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "lib/filefunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"  // for TaskPtr


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app, tr("CamCOPS self-tests"), ""),
      m_netmgr(nullptr),
      m_player(nullptr)
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
        ),
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
        MenuItem(
            "Test ICD-10 code set creation",
            std::bind(&TestMenu::testIcd10CodeSetCreation, this)
        ),
        MenuItem(
            "Test ICD-9-CM code set creation",
            std::bind(&TestMenu::testIcd9cmCodeSetCreation, this)
        ),
        MenuItem(
            "Test HTML display, and fullscreen display",
            HtmlMenuItem("Example HTML: this window should be full-screen",
                         FileFunc::taskHtmlFilename("ace3"),
                         "", true)
        ),
        MenuItem(tr("Test card 1 (black, white)")),  // ***
        MenuItem(tr("Test card 2 (scaling, scrolling)")),  // ***
    };
}


TestMenu::~TestMenu()
{
    // Unsure if necessary - but similar code in QuAudioPlayer was crashing.
    if (m_player) {
        m_player->stop();
    }
}


void TestMenu::testDebugConsole()
{
    qInfo() << "Testing debug console. This is the entire test. Success.";
    UiFunc::alert("Success! See the debug console for output.");
}


void TestMenu::testSound()
{
    m_player = QSharedPointer<QMediaPlayer>(new QMediaPlayer(),
                                            &QObject::deleteLater);
    // http://doc.qt.io/qt-5/qsharedpointer.html
    // Failing to use deleteLater() can cause crashes, as there may be
    // outstanding events relating to this object.
    QUrl url(UiConst::DEMO_SOUND_URL);
    qDebug() << "Trying to play:" << url;
    m_player->setMedia(url);
    m_player->setVolume(50);
    m_player->play();
}


void TestMenu::testHttps()
{
    // To find bad certificates, see
    // https://www.ssllabs.com/ssltest/analyze.html
    QString url = "https://egret.psychol.cam.ac.uk/index.html";  // good cert
    // QString url = "https://www.veltigroup.com/";  // bad cert (then Forbidden)

    m_netmgr = QSharedPointer<NetworkManager>(new NetworkManager(url));
    m_netmgr->testHttps();
}


void TestMenu::testHttp()
{
    QString url = "http://egret.psychol.cam.ac.uk/index.html";
    m_netmgr = QSharedPointer<NetworkManager>(new NetworkManager(url));
    m_netmgr->testHttp();
}


void TestMenu::testPhq9Creation()
{
    QString tablename = "phq9";
    TaskPtr p_task = m_app.factory()->create(tablename);
    if (!p_task) {
        qCritical() << Q_FUNC_INFO << "Failed to create task: "
                    << qUtf8Printable(tablename);
        return;
    }
    qDebug() << *p_task;
    m_app.setWhiskerConnected(true); // *** remove
    doneSeeConsole();
    m_app.setWhiskerConnected(false); // *** remove
}


void TestMenu::testIcd10CodeSetCreation()
{
    Icd10 icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
}


void TestMenu::testIcd9cmCodeSetCreation()
{
    Icd9cm icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
}


void TestMenu::doneSeeConsole()
{
    if (Platform::PLATFORM_TABLET) {
        UiFunc::alert("Done; see USB debugging output");
    } else {
        UiFunc::alert("Done; see console");
    }
}
