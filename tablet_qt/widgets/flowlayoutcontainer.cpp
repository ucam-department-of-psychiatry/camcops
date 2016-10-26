#include "flowlayoutcontainer.h"
// #include <QDebug>
#include <QLayout>
#include "lib/uifunc.h"


FlowLayoutContainer::FlowLayoutContainer(QWidget* parent) :
    QWidget(parent)
{
    // As for LabelWordWrapWide:
    setSizePolicy(UiFunc::horizExpandingHFWPolicy());
}


FlowLayoutContainer::~FlowLayoutContainer()
{
    // qDebug() << Q_FUNC_INFO;
}


void FlowLayoutContainer::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    QLayout* lay = layout();
    if (!lay || !lay->hasHeightForWidth()) {
        return;
    }
    int w = width();
    int h = lay->heightForWidth(w);
    setFixedHeight(h);
    updateGeometry();
}
