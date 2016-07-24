#include "test_menu.h"
#include <QDebug>
#include <QMediaPlayer>
#include "lib/netcore.h"


void test_debug_console()
{
    qDebug() << "Testing debug console. This is the entire test. Success.";
}

void test_sound()
{
    QMediaPlayer* player = new QMediaPlayer;
    QUrl url("qrc:///sounds/camcops/portal_still_alive.mp3");
    qDebug() << "Trying to play:" << url;
    player->setMedia(url);
    player->setVolume(50);
    player->play();
}


void test_https()
{
    NetworkManager netmgr("http://egret.psychol.cam.ac.uk/git/crate");
    netmgr.test_https();
}


MenuItem make_func_item(const QString& title, MenuItem::ActionFuncPtr func)
{
    MenuItem item = MenuItem();
    item.m_title = title;
    item.m_func = func;
    return item;
}


TestMenu::TestMenu(CamcopsApp& app)
    : MenuWindow(app)
{
    m_items = {
        make_func_item("Test debug console", &test_debug_console),
        make_func_item("Test sound", &test_sound),
        make_func_item("Test network (HTTPS/SSL)", &test_https),
    };

    buildMenu();
}

TestMenu::~TestMenu()
{
}

MenuWindow* buildTestWindow(CamcopsApp& app)
{
    return new TestMenu(app);
}
