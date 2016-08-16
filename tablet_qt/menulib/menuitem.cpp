#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPushButton>
#include <QScopedPointer>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "menuitem.h"
#include "menuwindow.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menu/singletaskmenu.h"
#include "tasklib/taskfactory.h"  // for TaskPtr

const int STRETCH_3COL_TASKNAME = 2;
const int STRETCH_3COL_TIMESTAMP = 2;
const int STRETCH_3COL_SUMMARY = 6;

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
                   const QString& icon) :
    m_title(title)
{
    setDefaults();
    m_func = func;
    m_icon = icon;
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


MenuItem::MenuItem(const TaskMenuItem& taskmenuitem, CamcopsApp& app)
    // m_title: below
{
    setDefaults();
    m_task_tablename = taskmenuitem.tablename;

    TaskPtr task = app.factory()->create(m_task_tablename);
    if (task == nullptr) {
        m_title = tr("UNKNOWN TASK") + ": " + taskmenuitem.tablename;
        m_implemented = false;
        return;
    }
    m_title = task->menutitle();
    m_subtitle = task->menusubtitle();
    m_crippled = task->isCrippled();
    if (task->isAnonymous()) {
        m_icon = ICON_ANONYMOUS;
    }
}


MenuItem::MenuItem(TaskPtr p_task, bool task_shows_taskname) :
    m_title("?")
{
    setDefaults();
    m_p_task = p_task;
    m_task_shows_taskname = task_shows_taskname;
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
    m_p_menuproxy = MenuProxyPtr(nullptr);
    m_task_tablename = "";
    m_p_task = TaskPtr(nullptr);
}


QString MenuItem::title()
{
    return m_title;
}


TaskPtr MenuItem::task()
{
    return m_p_task;
}


QWidget* MenuItem::getRowWidget(CamcopsApp& app) const
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
            QLabel* taskname = new QLabel(m_p_task->shortname());
            taskname->setObjectName(complete
                                    ? "task_item_taskname_complete"
                                    : "task_item_taskname_incomplete");
            QSizePolicy spTaskname(QSizePolicy::Preferred,
                                   QSizePolicy::Preferred);
            spTaskname.setHorizontalStretch(STRETCH_3COL_TASKNAME);
            taskname->setSizePolicy(spTaskname);
            rowlayout->addWidget(taskname);
        }
        // Timestamp
        QLabel* timestamp = new QLabel(m_p_task->whenCreatedMenuFormat());
        timestamp->setObjectName(complete ? "task_item_timestamp_complete"
                                          : "task_item_timestamp_incomplete");
        QSizePolicy spTimestamp(QSizePolicy::Preferred,
                                QSizePolicy::Preferred);
        spTimestamp.setHorizontalStretch(threecols ? STRETCH_3COL_TIMESTAMP
                                                   : STRETCH_2COL_TIMESTAMP);
        timestamp->setSizePolicy(spTimestamp);
        rowlayout->addWidget(timestamp);
        // Summary
        QLabel* summary = new QLabel(m_p_task->getSummaryWithCompleteSuffix());
        summary->setObjectName(complete ? "task_item_summary_complete"
                                        : "task_item_summary_incomplete");
        QSizePolicy spSummary(QSizePolicy::Preferred, QSizePolicy::Preferred);
        spSummary.setHorizontalStretch(threecols ? STRETCH_3COL_SUMMARY
                                                 : STRETCH_2COL_SUMMARY);
        timestamp->setSizePolicy(spSummary);
        rowlayout->addWidget(summary);
        // *** stretch not quite right yet, but close
    } else {
        // --------------------------------------------------------------------
        // Conventional menu item
        // --------------------------------------------------------------------

        // Icon
        if (!m_label_only) {  // Labels go full-left
            if (!m_icon.isEmpty()) {
                QLabel* icon = iconWidget(m_icon, row);
                rowlayout->addWidget(icon);
            } else if (m_chain) {
                QLabel* icon = iconWidget(ICON_CHAIN, row);
                rowlayout->addWidget(icon);
            } else {
                rowlayout->addWidget(blankIcon(row));
            }
        }

        // Title/subtitle
        QVBoxLayout* textlayout = new QVBoxLayout();

        QLabel* title = new QLabel(m_title);
        title->setObjectName("menu_item_title");
        textlayout->addWidget(title);
        if (!m_subtitle.isEmpty()) {
            QLabel* subtitle = new QLabel(m_subtitle);
            subtitle->setObjectName("menu_item_subtitle");
            textlayout->addWidget(subtitle);
        }
        rowlayout->addLayout(textlayout);

        // Arrow on right
        if (m_arrow_on_right) {
            rowlayout->addStretch();
            QLabel* iconLabel = iconWidget(ICON_HASCHILD, nullptr, false);
            rowlayout->addWidget(iconLabel);
        }

        // Background colour, via stylesheets
        if (m_label_only) {
            row->setObjectName("label_only");
        } else if (!m_implemented) {
            row->setObjectName("not_implemented");
        } else if (m_unsupported) {
            row->setObjectName("unsupported");
        } else if (m_not_if_locked && app.locked()) {
            row->setObjectName("locked");
        } else if (m_needs_privilege && !app.privileged()) {
            row->setObjectName("needs_privilege");
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

    // *** deal with different ways of displaying tasks
    // (taskname/date/detail, or date/detail)
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
        alert(tr("Not implemented yet!"));
        return;
    }
    if (m_unsupported) {
        alert(tr("Not supported on this platform!"));
        return;
    }
    if (m_needs_privilege && !app.privileged()) {
        alert(tr("You must set Privileged Mode first"));
        return;
    }
    if (m_not_if_locked && app.locked()) {
        alert(tr("Can’t perform this action when CamCOPS is locked"),
              tr("Unlock first"));
        return;
    }
    // ========================================================================
    // Ways to act
    // ========================================================================
    if (m_p_menuproxy) {
        MenuWindow* pWindow = m_p_menuproxy->create(app);
        app.pushScreen(pWindow);
        return;
    }
    if (m_func) {
        m_func();
        return;
    }
    if (!m_task_tablename.isEmpty()) {
        SingleTaskMenu* pWindow = new SingleTaskMenu(m_task_tablename, app);
        app.pushScreen(pWindow);
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
