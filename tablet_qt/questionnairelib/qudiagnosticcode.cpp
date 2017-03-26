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

#include "qudiagnosticcode.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QVBoxLayout>
#include <QWidget>
#include "common/camcopsapp.h"
#include "common/cssconst.h"
#include "diagnosis/diagnosticcodeset.h"
#include "lib/slowguiguard.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/basewidget.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/diagnosticcodeselector.h"
#include "widgets/labelwordwrapwide.h"


QuDiagnosticCode::QuDiagnosticCode(DiagnosticCodeSetPtr codeset,
                                   FieldRefPtr fieldref_code,
                                   FieldRefPtr fieldref_description) :
    m_codeset(codeset),
    m_fieldref_code(fieldref_code),
    m_fieldref_description(fieldref_description),
    m_offer_null_button(true),
    m_missing_indicator(nullptr),
    m_label_code(nullptr),
    m_label_description(nullptr),
    m_widget(nullptr)
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


QuDiagnosticCode* QuDiagnosticCode::setOfferNullButton(bool offer_null_button)
{
    m_offer_null_button = offer_null_button;
    return this;
}


void QuDiagnosticCode::setFromField()
{
    fieldValueChanged(m_fieldref_code.data());
}


QPointer<QWidget> QuDiagnosticCode::makeWidget(Questionnaire* questionnaire)
{
    m_questionnaire = questionnaire;
    bool read_only = questionnaire->readOnly();

    m_missing_indicator = uifunc::iconWidget(
                uifunc::iconFilename(uiconst::ICON_WARNING));
    m_label_code = new LabelWordWrapWide();
    m_label_code->setObjectName(cssconst::DIAGNOSTIC_CODE);
    m_label_description = new LabelWordWrapWide();
    m_label_description->setObjectName(cssconst::DIAGNOSTIC_CODE);

    QHBoxLayout* textlayout = new QHBoxLayout();
    textlayout->setContentsMargins(uiconst::NO_MARGINS);
    textlayout->addWidget(m_missing_indicator);
    textlayout->addWidget(m_label_code);
    textlayout->addWidget(m_label_description);
    textlayout->addStretch();

    ClickableLabelWordWrapWide* button = new ClickableLabelWordWrapWide(tr("Set diagnosis"));
    button->setObjectName(cssconst::DIAGNOSTIC_CODE);
    // button->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    button->setEnabled(!read_only);
    if (!read_only) {
        connect(button, &ClickableLabelWordWrapWide::clicked,
                this, &QuDiagnosticCode::setButtonClicked);
    }

    QHBoxLayout* buttonlayout = new QHBoxLayout();
    buttonlayout->setContentsMargins(uiconst::NO_MARGINS);
    buttonlayout->addWidget(button);

    if (m_offer_null_button) {
        ClickableLabelWordWrapWide* null_button = new ClickableLabelWordWrapWide(tr("Clear"));
        null_button->setObjectName(cssconst::DIAGNOSTIC_CODE);
        // null_button->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
        null_button->setEnabled(!read_only);
        if (!read_only) {
            connect(null_button, &ClickableLabelWordWrapWide::clicked,
                    this, &QuDiagnosticCode::nullButtonClicked);
        }
        buttonlayout->addWidget(null_button);
    }
    buttonlayout->addStretch();

    QVBoxLayout* toplayout = new QVBoxLayout();
    toplayout->setContentsMargins(uiconst::NO_MARGINS);
    toplayout->addLayout(textlayout);
    toplayout->addLayout(buttonlayout);

    m_widget = new BaseWidget();
    // m_widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    // ... no, keep as the default of expandingFixedHFWPolicy()?
    m_widget->setLayout(toplayout);

    setFromField();

    return m_widget;
}


void QuDiagnosticCode::setButtonClicked()
{
    if (!m_questionnaire) {
        qWarning() << Q_FUNC_INFO << "m_questionnaire missing";
        return;
    }
    SlowGuiGuard guard = m_questionnaire->app().getSlowGuiGuard();
    QString code = m_fieldref_code->valueString();
    QModelIndex selected = m_codeset->firstMatchCode(code);
    QString stylesheet = m_questionnaire->getSubstitutedCss(
                uiconst::CSS_CAMCOPS_DIAGNOSTIC_CODE);
    DiagnosticCodeSelector* selector = new DiagnosticCodeSelector(
                stylesheet, m_codeset, selected);
    connect(selector, &DiagnosticCodeSelector::codeChanged,
            this, &QuDiagnosticCode::widgetChangedCode);
    m_questionnaire->openSubWidget(selector);
}


void QuDiagnosticCode::nullButtonClicked()
{
    QVariant nullvalue;
    m_fieldref_description->setValue(nullvalue);  // BEFORE setting code, as:
    m_fieldref_code->setValue(nullvalue);  // ... will trigger valueChanged
    emit elementValueChanged();
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
    m_widget->updateGeometry();
}
