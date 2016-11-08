#pragma once
#include <QDoubleValidator>


class StrictDoubleValidator : public QDoubleValidator
{
    // Validates a double (floating-point) being typed in.
    // Checks the characters against the specified bottom/top (min/max) values.

    // http://stackoverflow.com/questions/19571033/allow-entry-in-qlineedit-only-within-range-of-qdoublevalidator
    // ... but that doesn't work properly (it prohibits valid things on the
    // way to success).
    Q_OBJECT
public:
    StrictDoubleValidator(double bottom, double top, int decimals,
                          bool allow_empty = false, QObject* parent = nullptr);
    virtual QValidator::State validate(QString& s, int& pos) const override;
protected:
    bool m_allow_empty;
};
