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

#define DEBUG_CSS

#include "graphicsfunc.h"
#include <QBrush>
#include <QColor>
#include <QDebug>
#include <QGraphicsProxyWidget>
#include <QGraphicsScene>
#include <QLabel>
#include <QMetaMethod>
#include <QPen>
#include <QPushButton>
#include <QRectF>
#include <QVBoxLayout>


namespace graphicsfunc
{

// ============================================================================
// CSS from Qt brush/pen objects
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


// ============================================================================
// ROUNDED BUTTONS
// ============================================================================

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
        QWidget* parent)
{
    // We want a button that can take word-wrapping text, but not with the more
    // sophisticated width-adjusting word wrap used by
    // ClickableLabelWordWrapWide.
    // So we add a QLabel, as per
    // - http://stackoverflow.com/questions/8960233/subclassing-qlabel-to-show-native-mouse-hover-button-indicator/8960548#8960548

    ButtonAndProxy result;

    result.button = new QPushButton(parent);
    result.button->setFlat(true);
    result.button->setAttribute(Qt::WA_TranslucentBackground);
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
    QString button_css = QString(
                "QPushButton {"
                " background-color: %1;"
                " border: %2;"
                " border-radius: %3;"
                " font-size: %4;"
                " padding: %5; "
                "} "
                "QPushButton:pressed {"
                " background-color: %5;"
                "}")
            .arg(colourCss(background_colour),  // 1
                 penCss(border_pen),  // 2
                 pixelCss(corner_radius_px),  // 3
                 pixelCss(font_size_px),  // 4
                 colourCss(pressed_background_colour));  // 5
    QString label_css = QString(
                "color: %1; "
                "padding: %2;")
            .arg(colourCss(text_colour),
                 pixelCss(padding_px));
#ifdef DEBUG_CSS
    qDebug() << "makeGraphicsTextButton: button CSS:" << button_css;
    qDebug() << "makeGraphicsTextButton: button CSS:" << label_css;
#endif
    result.button->setStyleSheet(button_css);

    QLabel* label = new QLabel(result.button);
    label->setStyleSheet(label_css);
    label->setText(text);
    label->setWordWrap(true);
    label->setAlignment(Qt::AlignCenter);
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


}  // namespace graphicsfunc
