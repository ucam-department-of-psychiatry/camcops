#pragma once
#include <QWidget>

class QString;


class VerticalLine : public QWidget
{
    // Simple vertical line (taking its colour from a stylesheet).

    Q_OBJECT
public:
    VerticalLine(int width, QWidget* parent = nullptr);
    // Colour: use CSS "background-color"
    void paintEvent(QPaintEvent*);
};
