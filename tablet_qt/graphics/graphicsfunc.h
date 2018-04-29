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
#include <QColor>
#include <QFont>
#include <QMap>
#include <QObject>
#include <QPen>
#include "common/colourdefs.h"
#include "graphics/buttonconfig.h"
#include "graphics/textconfig.h"
class AdjustablePie;
class SvgWidgetClickable;
class QBrush;
class QGraphicsPixmapItem;
class QGraphicsProxyWidget;
class QGraphicsScene;
class QGraphicsRectItem;
class QGraphicsTextItem;
class QLabel;
class QPushButton;
class QRectF;
class QString;
class QSvgRenderer;
class QWidget;


namespace graphicsfunc
{

// ============================================================================
// Constants
// ============================================================================

extern const QString TEST_SVG;

// ============================================================================
// Support structures
// ============================================================================

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


struct SvgWidgetAndProxy {
    SvgWidgetClickable* widget = nullptr;
    QGraphicsProxyWidget* proxy = nullptr;
};


// ============================================================================
// SvgTransform
// ============================================================================

class SvgTransform {
public:
    SvgTransform();
    SvgTransform& matrix(qreal a, qreal b, qreal c, qreal d, qreal e, qreal f);
    SvgTransform& translate(qreal x, qreal y = 0.0);
    SvgTransform& scale(qreal xy);
    SvgTransform& scale(qreal x, qreal y);
    SvgTransform& rotate(qreal a);
    SvgTransform& rotate(qreal a, qreal x, qreal y);
    SvgTransform& skewX(qreal a);
    SvgTransform& skewY(qreal a);
    QString string() const;
    bool active() const;
protected:
    QStringList transformations;
};


// ============================================================================
// SVG
// ============================================================================

QString xmlElement(const QString& tag, const QString& contents,
                   const QMap<QString, QString> attributes = QMap<QString, QString>());
QString xmlAttributes(const QMap<QString, QString> attributes);
QString svg(const QStringList& elements);
QString svgPath(const QString& contents,
                const QColor& stroke, int stroke_width,
                const QColor& fill,
                const SvgTransform& transform,
                const QString& element_id = "");
QString svgFromPathContents(const QString& path_contents,
                            const QColor& stroke, int stroke_width,
                            const QColor& fill,
                            const SvgTransform& transform,
                            const QString& element_id = "");
QString opacity(const QColor& colour);
int alpha(qreal opacity);


// ============================================================================
// Graphics calculations and painting
// ============================================================================

void alignRect(QRectF& rect, Qt::Alignment alignment);
QRectF centredRect(const QPointF& centre, qreal w, qreal h);

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

SvgWidgetAndProxy makeSvg(
        QGraphicsScene* scene,  // SVG is added to scene
        const QPointF& centre,
        const QString& svg,
        const QColor& pressed_background_colour = QCOLOR_TRANSPARENT,
        const QColor& background_colour = QCOLOR_TRANSPARENT,
        bool transparent_for_mouse = false,
        QWidget* parent = nullptr);

QGraphicsRectItem* makeObscuringRect(
        QGraphicsScene* scene,
        const QRectF& rect,
        qreal opacity = 0.5,  // 0-1
        const QColor& colour_ignoring_opacity = QCOLOR_BLACK);

QGraphicsPixmapItem* makeImage(
        QGraphicsScene* scene,
        const QRectF& rect,
        const QString& filename,
        qreal opacity = 1.0,
        Qt::AspectRatioMode aspect_ratio_mode = Qt::KeepAspectRatio,
        Qt::TransformationMode transformation_mode_1 = Qt::FastTransformation,
        Qt::TransformationMode transformation_mode_2 = Qt::FastTransformation);

}  // namespace graphicsfunc
