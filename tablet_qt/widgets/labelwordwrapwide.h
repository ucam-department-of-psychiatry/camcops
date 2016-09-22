#pragma once
#include "widgets/clickablelabel.h"


class LabelWordWrapWide : public ClickableLabel
{
    // Label that word-wraps its text, and prefers to be wide rather than tall.

    Q_OBJECT
public:
    explicit LabelWordWrapWide(const QString& text = "",
                               QWidget* parent = nullptr);
    void resizeEvent(QResizeEvent* event);
};
