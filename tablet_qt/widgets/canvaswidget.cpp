#include "canvaswidget.h"
#include <QColor>
#include <QMouseEvent>
#include <QPainter>
#include <QPaintEvent>


CanvasWidget::CanvasWidget(const QSize& size) :
    m_size(size)
{
    QSizePolicy sp(QSizePolicy::Fixed, QSizePolicy::Fixed);
    setSizePolicy(sp);
}


CanvasWidget::~CanvasWidget()
{
}


void CanvasWidget::clear(const QColor& background)
{
    m_canvas.fill(background);
    update();
}


void CanvasWidget::setImage(const QImage &image, bool resize_widget)
{
    if (resize_widget) {
        m_canvas = image;
        m_size = image.size();
    } else {
        // scale image onto m_canvas
        m_canvas = image.scaled(m_size);
    }
    update();
}


void CanvasWidget::paintEvent(QPaintEvent* event)
{
    QWidget::paintEvent(event);
    QPainter painter(this);
    painter.drawImage(0, 0, m_canvas);
}


void CanvasWidget::mousePressEvent(QMouseEvent* event)
{
    if (event->buttons() & Qt::LeftButton){
        drawPixel(event->pos());  // *** modify
        // repaint? update? ***
        repaint();
    }
}


void CanvasWidget::mouseMoveEvent(QMouseEvent* event)
{
    if (event->buttons() & Qt::LeftButton){
        drawPixel(event->pos());  // *** modify
        // repaint? update? ***
        repaint();
    }
}
