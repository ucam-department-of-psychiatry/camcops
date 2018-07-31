#pragma once

#include <QString>
#include <QWidget>


class DisplayWidget : public QWidget
{
    Q_OBJECT
public:
    DisplayWidget(const QString& text, bool fullscreen, QWidget* parent = nullptr);
    void mousePressEvent(QMouseEvent* event) override;
    void keyPressEvent(QKeyEvent* event) override;
public:
    QString m_text;
    bool m_fullscreen;
signals:
    void pleaseClose();
};
