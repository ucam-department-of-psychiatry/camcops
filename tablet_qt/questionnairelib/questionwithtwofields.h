#pragma once
#include <QString>
#include "db/fieldref.h"


class QuestionWithTwoFields
{
    // Encapsulates a question with two associated fields.
    // Used by e.g. QuMCQGridDouble.

public:
    QuestionWithTwoFields(const QString& question,
                          FieldRefPtr first_field,
                          FieldRefPtr second_field);
    QString question() const;
    FieldRefPtr firstFieldRef() const;
    FieldRefPtr secondFieldRef() const;
    FieldRefPtr fieldref(bool first_field) const;
protected:
    QString m_question;
    FieldRefPtr m_first_field;
    FieldRefPtr m_second_field;
};
