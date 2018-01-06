/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
    CanvasWidget(QImage::Format format = QImage::Format_RGB32,
                 QWidget* parent = nullptr);
    CanvasWidget(const QSize& size,
                 QImage::Format format = QImage::Format_RGB32,
                 QWidget* parent = nullptr);
    ~CanvasWidget();
    void setImageSizeAndClearImage(const QSize& size);
    void setAllowShrink(bool allow_shrink);
    void setMinimumShrinkHeight(int height);  // applicable if we can shrink
    void setBorderWidth(int width);
    void setBorderColour(const QColor& colour);
    void setBorder(int width, const QColor& colour);
    void setUnusedSpaceColour(const QColor& colour);
    void setPen(const QPen& pen);
    void clear(const QColor& background);
    void setImage(const QImage& image);
    void setAdjustDisplayForDpi(bool adjust_display_for_dpi);
    void drawTo(const QPoint& pt);
    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
    QImage image() const;  // read the image
signals:
    void imageChanged();
protected:
    void commonConstructor(const QSize& size, QImage::Format format);
    virtual void paintEvent(QPaintEvent* event) override;
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
    virtual void resizeEvent(QResizeEvent* event) override;
    QPoint transformDisplayToImageCoords(QPoint point) const;
    void setBorderCss();
    QSize imageSize() const;
    QSize desiredDisplaySize() const;
protected:
    // There are three relevant sizes:
    // - imageSize() = m_image.size(): the size of the image being edited
    // - the size of the entire canvas area, from contentsRect()
    // - a third size, displaysize, the display size of the image, such that
    //      image_size = m_image_to_display_ratio * displaysize
    //   The displaysize may be different from the widget contentsRect()
    //   because we maintain the aspect ratio of the image.

    QImage::Format m_format;
    QImage m_image;
    bool m_allow_shrink;
    int m_minimum_shrink_height;
    bool m_adjust_display_for_dpi;

    int m_border_width_px;
    QColor m_border_colour;
    QColor m_unused_space_colour;
    QPen m_pen;

    double m_image_to_display_ratio;
    QPoint m_point;
};
