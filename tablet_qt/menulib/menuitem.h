#pragma once
#include <functional>  // for std::function
#include <QLabel>
#include <QSharedPointer>
#include <QString>
#include <Qt>
#include "common/camcopsapp.h"
#include "menulib/menuproxy.h"

class QWidget;
class MenuWindow;
class Task;
typedef QSharedPointer<Task> TaskPtr;


struct TaskMenuItem
{
    // Exists only to improve polymorphic constructor of MenuItem
public:
    TaskMenuItem(const QString& tablename) :
        tablename(tablename)
    {}
    QString tablename;
};


struct HtmlMenuItem
{
public:
    HtmlMenuItem(const QString& filename) :
        filename(filename)
    {}
    QString filename;
};


class MenuItem
{
    Q_DECLARE_TR_FUNCTIONS(MenuItem)

public:
    typedef std::function<MenuWindow*(CamcopsApp&)> MenuWindowBuilder;
    typedef std::function<void()> ActionFunction;
    // http://stackoverflow.com/questions/14189440

public:
    MenuItem();
    MenuItem(const QString &title);  // for dummy use
    MenuItem(const QString& title, const ActionFunction& func,
             const QString& icon = "");
    MenuItem(MenuProxyPtr p_menuproxy, CamcopsApp& app);
    MenuItem(const TaskMenuItem& taskmenuitem, CamcopsApp& app);
    MenuItem(const QString& title, const HtmlMenuItem& htmlmenuitem);
    MenuItem(TaskPtr p_task, bool task_shows_taskname = true);

    QString title();
    TaskPtr task();

    // https://en.wikipedia.org/wiki/Method_chaining
    MenuItem& setImplemented(bool implemented);
    MenuItem& setLabelOnly(bool label_only = true);
    MenuItem& setNeedsPrivilege(bool needs_privilege = true);
    MenuItem& setNotIfLocked(bool not_if_locked = true);
    MenuItem& setUnsupported(bool unsupported = true);

    QWidget* getRowWidget(CamcopsApp& app) const;
    void act(CamcopsApp& app) const;
    void showHtml(const QString& filename) const;
    bool isImplemented() const;

protected:
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
    bool m_task_shows_taskname;
    bool m_unsupported;
    ActionFunction m_func;
    MenuProxyPtr m_p_menuproxy;
    QString m_task_tablename;
    TaskPtr m_p_task;
    QString m_html_filename;
//    SOMETHING m_event;
//    SOMETHING m_info;
//    SOMETHING m_chainList;

private:
    void setDefaults();
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

// This works, but using setObjectName and #selector is simpler!
/*
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
*/
