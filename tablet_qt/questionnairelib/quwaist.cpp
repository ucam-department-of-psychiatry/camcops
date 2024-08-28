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

#include "quwaist.h"

#include <QObject>
#include <QString>
#include <QWidget>

#include "db/fieldref.h"
#include "lib/convert.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/quunitselector.h"

QuWaist::QuWaist(
    FieldRefPtr fieldref,
    QPointer<QuUnitSelector> unit_selector,
    bool mandatory
) :
    QuMeasurement(fieldref, unit_selector, mandatory),
    m_fr_cm(nullptr),
    m_fr_in(nullptr)
{
}

FieldRefPtrList QuWaist::getMetricFieldrefs() const
{
    return FieldRefPtrList({m_fr_cm});
}

FieldRefPtrList QuWaist::getImperialFieldrefs() const
{
    return FieldRefPtrList({m_fr_in});
}

QPointer<QuElement> QuWaist::buildMetricGrid()
{
    auto centimetres_edit = new QuLineEditDouble(m_fr_cm, 0, 600, 1);
    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::centimetres(), centimetres_edit},
        },
        1,
        1
    );
}

QPointer<QuElement> QuWaist::buildImperialGrid()
{
    auto in_edit = new QuLineEditDouble(m_fr_in, 0, 236, 1);

    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::inches(), in_edit},
        },
        1,
        1
    );
}

void QuWaist::setUpFields()
{
    FieldRef::GetterFunction get_cm = std::bind(&QuWaist::getCm, this);
    FieldRef::GetterFunction get_in = std::bind(&QuWaist::getIn, this);
    FieldRef::SetterFunction set_cm
        = std::bind(&QuWaist::setCm, this, std::placeholders::_1);
    FieldRef::SetterFunction set_in
        = std::bind(&QuWaist::setIn, this, std::placeholders::_1);
    m_fr_cm = FieldRefPtr(new FieldRef(get_cm, set_cm, m_mandatory));
    m_fr_in = FieldRefPtr(new FieldRef(get_in, set_in, m_mandatory));
}

QVariant QuWaist::getCm() const
{
    return getFieldrefValue();
}

QVariant QuWaist::getIn() const
{
    return m_in;
}

bool QuWaist::setCm(const QVariant& value)
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

bool QuWaist::setIn(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    Q_ASSERT(m_fr_cm);
    const bool changed = value != m_in;
    if (changed) {
        m_in = value;
        updateMetric();
    }
    return changed;
}

void QuWaist::updateMetric()
{
    // Called when imperial units have been changed.
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_cm);
    if (m_in.isNull()) {
        setFieldrefValue(QVariant());
    } else {
        const double inches = m_in.toDouble();
        setFieldrefValue(convert::centimetresFromInches(inches));
    }
    m_fr_cm->emitValueChanged();
    emit elementValueChanged();
}

void QuWaist::updateImperial()
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_in);
    QVariant waist_cm_var = getFieldrefValue();
    if (waist_cm_var.isNull()) {
        m_in.clear();
    } else {
        const double waist_cm = waist_cm_var.toDouble();
        m_in = convert::inchesFromCentimetres(waist_cm);
    }
    m_fr_in->emitValueChanged();
    emit elementValueChanged();
}
