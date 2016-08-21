#include "openablewidget.h"

OpenableWidget::OpenableWidget(QWidget* parent) :
    QWidget(parent)
{
}


void OpenableWidget::build()
{
}


bool OpenableWidget::wantsFullscreen()
{
    return false;
}
