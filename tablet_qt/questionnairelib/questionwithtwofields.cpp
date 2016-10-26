#include "questionwithtwofields.h"


QuestionWithTwoFields::QuestionWithTwoFields(const QString& question,
                                             FieldRefPtr first_field,
                                             FieldRefPtr second_field) :
    m_question(question),
    m_first_field(first_field),
    m_second_field(second_field)
{
    Q_ASSERT(!m_question.isEmpty());
    Q_ASSERT(!m_first_field.isNull());
    Q_ASSERT(!m_second_field.isNull());
}


QString QuestionWithTwoFields::question() const
{
    return m_question;
}


FieldRefPtr QuestionWithTwoFields::firstFieldRef() const
{
    return m_first_field;
}


FieldRefPtr QuestionWithTwoFields::secondFieldRef() const
{
    return m_second_field;
}


FieldRefPtr QuestionWithTwoFields::fieldref(bool first_field) const
{
    return first_field ? m_first_field : m_second_field;
}
