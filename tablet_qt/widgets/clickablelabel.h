#pragma once
#include <QLabel>


class ClickableLabel : public QLabel
{
    Q_OBJECT
public:
    ClickableLabel(const QString& text = "", QWidget* parent = nullptr);
    void setClickable(bool clickable);
signals:
    void clicked();
protected:
    void mousePressEvent(QMouseEvent *event);
protected:
    bool m_clickable;
};
