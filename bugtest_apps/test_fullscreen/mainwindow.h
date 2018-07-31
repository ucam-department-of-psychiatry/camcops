#pragma once

#include <QPointer>
#include <QMainWindow>
#include "displaywidget.h"

class QStackedWidget;


class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget* parent = nullptr);
    ~MainWindow() = default;
    void openWidget(DisplayWidget* dw);

public slots:
    void closeTopWidget();

private:
    // For layout reasons (not part of this test application), we maintain a
    // visible and a hidden stack (because QStackedWidget asks its invisible
    // children for layout information, which can mess up layouts for our
    // purposes).
    QPointer<QStackedWidget> m_p_visible_stack;
    QPointer<QStackedWidget> m_p_hidden_stack;
};
