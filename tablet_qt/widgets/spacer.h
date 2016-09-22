#pragma once
#include <QWidget>


class Spacer : public QWidget
{
    // Spacer of fixed size.

    Q_OBJECT
public:
    Spacer(QWidget* parent = nullptr);
    virtual QSize sizeHint() const;
};
