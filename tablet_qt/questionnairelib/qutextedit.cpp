#include "qutextedit.h"
#include "lib/uifunc.h"
#include "widgets/growingtextedit.h"
#include "questionnaire.h"


QuTextEdit::QuTextEdit(FieldRefPtr fieldref, bool accept_rich_text) :
    m_fieldref(fieldref),
    m_accept_rich_text(accept_rich_text),
    m_hint("text"),
    m_editor(nullptr),
    m_ignore_widget_signal(false)
{
    Q_ASSERT(m_fieldref);
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
                this, &QuTextEdit::textChanged);
        // Note: no data sent along with the signal
    }
    setFromField();
    return QPointer<QWidget>(m_editor);
}


FieldRefPtrList QuTextEdit::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuTextEdit::textChanged()
{
    if (!m_editor || m_ignore_widget_signal) {
        return;
    }
    QString text = m_accept_rich_text ? m_editor->toHtml()
                                      : m_editor->toPlainText();
    m_fieldref->setValue(text, this);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuTextEdit::fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator)
{
    if (!m_editor) {
        return;
    }
    UiFunc::setPropertyMissing(m_editor, fieldref->missingInput());
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
