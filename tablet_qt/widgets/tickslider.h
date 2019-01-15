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

#pragma once
#include <QMap>
#include <QSlider>
#include <QStyle>
#include <QStyleOptionSlider>

class QHoverEvent;
class QKeyEvent;
class QMouseEvent;


// Slider with tick marks/labels.
//
// Tick marks vanish on a styled QSlider. So:
// http://stackoverflow.com/questions/27531542/tick-marks-disappear-on-styled-qslider
// ... and then modification including labels, and making it work with
// vertical sliders.

class TickSlider : public QWidget
{
    // As soon as we start re-jigging the layout of the slider itself, e.g.
    // to ensure labels have enough space at the edges, we need to override
    // functions like initStyleOption() that are not virtual in QSlider.
    // At that point, we have to go the whole hog and inherit from
    // QAbstractSlider instead, and re-implement QSlider.
    //
    // ... Unless we can fake the mouse coordinates.
    // ... Nope; mouse hovering involves QSlider::event(), which calls
    //     private functions.
    // ... Although maybe we only need to re-implement
    //     QSliderPrivate::updateHoverControl().
    // ... Tried hard; failed.
    // Reimplementation it is.
    //
    // The thing that makes it very hard is that QSlider has deep connections
    // to QSliderPrivate, which inherits from QAbstractSliderPrivate (with
    // deep links to QAbstractSlider), which inherits from QWidgetPrivate...
    // etc. (Even if we wanted to cheat, none of the *private*.h files are
    // exposed in Qt builds...)
    // No... it's an absolute nightmare; we regress into the bowels of
    // QWidgetPrivate and can't modify the data.
    // This is perhaps the weakest aspect of Qt.
    //
    // So: it has to be layouts, or layout-free widget composition.
    //
    // And that worked beautifully.

    Q_OBJECT

    // ========================================================================
    // Public interface
    // ========================================================================
public:
    TickSlider(QWidget* parent = nullptr);
    TickSlider(Qt::Orientation orientation, QWidget* parent = nullptr);
    virtual void setTickColor(const QColor& colour);
    virtual void setTickThickness(int thickness);
    virtual void setTickLength(int length);
    virtual void setTickLabelGap(int gap);
    virtual void setInterlabelGap(int gap);
    virtual void setGapToSlider(int gap);
    virtual void setEdgeInExtremeLabels(bool edge_in_extreme_labels);

    virtual QSize sizeHint() const override;

    virtual void setTickLabelPosition(QSlider::TickPosition position);
    virtual QSlider::TickPosition tickLabelPosition() const;

    virtual void addTickLabel(int position, const QString& text);
    virtual void setTickLabels(const QMap<int, QString>& labels);
    virtual void addDefaultTickLabels();

    virtual void setReverseHorizontalLabels(bool reverse);
    virtual void setReverseVerticalLabels(bool reverse);

    virtual void setCssName(const QString& name);

    // ========================================================================
    // Passing on calls to/from our slider
    // ========================================================================
public:

    // ------------------------------------------------------------------------
    // From QSlider:
    // ------------------------------------------------------------------------

    Qt::Orientation orientation() const { return m_slider.orientation(); }

    void setMinimum(int minimum) { m_slider.setMinimum(minimum); }
    int minimum() const { return m_slider.minimum(); }

    void setMaximum(int maximum) { m_slider.setMaximum(maximum); }
    int maximum() const { return m_slider.maximum(); }

    void setSingleStep(int step) { m_slider.setSingleStep(step); }
    int singleStep() const { return m_slider.singleStep(); }

    void setPageStep(int step) { m_slider.setPageStep(step); }
    int pageStep() const { return m_slider.pageStep(); }

    void setTracking(bool enable) { m_slider.setTracking(enable); }
    bool hasTracking() const { return m_slider.hasTracking(); }

    void setSliderDown(bool down) { m_slider.setSliderDown(down); }
    bool isSliderDown() const { return m_slider.isSliderDown(); }

    void setSliderPosition(int pos) { m_slider.setSliderPosition(pos); }
    int sliderPosition() const { return m_slider.sliderPosition(); }

    void setInvertedAppearance(bool inverted) { m_slider.setInvertedAppearance(inverted); }
    bool invertedAppearance() const { return m_slider.invertedAppearance(); }

    void setInvertedControls(bool inverted) { m_slider.setInvertedControls(inverted); }
    bool invertedControls() const { return m_slider.invertedControls(); }

    int value() const { return m_slider.value(); }

    void triggerAction(QSlider::SliderAction action) { return m_slider.triggerAction(action); }

public slots:
    void setValue(int value) { m_slider.setValue(value); }
    void setOrientation(Qt::Orientation orientation) { m_slider.setOrientation(orientation); }
    void setRange(int min, int max) { m_slider.setRange(min, max); }

signals:
    void valueChanged(int value);

    void sliderPressed();
    void sliderMoved(int position);
    void sliderReleased();

    void rangeChanged(int min, int max);

    void actionTriggered(int action);

    // ------------------------------------------------------------------------
    // From QAbstractSlider:
    // ------------------------------------------------------------------------
public:

    void setTickPosition(QSlider::TickPosition pos) { m_slider.setTickPosition(pos); }
    QSlider::TickPosition tickPosition() const { return m_slider.tickPosition();}

    void setTickInterval(int ti) { m_slider.setTickInterval(ti); }
    int tickInterval() const { return m_slider.tickInterval(); }

    // ========================================================================
    // Our internals
    // ========================================================================

protected:
    struct LabelOverspill {
        int left = 0;
        int right = 0;
        int top = 0;
        int bottom = 0;
    };

    // Get the size of the biggest label (more accurately, a size that will
    // hold all our labels).
    QSize maxLabelSize() const;

    // Are we using ticks?
    bool usingTicks() const;

    // Are we using labels?
    bool usingLabels() const;

    // Tick position (vertical or horizontal) along the slider.
    int getTickPos(int pos, int handle_extent,
                   int slider_extent, int initial_label_overspill) const;

    // Get label "overspill" distances.
    // - If m_edge_in_extreme_labels, these are all zero. Otherwise:
    // - Horizontal:
    //   - If we have a label for the leftmost (minimum) value, "left" is set
    //     to half the width of the leftmost label.
    //   - If we have a label for the rightmost (maximum) value, "right" is set
    //     to half the width of the rightmost label.
    // - Vertical:
    //   - If we have a label for the topmost (maximum) value, "top" is set to
    //     half the width of the topmost label.
    //   - If we have a label for the bottom (minimum) value, "bottom" is set
    //     to half the width of the bottom label.
    virtual LabelOverspill getLabelOverspill();

    // Clear cached information
    void clearCache();

    QRect getSliderRect();
    void repositionSlider();

    // Event handlers
    virtual bool event(QEvent* event) override;
    virtual void moveEvent(QMoveEvent* event) override;
    virtual void paintEvent(QPaintEvent* ev) override;
    virtual void resizeEvent(QResizeEvent* event) override;

    // Replicated from QSlider (where it's protected):
    void initStyleOption(QStyleOptionSlider* option) const;

protected:
    QColor m_tick_colour;
    int m_tick_thickness;
    int m_tick_length;
    int m_tick_label_gap;
    int m_min_interlabel_gap;
    int m_gap_to_slider;
    bool m_reverse_horizontal_labels;
    bool m_reverse_vertical_labels;
    QSlider::TickPosition m_label_position;
    QMap<int, QString> m_tick_labels;
    bool m_edge_in_extreme_labels;

    bool m_is_overspill_cached;
    LabelOverspill m_cached_overspill;

    QSlider m_slider;
};
