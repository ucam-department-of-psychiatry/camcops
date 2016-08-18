#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"
#include "menulib/menuitem.h"

class QListWidget;
class QListWidgetItem;
class QVBoxLayout;
class MenuHeader;


class MenuWindow : public QWidget
{
    Q_OBJECT

public:
    MenuWindow(CamcopsApp& app, const QString& title,
               const QString& icon = "", bool top = false);
    // Derived constructors should be LIGHTWEIGHT, as
    // MenuItem::MenuItem(MenuProxyPtr, CamcopsApp&) will create an INSTANCE
    // to get the title/subtitle.
    // If it's cheap, populate m_items in the constructor.
    // If it's expensive (e.g. task lists), override buildMenu() to do:
    // (a) populate m_items;
    // (b) call MenuWindow::buildMenu();
    // (c) +/- any additional work (e.g. signals/slots).
    virtual void buildMenu();  // called by framework prior to opening
    QString title() const;
    QString subtitle() const;
    QString icon() const;

signals:
    void offerViewEditDelete(bool offer_view, bool offer_edit,
                             bool offer_delete);

public slots:
    void menuItemClicked(QListWidgetItem* item);
    void lockStateChanged(LockState lockstate);

protected:
    CamcopsApp& m_app;
    QString m_title;
    QString m_subtitle;
    QString m_icon;
    bool m_top;
    QVector<MenuItem> m_items;
    QPointer<QVBoxLayout> m_mainlayout;
    QPointer<MenuHeader> m_p_header;
    QPointer<QListWidget> m_p_listwidget;
};
