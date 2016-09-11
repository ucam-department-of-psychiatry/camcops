#include "spacer.h"
#include "common/uiconstants.h"

Spacer::Spacer(QWidget* parent) :
    QWidget(parent)
{
    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
}


QSize Spacer::sizeHint() const
{
    return QSize(UiConst::SPACE, UiConst::SPACE);
}
