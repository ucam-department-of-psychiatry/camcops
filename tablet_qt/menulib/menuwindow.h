#pragma once
#include <QListWidgetItem>
#include <QMainWindow>
#include <QWidget>
#include "common/camcopsapp.h"
#include "menulib/menuitem.h"


class MenuWindow : public QWidget
{
    Q_OBJECT

public:
    MenuWindow(CamcopsApp& app, bool top = false);
    ~MenuWindow();
    void buildMenu();  // call after m_items is set up

public Q_SLOTS:
    void backClicked();
    void menuItemClicked(QListWidgetItem* item);

protected:
    CamcopsApp& m_app;
    bool m_top;
    QVector<MenuItem> m_items;
    QListWidget* m_p_listwidget;
};
