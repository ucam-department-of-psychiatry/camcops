#pragma once

#include <QSharedPointer>
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
    void testProgress();
    void testWait();
    void expensiveFunction();

protected:
    QSharedPointer<QMediaPlayer> m_player;
};
