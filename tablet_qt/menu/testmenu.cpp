#define DEBUG_OPTIONS

#include "testmenu.h"
#include <QCoreApplication>
#include <QMediaPlayer>
#include <QProgressDialog>
#include <QThread>
#include "common/platform.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "lib/filefunc.h"
#include "lib/networkmanager.h"
#include "lib/uifunc.h"
#include "lib/slownonguifunctioncaller.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"  // for TaskPtr

const int EXPENSIVE_FUNCTION_DURATION_MS = 20000;


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app, tr("CamCOPS self-tests"), ""),
      m_player(nullptr)
{
    m_items = {
        MenuItem(tr("User testing")).setLabelOnly(),
        MenuItem(
            tr("Test sound"),
            std::bind(&TestMenu::testSound, this)
        ).setNotIfLocked(),
        MenuItem(tr("Developer testing")).setLabelOnly(),
        MenuItem(
            tr("Test debug console"),
            std::bind(&TestMenu::testDebugConsole, this)
        ),
        MenuItem(
            tr("Test network (HTTP)"),
            std::bind(&TestMenu::testHttp, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Test network (HTTPS/SSL)"),
            std::bind(&TestMenu::testHttps, this)
        ).setNotIfLocked(),
#ifdef DEBUG_OPTIONS
        MenuItem(
            tr("Test PHQ9 creation"),
            std::bind(&TestMenu::testPhq9Creation, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Test ICD-10 code set creation"),
            std::bind(&TestMenu::testIcd10CodeSetCreation, this)
        ),
        MenuItem(
            tr("Test ICD-9-CM code set creation"),
            std::bind(&TestMenu::testIcd9cmCodeSetCreation, this)
        ),
#endif
        MenuItem(
            tr("Test HTML display, and fullscreen display"),
            HtmlMenuItem("Example HTML: this window should be full-screen",
                         FileFunc::taskHtmlFilename("ace3"),
                         "", true)
        ),
        MenuItem(
            tr("Test progress dialog"),
            std::bind(&TestMenu::testProgress, this)
        ),
        MenuItem(
            tr("Test wait dialog"),
            std::bind(&TestMenu::testWait, this)
        ),
        MenuItem(
            tr("(†) Run software unit tests (reporting to debugging stream)")
        ).setNeedsPrivilege(),  // ***
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

    NetworkManager* netmgr = m_app.networkManager();
    netmgr->setTitle("Test HTTPS");
    netmgr->testHttpsGet(url);
}


void TestMenu::testHttp()
{
    QString url = "http://egret.psychol.cam.ac.uk/index.html";
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->setTitle("Test HTTP");
    netmgr->testHttpGet(url);
}


void TestMenu::testPhq9Creation()
{
#ifdef DEBUG_OPTIONS
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
#endif
}


void TestMenu::testIcd10CodeSetCreation()
{
#ifdef DEBUG_OPTIONS
    Icd10 icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
#endif
}


void TestMenu::testIcd9cmCodeSetCreation()
{
#ifdef DEBUG_OPTIONS
    Icd9cm icd(m_app);
    qDebug() << icd;
    doneSeeConsole();
#endif
}


void TestMenu::doneSeeConsole()
{
    if (Platform::PLATFORM_TABLET) {
        UiFunc::alert("Done; see USB debugging output");
    } else {
        UiFunc::alert("Done; see console");
    }
}


void TestMenu::testProgress()
{
    qDebug() << Q_FUNC_INFO << "start";
    // http://doc.qt.io/qt-4.8/qprogressdialog.html#details
    // http://stackoverflow.com/questions/3752742/how-do-i-create-a-pause-wait-function-using-qt
    int num_things = 100;
    QProgressDialog progress(
        "Testing progress (but not doing anything; safe to abort)...",
        "Abort test", 0, num_things, this);
    progress.setWindowTitle("Progress dialog");
    progress.setWindowModality(Qt::WindowModal);
    progress.setMinimumDuration(0);
    for (int i = 0; i < num_things; i++) {
        progress.setValue(i);
        if (progress.wasCanceled()) {
            break;
        }
        // Do a small thing:
        QThread::msleep(50);
        // Prevent other things (like audio) from freezing:
        QCoreApplication::processEvents();
    }
    progress.setValue(num_things);
    qDebug() << Q_FUNC_INFO << "finish";
}


void TestMenu::testWait()
{
    SlowNonGuiFunctionCaller(
        std::bind(&TestMenu::expensiveFunction, this),
        this,
        QString("Running expensive function in worker thread (for %1 "
                "ms)").arg(EXPENSIVE_FUNCTION_DURATION_MS),
        "Please wait");
}


void TestMenu::expensiveFunction()
{
    qDebug() << Q_FUNC_INFO << "start: sleep time (ms)" << EXPENSIVE_FUNCTION_DURATION_MS;
    QThread::msleep(EXPENSIVE_FUNCTION_DURATION_MS);
    qDebug() << Q_FUNC_INFO << "finish";
}
