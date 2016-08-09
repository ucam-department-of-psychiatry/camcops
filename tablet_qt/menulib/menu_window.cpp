#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QPushButton>
#include <QScrollArea>
#include <QVBoxLayout>
#include "menu_window.h"
#include "common/ui_constants.h"
#include "lib/filefunc.h"
// #include "lib/uifunc.h"


MenuWindow::MenuWindow(CamcopsApp& app, bool top) :
    QWidget(),
    m_app(app),
    m_top(top)
{
}


MenuWindow::~MenuWindow()
{
}


void MenuWindow::buildMenu()
{
    qDebug() << "MenuWindow::buildMenu()";

    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    //QScrollArea* scrollarea = new QScrollArea();
    //mainlayout->addWidget(scrollarea);

    if (!m_top) {
        QPushButton* back = new QPushButton("back", this);
        mainlayout->addWidget(back);
        connect(back, &QPushButton::clicked,
                this, &MenuWindow::backClicked);
    }

    QListWidget* listwidget = new QListWidget();
    mainlayout->addWidget(listwidget);
    QSize rowheight = QSize(0, ICONSIZE + 20);  // ***
    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
        item.validate();
        QWidget* row = item.getRowWidget();
        QListWidgetItem* listitem = new QListWidgetItem("", listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
        listitem->setSizeHint(rowheight);
        listwidget->setItemWidget(listitem, row);
        listwidget->setStyleSheet(textfileContents(CSS_CAMCOPS_MENU));
    }
    connect(listwidget, &QListWidget::itemClicked,
            this, &MenuWindow::menuItemClicked);
}


void MenuWindow::backClicked()
{
    m_app.popScreen();
}


void MenuWindow::menuItemClicked(QListWidgetItem* item)
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
    m.act(m_app);
}
