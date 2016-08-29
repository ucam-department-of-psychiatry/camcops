#include "focuswatcher.h"
#include <QEvent>


FocusWatcher::FocusWatcher(QObject* parent) :
    QObject(parent)
{
    if (parent) {
        parent->installEventFilter(this);
    }
}


bool FocusWatcher::eventFilter(QObject* obj, QEvent* event)
{
    Q_UNUSED(obj)
    if (event->type() == QEvent::FocusIn) {
        emit focusChanged(true);
    } else if (event->type() == QEvent::FocusOut) {
        emit focusChanged(false);
    }
    return false;
}
