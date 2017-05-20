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

// #define DEBUG_CSS
// #define DEBUG_COORDS

#include "graphicsfunc.h"
#include <math.h>  // for std::fmod
#include <QBrush>
#include <QColor>
#include <QDebug>
#include <QGraphicsProxyWidget>
#include <QGraphicsScene>
#include <QGraphicsTextItem>
#include <QLabel>
#include <QMetaMethod>
#include <QPainter>
#include <QPen>
#include <QPushButton>
#include <QRectF>
#include <QtMath>
#include <QVBoxLayout>
#include "widgets/adjustablepie.h"


namespace graphicsfunc
{

// ============================================================================
// LineSegment
// ============================================================================

LineSegment::LineSegment(const QPointF& from, const QPointF& to) :
    from(from),
    to(to)
{
    // http://stackoverflow.com/questions/385305/efficient-maths-algorithm-to-calculate-intersections
    x0 = from.x();
    x1 = to.x();
    y0 = from.y();
    y1 = to.y();

    // Normalize:
    if (x0 > x1) {
        std::swap(x0, x1);
    }
    if (y0 > y1) {
        std::swap(y0, y1);
    }

    xm = (x0 + x1) / 2;
    ym = (y0 + y1) / 2;
    a = y1 - y0;
    b = x0 - x1;
}


qreal LineSegment::c(qreal x, qreal y) const
{
    return a * (x - xm) + b * (y - ym);
}


qreal LineSegment::c(const QPointF& pt) const
{
    return c(pt.x(), pt.y());
}


bool LineSegment::isPoint() const
{
    return x0 == x1 && y0 == y1;
}


bool LineSegment::xRangesOverlap(const LineSegment& other) const
{
    return rangesOverlap(x0, x1, other.x0, other.x1);
}


bool LineSegment::yRangesOverlap(const LineSegment& other) const
{
    return rangesOverlap(y0, y1, other.y0, other.y1);
}


bool LineSegment::intersects(const LineSegment& other) const
{
    if (isPoint() || other.isPoint()) {
        return false;
    }
    // Don't use QRectF::intersects(); that returns false when using a
    // rectangle without width (even if it has height) or vice versa.
    if (!xRangesOverlap(other) || !yRangesOverlap(other)) {
        return false;
    }
    // http://stackoverflow.com/questions/385305/efficient-maths-algorithm-to-calculate-intersections
    // See also: http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
    if (sgn(c(other.from)) == sgn(c(other.to))) {
        // Both other.from and other.to are on the same side of our
        // line, and therefore there can be no intersection.
        return false;
    }
    if (sgn(other.c(from)) == sgn(other.c(to))) {
        // Both from and to are on the same side of the other
        // line, and therefore there can be no intersection.
        return false;
    }
    // There must be an intersection.
    return true;
}


// ============================================================================
// CSS
// ============================================================================

QString pixelCss(int px)
{
    if (px <= 0) {
        return "0";  // no units for 0 in CSS
    }
    return QString("%1px").arg(px);
}


QString colourCss(const QColor& colour)
{
    return QString("rgba(%1,%2,%3,%4)")
            .arg(colour.red())
            .arg(colour.green())
            .arg(colour.blue())
            .arg(colour.alpha());
}


QString penStyleCss(const QPen& pen)
{
    // http://doc.qt.io/qt-4.8/qpen.html#pen-style
    // https://www.w3schools.com/cssref/pr_border-style.asp
    switch (pen.style()) {
    case Qt::NoPen:
        return "none";
    case Qt::SolidLine:
        return "solid";
    case Qt::DashLine:
        return "dashed";
    case Qt::DotLine:
        return "dotted";
    case Qt::DashDotLine:
    case Qt::DashDotDotLine:
    case Qt::CustomDashLine:
    default:
        qWarning() << Q_FUNC_INFO << "Qt pen style not supported in CSS";
        return "dashed";
    }
}


QString penCss(const QPen& pen)
{
    if (pen.width() <= 0 || pen.style() == Qt::NoPen) {
        // http://stackoverflow.com/questions/2922909/should-i-use-border-none-or-border-0
        return "none";
    }
    return QString("%1 %2 %3")
            .arg(pixelCss(pen.width()))
            .arg(penStyleCss(pen))
            .arg(colourCss(pen.color()));
}


QString labelCss(const QColor& colour)
{
    return QString("background-color: rgba(0,0,0,0);"  // transparent
                   "border: 0;"
                   "color: %1;"
                   "margin: 0;"
                   "padding: 0;")
            .arg(colourCss(colour));
}


// ============================================================================
// Graphics calculations and painting
// ============================================================================

void alignRect(QRectF& rect, Qt::Alignment alignment)
{
    // The assumed starting point is that the user wishes to have a rectangle
    // aligned at point (x,y), and that (x,y) is currently the top left point
    // of rect.

    // Horizontal
    qreal dx = 0;
    if (alignment & Qt::AlignLeft ||
            alignment & Qt::AlignJustify ||
            alignment & Qt::AlignAbsolute) {
        dx = 0;
    } else if (alignment & Qt::AlignCenter) {
        dx = -rect.width() / 2;
    } else if (alignment & Qt::AlignRight) {
        dx = -rect.width();
    } else {
        qWarning() << Q_FUNC_INFO << "Unknown horizontal alignment";
    }

    // Vertical
    qreal dy = 0;
    if (alignment & Qt::AlignTop) {
        dy = 0;
    } else if (alignment & Qt::AlignVCenter) {
        dy = -rect.height() / 2;
    } else if (alignment & Qt::AlignBottom ||
               alignment & Qt::AlignBaseline) {
        dy = -rect.height();
    } else {
        qWarning() << Q_FUNC_INFO << "Unknown horizontal alignment";
    }

    rect.translate(dx, dy);
}


QRectF textRectF(const QString& text, const QFont& font)
{
    QFontMetrics fm(font);
    return fm.boundingRect(text);
}


const qreal DEG_0 = 0.0;
const qreal DEG_90 = 90.0;
const qreal DEG_270 = 270.0;
const qreal DEG_180 = 180.0;
const qreal DEG_360 = 360.0;


bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1)
{
    // There are two ranges: (a0, a1) and (b0, b1). Is there overlap?
    if (a0 > a1) {
        std::swap(a0, a1);
    }
    if (b0 > b1) {
        std::swap(b0, b1);
    }
    if (a1 < b0 || b1 < a0) {
        // A is entirely less than B, or B is entirely less than A.
        return false;
    }
    // Otherwise, there's overlap.
    return true;
}


int sixteenthsOfADegree(qreal degrees)
{
    // http://doc.qt.io/qt-5/qpainter.html#drawPie
    return std::round(degrees * 16.0);
}


qreal normalizeHeading(qreal heading_deg)
{
    return mod(heading_deg, DEG_360);
}


bool headingNearlyEq(qreal heading_deg, qreal value_deg)
{
    return qFuzzyIsNull(normalizeHeading(heading_deg - value_deg));
}


bool headingInRange(qreal first_bound_deg,
                    qreal heading_deg,
                    qreal second_bound_deg,
                    bool inclusive)
{
    // The values in degrees are taken as a COMPASS HEADING, i.e. increasing
    // is clockwise. The valid sector is defined CLOCKWISE from the first bound
    // to the second.
    first_bound_deg = normalizeHeading(first_bound_deg);
    heading_deg = normalizeHeading(heading_deg);
    second_bound_deg = normalizeHeading(second_bound_deg);
    // First, we deal with "on the boundary" conditions:
    if (heading_deg == first_bound_deg || heading_deg == second_bound_deg) {
        return inclusive;
    }
    bool range_increases = first_bound_deg < second_bound_deg;
    qreal lower_bound;
    qreal upper_bound;
    if (range_increases) {
        lower_bound = first_bound_deg;
        upper_bound = second_bound_deg;
    } else {
        lower_bound = second_bound_deg;
        upper_bound = first_bound_deg;
    }
    bool within = lower_bound < heading_deg && heading_deg < upper_bound;
    // Second bound is clockwise ("right") from first.
    // If the second bound is numerically greater than the first, then
    // we have a simple range that doesn't cross "North" (0 = 360),
    // and the heading is in range if it's within the two. For example,
    // if the range is (50, 70), then the heading is in range if
    // 50 < x < 70. However, if the range decreases, we're crossing North,
    // e.g. (350, 10); in that case, the heading is in range if and only if
    // it is NOT true that 10 < x < 350.
    return within == range_increases;
}


qreal convertHeadingFromTrueNorth(qreal true_north_heading_deg,
                                  qreal pseudo_north_deg,
                                  bool normalize)
{
    // Example: pseudo_north_deg is 30;
    // then 0 in true North is -30 in pseudo-North.
    qreal h = true_north_heading_deg - pseudo_north_deg;
    return normalize ? normalizeHeading(h) : h;
}


qreal convertHeadingToTrueNorth(qreal pseudo_north_heading_deg,
                                qreal pseudo_north_deg,
                                bool normalize)
{
    // Inverts convertHeadingFromTrueNorth().
    qreal h = pseudo_north_heading_deg + pseudo_north_deg;
    return normalize ? normalizeHeading(h) : h;
}


QPointF polarToCartesian(qreal r, qreal theta_deg, bool y_down_as_per_qt)
{
    // theta == 0 implies along the x axis in a positive direction (right).
    qreal theta_rad = qDegreesToRadians(theta_deg);
    if (y_down_as_per_qt) {
        // Qt uses y-inverted coordinates where positive is (right, down).
        return QPointF(r * qCos(theta_rad), -r * qSin(theta_rad));
    } else {
        return QPointF(r * qCos(theta_rad), r * qSin(theta_rad));
    }
}


qreal distanceBetween(const QPointF& from, const QPointF& to)
{
    qreal dx = to.x() - from.x();
    qreal dy = to.y() - from.y();
    // Pythagoras:
    return qSqrt(qPow(dx, 2) + qPow(dy, 2));
}


qreal polarThetaToHeading(qreal theta_deg, qreal north_deg)
{
    // Polar coordinates have theta 0 == East, and theta positive is
    // anticlockwise. Compass headings have 0 == North, unless adjusted by
    // north_deg (e.g. specifying north_deg = 90 makes the heading 0 when
    // actually East), and positive clockwise.
    // - The first step converts to "clockwise, up is 0":
    qreal true_north_heading = DEG_90 - theta_deg;
    return convertHeadingFromTrueNorth(true_north_heading, north_deg);
}


qreal headingToPolarTheta(qreal heading_deg, qreal north_deg, bool normalize)
{
    // Polar coordinates have theta 0 == East, and theta positive is
    // anticlockwise. Compass headings have 0 == North, unless adjusted by
    // north_deg (e.g. specifying north_deg = 90 makes the heading 0 when
    // actually East), and positive clockwise.
    qreal true_north_heading = convertHeadingToTrueNorth(
                heading_deg, north_deg, normalize);
    qreal theta = DEG_90 - true_north_heading;
    return normalize ? normalizeHeading(theta) : theta;
}


qreal polarTheta(const QPointF& from, const QPointF& to, bool y_down_as_per_qt)
{
    qreal dx = to.x() - from.x();
    qreal dy_up = y_down_as_per_qt ? (from.y() - to.y())  // y positive = down
                                   : (to.y() - from.y());  // y positive = up
    if (dx == 0 && dy_up == 0) {
        // Nonsensical; no movement.
        return 0.0;
    }
    // The arctan function will give us 0 = East, the geometric form.
    return qRadiansToDegrees(qAtan2(dy_up, dx));
}


qreal polarTheta(const QPointF& to, bool y_down_as_per_qt)
{
    return polarTheta(QPointF(0, 0), to, y_down_as_per_qt);
}


qreal headingDegrees(const QPointF& from, const QPointF& to,
                     bool y_down_as_per_qt, qreal north_deg)
{
    // Returns a COMPASS HEADING (0 is North = up).
    return polarThetaToHeading(polarTheta(from, to, y_down_as_per_qt),
                               north_deg);
}


bool lineSegmentsIntersect(const QPointF& first_from, const QPointF& first_to,
                           const QPointF& second_from, const QPointF& second_to)
{
    LineSegment s1(first_from, first_to);
    LineSegment s2(second_from, second_to);
    return s1.intersects(s2);
}


bool lineCrossesHeadingWithinRadius(const QPointF& from, const QPointF& to,
                                    const QPointF& point, qreal heading_deg,
                                    qreal north_deg, qreal radius,
                                    bool y_down_as_per_qt)
{
    // (1) Draw a line from "from" to "to".
    // (2) Draw a line from "point" in direction "heading", where increasing
    //     values of "heading" are clockwise, and a heading of 0 points in
    //     the North direction, where that is defined by north_deg degrees
    //     clockwise of "screen up".
    if (from == to) {
        return false;
    }
    qreal theta = headingToPolarTheta(heading_deg, north_deg);
    QPointF distant_point = point + polarToCartesian(radius, theta,
                                                     y_down_as_per_qt);
    return lineSegmentsIntersect(from, to, point, distant_point);
}


bool linePassesBelowPoint(const QPointF& from, const QPointF& to,
                          const QPointF& point, bool y_down_as_per_qt)
{
    return lineCrossesHeadingWithinRadius(from, to, point, DEG_180, 0,
                                          QWIDGETSIZE_MAX, y_down_as_per_qt);
}


void drawSector(QPainter& painter,
                const QPointF& tip,
                qreal radius,
                qreal start_angle_deg,
                qreal end_angle_deg,
                bool treat_as_clockwise_angles,
                const QPen& pen,
                const QBrush& brush)
{
    painter.setPen(pen);
    painter.setBrush(brush);
    qreal diameter = radius * 2;
    QRectF rect(tip - QPointF(radius, radius), QSizeF(diameter, diameter));
    if (treat_as_clockwise_angles) {
        std::swap(start_angle_deg, end_angle_deg);
    }
    qreal span_angle_deg = end_angle_deg - start_angle_deg;
#ifdef DEBUG_COORDS
    qDebug() << "drawSector:"
             << "tip" << tip
             << "radius" << radius
             << "rect" << rect
             << "start_angle_deg" << start_angle_deg
             << "span_angle_deg" << span_angle_deg;
#endif
    painter.drawPie(rect,
                    sixteenthsOfADegree(start_angle_deg),
                    sixteenthsOfADegree(span_angle_deg));
}


// ============================================================================
// Creating QGraphicsScene objects
// ============================================================================

// ROUNDED BUTTONS
// Method 1:
// http://stackoverflow.com/questions/17295329/qt-add-a-round-rect-to-a-graphics-item-group

// http://falsinsoft.blogspot.co.uk/2015/11/qt-snippet-rounded-corners-qpushbutton.html
/*
QPushButton *pButtonWidget = new QPushButton();
pButtonWidget->setGeometry(QRect(0, 0, 150, 100));
pButtonWidget->setText("Test");
pButtonWidget->setFlat(true);
pButtonWidget->setAttribute(Qt::WA_TranslucentBackground);
pButtonWidget->setStyleSheet(
    "background-color: darkRed;"
    "border: 1px solid black;"
    "border-radius: 15px;"
    "color: lightGray; "
    "font-size: 25px;"
    );
QGraphicsProxyWidget *pButtonProxyWidget = scene()->addWidget(pButtonWidget);
*/

// https://dzone.com/articles/returning-multiple-values-from-functions-in-c


/*
// Doesn't work:
QMetaObject::Connection ButtonAndProxy::connect(const QObject* receiver,
                                                const QMetaMethod& method,
                                                Qt::ConnectionType type)
{
    return QObject::connect(button, &QPushButton::clicked,
                            receiver, method, type);
}
*/


ButtonAndProxy makeTextButton(QGraphicsScene* scene,  // button is added to scene
                              const QRectF& rect,
                              const ButtonConfig& config,
                              const QString& text,
                              const QFont& font,
                              QWidget* parent)
{
    Q_ASSERT(scene);
    // We want a button that can take word-wrapping text, but not with the more
    // sophisticated width-adjusting word wrap used by
    // ClickableLabelWordWrapWide.
    // So we add a QLabel, as per
    // - http://stackoverflow.com/questions/8960233/subclassing-qlabel-to-show-native-mouse-hover-button-indicator/8960548#8960548

    // We can't have a stylesheet with both plain "attribute: value;"
    // and "QPushButton:pressed { attribute: value; }"; we get an error
    // "Could not parse stylesheet of object 0x...".
    // So we probably need a full stylesheet, and note that the text is in
    // a QLabel, not a QPushButton. We could generalize with a QWidget or
    // specify them exactly ("QPushButton, QLabel"). But "QWidget:pressed"
    // doesn't work.
    // Also, blending the QPushButton and the QLabel stuff and installing it
    // on the button screws things up w.r.t. the "pressed" bit.
    // A QLabel can't have the "pressed" attribute, but it screws up the button
    // press.
    // Also, the QLabel also needs to have the "pressed" background.
    // Re padding etc., see https://www.w3schools.com/css/css_boxmodel.asp
    QString button_css = QString(
                "QPushButton {"
                " background-color: %1;"
                " border: %2;"
                " border-radius: %3;"
                " font-size: %4;"
                " margin: 0;"
                " padding: %5; "
                "} "
                "QPushButton:pressed {"
                " background-color: %6;"
                "}")
            .arg(colourCss(config.background_colour),  // 1
                 penCss(config.border_pen),  // 2
                 pixelCss(config.corner_radius_px),  // 3
                 pixelCss(config.font_size_px),  // 4
                 pixelCss(config.padding_px),  // 5
                 colourCss(config.pressed_background_colour));  // 6
    QString label_css = labelCss(config.text_colour);
#ifdef DEBUG_CSS
    qDebug() << "makeGraphicsTextButton: button CSS:" << button_css;
    qDebug() << "makeGraphicsTextButton: label CSS:" << label_css;
#endif

    ButtonAndProxy result;

    result.button = new QPushButton(parent);
    result.button->setFlat(true);
    result.button->setAttribute(Qt::WA_TranslucentBackground);
    result.button->setStyleSheet(button_css);

    QLabel* label = new QLabel(result.button);
    label->setStyleSheet(label_css);
    label->setFont(font);
    label->setText(text);
    label->setWordWrap(true);
    label->setAlignment(config.text_alignment);
    label->setMouseTracking(false);
    label->setTextInteractionFlags(Qt::NoTextInteraction);

    QVBoxLayout* layout = new QVBoxLayout();
    layout->setMargin(0);
    layout->addWidget(label);

    result.button->setLayout(layout);

    result.proxy = scene->addWidget(result.button);
    result.proxy->setGeometry(rect);

    return result;
}


LabelAndProxy makeText(QGraphicsScene* scene,  // text is added to scene
                       const QPointF& pos,
                       const TextConfig& config,
                       const QString& text,
                       const QFont& font,
                       QWidget* parent)
{
    Q_ASSERT(scene);
    // QGraphicsTextItem does not support alignment.
    // http://stackoverflow.com/questions/29483125/does-qgraphicstextitem-support-vertical-center-alignment
    QString css = labelCss(config.colour);
#ifdef DEBUG_CSS
    qDebug() << "makeText: CSS:" << css;
#endif

    LabelAndProxy result;
    result.label = new QLabel(text, parent);
    result.label->setStyleSheet(css);
    result.label->setFont(font);
    result.label->setOpenExternalLinks(false);
    result.label->setTextInteractionFlags(Qt::NoTextInteraction);
    result.label->setAlignment(config.alignment);  // alignment WITHIN label

    QRectF rect(pos, QSizeF());
    if (config.width == -1) {
        result.label->setWordWrap(false);
        rect.setSize(result.label->size());
    } else {
        // word wrap
        result.label->setWordWrap(true);
        rect.setSize(QSizeF(config.width,
                            result.label->heightForWidth(config.width)));
    }

    // Now fix alignment of WHOLE object
    alignRect(rect, config.alignment);

    result.proxy = scene->addWidget(result.label);
    result.proxy->setGeometry(rect);

    return result;
}


AdjustablePieAndProxy makeAdjustablePie(QGraphicsScene* scene,
                                        const QPointF& centre,
                                        int n_sectors,
                                        qreal diameter,
                                        QWidget* parent)
{
    qreal radius = diameter / 2.0;
    QPointF top_left(centre - QPointF(radius, radius));
    AdjustablePieAndProxy result;
    result.pie = new AdjustablePie(n_sectors, parent);
    result.pie->setOverallRadius(radius);
    QRectF rect(top_left, QSizeF(diameter, diameter));
    result.proxy = scene->addWidget(result.pie);
    result.proxy->setGeometry(rect);
    return result;
}


}  // namespace graphicsfunc
