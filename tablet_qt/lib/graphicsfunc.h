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
#include <QWidget>  // for QWIDGETSIZE_MAX
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
// Support templates
// ============================================================================

template<typename T>
int sgn(T val)
{
    // Returns -1 if val is negative, 0 if zero, and +1 if positive.
    // http://stackoverflow.com/questions/1903954/is-there-a-standard-sign-function-signum-sgn-in-c-c
    return (T(0) < val) - (val < T(0));
}


template<typename T>
T mod(T x, T y)
{
    // Returns x mod y, coping with negatives.
    // http://stackoverflow.com/questions/11980292/how-to-wrap-around-a-range
    if (y == 0) {
        return 0;  // stupid caller
    }
    return x - y * std::floor(x / y);
}


// ============================================================================
// Support structures
// ============================================================================

struct TextConfig {
    TextConfig(int font_size_px,
               const QColor& colour,
               qreal width = -1,
               Qt::Alignment alignment = Qt::AlignCenter) :
        font_size_px(font_size_px),
        colour(colour),
        width(width),
        alignment(alignment)
    {}
    int font_size_px;
    QColor colour;
    qreal width;
    Qt::Alignment alignment;
};


struct ButtonConfig {
    ButtonConfig(int padding_px,
                 int font_size_px,
                 const QColor& text_colour,
                 Qt::Alignment text_alignment,
                 const QColor& background_colour,
                 const QColor& pressed_background_colour,
                 const QPen& border_pen,
                 int corner_radius_px) :
        padding_px(padding_px),
        font_size_px(font_size_px),
        text_colour(text_colour),
        text_alignment(text_alignment),
        background_colour(background_colour),
        pressed_background_colour(pressed_background_colour),
        border_pen(border_pen),
        corner_radius_px(corner_radius_px)
    {}
    int padding_px;
    int font_size_px;
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

class LineSegment {
    // a(x - xm) + b(y - ym) = c
    // http://stackoverflow.com/questions/385305/efficient-maths-algorithm-to-calculate-intersections
public:
    LineSegment(const QPointF& from, const QPointF& to);
    qreal c(qreal x, qreal y) const;  // 0 if point is on the line; otherwise, sign gives side
    qreal c(const QPointF& pt) const;
    bool isPoint() const;
    bool xRangesOverlap(const LineSegment& other) const;
    bool yRangesOverlap(const LineSegment& other) const;
    bool intersects(const LineSegment& other) const;

protected:
    QPointF from;
    QPointF to;
    qreal x0;  // lower x coordinate
    qreal x1;  // higher x coordinate
    qreal y0;  // lower y coordinate
    qreal y1;  // higher y coordinate

    qreal a;  // y span of line segment
    qreal xm;  // x median of line segment
    qreal b;  // x span of line segment
    qreal ym;  // y median of line segment
};


// ============================================================================
// CSS
// ============================================================================

QString pixelCss(int px);
QString colourCss(const QColor& colour);
QString penStyleCss(const QPen& pen);
QString penCss(const QPen& pen);
QString labelCss(const QColor& colour);

// ============================================================================
// Graphics calculations and painting
// ============================================================================

void alignRect(QRectF& rect, Qt::Alignment alignment);
QRectF textRectF(const QString& text, const QFont& font);

bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1);

extern const qreal DEG_0;
extern const qreal DEG_90;
extern const qreal DEG_270;
extern const qreal DEG_180;
extern const qreal DEG_360;

int sixteenthsOfADegree(qreal degrees);

qreal normalizeHeading(qreal heading_deg);
bool headingNearlyEq(qreal heading_deg, qreal value_deg);
bool headingInRange(qreal first_bound_deg,
                    qreal heading_deg,
                    qreal second_bound_deg,
                    bool inclusive = false);
qreal convertHeadingFromTrueNorth(qreal true_north_heading_deg,
                                  qreal pseudo_north_deg,
                                  bool normalize = true);
qreal convertHeadingToTrueNorth(qreal pseudo_north_heading_deg,
                                qreal pseudo_north_deg,
                                bool normalize = true);

QPointF polarToCartesian(qreal r, qreal theta_degrees,
                         bool y_down_as_per_qt = true);
qreal distanceBetween(const QPointF& from, const QPointF& to);
qreal polarTheta(const QPointF& from, const QPointF& to,
                 bool y_down_as_per_qt = true);
qreal polarTheta(const QPointF& to, bool y_down_as_per_qt = true);
qreal polarThetaToHeading(qreal theta, qreal north_deg = 0.0);
qreal headingToPolarTheta(qreal heading_deg, qreal north_deg = 0.0,
                          bool normalize = true);
qreal headingDegrees(const QPointF& from, const QPointF& to,
                     bool y_down_as_per_qt = true, qreal north_deg = 0.0);
LineSegment lineFormula(const QPointF& from, const QPointF& to);
bool lineCrossesHeadingWithinRadius(const QPointF& from, const QPointF& to,
                                    const QPointF& point, qreal heading_deg,
                                    qreal north_deg = 0.0,
                                    qreal radius = QWIDGETSIZE_MAX,
                                    bool y_down_as_per_qt = true);
bool linePassesBelowPoint(const QPointF& from, const QPointF& to,
                          const QPointF& point, bool y_down_as_per_qt = true);

void drawSector(QPainter& painter,
                const QPointF& tip,
                qreal radius,
                qreal start_angle_deg,  // zero is 3 o'clock
                qreal end_angle_deg,  // zero is 3 o'clock
                bool treat_as_clockwise_angles,
                const QPen& pen,
                const QBrush& brush);

// ============================================================================
// Creating QGraphicsScene objects
// ============================================================================

ButtonAndProxy makeTextButton(
        QGraphicsScene* scene,  // button is added to scene
        const QRectF& rect,
        const ButtonConfig& config,
        const QString& text,
        const QFont& font = QFont(),
        QWidget* parent = nullptr);

LabelAndProxy makeText(
        QGraphicsScene* scene,  // text is added to scene
        const QPointF& point,
        const TextConfig& config,
        const QString& text,
        const QFont& font = QFont(),
        QWidget* parent = nullptr);

AdjustablePieAndProxy makeAdjustablePie(
        QGraphicsScene* scene,  // pie is added to scene
        const QPointF& centre,
        int n_sectors,
        qreal diameter,
        QWidget* parent = nullptr);


}  // namespace graphicsfunc
