/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "quspinboxdouble.h"
#include <QDoubleSpinBox>
#include "lib/uifunc.h"
#include "questionnaire.h"


QuSpinBoxDouble::QuSpinBoxDouble(FieldRefPtr fieldref, double minimum,
                                 double maximum, int decimals) :
    m_fieldref(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_decimals(decimals)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuSpinBoxDouble::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuSpinBoxDouble::fieldValueChanged);
}


void QuSpinBoxDouble::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}


QPointer<QWidget> QuSpinBoxDouble::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_spinbox = new QDoubleSpinBox();
    m_spinbox->setEnabled(!read_only);
    m_spinbox->setDecimals(m_decimals);
    m_spinbox->setRange(m_minimum, m_maximum);
    m_spinbox->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    m_spinbox->setMinimumHeight(uiconst::MIN_SPINBOX_HEIGHT);  // room for spin arrows
    m_spinbox->setButtonSymbols(uiconst::SPINBOX_SYMBOLS);

    // QDoubleSpinBox has two signals named valueChanged, differing only
    // in the parameter they pass (double versus QString&). You get
    // "no matching function for call to ... unresolved overloaded function
    // type..."
    // Disambiguate like this:
    void (QDoubleSpinBox::*vc_sig_dbl)(double) = &QDoubleSpinBox::valueChanged;
    // void (QDoubleSpinBox::*vc_sig_str)(const QString&) = &QDoubleSpinBox::valueChanged;
    if (!read_only) {
        connect(m_spinbox.data(), vc_sig_dbl,
                this, &QuSpinBoxDouble::widgetValueChanged);
        //connect(m_spinbox.data(), vc_sig_str,
        //        this, &QuSpinBoxDouble::widgetValueChangedString);
    }
    setFromField();
    return QPointer<QWidget>(m_spinbox);
}


FieldRefPtrList QuSpinBoxDouble::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuSpinBoxDouble::widgetValueChanged(double value)
{
    bool changed = m_fieldref->setValue(value, this);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


//void QuSpinBoxDouble::widgetValueChangedString(const QString& text)
//{
//    qDebug() << Q_FUNC_INFO << text;
//}


void QuSpinBoxDouble::fieldValueChanged(const FieldRef* fieldref,
                                        const QObject* originator)
{
    if (!m_spinbox) {
        return;
    }
    uifunc::setPropertyMissing(m_spinbox, fieldref->missingInput());
    if (originator != this) {
        const QSignalBlocker blocker(m_spinbox);
        m_spinbox->setValue(fieldref->valueDouble());
    }
}
