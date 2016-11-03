#include "qumcqgridsignaller.h"
#include "db/fieldref.h"
#include "questionnairelib/qumcqgrid.h"


QuMCQGridSignaller::QuMCQGridSignaller(QuMCQGrid* recipient,
                                       int question_index) :
    m_recipient(recipient),
    m_question_index(question_index)
{
}


void QuMCQGridSignaller::valueChanged(const FieldRef* fieldref)
{
    m_recipient->fieldValueChanged(m_question_index, fieldref);
}
