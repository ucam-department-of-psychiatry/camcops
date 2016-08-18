#pragma once
#include <QWidget>


class Spacer : public QWidget
{
    Q_OBJECT
public:
    Spacer(QWidget* parent = nullptr);
    virtual QSize sizeHint() const;
};
