#pragma once
#include <QImage>
#include <QPen>
#include <QPoint>
#include <QSize>
#include <QFrame>

class QColor;
class QPaintEvent;
class QMouseEvent;

// See also http://stackoverflow.com/questions/28947235/qt-draw-on-canvas


class CanvasWidget : public QFrame
{
    Q_OBJECT
public:
    CanvasWidget();
    CanvasWidget(const QSize& size);
    ~CanvasWidget();
    void setSize(const QSize& size);
    void setPen(const QPen& pen);
    void clear(const QColor& background);
    void setImage(const QImage& image, bool resize_widget = true);
    // ... if resize_widget is false, the image will be resized
    void drawTo(QPoint pt);
    virtual QSize sizeHint() const;
    QImage image() const;
signals:
    void imageChanged();
protected:
    void commonConstructor(const QSize& size);
    virtual void paintEvent(QPaintEvent* event) override;
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
protected:
    QSize m_size;
    QImage m_image;
    QPen m_pen;
    QPoint m_point;
};
