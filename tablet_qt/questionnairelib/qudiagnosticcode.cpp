#include "qudiagnosticcode.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QVBoxLayout>
#include <QWidget>
#include "lib/uifunc.h"
#include "widgets/diagnosticcodeselector.h"
#include "questionnaire.h"


QuDiagnosticCode::QuDiagnosticCode(QSharedPointer<DiagnosticCodeSet> codeset,
                                   FieldRefPtr fieldref_code,
                                   FieldRefPtr fieldref_description) :
    m_codeset(codeset),
    m_fieldref_code(fieldref_code),
    m_fieldref_description(fieldref_description),
    m_missing_indicator(nullptr),
    m_label_code(nullptr),
    m_label_description(nullptr)
{
    Q_ASSERT(m_codeset);
    Q_ASSERT(m_fieldref_code);
    Q_ASSERT(m_fieldref_description);
    connect(m_fieldref_code.data(), &FieldRef::valueChanged,
            this, &QuDiagnosticCode::fieldValueChanged);
    connect(m_fieldref_code.data(), &FieldRef::mandatoryChanged,
            this, &QuDiagnosticCode::fieldValueChanged);
    // We don't track changes to the description; they're assumed to follow
    // code changes directly.
    // NOTE that this method violates the "DRY" principle but is for clinical
    // margin-of-safety reasons so that a record of what the user saw when they
    // picked the diagnosis is preserved with the code.
}


void QuDiagnosticCode::setFromField()
{
    fieldValueChanged(m_fieldref_code.data());
}


QPointer<QWidget> QuDiagnosticCode::makeWidget(Questionnaire* questionnaire)
{
    m_questionnaire = questionnaire;
    bool read_only = questionnaire->readOnly();

    m_missing_indicator = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_WARNING));
    m_label_code = new QLabel();
    m_label_description = new QLabel();

    QHBoxLayout* textlayout = new QHBoxLayout();
    textlayout->addWidget(m_missing_indicator);
    textlayout->addWidget(m_label_code);
    textlayout->addWidget(m_label_description);
    textlayout->addStretch();

    QPushButton* button = new QPushButton(tr("Set diagnosis"));
    button->setEnabled(!read_only);
    if (!read_only) {
        connect(button, &QPushButton::clicked,
                this, &QuDiagnosticCode::setButtonClicked);
    }

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->addLayout(textlayout);
    toplayout->addWidget(button);

    QWidget* widget = new QWidget();
    widget->setLayout(toplayout);

    return widget;
}


void QuDiagnosticCode::setButtonClicked()
{
    if (!m_questionnaire) {
        qWarning() << Q_FUNC_INFO << "m_questionnaire missing";
        return;
    }
    QString code = m_fieldref_code->valueString();
    int selected_index = m_codeset->firstIndexFromCode(code);
    QString stylesheet = m_questionnaire->getSubstitutedCss(
                UiConst::CSS_CAMCOPS_DIAGNOSTIC_CODE);
    DiagnosticCodeSelector* selector = new DiagnosticCodeSelector(
                stylesheet, m_codeset, selected_index);
    connect(selector, &DiagnosticCodeSelector::codeChanged,
            this, &QuDiagnosticCode::widgetChangedCode);
    m_questionnaire->openSubWidget(selector);
}


FieldRefPtrList QuDiagnosticCode::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref_code,
                           m_fieldref_description};
}


void QuDiagnosticCode::widgetChangedCode(const QString& code,
                                         const QString& description)
{
    m_fieldref_description->setValue(description);  // BEFORE setting code, as:
    m_fieldref_code->setValue(code);  // ... will trigger valueChanged
    emit elementValueChanged();
}


void QuDiagnosticCode::fieldValueChanged(const FieldRef* fieldref_code)
{
    if (m_missing_indicator) {
        m_missing_indicator->setVisible(fieldref_code->missingInput());
    }
    if (m_label_code) {
        m_label_code->setText(fieldref_code->valueString());
    }
    if (m_label_description) {
        m_label_description->setText(m_fieldref_description->valueString());
    }
}
