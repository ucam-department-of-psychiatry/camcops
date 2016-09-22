#include "shootabug.h"
#include <QDebug>
#include <QEvent>
#include <QMouseEvent>
#include "lib/debugfunc.h"


bool ShootABug::eventFilter(QObject* recv, QEvent* event)
{
    if (event->type() != QEvent::MouseButtonPress) {
        return false;  // pass it on
    }
    QMouseEvent* mevent = static_cast<QMouseEvent*>(event);
    if ((mevent->modifiers() & Qt::ControlModifier) &&
            (mevent->button() & Qt::LeftButton)) {  // Ctrl + left mouse click.
        DebugFunc::dumpQObject(recv);
        // Return false, if you want the application to receive the event;
        // return true to block.
        return true;  // Block
    }
    return false;
}
