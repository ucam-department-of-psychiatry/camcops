#pragma once
#include <functional>  // for std::function
#include <QLabel>
#include <QString>
#include <Qt>
#include "common/camcopsapp.h"
#include "menulib/menuproxy.h"

class QWidget;
class MenuWindow;


class TaskMenuItem
{
    // Exists only to improve polymorphic constructor of MenuItem
public:
    TaskMenuItem(const QString& tablename) :
        tablename(tablename) {}
    QString tablename;
};


class MenuItem
{
    Q_DECLARE_TR_FUNCTIONS(MenuItem)

public:
    typedef std::function<MenuWindow*(CamcopsApp&)> MenuWindowBuilder;
    typedef std::function<void()> ActionFunction;
    // http://stackoverflow.com/questions/14189440

public:
    MenuItem(QWidget* parent = nullptr);
    MenuItem(const QString &title, QWidget* parent = nullptr);  // for dummy use
    MenuItem(const QString& title, const ActionFunction& func,
             const QString& icon = "", QWidget* parent = nullptr);
    MenuItem(MenuProxyPtr p_menuproxy,
             CamcopsApp& app, QWidget* parent = nullptr);
    MenuItem(const TaskMenuItem& taskmenuitem,
             CamcopsApp& app, QWidget* parent = nullptr);
    MenuItem(TaskPtr p_task, QWidget* parent = nullptr);

    ~MenuItem() {}

    // https://en.wikipedia.org/wiki/Method_chaining
    MenuItem& setImplemented(bool implemented);
    MenuItem& setLabelOnly(bool label_only = true);
    MenuItem& setNeedsPrivilege(bool needs_privilege = true);
    MenuItem& setNotIfLocked(bool not_if_locked = true);
    MenuItem& setUnsupported(bool unsupported = true);

    QWidget* getRowWidget(CamcopsApp& app) const;
    void validate() const;
    void act(CamcopsApp& app) const;
    bool isImplemented() const;

public:
    QWidget* m_p_parent;
    QString m_title;
    QString m_subtitle;
    QString m_icon;
    bool m_arrow_on_right;
    bool m_chain;
    bool m_copyright_details_pending;
    bool m_crippled;
    bool m_implemented;
    bool m_label_only;
    bool m_needs_privilege;
    bool m_not_if_locked;
    bool m_unsupported;
    ActionFunction m_func;
    MenuProxyPtr m_p_menuproxy;
    QString m_task_tablename;
    TaskPtr m_p_task;
//    SOMETHING m_event;
//    SOMETHING m_task;
//    SOMETHING m_info;
//    SOMETHING m_chainList;
};


// ============================================================================
// Convenience macros
// ============================================================================

#define MAKE_MENU_MENU_ITEM(MenuClass, app) \
    MenuItem(MenuProxyPtr(new MenuProxy<MenuClass>), app)
#define MAKE_TASK_MENU_ITEM(tablename, app) \
    MenuItem(TaskMenuItem(tablename), app)
#define MAKE_CHANGE_PATIENT(app) \
    MenuItem(tr("Change patient")).setNotIfLocked()
    // *** function, using app? Or menu?
    // *** ICON_CHOOSE_PATIENT


// ============================================================================
// The following classes exist just for CSS.
// ============================================================================

class MenuItemTitle : public QLabel
{
    Q_OBJECT
public:
    MenuItemTitle(QWidget* parent = nullptr, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuItemTitle(const QString& text, QWidget* parent = nullptr,
                  Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuItemTitle() {}
};


class MenuItemSubtitle : public QLabel
{
    Q_OBJECT
public:
    MenuItemSubtitle(QWidget* parent = nullptr, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuItemSubtitle(const QString& text, QWidget* parent = nullptr,
                     Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuItemSubtitle() {}
};
