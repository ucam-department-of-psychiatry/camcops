#include "quspacer.h"
#include <QSizePolicy>
#include <QWidget>
#include "widgets/spacer.h"


QuSpacer::QuSpacer()
{
}


QPointer<QWidget> QuSpacer::makeWidget(Questionnaire* questionnaire)
{
    Q_UNUSED(questionnaire)
    return QPointer<QWidget>(new Spacer());
}
