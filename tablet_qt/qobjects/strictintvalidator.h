#pragma once
#include <QIntValidator>


class StrictIntValidator : public QIntValidator
{
    // Validates an integer being typed in.
    // Checks the characters against the specified bottom/top (min/max) values.

    Q_OBJECT
public:
    StrictIntValidator(int bottom, int top, bool allow_empty = false,
                       QObject* parent = nullptr);
    virtual QValidator::State validate(QString& s, int& pos) const override;
protected:
    bool m_allow_empty;
};


// What about validating a qulonglong = quint64 (unsigned 64-bit int), etc.?
// Normally we would use C++ templates, but you can't mix that with Q_OBJECT.
// So we have to faff a great deal to make StrictUInt64Validator (q.v.).
