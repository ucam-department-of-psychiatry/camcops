#include "menuwindow.h"
#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QMessageBox>
#include <QVBoxLayout>
#include "menuheader.h"
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "tasklib/task.h"

const int BAD_INDEX = -1;


MenuWindow::MenuWindow(CamcopsApp& app, const QString& title,
                       const QString& icon, bool top) :
    OpenableWidget(),
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

    setStyleSheet(m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_MENU));
    setObjectName("menu_window_outer_object");

    QVBoxLayout* dummy_layout = new QVBoxLayout();
    dummy_layout->setContentsMargins(UiConst::NO_MARGINS);
    setLayout(dummy_layout);
    QWidget* dummy_widget = new QWidget();
    dummy_widget->setObjectName("menu_window_background");
    dummy_layout->addWidget(dummy_widget);

    m_mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    dummy_widget->setLayout(m_mainlayout);

    // QListWidget objects scroll themselves.
    // But we want everything to scroll within a QScrollArea.
    // https://forum.qt.io/topic/2058/expanding-qlistview-within-qscrollarea/2
    // It turns out to be very fiddly, and it's also perfectly reasonable to
    // keep the menu header visible, and have scroll bars showing the position
    // within the list view (both for menus and questionnaires, I'd think).
    // So we'll stick with a simple layout.
}


void MenuWindow::build()
{
    // qDebug() << Q_FUNC_INFO;

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
            this, &MenuWindow::finished,
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
        QWidget* row = item.rowWidget(m_app);
        QListWidgetItem* listitem = new QListWidgetItem("", m_p_listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
        QSize rowsize = row->sizeHint();
        listitem->setSizeHint(rowsize);
        m_p_listwidget->setItemWidget(listitem, row);
    }
    connect(m_p_listwidget, &QListWidget::itemClicked,
            this, &MenuWindow::menuItemClicked,
            Qt::UniqueConnection);
    connect(m_p_header, &MenuHeader::viewClicked,
            this, &MenuWindow::viewItem,
            Qt::UniqueConnection);
    connect(m_p_header, &MenuHeader::editClicked,
            this, &MenuWindow::editItem,
            Qt::UniqueConnection);
    connect(m_p_header, &MenuHeader::deleteClicked,
            this, &MenuWindow::deleteItem,
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
    if (i < 0 || i >= m_items.size()) {
        qWarning() << Q_FUNC_INFO << "Selection out of range:" << i
                   << "(vector size:" << m_items.size() << ")";
        return;
    }
    MenuItem& m = m_items[i];
    qInfo() << "Selected:" << m.title();

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


void MenuWindow::lockStateChanged(CamcopsApp::LockState lockstate)
{
    (void)lockstate;  // mark as unused; http://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
    build();  // calls down to derived class
}


void MenuWindow::viewItem()
{
    // View a task, if one is selected.
    TaskPtr task = currentTask();
    if (!task) {
        return;
    }
    bool facsimile_available = task->isEditable();
    QString instance_title = task->instanceTitle();
    QMessageBox::StandardButtons buttons = (QMessageBox::Yes |
                                            QMessageBox::Ok |
                                            QMessageBox::Cancel);
    if (facsimile_available) {
        buttons |= QMessageBox::Open;
    }
    QMessageBox msgbox(QMessageBox::Question,  // icon
                       tr("View task"),  // title
                       tr("View in what format?"),  // text
                       buttons,  // buttons
                       this);  // parent
    msgbox.setButtonText(QMessageBox::Yes, tr("Summary"));
    msgbox.setButtonText(QMessageBox::Ok, tr("Detail"));
    msgbox.setButtonText(QMessageBox::Cancel, tr("Cancel"));
    if (facsimile_available) {
        msgbox.setButtonText(QMessageBox::Open, tr("Facsimile"));
    }
    int reply = msgbox.exec();
    switch (reply) {
    case QMessageBox::Open:  // facsimile
        if (facsimile_available) {
            qInfo() << "View as facsimile:" << instance_title;
            OpenableWidget* widget = task->editor(m_app, true);
            m_app.open(widget, task);
        }
        break;
    case QMessageBox::Ok:  // detail
        qInfo() << "View detail:" << instance_title;
        UiFunc::alert(task->detail(), instance_title);
        break;
    case QMessageBox::Yes:  // summary
        qInfo() << "View summary:" << instance_title;
        UiFunc::alert(task->summary(), instance_title);
        break;
    case QMessageBox::No:  // cancel
    default:
        break;
    }
}


void MenuWindow::editItem()
{
    // Edit a task, if one is selected and editable
    TaskPtr task = currentTask();
    if (!task || !task->isEditable()) {
        return;
    }
    QString instance_title = task->instanceTitle();
    QMessageBox msgbox(
        QMessageBox::Question,  // icon
        tr("Edit"),  // title
        tr("Edit this task?") + "\n\n" +  instance_title,  // text
        QMessageBox::Yes | QMessageBox::No,  // buttons
        this);  // parent
    msgbox.setButtonText(QMessageBox::Yes, tr("Yes, edit"));
    msgbox.setButtonText(QMessageBox::No, tr("No, cancel"));
    int reply = msgbox.exec();
    if (reply != QMessageBox::Yes) {
        return;
    }
    qInfo() << "Edit:" << instance_title;
    OpenableWidget* widget = task->editor(m_app);
    m_app.open(widget, task, true);
}


void MenuWindow::deleteItem()
{
    // Edit a task, if one is selected and editable
    TaskPtr task = currentTask();
    if (!task || !task->isEditable()) {
        return;
    }
    QString instance_title = task->instanceTitle();
    QMessageBox msgbox(
        QMessageBox::Warning,  // icon
        tr("Delete"),  // title
        tr("Delete this task?") + "\n\n" +  instance_title,  // text
        QMessageBox::Yes | QMessageBox::No,  // buttons
        this);  // parent
    msgbox.setButtonText(QMessageBox::Yes, tr("Yes, delete"));
    msgbox.setButtonText(QMessageBox::No, tr("No, cancel"));
    int reply = msgbox.exec();
    if (reply != QMessageBox::Yes) {
        return;
    }
    qInfo() << "Delete:" << instance_title;
    task->deleteFromDatabase();
    build();
}


int MenuWindow::currentIndex() const
{
    QListWidgetItem* item = m_p_listwidget->currentItem();
    if (!item) {
        return BAD_INDEX;
    }
    QVariant v = item->data(Qt::UserRole);
    int i = v.toInt();
    if (i >= m_items.size() || i <= -1) {
        // Out of bounds; coerce to -1
        return BAD_INDEX;
    }
    return i;
}


TaskPtr MenuWindow::currentTask() const
{
    int index = currentIndex();
    if (index == BAD_INDEX) {
        return TaskPtr(nullptr);
    }
    const MenuItem& item = m_items[index];
    return item.task();
}
