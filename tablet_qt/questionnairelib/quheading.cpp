#include "quheading.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "questionnaire.h"
#include "widgets/labelwordwrapwide.h"


QuHeading::QuHeading(const QString& text) :
    QuText(text)
{
}


QuHeading::QuHeading(FieldRefPtr fieldref) :
    QuText(fieldref)
{
}


QPointer<QWidget> QuHeading::makeWidget(Questionnaire* questionnaire)
{
    QString text;
    if (m_fieldref && m_fieldref->valid()) {
        text = m_fieldref->valueString();
    } else {
        text = m_text;
    }
    LabelWordWrapWide* label = new LabelWordWrapWide(text);
    int fontsize = questionnaire->fontSizePt(UiConst::FontSize::Heading);
    QString colour = "";
    QString css = UiFunc::textCSS(fontsize, true, false, colour);
    label->setStyleSheet(css);
    return QPointer<QWidget>(label);
}
