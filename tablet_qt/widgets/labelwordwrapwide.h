#pragma once
#include <QLabel>


class LabelWordWrapWide : public QLabel
{
    Q_OBJECT
public:
    explicit LabelWordWrapWide(const QString& text = "",
                               QWidget* parent = nullptr);
    void resizeEvent(QResizeEvent* event);
};
