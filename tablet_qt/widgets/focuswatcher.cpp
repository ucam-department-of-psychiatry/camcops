// #define DEBUG_FOCUS
#include "focuswatcher.h"
#ifdef DEBUG_FOCUS
#include <QDebug>
#endif
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

#ifdef DEBUG_FOCUS
        qDebug() << obj->objectName() << "FocusIn";
#endif
        emit focusChanged(true);

    } else if (event->type() == QEvent::FocusOut) {

#ifdef DEBUG_FOCUS
        qDebug() << obj->objectName() << "FocusOut";
#endif
        emit focusChanged(false);

    }
    return false;
}
