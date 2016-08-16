#include "menuwindow.h"
#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QVBoxLayout>
#include "menuheader.h"
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "tasklib/task.h"


MenuWindow::MenuWindow(CamcopsApp& app, const QString& title,
                       const QString& icon, bool top) :
    QWidget(),
    m_app(app),
    m_title(title),
    m_subtitle(""),
    m_icon(icon),
    m_top(top),
    m_mainlayout(new QVBoxLayout()),
    m_p_header(nullptr),
    m_p_listwidget(nullptr)
{
    /*
    For no clear reason, I have been unable to set the background colour
    of the widget that goes inside the QStackedLayout, either by class name
    or via setObjectName(), or with setAutoFillBackground(true).

    However, it works perfectly well to set the  background colour of inner
    widgets. So instead of this:

        QStackedLayout (main app)
            QWidget (MainWindow or Questionnaire)  <-- can't set bg colour
                m_mainlayout
                    widgets of interest

    it seems we have to do this:

        QStackedLayout (main app)
            QWidget (MainWindow or Questionnaire)
                dummy_layout
                    dummy_widget  <-- set background colour of this one
                        m_mainlayout
                            widgets of interest
    */

    setStyleSheet(textfileContents(CSS_CAMCOPS_MENU));
    setObjectName("menu_window_outer_object");

    QVBoxLayout* dummy_layout = new QVBoxLayout();
    setLayout(dummy_layout);
    QWidget* dummy_widget = new QWidget();
    dummy_widget->setObjectName("menu_window_background");
    dummy_layout->addWidget(dummy_widget);

    dummy_widget->setLayout(m_mainlayout);

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
    // qDebug() << "MenuWindow::buildMenu()";

    // You can't call setLayout() twice. So clear the existing layout if
    // rebuilding.
    // And removeAllChildWidgets() doesn't work for layouts. Therefore, thanks
    // to excellent deletion handling by Qt:
    if (m_p_header) {
        m_p_header->deleteLater();  // later, in case it's currently calling us
    }
    if (m_p_listwidget) {
        m_p_listwidget->deleteLater();
    }

    m_p_header = new MenuHeader(this, m_app, m_top, m_title, m_icon);
    m_mainlayout->addWidget(m_p_header);
    connect(m_p_header, &MenuHeader::backClicked,
            &m_app, &CamcopsApp::popScreen,
            Qt::UniqueConnection);  // unique as we may rebuild... safer.
    connect(this, &MenuWindow::offerViewEditDelete,
            m_p_header, &MenuHeader::offerViewEditDelete,
            Qt::UniqueConnection);

    // Method 1: QListWidget, QListWidgetItem
    // Size hints: https://forum.qt.io/topic/17481/easiest-way-to-have-a-simple-list-with-custom-items/4
    // Note that the widgets call setSizePolicy.
    m_p_listwidget = new QListWidget();
    m_mainlayout->addWidget(m_p_listwidget);
    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
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

    // Stretch not necessary, even if the menu is short (the QListWidget
    // seems to handle this fine).

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
    qDebug() << "Selected:" << m.title();

    if (m.task()) {
        // Notify the header (with its verb buttons). Leave it selected.
        emit offerViewEditDelete(true, m.task()->isEditable(), true);
    }
    else {
        // ACT ON IT. And clear the selection.
        emit offerViewEditDelete(false, false, false);
        // ... in case a task was selected before
        m.act(m_app);
        m_p_listwidget->clearSelection();
    }
}


void MenuWindow::lockStateChanged(LockState lockstate)
{
    (void)lockstate;  // mark as unused; http://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
    buildMenu();
}
