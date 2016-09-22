#include "mcqgridsubtitle.h"

McqGridSubtitle::McqGridSubtitle(int pos, const QString& string,
                                 bool repeat_options) :
    m_pos(pos),
    m_string(string),
    m_repeat_options(repeat_options)
{
}


int McqGridSubtitle::pos() const
{
    return m_pos;
}


QString McqGridSubtitle::string() const
{
    return m_string;
}


bool McqGridSubtitle::repeatOptions() const
{
    return m_repeat_options;
}
