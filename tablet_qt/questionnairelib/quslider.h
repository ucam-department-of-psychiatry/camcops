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
    QuSlider(FieldRefPtr fieldref, int minimum, int maximum, int step);
    QuSlider* setBigStep(int big_step);
    QuSlider* setTickInterval(int tick_interval);  // 0 for none
    QuSlider* setTickPosition(QSlider::TickPosition position);
    QuSlider* setNullApparentValue(int null_apparent_value);
    QuSlider* setConvertForRealField(bool convert_for_real_field,
                                     double field_minimum = 0,
                                     double field_maximum = 1,
                                     int display_dp = 2);
    QuSlider* setHorizontal(bool horizontal);
    QuSlider* setShowValue(bool show_value);
    QuSlider* setTickLabels(const QMap<int, QString>& labels);
    QuSlider* setTickLabelPosition(QSlider::TickPosition position);
    QuSlider* setUseDefaultTickLabels(bool use_default);
    QuSlider* setEdgeInExtremeLabels(bool edge_in_extreme_labels);
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
    // Internals
    QPointer<QWidget> m_container_widget;
    QPointer<QLabel> m_value_label;
    QPointer<TickSlider> m_slider;
    bool m_field_write_pending;
    int m_field_write_slider_value;
    QSharedPointer<QTimer> m_timer;
};
