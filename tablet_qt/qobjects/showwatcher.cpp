#include "showwatcher.h"
#include <QEvent>
#include "lib/layoutdumper.h"


ShowWatcher::ShowWatcher(QObject* parent, bool debug_layout) :
    QObject(parent),
    m_debug_layout(debug_layout)
{
    if (parent) {
        parent->installEventFilter(this);
    }
}


bool ShowWatcher::eventFilter(QObject* obj, QEvent* event)
{
    Q_UNUSED(obj)
    if (event->type() == QEvent::Show) {
        emit showing();
        if (m_debug_layout) {
            QWidget* w = dynamic_cast<QWidget*>(obj);
            if (w) {
                LayoutDumper::dumpWidgetHierarchy(w);
            }
        }
    }
    return false;  // continue processing the event
}
