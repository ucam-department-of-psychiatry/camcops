// #define DEBUG_OPENABLE_WIDGET_LAYOUT

#include "openablewidget.h"
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
#include "qobjects/showwatcher.h"
#endif

OpenableWidget::OpenableWidget(QWidget* parent) :
    QWidget(parent),
    m_wants_fullscreen(false)
{
#ifdef DEBUG_OPENABLE_WIDGET_LAYOUT
    ShowWatcher* showwatcher = new ShowWatcher(this, true);
    Q_UNUSED(showwatcher);
#endif
}


void OpenableWidget::build()
{
}


bool OpenableWidget::wantsFullscreen()
{
    return m_wants_fullscreen;
}


void OpenableWidget::setWantsFullscreen(bool fullscreen)
{
    m_wants_fullscreen = fullscreen;
}
