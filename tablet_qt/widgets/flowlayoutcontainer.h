#pragma once
#include <QWidget>


class FlowLayoutContainer : public QWidget
{
    // A widget that knows that its layout implements a height-for-width
    // function and deals with it properly, adjusting the widget's height
    // to the layout (and its contents).
    // - SPECIFICALLY: IT WILL REDUCE ITS HEIGHT (TO FIT THE CONTENTS) AS THE
    //   LAYOUT SPREADS OUT CHILD WIDGETS TO THE RIGHT (in a way that a plain
    //   QWidget won't).
    // - Use this when you want to put a FlowLayout in (e.g. see QuMCQ).
    // - You might also use this when you want a widget containing a layout
    //   containing a LabelWordWrapWide object, or similar (e.g. see
    //   ClickableLabelWordWrapWide -- though that has to re-implement, not
    //   inherit, for Qt inheritance reasons).
    Q_OBJECT
public:
    FlowLayoutContainer(QWidget* parent = nullptr);
    virtual ~FlowLayoutContainer();
    virtual void resizeEvent(QResizeEvent* event) override;
};
