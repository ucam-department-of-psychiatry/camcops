#pragma once
#include "qulineedit.h"


class QuLineEditDouble : public QuLineEdit
{
    // Offers a one-line text editor, for a floating-point number.

    Q_OBJECT
public:
    QuLineEditDouble(FieldRefPtr fieldref, bool allow_empty = true);
    QuLineEditDouble(FieldRefPtr fieldref, double minimum, double maximum,
                     int decimals, bool allow_empty = true);
    QuLineEditDouble* setStrictValidator(bool strict);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    double m_minimum;
    double m_maximum;
    int m_decimals;
    bool m_allow_empty;
    bool m_strict_validator;
};
