#include "quhorizontalline.h"
#include "common/cssconst.h"
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
    horizline->setObjectName(CssConst::QUESTIONNAIRE_HORIZONTAL_LINE);
    return QPointer<QWidget>(horizline);
}
