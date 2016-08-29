#include "quheading.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "questionnaire.h"
#include "widgets/labelwordwrapwide.h"


QuHeading::QuHeading(const QString& text) :
    QuText(text)
{
    m_fontsize = UiConst::FontSize::Heading;
    m_bold = true;
}


QuHeading::QuHeading(FieldRefPtr fieldref) :
    QuText(fieldref)
{
    m_fontsize = UiConst::FontSize::Heading;
    m_bold = true;
}
