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

#include "quheight.h"
#include <QObject>
#include <QString>
#include <QWidget>
#include "db/fieldref.h"
#include "layouts/layouts.h"
#include "lib/convert.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/quunitselector.h"
#include "questionnairelib/qumcq.h"


QuHeight::QuHeight(FieldRefPtr fieldref, QPointer<QuUnitSelector> unit_selector) :
    m_fieldref(fieldref),
    m_unit_selector(unit_selector),
    m_fr_m(nullptr),
    m_fr_ft(nullptr),
    m_fr_in(nullptr),
    m_metric_grid(nullptr),
    m_imperial_grid(nullptr)
{
    Q_ASSERT(m_fieldref);
}


FieldRefPtrList QuHeight::fieldrefs() const
{
    FieldRefPtrList fieldrefs;

    if (m_metric_grid->visible()) {
        fieldrefs.append({m_fr_m});
    }

    if (m_imperial_grid->visible()) {
        fieldrefs.append({m_fr_ft, m_fr_in});
    }

    return fieldrefs;
}


QPointer<QWidget> QuHeight::makeWidget(Questionnaire* questionnaire)
{
    setUpFields();

    auto layout = new VBoxLayout();

    auto metres_edit = new QuLineEditDouble(m_fr_m, 0, 5, 3);
    m_metric_grid = questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::metres(), metres_edit},
        }, 1, 1);

    layout->addWidget(m_metric_grid->widget(questionnaire));

    auto ft_edit = new QuLineEditInteger(m_fr_ft, 0, 15);
    auto in_edit = new QuLineEditDouble(m_fr_in, 0, convert::INCHES_PER_FOOT, 2);

    m_imperial_grid = questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::feet(), ft_edit},
            {CommonOptions::inches(), in_edit},
        }, 1, 1);

    layout->addWidget(m_imperial_grid->widget(questionnaire));

    QPointer<QWidget> widget = new BaseWidget();
    widget->setLayout(layout);

    if (m_unit_selector) {
        connect(m_unit_selector, &QuUnitSelector::unitsChanged,
                this, &QuHeight::unitsChanged);
        unitsChanged(m_unit_selector->getUnits().toInt());
    }

    updateImperial();

    return widget;
}

void QuHeight::setUpFields()
{
    FieldRef::GetterFunction get_m = std::bind(&QuHeight::getM, this);
    FieldRef::GetterFunction get_ft = std::bind(&QuHeight::getFt, this);
    FieldRef::GetterFunction get_in = std::bind(&QuHeight::getIn, this);
    FieldRef::SetterFunction set_m = std::bind(&QuHeight::setM, this, std::placeholders::_1);
    FieldRef::SetterFunction set_ft = std::bind(&QuHeight::setFt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_in = std::bind(&QuHeight::setIn, this, std::placeholders::_1);
    m_fr_m = FieldRefPtr(new FieldRef(get_m, set_m, true));
    m_fr_ft = FieldRefPtr(new FieldRef(get_ft, set_ft, true));
    m_fr_in = FieldRefPtr(new FieldRef(get_in, set_in, true));
}


// ============================================================================
// Signal handlers
// ============================================================================

void QuHeight::unitsChanged(int units)
{
    // Update the display to show "mass" units: metric/imperial/both.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    const bool imperial = units == CommonOptions::IMPERIAL ||
        units == CommonOptions::BOTH;
    const bool metric = units == CommonOptions::METRIC ||
        units == CommonOptions::BOTH;

    Q_ASSERT(imperial || metric);

    m_metric_grid->setVisible(metric);
    m_imperial_grid->setVisible(imperial);

    emit elementValueChanged();
}


QVariant QuHeight::getM() const
{
    return m_fieldref->value();
}


QVariant QuHeight::getFt() const
{
    return m_ft;
}


QVariant QuHeight::getIn() const
{
    return m_in;
}


bool QuHeight::setM(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    const bool changed = m_fieldref->setValue(value);
    if (changed) {
        updateImperial();
    }
    return changed;
}


bool QuHeight::setFt(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    const bool changed = value != m_ft;
    if (changed) {
        m_ft = value;
        updateMetric();
    }
    return changed;
}


bool QuHeight::setIn(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    Q_ASSERT(m_fr_m);
    const bool changed = value != m_in;
    if (changed) {
        m_in = value;
        updateMetric();
    }
    return changed;
}


void QuHeight::updateMetric()
{
    // Called when imperial units have been changed.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_m);
    if (m_ft.isNull() && m_in.isNull()) {
        m_fieldref->setValue(QVariant());
    } else {
        const int feet = m_ft.toInt();
        const double inches = m_in.toDouble();
        m_fieldref->setValue(convert::metresFromFeetInches(feet, inches));
    }
    m_fr_m->emitValueChanged();
    emit elementValueChanged();
}


void QuHeight::updateImperial()
{
    // Called when we create the editor, to set imperial units from the
    // underlying (database) metric unit. Also called when metric mass has
    // been changed. Sets the internal imperial representatio.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_ft);
    Q_ASSERT(m_fr_in);
    QVariant height_m_var = m_fieldref->value();
    if (height_m_var.isNull()) {
        m_ft.clear();
        m_in.clear();
    } else {
        const double height_m = height_m_var.toDouble();
        int feet;
        double inches;
        convert::feetInchesFromMetres(height_m, feet, inches);
        m_ft = feet;
        m_in = inches;
    }
    m_fr_ft->emitValueChanged();
    m_fr_in->emitValueChanged();
    emit elementValueChanged();
}
