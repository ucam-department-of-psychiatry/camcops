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
#include <QBrush>
#include <QPen>
#include <QPoint>
#include <QWidget>
#include "graphics/penbrush.h"


class AdjustablePie : public QWidget
{
    Q_OBJECT
public:
    // ========================================================================
    // Construction and configuration
    // ========================================================================
    AdjustablePie(int n_sectors, QWidget* parent = nullptr);
    // How many sectors?
    // (For n_sectors == 1, no cursors are shown; that's a fixed, whole pie.)
    void setNSectors(int n_sectors);

    // Background colour:
    void setBackgroundBrush(const QBrush& brush);

    // Colour of each sector
    void setSectorPenBrush(int sector_index, const PenBrush& penbrush);
    void setSectorPenBrushes(const QVector<PenBrush>& penbrushes);

    // Labels for each sector
    void setLabel(int sector_index, const QString& label);
    void setLabels(const QVector<QString>& labels);
    void setLabelColour(int sector_index, const QColor& colour);
    void setLabelColours(const QVector<QColor>& colours);
    void setLabelRotation(bool rotate);

    // Cursors that sit as fenceposts between each sector
    void setCursorPenBrush(int cursor_index, const PenBrush& penbrush);
    void setCursorPenBrushes(const QVector<PenBrush>& penbrushes);
    void setCursorActivePenBrush(int cursor_index, const PenBrush& penbrush);
    void setCursorActivePenBrushes(const QVector<PenBrush>& penbrushes);

    // Proportions for each {sector -> cursor}, up to n - 1
    // ... though setProportions will also accept n and ignore the last.
    void setProportions(const QVector<qreal>& proportions);
    void setProportionCumulative(int cursor_index, qreal proportion);
    void setProportionsCumulative(const QVector<qreal>& proportions);

    // Font for sector labels:
    void setOuterLabelFont(const QFont& font);

    // If n_sectors == 1, you may want a centre label:
    void setCentreLabel(const QString& label);
    void setCentreLabelFont(const QFont& font);
    void setCentreLabelColour(const QColor& colour);

    // Radius of the sectors:
    void setSectorRadius(int radius);

    // Radii for the inner and outer circles defining the cursors:
    void setCursorRadius(int inner_radius, int outer_radius);

    // Angle that each cursor (itself a sector shape) subtends:
    void setCursorAngle(qreal degrees);

    // Radius for the labels (typically, for autorotating labels, the bottom
    // of the text):
    void setLabelStartRadius(int radius);

    // Radius of the whole widget:
    void setOverallRadius(int radius);

    // Rotation of the pie:
    void setBaseCompassHeading(int degrees);  // 0 is up, 180 is down, default 180

    // Delay (ms) between movement and event generation:
    void setReportingDelay(int delay_ms);

    // ========================================================================
    // Widget information and events
    // ========================================================================

    virtual QSize sizeHint() const override;
    virtual bool hasHeightForWidth() const override { return false; }
    virtual void paintEvent(QPaintEvent* event) override;
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
    virtual void mouseReleaseEvent(QMouseEvent* event) override;

    // ========================================================================
    // Readout
    // ========================================================================

    // Get the n - 1 proportions for each {sector -> cursor}:
    QVector<qreal> cursorProportions() const;
    QVector<qreal> cursorProportionsCumulative() const;

    // Get the n sector proportions (which will add up to 1):
    QVector<qreal> allProportions() const;
    QVector<qreal> allProportionsCumulative() const;

signals:
    // When a cursor is moved, this signal is emitted, with all n proportions:
    void proportionsChanged(QVector<qreal> all_proportions);
    void cumulativeProportionsChanged(QVector<qreal> all_proportions);

    // ========================================================================
    // Internals
    // ========================================================================
protected:
    void normalize();
    void normalizeProportions();
    qreal sectorProportionCumulative(int sector_index) const;
    qreal convertAngleToQt(qreal degrees) const;
    qreal convertAngleToInternal(qreal degrees) const;
    bool posInCursor(const QPoint& pos, int cursor_index) const;
    qreal angleToProportion(qreal angle_degrees) const;
    qreal proportionToAngle(qreal proportion) const;
    qreal angleOfPos(const QPoint& pos) const;
    qreal radiusOfPos(const QPoint& pos) const;
    qreal cursorAngle(int cursor_index) const;
    void scheduleReport();
    void report();

protected:
    // Fairly static:
    int m_n_sectors;
    QBrush m_background_brush;
    QVector<PenBrush> m_sector_penbrushes;  // n
    QVector<QString> m_labels;  // n
    QVector<QColor> m_label_colours;  // n
    QVector<PenBrush> m_cursor_penbrushes;  // n - 1
    QVector<PenBrush> m_cursor_active_penbrushes;  // n - 1
    QFont m_outer_label_font;
    QFont m_centre_label_font;
    QColor m_centre_label_colour;
    int m_sector_radius;
    int m_cursor_inner_radius;
    int m_cursor_outer_radius;
    qreal m_cursor_angle_degrees;
    int m_label_start_radius;
    QString m_centre_label;
    int m_overall_radius;
    int m_base_compass_heading_deg;
    int m_reporting_delay_ms;
    // Dynamic:
    QVector<qreal> m_cursor_props_cum;  // n - 1
    // Internal state:
    bool m_rotate_labels;
    bool m_user_dragging_cursor;  // or touch equivalent
    int m_cursor_num_being_dragged;
    QPoint m_last_mouse_pos;
    qreal m_angle_offset_from_cursor_centre;
    QSharedPointer<QTimer> m_timer;
};
