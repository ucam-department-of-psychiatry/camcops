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
#include "lib/convert.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/quunitselector.h"

const double MINIMUM_HEIGHT_CM = 0;
const double MINIMUM_HEIGHT_M = MINIMUM_HEIGHT_CM / convert::CM_PER_M;
const double MAXIMUM_HEIGHT_M = 5;
const int HEIGHT_M_DP = 3;

const int MINIMUM_HEIGHT_FT = 0;
const int MAXIMUM_HEIGHT_FT = 15;
const double MINIMUM_HEIGHT_IN
    = convert::inchesFromCentimetres(MINIMUM_HEIGHT_CM);
const double MAXIMUM_HEIGHT_IN = convert::INCHES_PER_FOOT;
const int HEIGHT_IN_DP = 2;

QuHeight::QuHeight(
    FieldRefPtr fieldref,
    QPointer<QuUnitSelector> unit_selector,
    bool mandatory
) :
    QuMeasurement(fieldref, unit_selector, mandatory),
    m_fr_m(nullptr),
    m_fr_ft(nullptr),
    m_fr_in(nullptr)
{
}

FieldRefPtrList QuHeight::getMetricFieldrefs() const
{
    return FieldRefPtrList({m_fr_m});
}

FieldRefPtrList QuHeight::getImperialFieldrefs() const
{
    return FieldRefPtrList({m_fr_ft, m_fr_in});
}

QPointer<QuElement> QuHeight::buildMetricGrid()
{
    auto metres_edit = new QuLineEditDouble(
        m_fr_m, MINIMUM_HEIGHT_M, MAXIMUM_HEIGHT_M, HEIGHT_M_DP
    );
    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::metres(), metres_edit},
        },
        1,
        1
    );
}

QPointer<QuElement> QuHeight::buildImperialGrid()
{
    auto ft_edit
        = new QuLineEditInteger(m_fr_ft, MINIMUM_HEIGHT_FT, MAXIMUM_HEIGHT_FT);
    auto in_edit = new QuLineEditDouble(
        m_fr_in, MINIMUM_HEIGHT_IN, MAXIMUM_HEIGHT_IN, HEIGHT_IN_DP
    );

    return questionnairefunc::defaultGridRawPointer(
        {
            {CommonOptions::feet(), ft_edit},
            {CommonOptions::inches(), in_edit},
        },
        1,
        1
    );
}

void QuHeight::setUpFields()
{
    FieldRef::GetterFunction get_m = std::bind(&QuHeight::getM, this);
    FieldRef::GetterFunction get_ft = std::bind(&QuHeight::getFt, this);
    FieldRef::GetterFunction get_in = std::bind(&QuHeight::getIn, this);
    FieldRef::SetterFunction set_m
        = std::bind(&QuHeight::setM, this, std::placeholders::_1);
    FieldRef::SetterFunction set_ft
        = std::bind(&QuHeight::setFt, this, std::placeholders::_1);
    FieldRef::SetterFunction set_in
        = std::bind(&QuHeight::setIn, this, std::placeholders::_1);
    m_fr_m = FieldRefPtr(new FieldRef(get_m, set_m, m_mandatory));
    m_fr_ft = FieldRefPtr(new FieldRef(get_ft, set_ft, m_mandatory));
    m_fr_in = FieldRefPtr(new FieldRef(get_in, set_in, m_mandatory));
}

QVariant QuHeight::getM() const
{
    return getFieldrefValue();
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
    const bool changed = setFieldrefValue(value);
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
        setFieldrefValue(QVariant());
    } else {
        const int feet = m_ft.toInt();
        const double inches = m_in.toDouble();
        setFieldrefValue(convert::metresFromFeetInches(feet, inches));
    }
    m_fr_m->emitValueChanged();
    emit elementValueChanged();
}

void QuHeight::updateImperial()
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif
    Q_ASSERT(m_fr_ft);
    Q_ASSERT(m_fr_in);
    QVariant height_m_var = getFieldrefValue();
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
