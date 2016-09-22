#pragma once
#include <QWidget>

class QString;


class HorizontalLine : public QWidget
{
    // Simple horizontal line (taking its colour from a stylesheet).

    Q_OBJECT
public:
    HorizontalLine(int width, QWidget* parent = nullptr);
    // Colour: use CSS "background-color"
    void paintEvent(QPaintEvent*);
};
