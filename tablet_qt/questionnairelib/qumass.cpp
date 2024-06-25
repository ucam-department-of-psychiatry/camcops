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
#include "lib/convert.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/quunitselector.h"

QuMass::QuMass(
    FieldRefPtr fieldref,
    QPointer<QuUnitSelector> unit_selector,
    bool mandatory
) :
    QuMeasurement(fieldref, unit_selector, mandatory),
    m_fr_kg(nullptr),
    m_fr_st(nullptr),
    m_fr_lb(nullptr),
    m_fr_oz(nullptr)
{
}

FieldRefPtrList QuMass::getMetricFieldrefs() const
{
    return FieldRefPtrList({m_fr_kg});
}

FieldRefPtrList QuMass::getImperialFieldrefs() const
{
    return FieldRefPtrList({m_fr_st, m_fr_lb, m_fr_oz});
}

QPointer<QuElement> QuMass::buildMetricGrid()
{
    auto kg_edit = new QuLineEditDouble(m_fr_kg, 0, 1000, 3);
    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::kilograms(), kg_edit},
        },
        1,
        1
    );
}

QPointer<QuElement> QuMass::buildImperialGrid()
{
    auto st_edit = new QuLineEditInteger(m_fr_st, 0, 150);
    auto lb_edit
        = new QuLineEditInteger(m_fr_lb, 0, convert::POUNDS_PER_STONE);
    auto oz_edit
        = new QuLineEditDouble(m_fr_oz, 0, convert::OUNCES_PER_POUND, 2);

    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::stones(), st_edit},
            {CommonOptions::pounds(), lb_edit},
            {CommonOptions::ounces(), oz_edit},
        },
        1,
        1
    );
}

void QuMass::setUpFields()
{
    FieldRef::GetterFunction get_kg = std::bind(&QuMass::getKg, this);
    FieldRef::GetterFunction get_st = std::bind(&QuMass::getSt, this);
    FieldRef::GetterFunction get_lb = std::bind(&QuMass::getLb, this);
    FieldRef::GetterFunction get_oz = std::bind(&QuMass::getOz, this);
    FieldRef::SetterFunction set_kg
        = std::bind(&QuMass::setKg, this, std::placeholders::_1);
    FieldRef::SetterFunction set_st
        = std::bind(&QuMass::setSt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_lb
        = std::bind(&QuMass::setLb, this, std::placeholders::_1);
    FieldRef::SetterFunction set_oz
        = std::bind(&QuMass::setOz, this, std::placeholders::_1);
    m_fr_kg = FieldRefPtr(new FieldRef(get_kg, set_kg, m_mandatory));
    m_fr_st = FieldRefPtr(new FieldRef(get_st, set_st, m_mandatory));
    m_fr_lb = FieldRefPtr(new FieldRef(get_lb, set_lb, m_mandatory));
    m_fr_oz = FieldRefPtr(new FieldRef(get_oz, set_oz, m_mandatory));
}

QVariant QuMass::getKg() const
{
    return getFieldrefValue();
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
    const bool changed = setFieldrefValue(value);
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
        setFieldrefValue(QVariant());
    } else {
        const int stones = m_st.toInt();
        const int pounds = m_lb.toInt();
        const double ounces = m_oz.toDouble();
        setFieldrefValue(
            convert::kilogramsFromStonesPoundsOunces(stones, pounds, ounces)
        );
    }
    m_fr_kg->emitValueChanged();
    emit elementValueChanged();
}

void QuMass::updateImperial()
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_st);
    Q_ASSERT(m_fr_lb);
    Q_ASSERT(m_fr_oz);
    QVariant mass_kg_var = getFieldrefValue();
    if (mass_kg_var.isNull()) {
        m_st.clear();
        m_lb.clear();
        m_oz.clear();
    } else {
        const double mass_kg = mass_kg_var.toDouble();
        int stones, pounds;
        double ounces;
        convert::stonesPoundsOuncesFromKilograms(
            mass_kg, stones, pounds, ounces
        );
        m_st = stones;
        m_lb = pounds;
        m_oz = ounces;
    }
    m_fr_st->emitValueChanged();
    m_fr_lb->emitValueChanged();
    m_fr_oz->emitValueChanged();
    emit elementValueChanged();
}
