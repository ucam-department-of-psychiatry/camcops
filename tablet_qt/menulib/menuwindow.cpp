#include "menuwindow.h"
#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QVBoxLayout>
#include "menuheader.h"
#include "common/uiconstants.h"
#include "lib/filefunc.h"
// #include "lib/uifunc.h"


MenuWindow::MenuWindow(CamcopsApp& app, const QString& title,
                       const QString& icon, bool top) :
    QWidget(),
    m_app(app),
    m_title(title),
    m_subtitle(""),
    m_icon(icon),
    m_top(top),
    m_offer_add_task(false),
    m_mainlayout(new QVBoxLayout()),
    m_p_header(nullptr),
    m_p_listwidget(nullptr)
{
    setStyleSheet(textfileContents(CSS_CAMCOPS_MENU));
    setLayout(m_mainlayout);
    // QListWidget objects scroll themselves.
    // But we want everything to scroll within a QScrollArea.
    // https://forum.qt.io/topic/2058/expanding-qlistview-within-qscrollarea/2
    // It turns out to be very fiddly, and it's also perfectly reasonable to
    // keep the menu header visible, and have scroll bars showing the position
    // within the list view (both for menus and questionnaires, I'd think).
    // So we'll stick with a simple layout.
}


MenuWindow::~MenuWindow()
{
}


void MenuWindow::buildMenu()
{
    qDebug() << "MenuWindow::buildMenu()";
    // You can't call setLayout() twice. So clear the existing layout if
    // rebuilding.
    // And removeAllChildWidgets() doesn't work for layouts. Therefore, thanks
    // to excellent deletion handling by Qt:
    delete m_p_header;
    delete m_p_listwidget;

    m_p_header = new MenuHeader(this, m_app, m_top, m_title, m_icon,
                                m_offer_add_task);
    m_mainlayout->addWidget(m_p_header);
    connect(m_p_header, &MenuHeader::back,
            this, &MenuWindow::backClicked,
            Qt::UniqueConnection);  // unique as we may rebuild... safer.
    connect(this, &MenuWindow::taskSelectionChanged,
            m_p_header, &MenuHeader::taskSelectionChanged,
            Qt::UniqueConnection);

    // Method 1: QListWidget, QListWidgetItem
    // Size hints: https://forum.qt.io/topic/17481/easiest-way-to-have-a-simple-list-with-custom-items/4
    // Note that the widgets call setSizePolicy.
    m_p_listwidget = new QListWidget();
    m_mainlayout->addWidget(m_p_listwidget);
    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
        item.validate();
        QWidget* row = item.getRowWidget(m_app);
        QListWidgetItem* listitem = new QListWidgetItem("", m_p_listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
        QSize rowsize = row->sizeHint();
        listitem->setSizeHint(rowsize);
        m_p_listwidget->setItemWidget(listitem, row);
    }
    connect(m_p_listwidget, &QListWidget::itemClicked,
            this, &MenuWindow::menuItemClicked,
            Qt::UniqueConnection);

    // Method 2: QListView, QStandardItemModel, custom delegate
    // http://doc.qt.io/qt-5/qlistview.html
    // argh!

    connect(&m_app, &CamcopsApp::lockStateChanged,
            this, &MenuWindow::lockStateChanged,
            Qt::UniqueConnection);
}


QString MenuWindow::title() const
{
    return m_title;
}


QString MenuWindow::subtitle() const
{
    return m_subtitle;
}


QString MenuWindow::icon() const
{
    return m_icon;
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

    if (m.m_p_task) {
        // Notify the header (with its verb buttons). Leave it selected.
        emit taskSelectionChanged(m.m_p_task.data());
    }
    else {
        // ACT ON IT. And clear the selection.
        emit taskSelectionChanged(nullptr);
        // ... in case a task was selected before
        m.act(m_app);
        m_p_listwidget->clearSelection();
    }
}


void MenuWindow::lockStateChanged(LockState lockstate)
{
    (void)lockstate;  // mark as unused; http://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
    qDebug() << "REBUILDING MENU ***";
    buildMenu();
}
