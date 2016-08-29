#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class QSpinBox;


class QuSpinBoxInteger : public QuElement
{
    Q_OBJECT
public:
    QuSpinBoxInteger(FieldRefPtr fieldref, int minimum, int maximum);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void widgetValueChanged(int value);
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    FieldRefPtr m_fieldref;
    int m_minimum;
    int m_maximum;
    QPointer<QSpinBox> m_spinbox;
};
