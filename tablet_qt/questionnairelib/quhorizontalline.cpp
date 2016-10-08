#include "quhorizontalline.h"
#include "common/uiconstants.h"
#include "widgets/horizontalline.h"


QuHorizontalLine::QuHorizontalLine()
{
}


QPointer<QWidget> QuHorizontalLine::makeWidget(Questionnaire* questionnaire)
{
    Q_UNUSED(questionnaire)
    HorizontalLine* horizline = new HorizontalLine(
                UiConst::QUESTIONNAIRE_HLINE_WIDTH);
    horizline->setObjectName("questionnaire_horizontal_line");
    return QPointer<QWidget>(horizline);
}
