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
#include <QColor>
#include <QFont>
#include <QObject>
#include <QPen>
class AdjustablePie;
class QBrush;
class QGraphicsProxyWidget;
class QGraphicsScene;
class QGraphicsTextItem;
class QLabel;
class QPushButton;
class QRectF;
class QString;
class QWidget;


namespace graphicsfunc
{

// ============================================================================
// Support structures
// ============================================================================

struct TextConfig {
    TextConfig(qreal font_size_pt,
               const QColor& colour,
               qreal width = -1,
               Qt::Alignment alignment = Qt::AlignCenter) :
        font_size_pt(font_size_pt),
        colour(colour),
        width(width),
        alignment(alignment)
    {}
    qreal font_size_pt;
    QColor colour;
    qreal width;
    Qt::Alignment alignment;
};


struct ButtonConfig {
    ButtonConfig(int padding_px,
                 qreal font_size_pt,
                 const QColor& text_colour,
                 Qt::Alignment text_alignment,
                 const QColor& background_colour,
                 const QColor& pressed_background_colour,
                 const QPen& border_pen,
                 int corner_radius_px) :
        padding_px(padding_px),
        font_size_pt(font_size_pt),
        text_colour(text_colour),
        text_alignment(text_alignment),
        background_colour(background_colour),
        pressed_background_colour(pressed_background_colour),
        border_pen(border_pen),
        corner_radius_px(corner_radius_px)
    {}
    int padding_px;
    qreal font_size_pt;
    QColor text_colour;
    Qt::Alignment text_alignment;
    QColor background_colour;
    QColor pressed_background_colour;
    QPen border_pen;
    int corner_radius_px;
};


struct ButtonAndProxy {
    // Ownership of QGraphicsProxyWidget/QWidget pairs is shared, i.e. if
    // either is destroyed, the other is automatically destroyed.
    // Since the proxy is owned by the scene when added to the scene (which
    // happens as it's created), I think all these things are owned by the
    // scene.
    QPushButton* button = nullptr;
    QGraphicsProxyWidget* proxy = nullptr;
    // No success in implementing this:
    /*
    QMetaObject::Connection connect(
            const QObject* receiver,
            const QMetaMethod& method,
            Qt::ConnectionType type = Qt::AutoConnection);
    */
    // ... get "static assertion failed: Signal and slot arguments are not compatible."
};


struct LabelAndProxy {
    QLabel* label = nullptr;
    QGraphicsProxyWidget* proxy = nullptr;
};


struct AdjustablePieAndProxy {
    AdjustablePie* pie = nullptr;
    QGraphicsProxyWidget* proxy = nullptr;
};


// ============================================================================
// CSS
// ============================================================================

QString pixelCss(int px);
QString ptCss(qreal pt);
QString colourCss(const QColor& colour);
QString penStyleCss(const QPen& pen);
QString penCss(const QPen& pen);
QString labelCss(const QColor& colour);

// ============================================================================
// Graphics calculations and painting
// ============================================================================

void alignRect(QRectF& rect, Qt::Alignment alignment);

void drawSector(QPainter& painter,
                const QPointF& tip,
                qreal radius,
                qreal start_angle_deg,  // zero is 3 o'clock
                qreal end_angle_deg,  // zero is 3 o'clock
                bool treat_as_clockwise_angles,
                const QPen& pen,
                const QBrush& brush);

QRectF textRectF(const QString& text, const QFont& font);
// Text with alignment:
void drawText(QPainter& painter, const QPointF& point, const QString& text,
              const QFont& font, Qt::Alignment align);
// Drawing text with alignment at a point (not a rectangle):
void drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect = 0);
void drawText(QPainter& painter, const QPointF& point, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect = 0);

// ============================================================================
// Creating QGraphicsScene objects
// ============================================================================

ButtonAndProxy makeTextButton(
        QGraphicsScene* scene,  // button is added to scene
        const QRectF& rect,
        const ButtonConfig& config,
        const QString& text,
        QFont font = QFont(),
        QWidget* parent = nullptr);

LabelAndProxy makeText(
        QGraphicsScene* scene,  // text is added to scene
        const QPointF& point,
        const TextConfig& config,
        const QString& text,
        QFont font = QFont(),
        QWidget* parent = nullptr);

AdjustablePieAndProxy makeAdjustablePie(
        QGraphicsScene* scene,  // pie is added to scene
        const QPointF& centre,
        int n_sectors,
        qreal diameter,
        QWidget* parent = nullptr);


}  // namespace graphicsfunc
