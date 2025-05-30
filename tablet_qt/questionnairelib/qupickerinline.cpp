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

#include "qupickerinline.h"

#include <QComboBox>
#include <QLabel>

#include "common/cssconst.h"
#include "lib/widgetfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"


const int MAX_LENGTH = 100;

QuPickerInline::QuPickerInline(
    FieldRefPtr fieldref, const NameValueOptions& options, QObject* parent
) :
    QuElement(parent),
    m_fieldref(fieldref),
    m_options(options),
    m_randomize(false),
    m_cbox(nullptr)
{
    m_options.validateOrDie();
    Q_ASSERT(m_fieldref);
    connect(
        m_fieldref.data(),
        &FieldRef::valueChanged,
        this,
        &QuPickerInline::fieldValueChanged
    );
    connect(
        m_fieldref.data(),
        &FieldRef::mandatoryChanged,
        this,
        &QuPickerInline::fieldValueChanged
    );
}

QuPickerInline* QuPickerInline::setRandomize(const bool randomize)
{
    m_randomize = randomize;
    return this;
}

QPointer<QWidget> QuPickerInline::makeWidget(Questionnaire* questionnaire)
{
    // Randomize?
    if (m_randomize) {
        m_options.shuffle();
    }

    const bool read_only = questionnaire->readOnly();
    m_cbox = new QComboBox();
    m_cbox->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    for (int position = 0; position < m_options.size(); ++position) {
        const NameValuePair& nvp = m_options.atPosition(position);
        m_cbox->insertItem(position, nvp.name().left(MAX_LENGTH));
        // No real point in passing the third QVariant parameter.
    }
    // QComboBox has two signals named currentIndexChanged, differing only
    // in the parameter they pass (int versus QString&). You get
    // "no matching function for call to ... unresolved overloaded function
    // type..."
    // Disambiguate like this:
    void (QComboBox::*ic_signal)(int) = &QComboBox::currentIndexChanged;
    if (!read_only) {
        // The currentIndex on the QCombobox is what we are calling the
        // position of the item in the list of options (the index being the
        // original, unrandomized position).
        connect(
            m_cbox.data(), ic_signal, this, &QuPickerInline::currentItemChanged
        );
    }
    m_cbox->setEnabled(!read_only);
    m_cbox->setObjectName(cssconst::PICKER_INLINE);
    setFromField();
    return QPointer<QWidget>(m_cbox);
}

void QuPickerInline::currentItemChanged(const int position)
{
    // qDebug().nospace() << "QuPickerInline::currentItemChanged("
    //      << position << ")";
    if (!m_options.validIndex(position)) {
        return;
    }
    const QVariant newvalue = m_options.atPosition(position).value();
    const bool changed = m_fieldref->setValue(newvalue);
    // ... Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}

void QuPickerInline::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}

void QuPickerInline::fieldValueChanged(const FieldRef* fieldref)
{
    const int index = m_options.indexFromValue(fieldref->value());
    const bool missing = fieldref->missingInput();
    if (m_cbox) {
        {
            const QSignalBlocker blocker(m_cbox);
            // qDebug() << "QuPickerInline::valueChanged(): index =" << index;
            m_cbox->setCurrentIndex(index);  // it's happy with -1
        }
        widgetfunc::setPropertyMissing(m_cbox, missing);
    }
}

FieldRefPtrList QuPickerInline::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
