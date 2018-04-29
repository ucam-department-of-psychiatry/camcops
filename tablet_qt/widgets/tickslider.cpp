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

#include "tickslider.h"
#include <QDebug>
#include <QKeyEvent>
#include <QMouseEvent>
#include <QStyleOptionSlider>
#include <QStylePainter>
#include "graphics/graphicsfunc.h"


const QColor DEFAULT_TICK_COLOR(0, 0, 0, 255);  // black, opaque
const int DEFAULT_TICK_WIDTH = 0;
const int DEFAULT_TICK_LENGTH = 4;
const int DEFAULT_TICK_LABEL_GAP = 4;
const int DEFAULT_INTERLABEL_GAP = 4;
const int DEFAULT_GAP_TO_SLIDER = 6;


TickSlider::TickSlider(QWidget* parent) :
    QSlider(parent)
{
    commonConstructor();
}


TickSlider::TickSlider(Qt::Orientation orientation,
                       QWidget* parent) :
    QSlider(orientation, parent)
{
    commonConstructor();
}


void TickSlider::commonConstructor()
{
    m_tick_colour = DEFAULT_TICK_COLOR;
    m_tick_thickness = DEFAULT_TICK_WIDTH;
    m_tick_length = DEFAULT_TICK_LENGTH;
    m_tick_label_gap = DEFAULT_TICK_LABEL_GAP;
    m_min_interlabel_gap = DEFAULT_INTERLABEL_GAP;
    m_gap_to_slider = DEFAULT_GAP_TO_SLIDER;
    m_reverse_horizontal_labels = false;
    m_reverse_vertical_labels = false;
    m_edge_in_extreme_labels = false;
}


void TickSlider::setTickColor(const QColor& colour)
{
    m_tick_colour = colour;
}


void TickSlider::setTickThickness(const int thickness)
{
    m_tick_thickness = thickness;
}


void TickSlider::setTickLength(const int length)
{
    m_tick_length = length;
}


void TickSlider::setTickLabelGap(const int gap)
{
    m_tick_label_gap = gap;
}


void TickSlider::setInterlabelGap(const int gap)
{
    m_min_interlabel_gap = gap;
}


void TickSlider::setGapToSlider(const int gap)
{
    m_gap_to_slider = gap;
}


void TickSlider::setTickLabelPosition(const QSlider::TickPosition position)
{
    m_label_position = position;
}


QSlider::TickPosition TickSlider::tickLabelPosition() const
{
    return m_label_position;
}


void TickSlider::addTickLabel(const int position, const QString& text)
{
    m_tick_labels[position] = text;
}


void TickSlider::setTickLabels(const QMap<int, QString>& labels)
{
    m_tick_labels = labels;
}


void TickSlider::addDefaultTickLabels()
{
    int interval = tickInterval();
    if (interval == 0) {
        interval = pageStep();
    }
    for (int i = minimum(); i <= maximum(); i += interval) {
        m_tick_labels[i] = QString::number(i);
    }
}


void TickSlider::setReverseHorizontalLabels(const bool reverse)
{
    m_reverse_horizontal_labels = reverse;
}


void TickSlider::setReverseVerticalLabels(const bool reverse)
{
    m_reverse_vertical_labels = reverse;
}


void TickSlider::setEdgeInExtremeLabels(const bool edge_in_extreme_labels)
{
    m_edge_in_extreme_labels = edge_in_extreme_labels;
}


QSize TickSlider::biggestLabel() const
{
    QSize maxsize;
    const QFontMetrics fm = fontMetrics();
    for (const QString& label : m_tick_labels) {
        QSize labelsize = fm.size(Qt::TextSingleLine, label);
        maxsize = maxsize.expandedTo(labelsize);
    }
    return maxsize;
}



/*

Horizontal:

        |   |   |   |   |   |
    ----------------XX------------
        |   |   |   |   |   |
        1  two  3   4       6

Vertical:

     |
    -|- 6
     |
    -|- 5
     |
    -X- 4
     |
    -|- 4
     |
    -|- 3
     |
    -|- two
     |
    -|- 1
     |

I don't know how to make Qt do anything except draw its slider centrally,
so we have to expand the whole widget to allow for labels either side,
and similarly we have to right-justify the leftmost label and left-justify
the rightmost label (when in horizontal mode) or they dangle off the end;
neither is perfect.

*/

void TickSlider::paintEvent(QPaintEvent* ev)
{
    Q_UNUSED(ev);
    QStylePainter p(this);
    QStyleOptionSlider opt;
    initStyleOption(&opt);

    const QRect handle = style()->subControlRect(QStyle::CC_Slider, &opt,
                                                 QStyle::SC_SliderHandle, this);

    // Draw the slider first
    opt.subControls = QStyle::SC_SliderGroove | QStyle::SC_SliderHandle;
    opt.activeSubControls = getHoverControl();  // addition here
    p.drawComplexControl(QStyle::CC_Slider, opt);

    // draw tick marks
    // do this manually because they are very badly behaved with style sheets
    int interval = tickInterval();
    if (interval == 0) {
        interval = pageStep();
    }

    // see http://doc.qt.io/qt-5.7/coordsys.html
    // ... positive is right and down

    const bool using_ticks = tickPosition() != NoTicks;
    const bool using_labels = tickLabelPosition() != NoTicks;
    if (!using_ticks && !using_labels) {
        return;
    }
    QPen pen;
    pen.setColor(m_tick_colour);
    pen.setWidth(m_tick_thickness);
    p.setPen(pen);
    const bool horizontal = orientation() == Qt::Horizontal;
    const QSize biggest_label = biggestLabel();
    const int max_label_height = using_labels ? biggest_label.height() : 0;
    const int max_label_width = using_labels ? biggest_label.width() : 0;
    if (horizontal) {
        // --------------------------------------------------------------------
        // HORIZONTAL
        // --------------------------------------------------------------------
        const int move_tick_vertically_by = (max_label_height > 0)
                ? (max_label_height + m_tick_label_gap)
                : 0;
        // Top
        const int bounding_box_top = this->rect().top();
        const int top_label_top = bounding_box_top;
        const int top_tick_top = bounding_box_top + move_tick_vertically_by;
        const int top_tick_bottom = top_tick_top + m_tick_length;
        // Bottom, working up
        const int bounding_box_bottom = this->rect().bottom();
        const int bottom_label_bottom = bounding_box_bottom;
        const int bottom_tick_bottom = bounding_box_bottom - move_tick_vertically_by;
        const int bottom_tick_top = bottom_tick_bottom - m_tick_length;
        // OK:
        for (int i = minimum(); i <= maximum(); i += interval) {
            Qt::Alignment halign = Qt::AlignHCenter;
            if (m_edge_in_extreme_labels) {
                const bool leftmost = i == minimum();
                const bool rightmost = i == maximum();
                if (leftmost) {
                    halign = Qt::AlignLeft;
                } else if (rightmost) {
                    halign = Qt::AlignRight;
                }
            }
            const int q = m_reverse_horizontal_labels ? (maximum() - i) : i;
            const int x = round(
                (double)(
                    (double)(
                        (double)(q - this->minimum()) /
                        (double)(this->maximum() - this->minimum())
                    ) * (double)(this->width() - handle.width()) +
                    (double)(handle.width() / 2.0)
                )
            ) - 1;
            const bool has_label = m_tick_labels.contains(i);
            QString label_text;
            if (has_label) {
                label_text = m_tick_labels[i];
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksAbove) {
                p.drawLine(x, top_tick_top, x, top_tick_bottom);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksAbove)) {
                graphicsfunc::drawText(p, x, top_label_top,
                                       halign | Qt::AlignTop, label_text);
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksBelow) {
                p.drawLine(x, bottom_tick_top, x, bottom_tick_bottom);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksBelow)) {
                graphicsfunc::drawText(p, x, bottom_label_bottom,
                                       halign | Qt::AlignBottom, label_text);
            }
        }
    } else {
        // --------------------------------------------------------------------
        // VERTICAL
        // --------------------------------------------------------------------
        const int move_tick_horizontally_by = (max_label_width > 0)
                ? (max_label_width + m_tick_label_gap)
                : 0;
        // Left
        const int bounding_box_left = this->rect().left();
        const int left_label_right = bounding_box_left + max_label_width;
        const int left_tick_left = bounding_box_left + move_tick_horizontally_by;
        const int left_tick_right = left_tick_left + m_tick_length;
        // Right, working leftwards
        const int bounding_box_right = this->rect().right();
        const int right_label_left = bounding_box_right - max_label_width;
        const int right_tick_right = bounding_box_right - move_tick_horizontally_by;
        const int right_tick_left = right_tick_right - m_tick_length;
        // OK:
        for (int i = minimum(); i <= maximum(); i += interval) {
            Qt::Alignment valign = Qt::AlignVCenter;
            const int q = m_reverse_vertical_labels ? (maximum() - i) : i;
            const int y = round(
                (double)(
                    (double)(
                        (double)(q - this->minimum()) /
                        (double)(this->maximum() - this->minimum())
                    ) * (double)(this->height() - handle.height()) +
                    (double)(handle.height() / 2.0)
                )
            ) - 1;
            const bool has_label = m_tick_labels.contains(i);
            QString label_text;
            if (has_label) {
                label_text = m_tick_labels[i];
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksLeft) {
                p.drawLine(left_tick_left, y, left_tick_right, y);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksLeft)) {
                graphicsfunc::drawText(p, left_label_right, y,
                                       Qt::AlignRight | valign, label_text);
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksRight) {
                p.drawLine(right_tick_left, y, right_tick_right, y);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksRight)) {
                graphicsfunc::drawText(p, right_label_left, y,
                                       Qt::AlignLeft | valign, label_text);
            }
        }
    }
}


QSize TickSlider::sizeHint() const
{
    QSize size = QSlider::sizeHint();
    const bool using_labels = tickLabelPosition() != NoTicks;
    const QSize label = using_labels ? biggestLabel() : QSize();
    const bool using_ticks = tickPosition() != NoTicks;
    const int n_potential_labels = (maximum() - minimum()) / tickInterval();
    if (orientation() == Qt::Horizontal) {
        // Horizontal
        if (using_labels) {
            size.rheight() += 2 * label.height();
            size = size.expandedTo(QSize(
                n_potential_labels * label.width() +
                (n_potential_labels - 1) * m_min_interlabel_gap,
                0));
        }
        if (using_ticks) {
            size.rheight() += 2 * m_tick_length;
        }
        if (using_labels && using_ticks) {
            size.rheight() += 2 * m_tick_label_gap;
        }
        if (using_labels || using_ticks) {
            size.rheight() += 2 * m_gap_to_slider;
        }
    } else {
        // Vertical
        if (using_labels) {
            size.rwidth() += 2 * label.width();
            size = size.expandedTo(QSize(
                0,
                n_potential_labels * label.height() +
                (n_potential_labels - 1) * m_min_interlabel_gap));
        }
        if (using_ticks) {
            size.rwidth() += 2 * m_tick_length;
        }
        if (using_labels && using_ticks) {
            size.rwidth() += 2 * m_tick_label_gap;
        }
        if (using_labels || using_ticks) {
            size.rwidth() += 2 * m_gap_to_slider;
        }
    }
    return size;
}


QStyle::SubControls TickSlider::getHoverControl() const
{
    // This replaces the functionality of QSlider::paintEvent has, but without
    // access to the QSliderPrivate class. But see
    // http://cep.xray.aps.anl.gov/software/qt4-x11-4.8.6-browser/de/dbb/class_q_slider_private.html
    // And see QSliderPrivate::newHoverControl (in qslider.cpp)

    const QPoint pos = mapFromGlobal(QCursor::pos());
    QStyle::SubControls hoverControl;

    // Then the rest of this is lightly modified from QSliderPrivate::newHoverControl

    QStyleOptionSlider opt;
    initStyleOption(&opt);
    opt.subControls = QStyle::SC_All;
    const QRect handleRect = style()->subControlRect(
                QStyle::CC_Slider, &opt, QStyle::SC_SliderHandle, this);
    const QRect grooveRect = style()->subControlRect(
                QStyle::CC_Slider, &opt, QStyle::SC_SliderGroove, this);
    const QRect tickmarksRect = style()->subControlRect(
                QStyle::CC_Slider, &opt, QStyle::SC_SliderTickmarks, this);
    // These rectangles are in widget-relative space.

    if (handleRect.contains(pos)) {
        hoverControl = QStyle::SC_SliderHandle;
    } else if (grooveRect.contains(pos)) {
        hoverControl = QStyle::SC_SliderGroove;
    } else if (tickmarksRect.contains(pos)) {
        hoverControl = QStyle::SC_SliderTickmarks;
    } else {
        hoverControl = QStyle::SC_None;
    }

    return hoverControl;
}
