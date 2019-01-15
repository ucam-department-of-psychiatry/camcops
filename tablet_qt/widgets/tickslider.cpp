/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
#include <cmath>  // for round()
#include <QApplication>
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

const int FM_TEXTFLAGS = 0;  // http://doc.qt.io/qt-5/qfontmetrics.html#size


// ============================================================================
// TickSlider main
// ============================================================================

TickSlider::TickSlider(QWidget* parent) :
    TickSlider(Qt::Vertical, parent)
{
}


TickSlider::TickSlider(Qt::Orientation orientation,
                       QWidget* parent) :
    QWidget(parent),
    m_slider(orientation, this)
{
    connect(&m_slider, &QSlider::valueChanged,
            this, &TickSlider::valueChanged);

    connect(&m_slider, &QSlider::sliderPressed,
            this, &TickSlider::sliderPressed);
    connect(&m_slider, &QSlider::sliderMoved,
            this, &TickSlider::sliderMoved);
    connect(&m_slider, &QSlider::sliderReleased,
            this, &TickSlider::sliderReleased);

    connect(&m_slider, &QSlider::rangeChanged,
            this, &TickSlider::rangeChanged);

    connect(&m_slider, &QSlider::actionTriggered,
            this, &TickSlider::actionTriggered);

    m_tick_colour = DEFAULT_TICK_COLOR;
    m_tick_thickness = DEFAULT_TICK_WIDTH;
    m_tick_length = DEFAULT_TICK_LENGTH;
    m_tick_label_gap = DEFAULT_TICK_LABEL_GAP;
    m_min_interlabel_gap = DEFAULT_INTERLABEL_GAP;
    m_gap_to_slider = DEFAULT_GAP_TO_SLIDER;
    m_reverse_horizontal_labels = false;
    m_reverse_vertical_labels = false;
    m_edge_in_extreme_labels = false;

    m_is_overspill_cached = false;
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


bool TickSlider::usingTicks() const
{
    return tickPosition() != QSlider::NoTicks;
}


bool TickSlider::usingLabels() const
{
    return tickLabelPosition() != QSlider::NoTicks;
}


QSize TickSlider::maxLabelSize() const
{
    if (!usingLabels()) {
        return QSize(0, 0);
    }
    QSize maxsize;
    const QFontMetrics fm = fontMetrics();
    for (const QString& label : m_tick_labels) {
        QSize labelsize = fm.size(FM_TEXTFLAGS, label);
        maxsize = maxsize.expandedTo(labelsize);
    }
    return maxsize;
}



/*

Horizontal:

        |   |   |   |   |   |           ticks
    ----------------XX------------      the slider
        |   |   |   |   |   |           ticks
        1  two  3   4       6           tick labels

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

Aha! 2019-01-14. We modify opt.rect as below.

*/


void TickSlider::paintEvent(QPaintEvent* ev)
{
    // Coordinate systems: see http://doc.qt.io/qt-5.7/coordsys.html
    // ... positive is right and DOWN.

    Q_UNUSED(ev);

    // Draw the slider first...
    // ... will happen spontaneously.

    // Do we need to do more?
    if (!usingTicks() && !usingLabels()) {
        return;
    }

    QStylePainter p(this);
    const LabelOverspill overspill = getLabelOverspill();

    QStyleOptionSlider opt;
    initStyleOption(&opt);
    const QRect& slider_rect = opt.rect;

    // Find the handle extent (we need to know this because the end ticks
    // are half a handle width in from the edge of the slider)
    m_slider.ensurePolished();
    const QRect handle = m_slider.style()->subControlRect(
                QStyle::CC_Slider, &opt, QStyle::SC_SliderHandle, &m_slider);
    // qDebug() << "Slider handle:" << handle;

    // Draw tick marks (and labels).
    // Do this manually because they are very badly behaved with style sheets.
    int interval = tickInterval();
    if (interval == 0) {
        interval = pageStep();
    }
    QPen pen;
    pen.setColor(m_tick_colour);
    pen.setWidth(m_tick_thickness);
    p.setPen(pen);
    const bool horizontal = orientation() == Qt::Horizontal;
    const QSize max_label_size = maxLabelSize();
    const QSlider::TickPosition tickpos = tickPosition();
    const QSlider::TickPosition ticklabelpos = tickLabelPosition();
    if (horizontal) {
        // --------------------------------------------------------------------
        // HORIZONTAL
        // --------------------------------------------------------------------
        const int move_tick_vertically_by = (max_label_size.height() > 0)
                ? (max_label_size.height() + m_tick_label_gap)
                : 0;
        // Top
        const int bounding_box_top = slider_rect.top();
        const int top_label_top = bounding_box_top;
        const int top_tick_top = bounding_box_top + move_tick_vertically_by;
        const int top_tick_bottom = top_tick_top + m_tick_length;
        // Bottom, working up
        const int bounding_box_bottom = slider_rect.bottom();
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
            // x position (tick position and horizontal alignment point of text)
            const int x = getTickPos(q, handle.width(),
                                     slider_rect.width(), overspill.left);
            const bool has_label = m_tick_labels.contains(i);
            QString label_text;
            if (has_label) {
                label_text = m_tick_labels[i];
            }
            // Top tick
            if (tickpos == QSlider::TicksBothSides ||
                    tickpos == QSlider::TicksAbove) {
                p.drawLine(x, top_tick_top, x, top_tick_bottom);
            }
            // Top label
            if (has_label && (ticklabelpos == QSlider::TicksBothSides ||
                              ticklabelpos == QSlider::TicksAbove)) {
                graphicsfunc::drawText(p, x, top_label_top,
                                       halign | Qt::AlignTop, label_text);
            }
            // Bottom tick
            if (tickpos == QSlider::TicksBothSides ||
                    tickpos == QSlider::TicksBelow) {
                p.drawLine(x, bottom_tick_top, x, bottom_tick_bottom);
            }
            // Bottom label
            if (has_label && (ticklabelpos == QSlider::TicksBothSides ||
                              ticklabelpos == QSlider::TicksBelow)) {
                graphicsfunc::drawText(p, x, bottom_label_bottom,
                                       halign | Qt::AlignBottom, label_text);
            }
        }
    } else {
        // --------------------------------------------------------------------
        // VERTICAL
        // --------------------------------------------------------------------
        const int move_tick_horizontally_by = (max_label_size.width() > 0)
                ? (max_label_size.width() + m_tick_label_gap)
                : 0;
        // Left
        const int bounding_box_left = slider_rect.left();
        const int left_label_right = bounding_box_left + max_label_size.width();
        const int left_tick_left = bounding_box_left + move_tick_horizontally_by;
        const int left_tick_right = left_tick_left + m_tick_length;
        // Right, working leftwards
        const int bounding_box_right = slider_rect.right();
        const int right_label_left = bounding_box_right - max_label_size.width();
        const int right_tick_right = bounding_box_right - move_tick_horizontally_by;
        const int right_tick_left = right_tick_right - m_tick_length;
        // OK:
        for (int i = minimum(); i <= maximum(); i += interval) {
            Qt::Alignment valign = Qt::AlignVCenter;
            const int q = m_reverse_vertical_labels ? (maximum() - i) : i;
            // y position (tick position and vertical alignment point of text)
            const int y = getTickPos(q, handle.height(),
                                     slider_rect.height(), overspill.bottom);
            const bool has_label = m_tick_labels.contains(i);
            QString label_text;
            if (has_label) {
                label_text = m_tick_labels[i];
            }
            // Left tick
            if (tickpos == QSlider::TicksBothSides ||
                    tickpos == QSlider::TicksLeft) {
                p.drawLine(left_tick_left, y, left_tick_right, y);
            }
            // Left label
            if (has_label && (ticklabelpos == QSlider::TicksBothSides ||
                              ticklabelpos == QSlider::TicksLeft)) {
                graphicsfunc::drawText(p, left_label_right, y,
                                       Qt::AlignRight | valign, label_text);
            }
            // Right tick
            if (tickpos == QSlider::TicksBothSides ||
                    tickpos == QSlider::TicksRight) {
                p.drawLine(right_tick_left, y, right_tick_right, y);
            }
            // Right label
            if (has_label && (ticklabelpos == QSlider::TicksBothSides ||
                              ticklabelpos == QSlider::TicksRight)) {
                graphicsfunc::drawText(p, right_label_left, y,
                                       Qt::AlignLeft | valign, label_text);
            }
        }
    }
}


int TickSlider::getTickPos(const int pos,
                           const int handle_extent,
                           const int slider_extent,
                           const int initial_label_overspill) const
{
    // Our slider represents a scale from minimum() to maximum(), and
    // we are considering position "pos".
    const double drelpos = static_cast<double>(pos - minimum());
    const double dmin = static_cast<double>(minimum());
    const double dmax = static_cast<double>(maximum());
    const double proportion = drelpos / (dmax - dmin);
    // ... so this is the proportion along the slider.

    // - We have a slider that is drawn as slider_extent pixels long.
    // - That value includes overhang for the handle: half the handle can
    //   overhang at each end.
    const double dhandle_extent = static_cast<double>(handle_extent);
    const double dslider_extent = static_cast<double>(slider_extent);
    const double slider_main_part = dslider_extent - dhandle_extent;
    const double half_handle = dhandle_extent / 2.0;

    // - We also allocate some extra space for label overspill
    const double dlabel_overspill = static_cast<double>(initial_label_overspill);

    const double tickpos = dlabel_overspill + half_handle +
                           (proportion * slider_main_part);

    return static_cast<int>(round(tickpos)) - 1;
}


QSize TickSlider::sizeHint() const
{
    // 1. Replicate QSlider::sizeHint()
    QSize size = m_slider.sizeHint();

    // 2. Modify the size for labels etc.
    const bool using_labels = usingLabels();
    const QSize label = maxLabelSize();
    const bool using_ticks = usingTicks();
    const int n_potential_labels = (maximum() - minimum()) / tickInterval();
    if (orientation() == Qt::Horizontal) {
        // Horizontal
        if (using_labels) {
            // Expand height to accommodate the labels
            size.rheight() += 2 * label.height();
            // Expand width to accommodate the labels
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
            // Expand width to accommodate the labels
            size.rwidth() += 2 * label.width();
            // Expand height to accommodate the labels
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


TickSlider::LabelOverspill TickSlider::getLabelOverspill()
{
    if (m_is_overspill_cached) {
        return m_cached_overspill;
    }
    m_cached_overspill = LabelOverspill();
    if (m_edge_in_extreme_labels) {
        return m_cached_overspill;
    }
    const bool horizontal = orientation() == Qt::Horizontal;
    const int min_value = minimum();
    const int max_value = maximum();
    const QFontMetrics fm = fontMetrics();
    if (horizontal) {
        if (m_tick_labels.contains(min_value)) {
            const QString label_text = m_tick_labels[min_value];
            const QSize label_size = fm.size(FM_TEXTFLAGS, label_text);
            m_cached_overspill.left = label_size.width() / 2;
        }
        if (m_tick_labels.contains(max_value)) {
            const QString label_text = m_tick_labels[max_value];
            const QSize label_size = fm.size(FM_TEXTFLAGS, label_text);
            m_cached_overspill.right = label_size.width() / 2;
        }
    } else {
        // Vertical
        if (m_tick_labels.contains(min_value)) {
            const QString label_text = m_tick_labels[min_value];
            const QSize label_size = fm.size(FM_TEXTFLAGS, label_text);
            m_cached_overspill.bottom = label_size.width() / 2;
        }
        if (m_tick_labels.contains(max_value)) {
            const QString label_text = m_tick_labels[max_value];
            const QSize label_size = fm.size(FM_TEXTFLAGS, label_text);
            m_cached_overspill.top = label_size.width() / 2;
        }
    }
    return m_cached_overspill;
}


void TickSlider::clearCache()
{
    m_is_overspill_cached = false;
}


QRect TickSlider::getSliderRect()
{
    LabelOverspill overspill = getLabelOverspill();
    const QRect entire_rect = rect();
    QRect slider_rect(entire_rect);
    // Remember: coordinate system has positive y = down
    slider_rect.adjust(
        overspill.left,  // dx1; left; move it right
        overspill.top,  // dy1; top; move it down
        -overspill.right,  // dx2; right; move it left
        -overspill.bottom  // dy2; bottom; move it up
    );
    return slider_rect;
}


void TickSlider::repositionSlider()
{
    m_slider.setGeometry(getSliderRect());
}


void TickSlider::moveEvent(QMoveEvent* event)
{
    Q_UNUSED(event);
    repositionSlider();
}


void TickSlider::resizeEvent(QResizeEvent* event)
{
    Q_UNUSED(event);
    repositionSlider();
}


bool TickSlider::event(QEvent* event)
{
    switch (event->type()) {

    // Need cache clearing:
    case QEvent::Type::ContentsRectChange:
    case QEvent::Type::DynamicPropertyChange:
    case QEvent::Type::FontChange:
    case QEvent::Type::Polish:
    case QEvent::Type::PolishRequest:
    case QEvent::Type::Resize:
    case QEvent::Type::StyleChange:
    case QEvent::Type::ScreenChangeInternal:  // undocumented? But see https://git.merproject.org/mer-core/qtbase/commit/49194275e02a9d6373767d6485bd8ebeeb0abba5
        clearCache();
        break;

    default:
        break;
    }
    return QWidget::event(event);
}


void TickSlider::initStyleOption(QStyleOptionSlider* option) const
{
    // http://doc.qt.io/qt-5/qstyleoptionslider.html

    // Fetch options; http://doc.qt.io/qt-5/qslider.html#initStyleOption.

    if (!option) {
        return;
    }

    // This populates opt.rect with our bounding box, m_slider.rect().
    option->initFrom(&m_slider);

    option->subControls = QStyle::SC_None;
    option->activeSubControls = QStyle::SC_None;
    option->orientation = m_slider.orientation();
    option->maximum = m_slider.maximum();
    option->minimum = m_slider.minimum();
    option->tickPosition = m_slider.tickPosition();
    option->tickInterval = m_slider.tickInterval();
    option->upsideDown = (m_slider.orientation() == Qt::Horizontal)
            ? (m_slider.invertedAppearance() != (option->direction == Qt::RightToLeft))
            : (!m_slider.invertedAppearance());
    option->direction = Qt::LeftToRight; // we use the upsideDown option instead

    // d->position is QAbstractSliderPrivate::position, which is an int
    // ... is it a zero-based int? Let's try this:
    option->sliderPosition = (m_slider.value() - m_slider.minimum()) / m_slider.singleStep();

    option->sliderValue = m_slider.value();
    option->singleStep = m_slider.singleStep();
    option->pageStep = m_slider.pageStep();
    if (m_slider.orientation() == Qt::Horizontal) {
        option->state |= QStyle::State_Horizontal;
    }
}


void TickSlider::setCssName(const QString& name)
{
    setObjectName(name);
    m_slider.setObjectName(name);
}
