#pragma once
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
    typedef MenuWindow* (*MenuWindowBuilder)(CamcopsApp &app);
    typedef void (*ActionFuncPtr)();

public:
    MenuItem(QWidget* parent = 0);
    ~MenuItem() {}
    QWidget* getRowWidget();
    void validate();
    void act(CamcopsApp& app);

public:
    QWidget* m_parent;
    QString m_title;
    QString m_subtitle;
    QString m_icon;
    bool m_arrowOnRight;
    bool m_copyrightDetailsPending;
    bool m_notImplemented;
    bool m_unsupported;
    bool m_crippled;
    bool m_needsPrivilege;
    bool m_notIfLocked;
    MenuWindowBuilder m_menu;  // pointer to function, as above
//    SOMETHING m_event;
    ActionFuncPtr m_func;
//    SOMETHING m_task;
//    SOMETHING m_html;
//    SOMETHING m_info;
    bool m_chain;
//    SOMETHING m_chainList;
    bool m_labelOnly;
};


template<typename Derived>
MenuWindow* MenuBuilder()
{
    return new Derived();
}


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
