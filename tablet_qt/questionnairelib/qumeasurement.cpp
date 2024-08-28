/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "qumeasurement.h"

#include <QObject>
#include <QString>
#include <QWidget>

#include "db/fieldref.h"
#include "layouts/layouts.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quunitselector.h"
#include "widgets/basewidget.h"

QuMeasurement::QuMeasurement(
    FieldRefPtr fieldref,
    QPointer<QuUnitSelector> unit_selector,
    bool mandatory
) :
    m_mandatory(mandatory),
    m_fieldref(fieldref),
    m_unit_selector(unit_selector),
    m_metric_grid(nullptr),
    m_imperial_grid(nullptr)
{
    Q_ASSERT(m_fieldref);
}

QVariant QuMeasurement::getFieldrefValue() const
{
    return m_fieldref->value();
}

bool QuMeasurement::setFieldrefValue(const QVariant& value)
{
    return m_fieldref->setValue(value);
}

FieldRefPtrList QuMeasurement::fieldrefs() const
{
    FieldRefPtrList fieldrefs;

    if (m_metric_grid->visible()) {
        fieldrefs.append(getMetricFieldrefs());
    }

    if (m_imperial_grid->visible()) {
        fieldrefs.append(getImperialFieldrefs());
    }

    return fieldrefs;
}

QPointer<QWidget> QuMeasurement::makeWidget(Questionnaire* questionnaire)
{
    setUpFields();

    auto layout = new VBoxLayout();

    m_metric_grid = buildMetricGrid();
    layout->addWidget(m_metric_grid->widget(questionnaire));

    m_imperial_grid = buildImperialGrid();
    layout->addWidget(m_imperial_grid->widget(questionnaire));

    QPointer<QWidget> widget = new BaseWidget();
    widget->setLayout(layout);

    if (m_unit_selector) {
        // Internal plumbing:
        // - We want imperial units to update when metric values are changed,
        //   and vice versa.
        // - We can't set up an infinite loop, though, e.g.
        //      metres.valueChanged() -> feet.valueChanged()
        //      feet.valueChanged() -> metres.valueChanged()
        // - The other obvious way is to hold onto a member copy of the
        //   fieldrefs, and manually cause them to emit valueChanged() at
        //   approriate times.
        //
        // BEWARE the consequences of floating-point error, e.g.
        // - 7 st 12 lb 0 oz -> 49.8951 kg
        // - 49.8951 kg -> 7 st 11 lb 0.999779 oz
        // ... the potential change in OTHER units means that all parts must be
        // updated, OR, a little more elegantly, internal records of the
        // imperial units kept.
        connect(
            m_unit_selector,
            &QuUnitSelector::unitsChanged,
            this,
            &QuMeasurement::unitsChanged
        );
        unitsChanged(m_unit_selector->getUnits().toInt());
    }

    updateImperial();

    return widget;
}

// ============================================================================
// Signal handlers
// ============================================================================

void QuMeasurement::unitsChanged(int units)
{
    // Update the display to show "mass" units: metric/imperial/both.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    const bool imperial
        = units == CommonOptions::IMPERIAL || units == CommonOptions::BOTH;
    const bool metric
        = units == CommonOptions::METRIC || units == CommonOptions::BOTH;

    Q_ASSERT(imperial || metric);

    m_metric_grid->setVisible(metric);
    m_imperial_grid->setVisible(imperial);

    emit elementValueChanged();
}
