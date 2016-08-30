#pragma once
#include <QImage>
#include <QPen>
#include <QSize>
#include <QWidget>

class QColor;
class QPaintEvent;
class QMouseEvent;

// See also http://stackoverflow.com/questions/28947235/qt-draw-on-canvas


class CanvasWidget : public QWidget
{
    Q_OBJECT
public:
    CanvasWidget(const QSize& size);
    ~CanvasWidget();
    void clear(const QColor& background);
    void setImage(const QImage& image, bool resize_widget = true);
    // ... if resize_widget is false, the image will be resized
signals:
    void paintEvent(QPaintEvent* event);
    void mousePressEvent(QMouseEvent* event);
    void mouseMoveEvent(QMouseEvent* event);
protected:
    QSize m_size;
    QImage m_canvas;
    QPen m_pen;
};

// ** see UIPaintView.java
// *** dirty state?
