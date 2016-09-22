#pragma once
#include <QIntValidator>


class StrictIntValidator : public QIntValidator
{
    // Validates an integer being typed in.
    // Checks the characters against the specified bottom/top (min/max) values.

    Q_OBJECT
public:
    StrictIntValidator(int bottom, int top, QObject* parent = nullptr);
    virtual QValidator::State validate(QString& s, int& pos) const override;
};
