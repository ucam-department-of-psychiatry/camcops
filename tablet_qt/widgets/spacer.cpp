#include "spacer.h"
#include "common/uiconstants.h"

Spacer::Spacer(QWidget* parent) :
    QWidget(parent)
{
    QSizePolicy sp(QSizePolicy::Fixed, QSizePolicy::Fixed);
    setSizePolicy(sp);
}


QSize Spacer::sizeHint() const
{
    return QSize(SPACE, SPACE);
}
