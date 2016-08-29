#pragma once
#include "qulineedit.h"


class QuLineEditDouble : public QuLineEdit
{
    Q_OBJECT
public:
    QuLineEditDouble(FieldRefPtr fieldref);
    QuLineEditDouble(FieldRefPtr fieldref, double minimum, double maximum,
                     int decimals);
    QuLineEditDouble* setStrictValidator(bool strict);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    double m_minimum;
    double m_maximum;
    int m_decimals;
    bool m_strict_validator;
};
