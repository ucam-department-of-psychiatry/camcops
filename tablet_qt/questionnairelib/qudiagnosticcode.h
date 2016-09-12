#pragma once
#include <QPointer>
#include <QSharedPointer>
#include "lib/fieldref.h"
#include "quelement.h"

class DiagnosticCodeSet;
class QLabel;
class QPushButton;


class QuDiagnosticCode : public QuElement
{
    Q_OBJECT
public:
    QuDiagnosticCode(QSharedPointer<DiagnosticCodeSet> codeset,
                     FieldRefPtr fieldref_code,
                     FieldRefPtr fieldref_description);
    virtual void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    virtual void setButtonClicked();
    virtual void widgetChangedCode(const QString& code,
                                   const QString& description);
    virtual void fieldValueChanged(const FieldRef* fieldref_code);
protected:
    QSharedPointer<DiagnosticCodeSet> m_codeset;
    FieldRefPtr m_fieldref_code;
    FieldRefPtr m_fieldref_description;
    QPointer<Questionnaire> m_questionnaire;
    QPointer<QLabel> m_missing_indicator;
    QPointer<QLabel> m_label_code;
    QPointer<QLabel> m_label_description;
};
