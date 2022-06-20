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

#include "qumass.h"
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


QuMass::QuMass(FieldRefPtr fieldref, QPointer<QuUnitSelector> unit_selector) :
    m_fieldref(fieldref),
    m_unit_selector(unit_selector),
    m_fr_kg(nullptr),
    m_fr_st(nullptr),
    m_fr_lb(nullptr),
    m_fr_oz(nullptr),
    m_metric_grid(nullptr),
    m_imperial_grid(nullptr)
{
    Q_ASSERT(m_fieldref);
}


QPointer<QWidget> QuMass::makeWidget(Questionnaire* questionnaire)
{
    setUpFields();

    auto layout = new VBoxLayout();

    auto kg_edit = new QuLineEditDouble(m_fr_kg, 0, 1000, 3);
    m_metric_grid = questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::kilograms(), kg_edit},
        }, 1, 1);

    layout->addWidget(m_metric_grid->widget(questionnaire));

    auto st_edit = new QuLineEditInteger(m_fr_st, 0, 150);
    auto lb_edit = new QuLineEditInteger(m_fr_lb, 0, convert::POUNDS_PER_STONE);
    auto oz_edit = new QuLineEditDouble(m_fr_oz, 0, convert::OUNCES_PER_POUND, 2);

    m_imperial_grid = questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::stones(), st_edit},
            {CommonOptions::pounds(), lb_edit},
            {CommonOptions::ounces(), oz_edit},
        }, 1, 1);

    layout->addWidget(m_imperial_grid->widget(questionnaire));

    QPointer<QWidget> widget = new BaseWidget();
    widget->setLayout(layout);

    if (m_unit_selector) {
        connect(m_unit_selector, &QuUnitSelector::unitsChanged,
                this, &QuMass::unitsChanged);
        unitsChanged(m_unit_selector->getUnits().toInt());
    }

    updateImperial();

    return widget;
}

void QuMass::setUpFields()
{
    FieldRef::GetterFunction get_kg = std::bind(&QuMass::getKg, this);
    FieldRef::GetterFunction get_st = std::bind(&QuMass::getSt, this);
    FieldRef::GetterFunction get_lb = std::bind(&QuMass::getLb, this);
    FieldRef::GetterFunction get_oz = std::bind(&QuMass::getOz, this);
    FieldRef::SetterFunction set_kg = std::bind(&QuMass::setKg, this, std::placeholders::_1);
    FieldRef::SetterFunction set_st = std::bind(&QuMass::setSt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_lb = std::bind(&QuMass::setLb, this, std::placeholders::_1);
    FieldRef::SetterFunction set_oz = std::bind(&QuMass::setOz, this, std::placeholders::_1);
    m_fr_kg = FieldRefPtr(new FieldRef(get_kg, set_kg, true));
    m_fr_st = FieldRefPtr(new FieldRef(get_st, set_st, true));
    m_fr_lb = FieldRefPtr(new FieldRef(get_lb, set_lb, true));
    m_fr_oz = FieldRefPtr(new FieldRef(get_oz, set_oz, true));
}


// ============================================================================
// Signal handlers
// ============================================================================

void QuMass::unitsChanged(int units)
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
}


QVariant QuMass::getKg() const
{
    return m_fieldref->value();
}


QVariant QuMass::getSt() const
{
    return m_st;
}


QVariant QuMass::getLb() const
{
    return m_lb;
}


QVariant QuMass::getOz() const
{
    return m_oz;
}


bool QuMass::setKg(const QVariant& value)
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


bool QuMass::setSt(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    const bool changed = value != m_st;
    if (changed) {
        m_st = value;
        updateMetric();
    }
    return changed;
}


bool QuMass::setLb(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    Q_ASSERT(m_fr_kg);
    const bool changed = value != m_lb;
    if (changed) {
        m_lb = value;
        updateMetric();
    }
    return changed;
}


bool QuMass::setOz(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    Q_ASSERT(m_fr_kg);
    const bool changed = value != m_oz;
    if (changed) {
        m_oz = value;
        updateMetric();
    }
    return changed;
}


void QuMass::updateMetric()
{
    // Called when imperial units have been changed.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_kg);
    if (m_st.isNull() && m_lb.isNull() && m_oz.isNull()) {
        m_fieldref->setValue(QVariant());
    } else {
        const int stones = m_st.toInt();
        const int pounds = m_lb.toInt();
        const double ounces = m_oz.toDouble();
        m_fieldref->setValue(convert::kilogramsFromStonesPoundsOunces(
                              stones, pounds, ounces));
    }
    m_fr_kg->emitValueChanged();
}


void QuMass::updateImperial()
{
    // Called when we create the editor, to set imperial units from the
    // underlying (database) metric unit. Also called when metric mass has
    // been changed. Sets the internal imperial representatio.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_st);
    Q_ASSERT(m_fr_lb);
    Q_ASSERT(m_fr_oz);
    QVariant mass_kg_var = m_fieldref->value();
    if (mass_kg_var.isNull()) {
        m_st.clear();
        m_lb.clear();
        m_oz.clear();
    } else {
        const double mass_kg = mass_kg_var.toDouble();
        int stones, pounds;
        double ounces;
        convert::stonesPoundsOuncesFromKilograms(mass_kg, stones, pounds, ounces);
        m_st = stones;
        m_lb = pounds;
        m_oz = ounces;
    }
    m_fr_st->emitValueChanged();
    m_fr_lb->emitValueChanged();
    m_fr_oz->emitValueChanged();
}
