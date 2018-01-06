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
#include <QPixmap>
#include <QPushButton>
#include <QSize>


class ImageButton : public QPushButton
{
    // Button that shows an icon image, and another when being pressed.
    // This should be more efficient than an equivalent method using
    // stylesheets, and also allows the use of the global QPixmapCache.
    //
    // Don't use for text; use ClickableLabel or ClickableLabelWordWrapWide
    // for that.

    Q_OBJECT
public:
    ImageButton(QWidget* parent = nullptr);
    ImageButton(const QString& normal_filename,
                const QString& pressed_filename,
                const QSize& size = QSize(),
                QWidget* parent = nullptr);
    ImageButton(const QString& base_filename,
                bool filename_is_camcops_stem = true,
                bool alter_unpressed_image = true,
                bool disabled = false,
                QWidget* parent = nullptr);  // Default button maker
    void setImages(const QString& base_filename,
                   bool filename_is_camcops_stem = true,
                   bool alter_unpressed_image = true,
                   bool pressed_marker_behind = true,
                   bool disabled = false,
                   bool read_only = false);
    void setNormalImage(const QString& filename, const QSize& size = QSize(),
                        bool cache = true);
    void setNormalImage(const QPixmap& pixmap, bool scale = true);
    void setPressedImage(const QString& filename, const QSize& size = QSize(),
                         bool cache = true);
    void setPressedImage(const QPixmap& pixmap, bool scale = true);
    virtual QSize sizeHint() const override;
    void setImageSize(const QSize& size, bool scale = false);
    void resizeImages(double factor);
protected:
    void commonConstructor(const QSize& size);
    virtual void paintEvent(QPaintEvent* e);
    void rescale(QPixmap& pm);
    void resizeIfNoSize();
protected:
    QPixmap m_normal_pixmap;
    QPixmap m_pressed_pixmap;
    QSize m_image_size;
};
