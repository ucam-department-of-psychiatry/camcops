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
#include <QVBoxLayout>
#include "lib/geometry.h"
#include "widgets/adjustablepie.h"
using geometry::clockwiseToAnticlockwise;
using geometry::sixteenthsOfADegree;


namespace graphicsfunc
{

// ============================================================================
// LineSegment
// ============================================================================


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


QString ptCss(qreal pt)
{
    if (pt <= 0) {
        return "0";  // no units for 0 in CSS
    }
    return QString("%1pt").arg(pt);
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
    } else if (alignment & Qt::AlignHCenter) {
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


void drawSector(QPainter& painter,
                const QPointF& tip,
                qreal radius,
                qreal start_angle_deg,
                qreal end_angle_deg,
                bool move_clockwise_from_start_to_end,
                const QPen& pen,
                const QBrush& brush)
{
#ifdef DEBUG_COORDS
    qDebug() << "drawSector:"
             << "tip" << tip
             << "radius" << radius
             << "start_angle_deg (polar)" << start_angle_deg
             << "end_angle_deg (polar)" << end_angle_deg
             << "move_clockwise_from_start_to_end" << move_clockwise_from_start_to_end;
#endif
    painter.setPen(pen);
    painter.setBrush(brush);
    qreal diameter = radius * 2;
    QRectF rect(tip - QPointF(radius, radius), QSizeF(diameter, diameter));
    if (!move_clockwise_from_start_to_end) {
        std::swap(start_angle_deg, end_angle_deg);
    }
    start_angle_deg = clockwiseToAnticlockwise(start_angle_deg);
    end_angle_deg = clockwiseToAnticlockwise(end_angle_deg);
    qreal span_angle_deg = end_angle_deg - start_angle_deg;
#ifdef DEBUG_COORDS
    qDebug() << "... "
             << "tip" << tip
             << "rect" << rect
             << "start_angle_deg (for QPainter::drawPie)" << start_angle_deg
             << "span_angle_deg (for QPainter::drawPie)" << span_angle_deg;
#endif
    painter.drawPie(rect,
                    sixteenthsOfADegree(start_angle_deg),
                    sixteenthsOfADegree(span_angle_deg));
}


QRectF textRectF(const QString& text, const QFont& font)
{
    QFontMetrics fm(font);
    return fm.boundingRect(text);
}


void drawText(QPainter& painter, const QPointF& point, const QString& text,
              const QFont& font, Qt::Alignment align)
{
    QRectF textrect = textRectF(text, font);

    qreal x = point.x();
    if (align & Qt::AlignRight) {
        x -= textrect.width();
    } else if (align & Qt::AlignHCenter) {
        x -= textrect.width() / 2.0;
    }

    qreal y = point.y();
    if (align & Qt::AlignTop) {
        y += textrect.height();
    } else if (align & Qt::AlignVCenter) {
        y += textrect.height() / 2.0;
    }

    painter.setFont(font);
    painter.drawText(x, y, text);
}


void drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect)
{
    // http://stackoverflow.com/questions/24831484
   const qreal size = 32767.0;
   QPointF corner(x, y - size);
   if (flags & Qt::AlignHCenter) {
       corner.rx() -= size / 2.0;
   }
   else if (flags & Qt::AlignRight) {
       corner.rx() -= size;
   }
   if (flags & Qt::AlignVCenter) {
       corner.ry() += size / 2.0;
   }
   else if (flags & Qt::AlignTop) {
       corner.ry() += size;
   }
   else {
       flags |= Qt::AlignBottom;
   }
   QRectF rect(corner, QSizeF(size, size));
   painter.drawText(rect, flags, text, boundingRect);
}


void drawText(QPainter& painter, const QPointF& point, Qt::Alignment flags,
              const QString& text, QRectF* boundingRect)
{
    // http://stackoverflow.com/questions/24831484
   drawText(painter, point.x(), point.y(), flags, text, boundingRect);
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
                              QFont font,
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
                 ptCss(config.font_size_pt),  // 4
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
    font.setPointSizeF(config.font_size_pt);
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
                       QFont font,
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
    font.setPointSizeF(config.font_size_pt);
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
