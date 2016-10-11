// #define DEBUG_GUI_GUARD
#include "slowguiguard.h"
#include <QApplication>
#ifdef DEBUG_GUI_GUARD
#include <QDebug>
#endif
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
#ifdef DEBUG_GUI_GUARD
        qDebug() << Q_FUNC_INFO << "Making wait box";
#endif
        s_waiting = true;
        m_wait_box = new WaitBox(parent, text, title, minimum_duration_ms);
        m_wait_box->show();
    } else {
#ifdef DEBUG_GUI_GUARD
        qDebug() << Q_FUNC_INFO
                 << "Not making another wait box; one is already open";
#endif
    }
    app.processEvents();
}


SlowGuiGuard::~SlowGuiGuard()
{
#ifdef DEBUG_GUI_GUARD
    if (s_waiting) {
        qDebug() << Q_FUNC_INFO << "Closing wait box";
    }
#endif
    delete m_wait_box;
    s_waiting = false;
}
