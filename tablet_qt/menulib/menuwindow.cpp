/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#define OFFER_LAYOUT_DEBUG_BUTTON
#define SHOW_TASK_TIMING

#include "menuwindow.h"
#include <QDebug>
#include <QListWidget>
#include <QListWidgetItem>
#include <QMessageBox>
#include <QVBoxLayout>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
#include "lib/filefunc.h"
#include "lib/layoutdumper.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menulib/menuheader.h"
#include "questionnairelib/questionnaire.h"
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

    loadStyleSheet();
    setObjectName(CssConst::MENU_WINDOW_OUTER_OBJECT);

    QVBoxLayout* dummy_layout = new QVBoxLayout();
    dummy_layout->setContentsMargins(UiConst::NO_MARGINS);
    setLayout(dummy_layout);
    QWidget* dummy_widget = new QWidget();
    dummy_widget->setObjectName(CssConst::MENU_WINDOW_BACKGROUND);
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

    // ------------------------------------------------------------------------
    // Code removed from build()
    // ------------------------------------------------------------------------

    /*

    // You can't call setLayout() twice. So clear the existing layout if
    // rebuilding.
    // And removeAllChildWidgets() doesn't work for layouts. Therefore, thanks
    // to excellent deletion handling by Qt:
    if (m_p_header) {
        // qDebug() << Q_FUNC_INFO << "Deleting old MenuHeader with this ="
        //          << m_p_header.data();
        m_p_header->disconnect();  // prevent double signalling
        m_p_header->deleteLater();  // later, in case it's currently calling us
        m_p_header.clear();
    }
    if (m_p_listwidget) {
        m_p_listwidget->disconnect();  // prevent double signalling
        m_p_listwidget->deleteLater();
        m_p_listwidget.clear();
    }
    // UiFunc::clearLayout(m_mainlayout);

    */

    // ------------------------------------------------------------------------
    // Header
    // ------------------------------------------------------------------------

#ifdef OFFER_LAYOUT_DEBUG_BUTTON
    bool offer_debug_layout = true;
#else
    bool offer_debug_layout = false;
#endif
    m_p_header = new MenuHeader(this, m_app, m_top, m_title, m_icon,
                                offer_debug_layout);
    m_mainlayout->addWidget(m_p_header);

    // header to us
    connect(m_p_header, &MenuHeader::backClicked,
            this, &MenuWindow::finished,
            Qt::UniqueConnection);  // unique as we may rebuild... safer.
    connect(m_p_header, &MenuHeader::debugLayout,
            this, &MenuWindow::debugLayout,
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
    connect(m_p_header, &MenuHeader::finishFlagClicked,
            this, &MenuWindow::toggleFinishFlag,
            Qt::UniqueConnection);

    // us to header
    connect(this, &MenuWindow::offerAdd,
            m_p_header, &MenuHeader::offerAdd,
            Qt::UniqueConnection);
    connect(this, &MenuWindow::offerView,
            m_p_header, &MenuHeader::offerView,
            Qt::UniqueConnection);
    connect(this, &MenuWindow::offerEditDelete,
            m_p_header, &MenuHeader::offerEditDelete,
            Qt::UniqueConnection);
    connect(this, &MenuWindow::offerFinishFlag,
            m_p_header, &MenuHeader::offerFinishFlag,
            Qt::UniqueConnection);

    // ------------------------------------------------------------------------
    // List
    // ------------------------------------------------------------------------

#ifdef USE_HFW_LISTWIDGET
    m_p_listwidget = new HeightForWidthListWidget();
#else
    m_p_listwidget = new QListWidget();
#endif
    m_mainlayout->addWidget(m_p_listwidget);

    connect(m_p_listwidget, &QListWidget::itemSelectionChanged,
            this, &MenuWindow::menuItemSelectionChanged,
            Qt::UniqueConnection);
    connect(m_p_listwidget, &QListWidget::itemClicked,
            this, &MenuWindow::menuItemClicked,
            Qt::UniqueConnection);
    connect(m_p_listwidget, &QListWidget::itemActivated,
            this, &MenuWindow::menuItemClicked,
            Qt::UniqueConnection);

    // ------------------------------------------------------------------------
    // Other signals
    // ------------------------------------------------------------------------

    // Do this in main constructor, not build(), since build() can be called
    // from this signal!
    connect(&m_app, &CamcopsApp::lockStateChanged,
            this, &MenuWindow::lockStateChanged,
            Qt::UniqueConnection);
}


void MenuWindow::setIcon(const QString& icon)
{
    m_icon = icon;
}


void MenuWindow::loadStyleSheet()
{
    setStyleSheet(m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_MENU));
}


void MenuWindow::reloadStyleSheet()
{
    loadStyleSheet();
    UiFunc::repolish(this);
}


void MenuWindow::build()
{
    // qDebug() << Q_FUNC_INFO;

    m_p_listwidget->clear();

    // Method 1: QListWidget, QListWidgetItem
    // Size hints: https://forum.qt.io/topic/17481/easiest-way-to-have-a-simple-list-with-custom-items/4
    // Note that the widgets call setSizePolicy.
    bool preselected = false;
    int app_selected_patient_id = m_app.selectedPatientId();
    for (int i = 0; i < m_items.size(); ++i) {
        MenuItem item = m_items.at(i);
        QWidget* row = item.rowWidget(m_app);
        QListWidgetItem* listitem = new QListWidgetItem("", m_p_listwidget);
        listitem->setData(Qt::UserRole, QVariant(i));
#ifdef USE_HFW_LISTWIDGET
        listitem->setSizeHint(m_p_listwidget->widgetSizeHint(row));
#else
        listitem->setSizeHint(row->sizeHint());
#endif
        m_p_listwidget->setItemWidget(listitem, row);
        if (item.patient()
                && item.patient()->id() == app_selected_patient_id) {
            // qDebug() << Q_FUNC_INFO << "preselecting patient at index" << i;
            // m_p_listwidget->item(i)->setSelected(true);
            m_p_listwidget->setCurrentItem(listitem);

            // DO NOT just setSelected(); that leaves currentItem() and the
            // (obviously) visible selection out of sync, which leads to
            // major user errors.
            // setCurrentItem() will also select the item;
            // http://doc.qt.io/qt-5/qlistwidget.html#setCurrentItem

            preselected = true;
        }
    }
    menuItemSelectionChanged();
    if (preselected) {
        m_p_listwidget->setFocus();
        // http://stackoverflow.com/questions/23065151/how-to-set-an-item-in-a-qlistwidget-as-initially-highlighted
    }

    // Method 2: QListView, QStandardItemModel, custom delegate
    // http://doc.qt.io/qt-5/qlistview.html
    // argh!

    // Stretch not necessary, even if the menu is short (the QListWidget
    // seems to handle this fine).
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


void MenuWindow::menuItemSelectionChanged()
{
    // Set the verb buttons

    // WHAT'S BEEN CHOSEN?
    QList<QListWidgetItem*> selected_items = m_p_listwidget->selectedItems();
    if (selected_items.isEmpty()) {
        // qDebug() << Q_FUNC_INFO << "Nothing selected";
        emit offerView(false);
        emit offerEditDelete(false, false);
        emit offerFinishFlag(false);
        return;
    }
    QListWidgetItem* item = selected_items.at(0);
    QVariant v = item->data(Qt::UserRole);
    int i = v.toInt();
    if (i < 0 || i >= m_items.size()) {
        qWarning() << Q_FUNC_INFO << "Selection out of range:" << i
                   << "(vector size:" << m_items.size() << ")";
        return;
    }
    MenuItem& m = m_items[i];
    // qInfo() << "Selected:" << m;
    TaskPtr task = m.task();
    PatientPtr patient = m.patient();

    if (task) {
        // Notify the header (with its verb buttons). Leave it selected.
        emit offerView(true);
        emit offerEditDelete(task->isEditable(), true);
        emit offerFinishFlag(task->isAnonymous());
    } else if (patient) {
        bool selected = true;
        emit offerView(selected);
        emit offerEditDelete(selected, selected);
        emit offerFinishFlag(true);
    } else {
        emit offerView(false);
        emit offerEditDelete(false, false);
        // ... in case a task was selected before
        emit offerFinishFlag(false);
    }

    // The finish-flag button allows the user to mark either PATIENTS or
    // ANONYMOUS TASKS for removal from the tablet even if the user picks
    // the "copy" style of upload.
}


void MenuWindow::menuItemClicked(QListWidgetItem *item)
{
    // Act on a click

    QVariant v = item->data(Qt::UserRole);
    int i = v.toInt();
    if (i < 0 || i >= m_items.size()) {
        qWarning() << Q_FUNC_INFO << "Selection out of range:" << i
                   << "(vector size:" << m_items.size() << ")";
        return;
    }
    MenuItem& m = m_items[i];
    qInfo() << "Clicked:" << m;
    TaskPtr task = m.task();
    PatientPtr patient = m.patient();

    if (task) {
        // Nothing to do; see menuItemSelectionChanged()
    } else if (patient) {
        qDebug() << Q_FUNC_INFO << "non-null patient pointer =" << patient
                 << ", this =" << this;
        bool selected = false;
        if (m_app.selectedPatientId() == patient->id()) {
            // Clicked on currently selected patient; deselect it.
            m_app.setSelectedPatient(DbConst::NONEXISTENT_PK);
            m_p_listwidget->clearSelection();
        } else {
            selected = true;
            m_app.setSelectedPatient(patient->id());
        }
        emit offerView(selected);
        emit offerEditDelete(selected, selected);
    } else {
        // ACT ON IT. And clear the selection.
        m.act(m_app);
        m_p_listwidget->clearSelection();
    }
}


void MenuWindow::lockStateChanged(CamcopsApp::LockState lockstate)
{
    Q_UNUSED(lockstate)
    // mark as unused; http://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
    qDebug() << Q_FUNC_INFO;
    build();  // calls down to derived class
}


void MenuWindow::viewItem()
{
    viewTask();
}


void MenuWindow::viewTask()
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
            OpenableWidget* widget = task->editor(true);
            m_app.open(widget, task);
        }
        break;
    case QMessageBox::Ok:  // detail
        {
            qInfo() << "View detail:" << instance_title;
            QString detail = task->detail();
#ifdef SHOW_TASK_TIMING
            detail += QString("<br><br>Editing time: <b>%1</b> s")
                    .arg(task->editingTimeSeconds());
#endif
            UiFunc::alert(detail, instance_title, true);  // with scrolling
        }
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
    editTask();
}


void MenuWindow::editTask()
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
    editTaskConfirmed(task);
}


void MenuWindow::editTaskConfirmed(const TaskPtr& task)
{
    QString instance_title = task->instanceTitle();
    qInfo() << "Edit:" << instance_title;
    OpenableWidget* widget = task->editor(false);
    connectQuestionnaireToTask(widget, task.data());
    m_app.open(widget, task, true);
}


void MenuWindow::connectQuestionnaireToTask(OpenableWidget* widget, Task* task)
{
    if (!widget || !task) {
        qWarning() << Q_FUNC_INFO << "null widget or null task";
        return;
    }
    Questionnaire* questionnaire = dynamic_cast<Questionnaire*>(widget);
    if (!questionnaire) {
        return;
    }
    connect(questionnaire, &Questionnaire::editStarted,
            task, &Task::editStarted);
    connect(questionnaire, &Questionnaire::editFinished,
            task, &Task::editFinished);
}


void MenuWindow::deleteItem()
{
    deleteTask();
}


void MenuWindow::deleteTask()
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


void MenuWindow::toggleFinishFlag()
{
    TaskPtr task = currentTask();
    PatientPtr patient = currentPatient();
    if (task && task->isAnonymous()) {
        task->toggleMoveOffTablet();
        build();
    } else if (patient) {
        patient->toggleMoveOffTablet();
        build();
    }
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


PatientPtr MenuWindow::currentPatient() const
{
    int index = currentIndex();
    qDebug() << Q_FUNC_INFO << "index =" << index;
    if (index == BAD_INDEX) {
        qDebug() << "... bad index";
        return PatientPtr(nullptr);
    }
    const MenuItem& item = m_items[index];
    return item.patient();
}


void MenuWindow::debugLayout()
{
    LayoutDumper::dumpWidgetHierarchy(this);
}
