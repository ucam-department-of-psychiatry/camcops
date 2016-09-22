#pragma once
#include "qulineedit.h"


class QuLineEditInteger : public QuLineEdit
{
    // Offers a one-line text editor, for an integer.

    Q_OBJECT
public:
    QuLineEditInteger(FieldRefPtr fieldref);
    QuLineEditInteger(FieldRefPtr fieldref, int minimum, int maximum);
    QuLineEditInteger* setStrictValidator(bool strict);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    int m_minimum;
    int m_maximum;
    bool m_strict_validator;
};
