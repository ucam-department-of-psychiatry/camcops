#pragma once
#include "qulineedit.h"


class QuLineEditInteger : public QuLineEdit
{
    // Offers a one-line text editor, for an integer.

    Q_OBJECT
public:
    QuLineEditInteger(FieldRefPtr fieldref, bool allow_empty = true);
    QuLineEditInteger(FieldRefPtr fieldref, int minimum, int maximum,
                      bool allow_empty = true);
    QuLineEditInteger* setStrictValidator(bool strict);
protected:
    virtual void extraLineEditCreation(QLineEdit* editor) override;
protected:
    virtual void setDefaultHint();
protected:
    int m_minimum;
    int m_maximum;
    bool m_allow_empty;
    bool m_strict_validator;
};
