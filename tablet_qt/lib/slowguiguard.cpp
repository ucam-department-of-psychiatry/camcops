#include "slowguiguard.h"
#include <QApplication>
#include <QDebug>
#include <QWidget>
#include "widgets/waitbox.h"


bool SlowGuiGuard::s_waiting = false;


SlowGuiGuard::SlowGuiGuard(QApplication& app,
                           QWidget* parent,
                           const QString& text,
                           const QString& title,
                           int minimum_duration_ms) :
    m_wait_box(nullptr)

{
    if (!s_waiting) {
        qDebug() << Q_FUNC_INFO << "Making wait box";
        s_waiting = true;
        m_wait_box = new WaitBox(parent, text, title, minimum_duration_ms);
        m_wait_box->show();
    } else {
        qDebug() << Q_FUNC_INFO
                 << "Not making another wait box; one is already open";
    }
    app.processEvents();
}


SlowGuiGuard::~SlowGuiGuard()
{
    if (s_waiting) {
        qDebug() << Q_FUNC_INFO << "Closing wait box";
    }
    delete m_wait_box;
    s_waiting = false;
}
