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


const QColor COLOUR_LOCKED(255, 0, 0, 50);
const QColor COLOUR_NEEDS_PRIVILEGE(255, 255, 0, 100);


MenuItem::MenuItem(QWidget* parent) :
    m_p_parent(parent),
    m_title("?"),
    m_subtitle(""),
    m_icon(""),
    m_arrow_on_right(false),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),
    m_implemented(true),
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(nullptr),
    m_p_menuproxy(nullptr),
    m_task_tablename(""),
    m_p_task(nullptr)
{
}


MenuItem::MenuItem(const QString& title, QWidget* parent) :
    m_p_parent(parent),
    m_title(title),
    m_subtitle(""),
    m_icon(""),
    m_arrow_on_right(false),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),
    m_implemented(false),  // placeholder for not-implemented stuff
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(nullptr),
    m_p_menuproxy(nullptr),
    m_task_tablename(""),
    m_p_task(nullptr)
{
}


MenuItem::MenuItem(const QString& title, const MenuItem::ActionFunction& func,
                   const QString& icon, QWidget* parent) :
    m_p_parent(parent),
    m_title(title),
    m_subtitle(""),
    m_icon(icon),
    m_arrow_on_right(false),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),
    m_implemented(true),
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(func),
    m_p_menuproxy(nullptr),
    m_task_tablename(""),
    m_p_task(nullptr)
{
}


MenuItem::MenuItem(MenuProxyPtr p_menuproxy,
                   CamcopsApp& app, QWidget* parent) :
    m_p_parent(parent),
    // m_title: below
    // m_subtitle: below,
    // m_icon: below
    m_arrow_on_right(true),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),
    m_implemented(true),
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(nullptr),
    m_p_menuproxy(p_menuproxy),
    m_task_tablename(""),
    m_p_task(nullptr)
{
    QScopedPointer<MenuWindow> mw(m_p_menuproxy->create(app));
    m_title = mw->title();
    m_subtitle = mw->subtitle();
    m_icon = mw->icon();
}


MenuItem::MenuItem(const TaskMenuItem& taskmenuitem,
                   CamcopsApp& app, QWidget* parent) :
    m_p_parent(parent),
    // m_title: below
    m_subtitle(""),  // may be replaced below
    m_icon(""),  // may be replaced below
    m_arrow_on_right(false),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),  // may be replaced below
    m_implemented(true),
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(nullptr),
    m_p_menuproxy(nullptr),
    m_task_tablename(taskmenuitem.tablename),
    m_p_task(nullptr)
{
    TaskPtr task = app.m_p_task_factory->create(m_task_tablename);
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


MenuItem::MenuItem(TaskPtr p_task, QWidget* parent) :
    m_p_parent(parent),
    m_title("?"),
    m_subtitle(""),
    m_icon(""),
    m_arrow_on_right(false),
    m_chain(false),
    m_copyright_details_pending(false),
    m_crippled(false),
    m_implemented(true),
    m_label_only(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_unsupported(false),
    m_func(nullptr),
    m_p_menuproxy(nullptr),
    m_task_tablename(""),
    m_p_task(p_task)
{
}



void MenuItem::validate() const
{
    // stopApp("test stop");
}


QWidget* MenuItem::getRowWidget(CamcopsApp& app) const
{
    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();
    row->setLayout(rowlayout);

    // Icon
    if (!m_label_only && !m_p_task) {  // Labels/task instances go full-left
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
    MenuItemTitle* title = new MenuItemTitle(m_title);
    textlayout->addWidget(title);
    if (!m_subtitle.isEmpty()) {
        MenuItemSubtitle* subtitle = new MenuItemSubtitle(m_subtitle);
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
