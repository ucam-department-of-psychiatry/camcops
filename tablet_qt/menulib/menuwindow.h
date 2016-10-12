#pragma once
#include <QPointer>
#include <QSharedPointer>
#include <QVector>
#include "common/camcopsapp.h"  // for LockState
#include "menulib/menuitem.h"
#include "widgets/openablewidget.h"

class QListWidget;
class QListWidgetItem;
class QVBoxLayout;
class MenuHeader;
class Task;
using TaskPtr = QSharedPointer<Task>;


class MenuWindow : public OpenableWidget
{
    Q_OBJECT

public:
    MenuWindow(CamcopsApp& app, const QString& title,
               const QString& icon = "", bool top = false);
    // Derived constructors should be LIGHTWEIGHT, as
    // MenuItem::MenuItem(MenuProxyPtr, CamcopsApp&) will create an INSTANCE
    // to get the title/subtitle.
    // If it's cheap, populate m_items in the constructor.
    // If it's expensive (e.g. task lists), override build() to do:
    // (a) populate m_items;
    // (b) call MenuWindow::build();
    // (c) +/- any additional work (e.g. signals/slots).
    virtual void build() override;  // called by framework prior to opening

    QString title() const;
    QString subtitle() const;
    QString icon() const;
    int currentIndex() const;
    TaskPtr currentTask() const;

protected:
    void reloadStyleSheet();
    void loadStyleSheet();

signals:
    void offerViewEditDelete(bool offer_view, bool offer_edit,
                             bool offer_delete);

public slots:
    void menuItemClicked(QListWidgetItem* item);
    void lockStateChanged(CamcopsApp::LockState lockstate);
    void viewItem();
    void editItem();
    void deleteItem();

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
