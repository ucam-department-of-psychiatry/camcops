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

#include "quthermometer.h"
#include <QLabel>
#include "layouts/layouts.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/imagebutton.h"


QuThermometer::QuThermometer(FieldRefPtr fieldref,
                             const QVector<QuThermometerItem>& items) :
    m_fieldref(fieldref),
    m_items(items)
{
    commonConstructor();
}


QuThermometer::QuThermometer(FieldRefPtr fieldref,
                             std::initializer_list<QuThermometerItem> items) :
    m_fieldref(fieldref),
    m_items(items)
{
    commonConstructor();
}


void QuThermometer::commonConstructor()
{
    m_rescale = false;
    m_rescale_factor = 0;
    m_main_widget = nullptr;
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuThermometer::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuThermometer::fieldValueChanged);
}


QuThermometer* QuThermometer::setRescale(const bool rescale,
                                         const double rescale_factor,
                                         const bool adjust_for_dpi)
{
    m_rescale = rescale;
    m_rescale_factor = rescale_factor;
    if (adjust_for_dpi) {
        m_rescale_factor *= uiconst::DPI / uiconst::DEFAULT_DPI;
    }
    return this;
}


QPointer<QWidget> QuThermometer::makeWidget(Questionnaire* questionnaire)
{
    m_active_widgets.clear();
    m_inactive_widgets.clear();
    const bool read_only = questionnaire->readOnly();
    m_main_widget = new QWidget();
    m_main_widget->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    GridLayout* grid = new GridLayout();
    grid->setContentsMargins(uiconst::NO_MARGINS);
    grid->setSpacing(0);
    m_main_widget->setLayout(grid);
    // In reverse order:
    const int n = m_items.size();
    for (int i = n - 1; i >= 0; --i) {
        const int row = (n - 1) - i;
        const QuThermometerItem& item = m_items.at(i);
        QPointer<ImageButton> active = new ImageButton();
        active->setImages(item.activeFilename(),
                          false, false, false, false, read_only);
        if (m_rescale) {
            active->resizeImages(m_rescale_factor);
        }
        QPointer<ImageButton> inactive = new ImageButton();
        inactive->setImages(item.inactiveFilename(),
                            false, false, false, false, read_only);
        if (m_rescale) {
            inactive->resizeImages(m_rescale_factor);
        }
        QLabel* label = new QLabel(item.text());
        grid->addWidget(active.data(), row, 0);
        grid->addWidget(inactive.data(), row, 0);
        grid->addWidget(label, row, 1);
        if (!read_only) {
            // Safe object lifespan signal: can use std::bind
            connect(active.data(), &ImageButton::clicked,
                    std::bind(&QuThermometer::clicked, this, i));
            connect(inactive.data(), &ImageButton::clicked,
                    std::bind(&QuThermometer::clicked, this, i));
        }
        m_active_widgets.append(active);
        m_inactive_widgets.append(inactive);
    }
    setFromField();
    return m_main_widget;
}


void QuThermometer::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


void QuThermometer::clicked(const int index)
{
    if (index < 0 || index >= m_items.size()) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    const QVariant newvalue = m_items.at(index).value();
    const bool changed = m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


int QuThermometer::indexFromValue(const QVariant &value) const
{
    if (value.isNull()) {
        return -1;
    }
    for (int i = 0; i < m_items.size(); ++i) {
        if (m_items.at(i).value() == value) {
            return i;
        }
    }
    return -1;
}


QVariant QuThermometer::valueFromIndex(const int index) const
{
    if (index < 0 || index >= m_items.size()) {
        return QVariant();
    }
    return m_items.at(index).value();
}


void QuThermometer::fieldValueChanged(const FieldRef* fieldref)
{
    if (!m_main_widget) {
        return;
    }
    uifunc::setPropertyMissing(m_main_widget, fieldref->missingInput());
    const int index = indexFromValue(fieldref->value());
    const int n = m_active_widgets.size();
    const int index_row = (n - 1) - index;  // operating in reverse
    for (int i = 0; i < m_active_widgets.size(); ++ i) {
        QPointer<ImageButton> active = m_active_widgets.at(i);
        QPointer<ImageButton> inactive = m_inactive_widgets.at(i);
        if (i == index_row) {
            active->show();
            inactive->hide();
        } else {
            active->hide();
            inactive->show();
        }
    }
    m_main_widget->update();
}


FieldRefPtrList QuThermometer::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
