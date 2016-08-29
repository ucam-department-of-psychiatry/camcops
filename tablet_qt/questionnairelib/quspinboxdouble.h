#pragma once
#include "lib/fieldref.h"
#include "quelement.h"

class QDoubleSpinBox;


class QuSpinBoxDouble : public QuElement
{
    Q_OBJECT
public:
    QuSpinBoxDouble(FieldRefPtr fieldref, double minimum, double maximum,
                    int decimals = 2);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void widgetValueChanged(double value);
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    FieldRefPtr m_fieldref;
    double m_minimum;
    double m_maximum;
    int m_decimals;
    QPointer<QDoubleSpinBox> m_spinbox;
};
