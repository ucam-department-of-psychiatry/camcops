#include "quspacer.h"
#include <QSizePolicy>
#include <QWidget>
#include "widgets/spacer.h"


QuSpacer::QuSpacer()
{
}


QPointer<QWidget> QuSpacer::makeWidget(Questionnaire* questionnaire)
{
    (void)questionnaire;
    return QPointer<QWidget>(new Spacer());
}
