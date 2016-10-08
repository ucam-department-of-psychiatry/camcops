#include "tickslider.h"
#include <QKeyEvent>
#include <QMouseEvent>
#include <QStyleOptionSlider>
#include <QStylePainter>
#include "lib/uifunc.h"


const QColor DEFAULT_TICK_COLOR(0, 0, 0, 255);
const int DEFAULT_TICK_WIDTH = 0;
const int DEFAULT_TICK_LENGTH = 4;
const int DEFAULT_TICK_LABEL_GAP = 4;
const int DEFAULT_INTERLABEL_GAP = 4;
const int DEFAULT_GAP_TO_SLIDER = 6;


TickSlider::TickSlider(QWidget *parent) :
    QSlider(parent)
{
    commonConstructor();
}


TickSlider::TickSlider(Qt::Orientation orientation,
                       QWidget *parent) :
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
}


void TickSlider::setTickColor(const QColor& colour)
{
    m_tick_colour = colour;
}


void TickSlider::setTickThickness(int thickness)
{
    m_tick_thickness = thickness;
}


void TickSlider::setTickLength(int length)
{
    m_tick_length = length;
}


void TickSlider::setTickLabelGap(int gap)
{
    m_tick_label_gap = gap;
}


void TickSlider::setInterlabelGap(int gap)
{
    m_min_interlabel_gap = gap;
}


void TickSlider::setGapToSlider(int gap)
{
    m_gap_to_slider = gap;
}

void TickSlider::setTickLabelPosition(QSlider::TickPosition position)
{
    m_label_position = position;
}


QSlider::TickPosition TickSlider::tickLabelPosition() const
{
    return m_label_position;
}


void TickSlider::addTickLabel(int position, const QString& text)
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


void TickSlider::setReverseHorizontalLabels(bool reverse)
{
    m_reverse_horizontal_labels = reverse;
}


void TickSlider::setReverseVerticalLabels(bool reverse)
{
    m_reverse_vertical_labels = reverse;
}


QSize TickSlider::biggestLabel() const
{
    QSize maxsize;
    QFontMetrics fm = fontMetrics();
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

void TickSlider::paintEvent(QPaintEvent *ev)
{
    Q_UNUSED(ev)
    QStylePainter p(this);
    QStyleOptionSlider opt;
    initStyleOption(&opt);

    QRect handle = style()->subControlRect(QStyle::CC_Slider, &opt,
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

    bool using_ticks = tickPosition() != NoTicks;
    bool using_labels = tickLabelPosition() != NoTicks;
    if (!using_ticks && !using_labels) {
        return;
    }
    QPen pen;
    pen.setColor(m_tick_colour);
    pen.setWidth(m_tick_thickness);
    p.setPen(pen);
    bool horizontal = orientation() == Qt::Horizontal;
    QSize biggest_label = biggestLabel();
    int max_label_height = using_labels ? biggest_label.height() : 0;
    int max_label_width = using_labels ? biggest_label.width() : 0;
    if (horizontal) {
        // --------------------------------------------------------------------
        // HORIZONTAL
        // --------------------------------------------------------------------
        int move_tick_by = (max_label_height > 0)
                ? (max_label_height + m_tick_label_gap)
                : 0;
        // Top
        int bounding_box_top = this->rect().top();
        int top_label_top = bounding_box_top;
        int top_tick_top = bounding_box_top + move_tick_by;
        int top_tick_bottom = top_tick_top + m_tick_length;
        // Bottom, working up
        int bounding_box_bottom = this->rect().bottom();
        int bottom_label_bottom = bounding_box_bottom;
        int bottom_tick_bottom = bounding_box_bottom - move_tick_by;
        int bottom_tick_top = bottom_tick_bottom - m_tick_length;
        // OK:
        for (int i = minimum(); i <= maximum(); i += interval) {
            bool leftmost = i == minimum();
            bool rightmost = i == maximum();
            Qt::Alignment halign = leftmost
                    ? Qt::AlignLeft
                    : (rightmost ? Qt::AlignRight : Qt::AlignHCenter);
            int q = m_reverse_horizontal_labels ? (maximum() - i) : i;
            int x = round(
                (double)(
                    (double)(
                        (double)(q - this->minimum()) /
                        (double)(this->maximum() - this->minimum())
                    ) * (double)(this->width() - handle.width()) +
                    (double)(handle.width() / 2.0)
                )
            ) - 1;
            bool has_label = m_tick_labels.contains(i);
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
                UiFunc::drawText(p, x, top_label_top,
                                 halign | Qt::AlignTop, label_text);
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksBelow) {
                p.drawLine(x, bottom_tick_top, x, bottom_tick_bottom);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksBelow)) {
                UiFunc::drawText(p, x, bottom_label_bottom,
                                 halign | Qt::AlignBottom, label_text);
            }
        }
    } else {
        // --------------------------------------------------------------------
        // VERTICAL
        // --------------------------------------------------------------------
        int move_tick_by = (max_label_width > 0)
                ? (max_label_width + m_tick_label_gap)
                : 0;
        // Left
        int bounding_box_left = this->rect().left();
        int left_label_right = bounding_box_left + max_label_width;
        int left_tick_left = bounding_box_left + move_tick_by;
        int left_tick_right = left_tick_left + m_tick_length;
        // Right, working leftwards
        int bounding_box_right = this->rect().right();
        int right_label_left = bounding_box_right - max_label_width;
        int right_tick_right = bounding_box_right - move_tick_by;
        int right_tick_left = right_tick_right - m_tick_length;
        // OK:
        for (int i = minimum(); i <= maximum(); i += interval) {
            Qt::Alignment valign = Qt::AlignVCenter;
            int q = m_reverse_vertical_labels ? (maximum() - i) : i;
            int y = round(
                (double)(
                    (double)(
                        (double)(q - this->minimum()) /
                        (double)(this->maximum() - this->minimum())
                    ) * (double)(this->height() - handle.height()) +
                    (double)(handle.height() / 2.0)
                )
            ) - 1;
            bool has_label = m_tick_labels.contains(i);
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
                UiFunc::drawText(p, left_label_right, y,
                                 Qt::AlignRight | valign, label_text);
            }
            if (tickPosition() == TicksBothSides ||
                    tickPosition() == TicksRight) {
                p.drawLine(right_tick_left, y, right_tick_right, y);
            }
            if (has_label && (tickLabelPosition() == TicksBothSides ||
                              tickLabelPosition() == TicksRight)) {
                UiFunc::drawText(p, right_label_left, y,
                                 Qt::AlignLeft | valign, label_text);
            }
        }
    }
}


QSize TickSlider::sizeHint() const
{
    QSize size = QSlider::sizeHint();
    bool using_labels = tickLabelPosition() != NoTicks;
    QSize label = using_labels ? biggestLabel() : QSize();
    bool using_ticks = tickPosition() != NoTicks;
    int n_potential_labels = (maximum() - minimum()) / tickInterval();
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

    QPoint pos = mapFromGlobal(QCursor::pos());
    QStyle::SubControls hoverControl;

    // Then the rest of this is lightly modified from QSliderPrivate::newHoverControl

    QStyleOptionSlider opt;
    initStyleOption(&opt);
    opt.subControls = QStyle::SC_All;
    QRect handleRect = style()->subControlRect(QStyle::CC_Slider, &opt,
                                               QStyle::SC_SliderHandle, this);
    QRect grooveRect = style()->subControlRect(QStyle::CC_Slider, &opt,
                                               QStyle::SC_SliderGroove, this);
    QRect tickmarksRect = style()->subControlRect(QStyle::CC_Slider, &opt,
                                                  QStyle::SC_SliderTickmarks, this);
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
