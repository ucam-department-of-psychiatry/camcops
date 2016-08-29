#pragma once
#include <QDoubleValidator>


class StrictDoubleValidator : public QDoubleValidator
{
    // http://stackoverflow.com/questions/19571033/allow-entry-in-qlineedit-only-within-range-of-qdoublevalidator
    // ... but that doesn't work properly (it prohibits valid things on the
    // way to success).
    Q_OBJECT
public:
    StrictDoubleValidator(double bottom, double top, int decimals,
                          QObject* parent = nullptr);
    virtual QValidator::State validate(QString& s, int& pos) const override;
};
