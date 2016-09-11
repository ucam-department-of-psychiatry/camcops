#include "qulineedit.h"
#include <QLineEdit>
#include <QValidator>
#include "lib/uifunc.h"
#include "widgets/focuswatcher.h"
#include "questionnaire.h"


QuLineEdit::QuLineEdit(FieldRefPtr fieldref) :
    m_fieldref(fieldref),
    m_focus_watcher(nullptr)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuLineEdit::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuLineEdit::fieldValueChanged);
}


QuLineEdit* QuLineEdit::setHint(const QString& hint)
{
    m_hint = hint;
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
    bool read_only = questionnaire->readOnly();
    m_editor = new QLineEdit();
    m_editor->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    m_editor->setEnabled(!read_only);
    m_editor->setPlaceholderText(m_hint);
    extraLineEditCreation(m_editor.data());  // allow subclasses to modify
    if (!read_only) {
        connect(m_editor.data(), &QLineEdit::editingFinished,
                this, &QuLineEdit::widgetTextChanged);
        // QLineEdit::textChanged: emitted whenever text changed.
        // QLineEdit::textEdited: NOT emitted when the widget's value is set
        //      programmatically.
        // QLineEdit::editingFinished: emitted when Return/Enter is pressed,
        //      or the editor loses focus. In the former case, only fires if
        //      validation is passed.

        // So, if we lose focus without validation, how are we going to revert
        // to something sensible?
        m_focus_watcher = new FocusWatcher(m_editor.data());
        connect(m_focus_watcher.data(), &FocusWatcher::focusChanged,
                this, &QuLineEdit::widgetFocusChanged);
    }
    setFromField();
    return QPointer<QWidget>(m_editor);
}


void QuLineEdit::extraLineEditCreation(QLineEdit* editor)
{
    (void)editor;
}


FieldRefPtrList QuLineEdit::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuLineEdit::widgetTextChanged()
{
    if (!m_editor) {
        return;
    }
    // qDebug() << "Validator:" << m_editor->validator();
    QString text = m_editor->text();
    m_fieldref->setValue(text, this);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuLineEdit::fieldValueChanged(const FieldRef* fieldref,
                                   const QObject* originator)
{
    if (!m_editor) {
        return;
    }
    UiFunc::setPropertyMissing(m_editor, fieldref->missingInput());
    if (originator != this) {
        // No need to block signals; see above.
        m_editor->setText(fieldref->valueString());
    }
}


void QuLineEdit::widgetFocusChanged(bool in)
{
    // If focus is leaving the widget, and its state is duff, restore from the
    // field value.
    if (in || !m_editor) {
        return;
    }
    const QValidator* validator = m_editor->validator();
    if (!validator) {
        return;
    }
    QString text = m_editor->text();
    int pos = 0;
    if (validator->validate(text, pos) != QValidator::Acceptable) {
        // Something duff
        setFromField();
    }
}
