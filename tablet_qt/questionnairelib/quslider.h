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
#include <QPointer>
#include <QSharedPointer>
#include <QVariant>
#include "db/fieldref.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quelement.h"
#include "widgets/tickslider.h"  // or style sheets + tick marks don't mix

class QLabel;
class QTimer;


class QuSlider : public QuElement
{
    // Offers a slider to choose a numerical value.

    Q_OBJECT
public:
    // Create a slider ranging from "minimum" to "maximum" with step size
    // "step". The slider always uses integers internally, but can display as
    // a float (see setConvertForRealField).
    QuSlider(FieldRefPtr fieldref, int minimum, int maximum, int step);

    // Set the "page step" size, if the user uses the PgUp/PgDn keys.
    // The default is twice the slider's step size.
    QuSlider* setBigStep(int big_step);

    // Interval between tick marks.
    QuSlider* setTickInterval(int tick_interval);  // 0 for none

    // Visually, where are the tick marks (e.g. left/right, above/below)?
    QuSlider* setTickPosition(QSlider::TickPosition position);

    // When the slider contains a null value, where should the handle sit?
    QuSlider* setNullApparentValue(int null_apparent_value);

    // Choose whether the slider should display its contents as a float
    // (convert_for_real_field). If so, the underlying integer (from minimum to
    // maximum) is mapped to a float range (from field_minimum to
    // field_maximum), and shown with the specified number of decimal places
    // (display_dp).
    QuSlider* setConvertForRealField(bool convert_for_real_field,
                                     double field_minimum = 0,
                                     double field_maximum = 1,
                                     int display_dp = 2);

    // Should the slider be horizontal or vertical?
    QuSlider* setHorizontal(bool horizontal);

    // Should the slider show its current numerical value?
    QuSlider* setShowValue(bool show_value);

    // Determine where tick labels should be shown (at which integer values of
    // the slider) and the strings used for the tick labels.
    // Calling this also (effectively) calls setUseDefaultTickLabels(false).
    QuSlider* setTickLabels(const QMap<int, QString>& labels);

    // Visually, where are the tick labels (e.g. left/right, above/below)?
    QuSlider* setTickLabelPosition(QSlider::TickPosition position);

    // Chooses whether default labels should be shown. Default labels are
    // integers from the minimum to the maximum, spaced by the tick interval
    // (or if there isn't one, the "big" step).
    QuSlider* setUseDefaultTickLabels(bool use_default);

    // Should the far left/right labels be edged in visually so that they don't
    // overspill the boundaries of the slider?
    QuSlider* setEdgeInExtremeLabels(bool edge_in_extreme_labels);

    // Should the slider be symmetric, with no colour below (vertical) or to
    // the left (horizontal) of the slider handle? If not, the slider will
    // show red left/below and white right/above, so the higher the value, the
    // more red is shown.
    QuSlider* setSymmetric(bool symmetric);

    // Invert the direction of the slider.
    // Default is left (low) -> right (high), and bottom (low) -> top (high).
    QuSlider* setInverted(bool inverted);

protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int sliderValueFromField(const QVariant& field_value) const;
    QVariant fieldValueFromSlider(int slider_value) const;
    virtual void closing() override;
protected slots:
    void sliderValueChanged(int slider_value);
    void completePendingFieldWrite();
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    // Core
    FieldRefPtr m_fieldref;
    int m_minimum;
    int m_maximum;
    int m_step;
    int m_big_step;
    bool m_convert_for_real_field;
    double m_field_minimum;
    double m_field_maximum;
    int m_display_dp;
    int m_null_apparent_value;

    // Visuals
    bool m_horizontal;
    bool m_show_value;
    int m_tick_interval;
    QSlider::TickPosition m_tick_position;
    bool m_use_default_labels;
    QMap<int, QString> m_tick_labels;
    QSlider::TickPosition m_tick_label_position;
    bool m_edge_in_extreme_labels;
    bool m_symmetric;
    bool m_inverted;

    // Internals
    QPointer<QWidget> m_container_widget;
    QPointer<QLabel> m_value_label;
    QPointer<TickSlider> m_slider;
    bool m_field_write_pending;
    int m_field_write_slider_value;
    QSharedPointer<QTimer> m_timer;
};
