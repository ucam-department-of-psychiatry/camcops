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

#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "db/fieldref.h"
#include "questionnairelib/quelement.h"

class DiagnosticCodeSet;
class LabelWordWrapWide;
class QLabel;
class QPushButton;
class QWidget;


class QuDiagnosticCode : public QuElement
{
    // Allows tree browsing and search of diagnostic codes from a structured
    // classification system.

    Q_OBJECT
public:
    QuDiagnosticCode(DiagnosticCodeSetPtr codeset,
                     FieldRefPtr fieldref_code,
                     FieldRefPtr fieldref_description);
    QuDiagnosticCode* setOfferNullButton(bool offer_null_button);
protected:
    virtual void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    virtual void setButtonClicked();
    virtual void nullButtonClicked();
    virtual void widgetChangedCode(const QString& code,
                                   const QString& description);
    virtual void fieldValueChanged(const FieldRef* fieldref_code);
protected:
    DiagnosticCodeSetPtr m_codeset;
    FieldRefPtr m_fieldref_code;
    FieldRefPtr m_fieldref_description;
    bool m_offer_null_button;

    QPointer<Questionnaire> m_questionnaire;
    QPointer<QLabel> m_missing_indicator;
    QPointer<LabelWordWrapWide> m_label_code;
    QPointer<LabelWordWrapWide> m_label_description;
    QPointer<QWidget> m_widget;
};
