#include "keypresswatcher.h"
#include <QDialog>
#include <QKeyEvent>
#include <QObject>


KeyPressWatcher::KeyPressWatcher(QDialog* parent) :
    QObject(parent)
{
    if (parent) {
        parent->installEventFilter(this);
    }
}


bool KeyPressWatcher::eventFilter(QObject* obj, QEvent* event)
{
    Q_UNUSED(obj)
    if (event->type() == QEvent::KeyPress) {
        QKeyEvent *key_event = static_cast<QKeyEvent*>(event);
        int key = key_event->key();
        emit keypress(key);
        if (m_map.contains(key)) {
            const CallbackFunction& func = m_map[key];
            func();
        }
    }
    return false;  // continue processing the event
}


void KeyPressWatcher::addKeyEvent(int key, const CallbackFunction& callback)
{
    m_map[key] = callback;
}
