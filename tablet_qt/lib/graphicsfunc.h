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
#include <QObject>
class QBrush;
class QColor;
class QGraphicsProxyWidget;
class QGraphicsScene;
class QPen;
class QPushButton;
class QRectF;
class QString;
class QWidget;


namespace graphicsfunc
{

QString pixelCss(int px);
QString colourCss(const QColor& colour);
QString penStyleCss(const QPen& pen);
QString penCss(const QPen& pen);

struct ButtonAndProxy {
    // Ownership of QGraphicsProxyWidget/QWidget pairs is shared, i.e. if
    // either is destroyed, the other is automatically destroyed.
    // Since the proxy is owned by the scene when added to the scene (which
    // happens as it's created), I think all these things are owned by the
    // scene.
    QPushButton* button;
    QGraphicsProxyWidget* proxy;
};

ButtonAndProxy makeGraphicsTextButton(
        QGraphicsScene* scene,  // button is added to scene
        const QRectF& rect,
        int padding_px,
        const QString& text,
        int font_size_px,
        const QColor& text_colour,
        const QColor& background_colour,
        const QColor& pressed_background_colour,
        const QPen& border_pen,
        int corner_radius_px,
        QWidget* parent = nullptr);

}  // namespace graphicsfunc
