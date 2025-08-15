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

#include "qulineedit.h"

#include <QValidator>

#include "common/textconst.h"
#include "lib/widgetfunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/validatinglineedit.h"

QuLineEdit::QuLineEdit(
    FieldRefPtr fieldref, bool allow_empty, QObject* parent
) :
    QuElement(parent),
    m_fieldref(fieldref),
    m_allow_empty(allow_empty),
    m_hint(TextConst::defaultHintText()),
    m_editor(nullptr),
    m_echo_mode(QLineEdit::Normal)
{
    Q_ASSERT(m_fieldref);
    connect(
        m_fieldref.data(),
        &FieldRef::valueChanged,
        this,
        &QuLineEdit::fieldValueChanged
    );
    connect(
        m_fieldref.data(),
        &FieldRef::mandatoryChanged,
        this,
        &QuLineEdit::fieldValueChanged
    );
}

QuLineEdit* QuLineEdit::setHint(const QString& hint)
{
    m_hint = hint;
    return this;
}

QuLineEdit* QuLineEdit::setEchoMode(const QLineEdit::EchoMode echo_mode)
{
    m_echo_mode = echo_mode;
    return this;
}

void QuLineEdit::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}

QPointer<QWidget> QuLineEdit::makeWidget(Questionnaire* questionnaire)
{
    const bool read_only = questionnaire->readOnly();
    const bool delayed = true;
    const bool vertical = false;

    m_editor = new ValidatingLineEdit(
        getValidator(), m_allow_empty, read_only, delayed, vertical
    );
    m_editor->addInputMethodHints(getInputMethodHints());
    m_editor->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    m_editor->setEnabled(!read_only);
    m_editor->setPlaceholderText(m_hint);
    m_editor->setEchoMode(m_echo_mode);
    if (!read_only) {
        connect(
            m_editor.data(),
            &ValidatingLineEdit::valid,
            this,
            &QuLineEdit::widgetTextChangedAndValid
        );
        connect(
            m_editor.data(),
            &ValidatingLineEdit::focusLost,
            this,
            &QuLineEdit::focusLost
        );
    }
    setFromField();

    return QPointer<QWidget>(m_editor);
}

Qt::InputMethodHints QuLineEdit::getInputMethodHints()
{
    // Override in derived class
    return Qt::ImhNone;
}

QPointer<QValidator> QuLineEdit::getValidator()
{
    // Override in derived class
    return nullptr;
}

FieldRefPtrList QuLineEdit::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}

void QuLineEdit::widgetTextChangedAndValid()
{
    // To cope with setting things to null, we need to use a QVariant.
    // We use null rather than a blank string, because QuLineEdit may be used
    // to set numeric fields (where "" will be converted to 0).
    const QString text = m_editor->text();
    const QVariant value = text.isEmpty() ? QVariant() : QVariant(text);
    const bool changed = m_fieldref->setValue(value, this);
    // ... Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}

void QuLineEdit::fieldValueChanged(
    const FieldRef* fieldref, const QObject* originator
)
{
    qDebug() << Q_FUNC_INFO;

    if (!m_editor) {
        return;
    }

    m_editor->setPropertyMissing(fieldref->missingInput());
    if (originator != this) {
        const QString text = fieldref->isNull() ? "" : fieldref->valueString();
        // qDebug() << Q_FUNC_INFO << "setting to" << text;
        m_editor->setTextBlockingSignals(text);
    }
}

void QuLineEdit::focusLost()
{
    auto state = m_editor->getState();
    // Validation should already have been run before the signal is emitted
    Q_ASSERT(!state.isNull());

    // If focus is leaving the widget, and its state is duff, reset the value.
    if (state != QValidator::Acceptable) {
        setFromField();
    }

    m_editor->resetValidatorFeedback();
}
