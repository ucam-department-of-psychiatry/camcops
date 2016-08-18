#include "quhorizontalline.h"
#include <QFrame>
#include "common/uiconstants.h"


QuHorizontalLine::QuHorizontalLine()
{
}


QPointer<QWidget> QuHorizontalLine::makeWidget(Questionnaire* questionnaire)
{
    (void)questionnaire;
    QFrame* horizline = new QFrame();
    horizline->setObjectName("questionnaire_horizontal_line");
    horizline->setFrameShape(QFrame::HLine);
    horizline->setFrameShadow(QFrame::Plain);
    horizline->setLineWidth(QUESTIONNAIRE_HLINE_WIDTH);
    return QPointer<QWidget>(horizline);
}
