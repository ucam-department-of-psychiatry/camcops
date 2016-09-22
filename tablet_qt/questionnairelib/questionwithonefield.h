#pragma once
#include <QString>
#include "lib/fieldref.h"


class QuestionWithOneField
{
    // Encapsulates a question (text) with a FieldRef.
    // Used by e.g. QuMCQGrid; QuMultipleResponse.

public:
    QuestionWithOneField(const QString& question, FieldRefPtr fieldref);
    QuestionWithOneField(FieldRefPtr fieldref, const QString& question);
    // ... for convenience
    QString question() const;
    QString text() const;  // synonym
    FieldRefPtr fieldref() const;
protected:
    QString m_question;
    FieldRefPtr m_fieldref;
};
