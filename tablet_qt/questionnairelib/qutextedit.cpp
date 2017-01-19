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

#include "qutextedit.h"
#include <QTimer>
#include "lib/uifunc.h"
#include "qobjects/focuswatcher.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/growingtextedit.h"


const int WRITE_DELAY_MS = 400;


QuTextEdit::QuTextEdit(FieldRefPtr fieldref, bool accept_rich_text) :
    m_fieldref(fieldref),
    m_accept_rich_text(accept_rich_text),
    m_hint("text"),
    m_editor(nullptr),
    m_ignore_widget_signal(false),
    m_focus_watcher(nullptr),
    m_timer(new QTimer())
{
    Q_ASSERT(m_fieldref);
    m_timer->setSingleShot(true);
    connect(m_timer.data(), &QTimer::timeout,
            this, &QuTextEdit::textChanged);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuTextEdit::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuTextEdit::fieldValueChanged);
}


QuTextEdit* QuTextEdit::setHint(const QString& hint)
{
    m_hint = hint;
    return this;
}


void QuTextEdit::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}


QPointer<QWidget> QuTextEdit::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_editor = new GrowingTextEdit();
    m_editor->setEnabled(!read_only);
    m_editor->setAcceptRichText(m_accept_rich_text);
    m_editor->setPlaceholderText(m_hint);
    if (!read_only) {
        connect(m_editor.data(), &GrowingTextEdit::textChanged,
                this, &QuTextEdit::widgetTextChanged);
        // QTextEdit::textChanged - Called *whenever* contents changed.
        // http://doc.qt.io/qt-5.7/qtextedit.html#textChanged
        // Note: no data sent along with the signal

        m_focus_watcher = new FocusWatcher(m_editor.data());
        connect(m_focus_watcher.data(), &FocusWatcher::focusChanged,
                this, &QuTextEdit::widgetFocusChanged);
    }
    setFromField();
    return QPointer<QWidget>(m_editor);
}


FieldRefPtrList QuTextEdit::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuTextEdit::widgetTextChanged()
{
    if (m_ignore_widget_signal) {
        // Note: ignore it now, not after the timer! Otherwise impossible
        // (well, harder) to synchronize flag distinguishing "real" and
        // "internally generated" changes with events at the far end of the
        // timer.
        return;
    }
    m_timer->start(WRITE_DELAY_MS);  // will restart if already timing
    // ... goes to textChanged()
}


void QuTextEdit::textChanged()
{
    if (!m_editor) {
        return;
    }
    QString text = m_editor->toPlainText();
    if (m_accept_rich_text && !text.isEmpty()) {
        text = m_editor->toHtml();
    }
    // ... That forces the text to empty (rather than a bunch of HTML
    // representing nothing) if there is no real text.
    bool changed = m_fieldref->setValue(text, this);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuTextEdit::fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator)
{
    if (!m_editor) {
        return;
    }
    uifunc::setPropertyMissing(m_editor, fieldref->missingInput());
    if (originator != this) {
        // In this case we don't want to block all signals, because the
        // GrowingTextEdit widget needs internal signals. However, we want
        // to stop signal receipt by our own textChanged() slot. So we
        // can set a flag:
        m_ignore_widget_signal = true;
        if (m_accept_rich_text) {
            m_editor->setHtml(fieldref->valueString());
        } else {
            m_editor->setPlainText(fieldref->valueString());
        }
        m_ignore_widget_signal = false;
    }
}


void QuTextEdit::widgetFocusChanged(bool in)
{
    // If focus is leaving the widget, save the field value.
    if (in || !m_editor) {
        return;
    }
    bool change_pending = m_timer->isActive();
    m_timer->stop();  // just in case it's running
    if (change_pending) {
        textChanged();  // maybe
    }
}
