#include "questionwithonefield.h"

QuestionWithOneField::QuestionWithOneField(const QString& question,
                                           FieldRefPtr fieldref) :
    m_question(question),
    m_fieldref(fieldref)
{
    Q_ASSERT(!m_question.isEmpty());
    Q_ASSERT(!m_fieldref.isNull());
}


QuestionWithOneField::QuestionWithOneField(FieldRefPtr fieldref,
                                           const QString& question) :
    m_question(question),
    m_fieldref(fieldref)
{
    Q_ASSERT(!m_question.isEmpty());
    Q_ASSERT(!m_fieldref.isNull());
}


QString QuestionWithOneField::question() const
{
    return m_question;
}


QString QuestionWithOneField::text() const
{
    return m_question;
}


FieldRefPtr QuestionWithOneField::fieldref() const
{
    return m_fieldref;
}
