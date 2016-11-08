#include "menuitem.h"
#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPushButton>
#include <QScopedPointer>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
#include "lib/datetimefunc.h"  // for SHORT_DATETIME_FORMAT
#include "lib/idpolicy.h"
#include "lib/uifunc.h"
#include "menu/choosepatientmenu.h"
#include "menu/singletaskmenu.h"
#include "menulib/htmlinfowindow.h"
#include "menulib/menuwindow.h"
#include "tasklib/taskfactory.h"
// #include "widgets/heightforwidthlayoutcontainer.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/openablewidget.h"

const int STRETCH_3COL_TASKNAME = 1;
const int STRETCH_3COL_TIMESTAMP = 2;
const int STRETCH_3COL_SUMMARY = 7;

const int STRETCH_2COL_TIMESTAMP = 2;
const int STRETCH_2COL_SUMMARY = 8;


MenuItem::MenuItem() :
    m_title("?")
{
    setDefaults();
}


MenuItem::MenuItem(const QString& title) :
    m_title(title)
{
    // this constructor used for placeholders for not-implemented stuff
    setDefaults();
    m_implemented = false;
}


MenuItem::MenuItem(const QString& title, const MenuItem::ActionFunction& func,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_func = func;
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(const QString& title,
                   const MenuItem::OpenableWidgetMaker& func,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_openable_widget_maker = func;
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(MenuProxyPtr p_menuproxy, CamcopsApp& app)
    // m_title: below
{
    setDefaults();
    m_p_menuproxy = p_menuproxy;

    QScopedPointer<MenuWindow> mw(m_p_menuproxy->create(app));
    m_title = mw->title();
    m_subtitle = mw->subtitle();
    m_icon = mw->icon();
}


MenuItem::MenuItem(const ChoosePatientMenuItem& choose_patient,
                   CamcopsApp& app)
{
    // We do some more of the work for the client, since "choose patient"
    // appears on lots of menus.
    Q_UNUSED(choose_patient);  // it's just a marker object
    // You can't call another constructor directly, so...

    setDefaults();
    m_p_menuproxy = MenuProxyPtr(new MenuProxy<ChoosePatientMenu>);

    QScopedPointer<MenuWindow> mw(m_p_menuproxy->create(app));
    m_title = mw->title();
    m_subtitle = mw->subtitle();
    m_icon = mw->icon();
}


MenuItem::MenuItem(const TaskMenuItem& taskmenuitem, CamcopsApp& app)
    // m_title: below
{
    setDefaults();
    m_task_tablename = taskmenuitem.tablename;

    TaskPtr task = app.taskFactory()->create(m_task_tablename);
    if (task == nullptr) {
        m_title = tr("UNKNOWN TASK") + ": " + taskmenuitem.tablename;
        m_implemented = false;
        return;
    }
    m_title = task->menutitle();
    m_subtitle = task->menusubtitle();
    m_crippled = task->isCrippled();
    if (task->isAnonymous()) {
        m_icon = UiFunc::iconFilename(UiConst::ICON_ANONYMOUS);
    }
}


MenuItem::MenuItem(const QString& title, const HtmlMenuItem& htmlmenuitem,
                   const QString& icon, const QString& subtitle) :
    m_title(title)
{
    setDefaults();
    m_html = htmlmenuitem;  // extra
    m_icon = icon;
    m_subtitle = subtitle;
}


MenuItem::MenuItem(TaskPtr p_task, bool task_shows_taskname) :
    m_title("?")
{
    setDefaults();
    m_p_task = p_task;
    m_task_shows_taskname = task_shows_taskname;
}


MenuItem::MenuItem(PatientPtr p_patient)
{
    setDefaults();
    m_p_patient = p_patient;
}


void MenuItem::setDefaults()
{
    // Not the most efficient, but saves lots of duplication

    // not m_title
    m_subtitle = "";
    m_icon = "";

    m_arrow_on_right = false;
    m_chain = false;
    m_copyright_details_pending = false;
    m_crippled = false;
    m_implemented = true;
    m_label_only = false;
    m_needs_privilege = false;
    m_not_if_locked = false;
    m_unsupported = false;

    m_func = nullptr;
    m_openable_widget_maker = nullptr;
    m_p_menuproxy = MenuProxyPtr(nullptr);
    m_task_tablename = "";
    m_p_task = TaskPtr(nullptr);
    m_p_patient = PatientPtr(nullptr);
}


QString MenuItem::title() const
{
    if (m_p_task) {
        return m_p_task->instanceTitle();
    }
    return m_title;
}


TaskPtr MenuItem::task() const
{
    return m_p_task;
}


PatientPtr MenuItem::patient() const
{
    return m_p_patient;
}


QWidget* MenuItem::rowWidget(CamcopsApp& app) const
{
    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();
    row->setLayout(rowlayout);

    if (m_p_task) {
        // --------------------------------------------------------------------
        // Task instance
        // --------------------------------------------------------------------
        // Stretch: http://stackoverflow.com/questions/14561516/qt-qhboxlayout-percentage-size

        bool complete = m_p_task->isComplete();
        const bool& threecols = m_task_shows_taskname;

        // Taskname
        if (m_task_shows_taskname) {
            QLabel* taskname = new LabelWordWrapWide(m_p_task->shortname());
            taskname->setObjectName(complete
                                    ? CssConst::TASK_ITEM_TASKNAME_COMPLETE
                                    : CssConst::TASK_ITEM_TASKNAME_INCOMPLETE);
            QSizePolicy spTaskname(QSizePolicy::Preferred,
                                   QSizePolicy::Preferred);
            spTaskname.setHorizontalStretch(STRETCH_3COL_TASKNAME);
            taskname->setSizePolicy(spTaskname);
            rowlayout->addWidget(taskname);
        }
        // Timestamp
        QLabel* timestamp = new LabelWordWrapWide(
            m_p_task->whenCreated().toString(DateTime::SHORT_DATETIME_FORMAT));
        timestamp->setObjectName(complete
                                 ? CssConst::TASK_ITEM_TIMESTAMP_COMPLETE
                                 : CssConst::TASK_ITEM_TIMESTAMP_INCOMPLETE);
        QSizePolicy spTimestamp(QSizePolicy::Preferred,
                                QSizePolicy::Preferred);
        spTimestamp.setHorizontalStretch(threecols ? STRETCH_3COL_TIMESTAMP
                                                   : STRETCH_2COL_TIMESTAMP);
        timestamp->setSizePolicy(spTimestamp);
        rowlayout->addWidget(timestamp);
        // Summary
        QLabel* summary = new LabelWordWrapWide(
                    m_p_task->summaryWithCompleteSuffix());
        summary->setObjectName(complete
                               ? CssConst::TASK_ITEM_SUMMARY_COMPLETE
                               : CssConst::TASK_ITEM_SUMMARY_INCOMPLETE);
        QSizePolicy spSummary(QSizePolicy::Preferred, QSizePolicy::Preferred);
        spSummary.setHorizontalStretch(threecols ? STRETCH_3COL_SUMMARY
                                                 : STRETCH_2COL_SUMMARY);
        summary->setSizePolicy(spSummary);
        rowlayout->addWidget(summary);

    } else if (m_p_patient) {
        // --------------------------------------------------------------------
        // Patient (for patient-choosing menu)
        // --------------------------------------------------------------------

        // Title/subtitle style
        QVBoxLayout* textlayout = new QVBoxLayout();

        QSizePolicy sp(QSizePolicy::Preferred, QSizePolicy::Preferred);

        LabelWordWrapWide* title = new LabelWordWrapWide(
                    QString("%1, %2")
                    .arg(m_p_patient->surname().toUpper())
                    .arg(m_p_patient->forename()));
        LabelWordWrapWide* subtitle1 = new LabelWordWrapWide(
                    QString("%1, %2y, DOB %3")
                    .arg(m_p_patient->sex())
                    .arg(m_p_patient->ageYears())
                    .arg(m_p_patient->dobText()));
        LabelWordWrapWide* subtitle2 = new LabelWordWrapWide(
                    m_p_patient->shortIdnumSummary());

        title->setObjectName(CssConst::MENU_ITEM_TITLE);
        subtitle1->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
        subtitle2->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
        title->setSizePolicy(sp);
        subtitle1->setSizePolicy(sp);
        subtitle2->setSizePolicy(sp);
        textlayout->addWidget(title);
        textlayout->addWidget(subtitle1);
        textlayout->addWidget(subtitle2);

        if (!m_p_patient->compliesWith(app.uploadPolicy())) {
            rowlayout->addWidget(UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_STOP)));
        } else if (!m_p_patient->compliesWith(app.finalizePolicy())) {
            rowlayout->addWidget(UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_WARNING)));
        } else {
            rowlayout->addWidget(UiFunc::blankIcon());
        }

        rowlayout->addLayout(textlayout);
        rowlayout->addStretch();

    } else {
        // --------------------------------------------------------------------
        // Conventional menu item
        // --------------------------------------------------------------------

        // Icon
        if (!m_label_only) {  // Labels go full-left
            if (!m_icon.isEmpty()) {
                QLabel* icon = UiFunc::iconWidget(m_icon, row);
                rowlayout->addWidget(icon);
            } else if (m_chain) {
                QLabel* icon = UiFunc::iconWidget(
                    UiFunc::iconFilename(UiConst::ICON_CHAIN), row);
                rowlayout->addWidget(icon);
            } else {
                rowlayout->addWidget(UiFunc::blankIcon(row));
            }
        }

        // Title/subtitle
        QVBoxLayout* textlayout = new QVBoxLayout();

        QLabel* title = new LabelWordWrapWide(m_title);
        title->setObjectName(CssConst::MENU_ITEM_TITLE);
        textlayout->addWidget(title);
        if (!m_subtitle.isEmpty()) {
            QLabel* subtitle = new LabelWordWrapWide(m_subtitle);
            subtitle->setObjectName(CssConst::MENU_ITEM_SUBTITLE);
            textlayout->addWidget(subtitle);
        }
        rowlayout->addLayout(textlayout);
        rowlayout->addStretch();

        // Arrow on right
        if (m_arrow_on_right) {
            QLabel* iconLabel = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_HASCHILD),
                nullptr, false);
            rowlayout->addWidget(iconLabel);
        }

        // Background colour, via stylesheets
        if (m_label_only) {
            row->setObjectName(CssConst::LABEL_ONLY);
        } else if (!m_implemented) {
            row->setObjectName(CssConst::NOT_IMPLEMENTED);
        } else if (m_unsupported) {
            row->setObjectName(CssConst::UNSUPPORTED);
        } else if (m_not_if_locked && app.locked()) {
            row->setObjectName(CssConst::LOCKED);
        } else if (m_needs_privilege && !app.privileged()) {
            row->setObjectName(CssConst::NEEDS_PRIVILEGE);
        }
        // ... but not for locked/needs privilege, as otherwise we'd need
        // to refresh the whole menu? Well, we could try it.
        // On Linux desktop, it's extremely fast.
    }

    // Size policy
    QSizePolicy size_policy(QSizePolicy::MinimumExpanding,  // horizontal
                            QSizePolicy::Fixed);  // vertical
    row->setSizePolicy(size_policy);

    return row;
}


void MenuItem::act(CamcopsApp& app) const
{
    // ========================================================================
    // Reasons to refuse
    // ========================================================================
    if (m_label_only) {
        // qDebug() << "Label-only row touched; ignored";
        return;
    }
    if (m_p_task) {
        // Handled via verb buttons instead.
        return;
    }
    if (!m_implemented) {
        UiFunc::alert(tr("Not implemented yet!"));
        return;
    }
    if (m_unsupported) {
        UiFunc::alert(tr("Not supported on this platform!"));
        return;
    }
    if (m_needs_privilege && !app.privileged()) {
        UiFunc::alert(tr("You must set Privileged Mode first"));
        return;
    }
    if (m_not_if_locked && app.locked()) {
        UiFunc::alert(tr("Can’t perform this action when CamCOPS is locked"),
                      tr("Unlock first"));
        return;
    }
    // ========================================================================
    // Ways to act
    // ========================================================================
    if (m_p_menuproxy) {
        MenuWindow* pWindow = m_p_menuproxy->create(app);
        app.open(pWindow);
        return;
    }
    if (m_func) {
        m_func();
        return;
    }
    if (m_openable_widget_maker) {
        OpenableWidget* widget = m_openable_widget_maker(app);
        app.open(widget);
        return;
    }
    if (!m_task_tablename.isEmpty()) {
        SingleTaskMenu* pWindow = new SingleTaskMenu(m_task_tablename, app);
        app.open(pWindow);
        return;
    }
    if (!m_html.filename.isEmpty()) {
        HtmlInfoWindow* pWindow = new HtmlInfoWindow(
            app, m_html.title, m_html.filename, m_html.icon, m_html.fullscreen);
        app.open(pWindow);
        return;
    }
    qWarning() << "Menu item selected but no action specified:"
               << m_title;
}


bool MenuItem::isImplemented() const
{
    return m_implemented;
}


MenuItem& MenuItem::setImplemented(bool implemented)
{
    m_implemented = implemented;
    return *this;
}


MenuItem& MenuItem::setLabelOnly(bool label_only)
{
    m_label_only = label_only;
    return *this;
}


MenuItem& MenuItem::setNeedsPrivilege(bool needs_privilege)
{
    m_needs_privilege = needs_privilege;
    if (needs_privilege) {
        m_not_if_locked = true;  // just for safety!
    }
    return *this;
}


MenuItem& MenuItem::setNotIfLocked(bool not_if_locked)
{
    m_not_if_locked = not_if_locked;
    return *this;
}


MenuItem& MenuItem::setUnsupported(bool unsupported)
{
    m_unsupported = unsupported;
    return *this;
}
