#include "qumcqgriddoublesignaller.h"
#include "db/fieldref.h"
#include "questionnairelib/qumcqgriddouble.h"


QuMCQGridDoubleSignaller::QuMCQGridDoubleSignaller(QuMCQGridDouble* recipient,
                                                   int question_index,
                                                   bool first_field) :
    m_recipient(recipient),
    m_question_index(question_index),
    m_first_field(first_field)
{
}


void QuMCQGridDoubleSignaller::valueChanged(const FieldRef* fieldref)
{
    m_recipient->fieldValueChanged(m_question_index, m_first_field, fieldref);
}
