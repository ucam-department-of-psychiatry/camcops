#include "flowlayoutcontainer.h"
// #include <QDebug>
#include <QLayout>
#include "lib/uifunc.h"


FlowLayoutContainer::FlowLayoutContainer(QWidget* parent) :
    QWidget(parent)
{
    // As for LabelWordWrapWide:
    setSizePolicy(UiFunc::expandingFixedHFWPolicy());
}


FlowLayoutContainer::~FlowLayoutContainer()
{
    // qDebug() << Q_FUNC_INFO;
}


void FlowLayoutContainer::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    UiFunc::resizeEventForHFWParentWidget(this);
}
