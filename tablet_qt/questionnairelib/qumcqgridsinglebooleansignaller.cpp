#include "qumcqgridsinglebooleansignaller.h"
#include "db/fieldref.h"
#include "questionnairelib/qumcqgridsingleboolean.h"


QuMCQGridSingleBooleanSignaller::QuMCQGridSingleBooleanSignaller(
        QuMCQGridSingleBoolean* recipient, int question_index) :
    m_recipient(recipient),
    m_question_index(question_index)
{
}


void QuMCQGridSingleBooleanSignaller::mcqFieldValueChanged(const FieldRef* fieldref)
{
    m_recipient->mcqFieldValueChanged(m_question_index, fieldref);
}


void QuMCQGridSingleBooleanSignaller::booleanFieldValueChanged(const FieldRef* fieldref)
{
    m_recipient->booleanFieldValueChanged(m_question_index, fieldref);
}
