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

#include "quunitselector.h"

#include <QObject>
#include <QString>
#include <QWidget>

#include "db/fieldref.h"
#include "layouts/layouts.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "widgets/basewidget.h"

QuUnitSelector::QuUnitSelector(NameValueOptions options) :
    m_units(CommonOptions::METRIC),
    m_fr_units(nullptr),
    m_options(options)
{
}

QPointer<QWidget> QuUnitSelector::makeWidget(Questionnaire* questionnaire)
{
    setUpFields();

    auto layout = new VBoxLayout();

    auto unit_selector = (new QuMcq(m_fr_units, m_options))
                             ->setHorizontal(true)
                             ->setAsTextButton(true);
    connect(
        m_fr_units.data(),
        &FieldRef::valueChanged,
        this,
        &QuUnitSelector::fieldChanged
    );
    layout->addWidget(unit_selector->widget(questionnaire));

    QPointer<QWidget> widget = new BaseWidget();
    widget->setLayout(layout);

    return widget;
}

void QuUnitSelector::setUpFields()
{
    FieldRef::GetterFunction get_units
        = std::bind(&QuUnitSelector::getUnits, this);
    FieldRef::SetterFunction set_units
        = std::bind(&QuUnitSelector::setUnits, this, std::placeholders::_1);
    m_fr_units = FieldRefPtr(new FieldRef(get_units, set_units, true));
}

// ============================================================================
// Signal handlers
// ============================================================================


void QuUnitSelector::fieldChanged()
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO;
#endif

    emit unitsChanged(m_units);
}

QVariant QuUnitSelector::getUnits() const
{
    return m_units;
}

bool QuUnitSelector::setUnits(const QVariant& value)
{
#ifdef DEBUG_DATA_FLOW
    qDebug() << Q_FUNC_INFO << value;
#endif
    int units = value.toInt();
    if (units != CommonOptions::METRIC && units != CommonOptions::IMPERIAL
        && units != CommonOptions::BOTH) {
        units = CommonOptions::METRIC;
    }
    const bool changed = units != m_units;
    m_units = units;

    return changed;
}
