#include "menuwindow.h"
#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QPushButton>
#include <QScrollArea>
#include <QVBoxLayout>
#include "menuheader.h"
#include "common/ui_constants.h"
#include "lib/filefunc.h"
// #include "lib/uifunc.h"


MenuWindow::MenuWindow(CamcopsApp& app, bool top) :
    QWidget(),
    m_app(app),
    m_top(top),
    m_p_listwidget(nullptr)
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
    setStyleSheet(textfileContents(CSS_CAMCOPS_MENU));

    //QScrollArea* scrollarea = new QScrollArea();
    //mainlayout->addWidget(scrollarea);

    MenuHeader* header = new MenuHeader(this, m_app, m_top, "sometitle");
    mainlayout->addWidget(header);
    connect(header, &MenuHeader::back,
            this, &MenuWindow::backClicked);

    m_p_listwidget = new QListWidget();
    mainlayout->addWidget(m_p_listwidget);
    QSize rowheight = QSize(0, ICONSIZE + 20);  // ***
    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
        item.validate();
        QWidget* row = item.getRowWidget();
        QListWidgetItem* listitem = new QListWidgetItem("", m_p_listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
        listitem->setSizeHint(rowheight);
        m_p_listwidget->setItemWidget(listitem, row);
    }
    connect(m_p_listwidget, &QListWidget::itemClicked,
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
        qWarning() << "Selection out of range:" << i
                   << "(vector size:" << m_items.size() << ")";
        return;
    }
    MenuItem& m = m_items[i];
    qDebug() << "Selected:" << m.m_title;

    // ACT ON IT.
    m.act(m_app);

    m_p_listwidget->clearSelection();
}
