#pragma once
#include "widgets/clickablelabel.h"


class LabelWordWrapWide : public ClickableLabel
{
    Q_OBJECT
public:
    explicit LabelWordWrapWide(const QString& text = "",
                               QWidget* parent = nullptr);
    void resizeEvent(QResizeEvent* event);
};
