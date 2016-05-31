#pragma once
#include <QCoreApplication>
#include <QLabel>
#include <QString>
#include <Qt>
#include <QWidget>


class MenuItem
{
    Q_DECLARE_TR_FUNCTIONS(MenuItem)

public:
    MenuItem();
    ~MenuItem() {}
    QWidget* get_row_widget();
    void validate();
    void act();

public:
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
//    QMenuWindow* m_window;
//    SOMETHING m_event;
//    SOMETHING m_func;
//    SOMETHING m_task;
//    SOMETHING m_html;
//    SOMETHING m_info;
    bool m_chain;
//    SOMETHING m_chainList;
    bool m_labelOnly;
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
