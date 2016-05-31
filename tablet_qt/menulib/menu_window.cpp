#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QVBoxLayout>
#include "menu_window.h"
#include "common/ui_constants.h"
#include "lib/uifunc.h"

MenuWindow::MenuWindow(QWidget *parent)
    : QMainWindow(parent)
{
}

MenuWindow::~MenuWindow()
{

}

void MenuWindow::show()
{
    QVBoxLayout *mainlayout = new QVBoxLayout;
    QListWidget *listwidget = new QListWidget();
    QSize rowheight = QSize(0, ICONSIZE + 20);  // ***

    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
        item.validate();
        QWidget* row = item.get_row_widget();
        QListWidgetItem *listitem = new QListWidgetItem("", listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
        listitem->setSizeHint(rowheight);
        listwidget->setItemWidget(listitem, row);
    }
    connect(listwidget, SIGNAL(itemClicked(QListWidgetItem*)),
            this, SLOT(onClicked(QListWidgetItem*)));
    mainlayout->addWidget(listwidget);

    // http://stackoverflow.com/questions/1508939/qt-layout-on-qmainwindow
    QWidget *mainwidget = new QWidget();
    mainwidget->setLayout(mainlayout);
    setCentralWidget(mainwidget);

    QMainWindow::show();
}

void MenuWindow::onClicked(QListWidgetItem* item)
{
    // WHAT'S BEEN CHOSEN?
    QVariant v = item->data(Qt::UserRole);
    int i = v.toInt();
    if (i < 0 || i > m_items.size()) {
        qDebug() << "Selection out of range:" << i
                 << "(vector size:" << m_items.size() << ")";
        return;
    }
    MenuItem& m = m_items[i];
    qDebug() << "Selected:" << m.m_title;

    // ACT ON IT.
    m.act();
}
