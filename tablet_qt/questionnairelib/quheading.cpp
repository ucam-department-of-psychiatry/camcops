#include "quheading.h"
#include "common/uiconstants.h"
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
    QString text = m_fieldref ? m_fieldref->getString() : m_text;
    LabelWordWrapWide* label = new LabelWordWrapWide(text);
    int fontsize = questionnaire->fontSizePt(FontSize::Heading);
    QString colour = "";
    QString css = textCSS(fontsize, true, false, colour);
    label->setStyleSheet(css);
    return QPointer<QWidget>(label);
}
