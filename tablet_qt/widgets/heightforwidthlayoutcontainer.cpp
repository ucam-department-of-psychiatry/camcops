#include "heightforwidthlayoutcontainer.h"
// #include <QDebug>
#include <QLayout>
#include "lib/uifunc.h"


HeightForWidthLayoutContainer::HeightForWidthLayoutContainer(QWidget* parent) :
    QWidget(parent)
{
    // As for LabelWordWrapWide:
    setSizePolicy(UiFunc::expandingFixedHFWPolicy());
}


HeightForWidthLayoutContainer::~HeightForWidthLayoutContainer()
{
    // qDebug() << Q_FUNC_INFO;
}


void HeightForWidthLayoutContainer::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    UiFunc::resizeEventForHFWParentWidget(this);
}
