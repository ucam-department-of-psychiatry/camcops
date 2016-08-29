#pragma once
#include <QIntValidator>


class StrictIntValidator : public QIntValidator
{
    Q_OBJECT
public:
    StrictIntValidator(int bottom, int top, QObject* parent = nullptr);
    virtual QValidator::State validate(QString& s, int& pos) const override;
};
