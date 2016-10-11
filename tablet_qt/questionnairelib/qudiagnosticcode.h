#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "db/fieldref.h"
#include "quelement.h"

class DiagnosticCodeSet;
class QLabel;
class QPushButton;


class QuDiagnosticCode : public QuElement
{
    // Allows tree browsing and search of diagnostic codes from a structured
    // classification system.
    // *** Not yet implemented from Titanium version: "clear" button.

    Q_OBJECT
public:
    QuDiagnosticCode(QSharedPointer<DiagnosticCodeSet> codeset,
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
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    FieldRefPtr m_fieldref_code;
    FieldRefPtr m_fieldref_description;
    bool m_offer_null_button;

    QPointer<Questionnaire> m_questionnaire;
    QPointer<QLabel> m_missing_indicator;
    QPointer<QLabel> m_label_code;
    QPointer<QLabel> m_label_description;
};
