#include "verticalline.h"
#include <QPainter>
#include <QStyleOption>


VerticalLine::VerticalLine(int width, QWidget* parent) :
    QWidget(parent)
{
    setFixedWidth(width);
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Expanding);
    // setStyleSheet(QString("background-color: %1;").arg(colour));
}


void VerticalLine::paintEvent(QPaintEvent*)
{
    // Must do this for stylesheets to work.
    QStyleOption opt;
    opt.init(this);
    QPainter p(this);
    style()->drawPrimitive(QStyle::PE_Widget, &opt, &p, this);
}
