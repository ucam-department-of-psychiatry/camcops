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
    (void)questionnaire;
    QString text;
    if (m_fieldref && m_fieldref->valid()) {
        text = m_fieldref->valueString();
    } else {
        text = m_text;
    }
    LabelWordWrapWide* label = new LabelWordWrapWide(text);
    label->setObjectName("heading");
    return QPointer<QWidget>(label);
}
