#include "openablewidget.h"

OpenableWidget::OpenableWidget(QWidget* parent) :
    QWidget(parent),
    m_wants_fullscreen(false)
{
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
