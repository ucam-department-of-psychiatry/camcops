#pragma once
#include "db/fieldref.h"
#include "quelement.h"

class QDoubleSpinBox;


class QuSpinBoxDouble : public QuElement
{
    // Offers a text editing box with spinbox controls, for floating-point
    // entry.

    Q_OBJECT
public:
    QuSpinBoxDouble(FieldRefPtr fieldref, double minimum, double maximum,
                    int decimals = 2);
protected:
    void setFromField();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
protected slots:
    void widgetValueChanged(double value);
    // void widgetValueChangedString(const QString& text);
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    FieldRefPtr m_fieldref;
    double m_minimum;
    double m_maximum;
    int m_decimals;
    QPointer<QDoubleSpinBox> m_spinbox;
};
