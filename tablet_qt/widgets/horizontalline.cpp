#include "horizontalline.h"
#include <QPainter>
#include <QStyleOption>

/*

===============================================================================
Horizontal/vertical lines
===============================================================================
- Option 1: QFrame
- Option 2: QWidget
    http://stackoverflow.com/questions/10053839/how-does-designer-create-a-line-widget

- Complex interaction between C++ properties and stylesheets.
  http://doc.qt.io/qt-4.8/stylesheet-examples.html#customizing-qframe

- If you inherit from a QWidget, you need to implement the stylesheet painter:
  http://stackoverflow.com/questions/7276330/qt-stylesheet-for-custom-widget
  http://doc.qt.io/qt-5.7/stylesheet-reference.html

*/

HorizontalLine::HorizontalLine(int width, QWidget* parent) :
    QWidget(parent)
{
    setFixedHeight(width);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    // setStyleSheet(QString("background-color: %1;").arg(colour));
}


void HorizontalLine::paintEvent(QPaintEvent*)
{
    // Must do this for stylesheets to work.
    QStyleOption opt;
    opt.init(this);
    QPainter p(this);
    style()->drawPrimitive(QStyle::PE_Widget, &opt, &p, this);
}
