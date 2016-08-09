#pragma once
#include <functional>  // for std::function
#include <QCoreApplication>
#include <QLabel>
#include <QString>
#include <Qt>
#include <QWidget>
#include "common/camcops_app.h"


class MenuWindow;


class MenuItem
{
    Q_DECLARE_TR_FUNCTIONS(MenuItem)

public:
    typedef std::function<MenuWindow*(CamcopsApp&)> MenuWindowBuilder;
    typedef std::function<void()> ActionFunction;
    // http://stackoverflow.com/questions/14189440

public:
    MenuItem(QWidget* parent = 0);
    ~MenuItem() {}
    QWidget* getRowWidget();
    void validate();
    void act(CamcopsApp& app);

    static MenuItem makeFuncItem(const QString& title,
                                 const ActionFunction& func);
    static MenuItem makeMenuItem(const QString& title,
                                 const MenuWindowBuilder& menufunc,
                                 const QString& icon = "");

public:
    QWidget* m_p_parent;
    QString m_title;
    QString m_subtitle;
    QString m_icon;
    bool m_arrow_on_right;
    bool m_copyright_details_pending;
    bool m_not_implemented;
    bool m_unsupported;
    bool m_crippled;
    bool m_needs_privilege;
    bool m_not_if_locked;
    MenuWindowBuilder m_menu;  // pointer to function, as above
//    SOMETHING m_event;
    ActionFunction m_func;
    // http://stackoverflow.com/questions/8711391
//    SOMETHING m_task;
//    SOMETHING m_html;
//    SOMETHING m_info;
    bool m_chain;
//    SOMETHING m_chainList;
    bool m_labelOnly;
    bool getNotImplemented() const;
    void setNotImplemented(bool not_implemented);
};


// ============================================================================
// The following classes exist just for CSS.
// ============================================================================

class MenuTitle : public QLabel
{
    Q_OBJECT
public:
    MenuTitle(QWidget* parent = 0, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuTitle(const QString& text, QWidget* parent = 0,
              Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuTitle() {}
};


class MenuSubtitle : public QLabel
{
    Q_OBJECT
public:
    MenuSubtitle(QWidget* parent = 0, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuSubtitle(const QString& text, QWidget* parent = 0,
                 Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuSubtitle() {}
};
