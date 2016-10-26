#pragma once
#include <QObject>

/*

See
    - http://www.kdab.com/~volker/devdays/2011/EffectiveDebuggingAndProfilingForQtAndQtQuick.pdf
    - http://www.vikingsoft.eu/blog/?p=8

Install with
    qApp->installEventFilter(new ShootABug());

That should filter events for the entire application:
    http://doc.qt.io/qt-5.7/eventsandfilters.html
    ... "such global event filters are called before the object-specific
    filters"

When a widget is CTRL-clicked, it should report details of itself to the
console.

HOWEVER, what I'm getting is that every click is being reported as coming
from widget name QMainWindowClassWindow, widget class QWidgetWindow

*/

class ShootABug : public QObject
{
    // Object that can report debugging information, given a debug build of Qt.

    Q_OBJECT
public:
    bool eventFilter(QObject* recv, QEvent* event);
};
