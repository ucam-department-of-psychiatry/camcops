/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

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
    // Widget for users to draw on a canvas (either blank, or with a starting
    // image).

    Q_OBJECT
public:
    CanvasWidget(QWidget* parent = nullptr);
    CanvasWidget(const QSize& size, QWidget* parent = nullptr);
    ~CanvasWidget();
    void setSize(const QSize& size);
    void setPen(const QPen& pen);
    void clear(const QColor& background);
    void setImage(const QImage& image, bool resize_widget = true);
    // ... if resize_widget is false, the image will be resized
    void drawTo(QPoint pt);
    virtual QSize sizeHint() const override;
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
