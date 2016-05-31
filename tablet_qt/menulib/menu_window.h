#pragma once
#include <QListWidgetItem>
#include <QMainWindow>
#include "menulib/menu_item.h"


class MenuWindow : public QMainWindow
{
    Q_OBJECT

public:
    MenuWindow(QWidget *parent = 0);
    ~MenuWindow();
    void show();

public Q_SLOTS:
    void onClicked(QListWidgetItem* item);

protected:
    QVector<MenuItem> m_items;
};
