#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPixmap>
#include <QPushButton>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "menu_item.h"
#include "menu_window.h"
#include "common/ui_constants.h"
#include "lib/uifunc.h"


MenuItem::MenuItem(QWidget* parent) :
    m_parent(parent),
    m_arrowOnRight(false),
    m_copyrightDetailsPending(false),
    m_notImplemented(false),
    m_unsupported(false),
    m_crippled(false),
    m_needsPrivilege(false),
    m_notIfLocked(false),
    m_menu(NULL),
    m_func(NULL),
    m_chain(false),
    m_labelOnly(false)
{
}


void MenuItem::validate()
{
    // stopApp("test stop");
}


QWidget* MenuItem::getRowWidget()
{
    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();

    QString iconFilename = m_chain ? ICON_CHAIN : m_icon;
    if (!iconFilename.isEmpty()) {
        QLabel* iconLabel = iconWidget(iconFilename);
        rowlayout->addWidget(iconLabel);
    } else {
        rowlayout->addSpacing(ICONSIZE);
    }

    QVBoxLayout* textLayout = new QVBoxLayout();
    MenuTitle* title = new MenuTitle(m_title);
    textLayout->addWidget(title);
    if (!m_subtitle.isEmpty()) {
        MenuSubtitle* subtitle = new MenuSubtitle(m_subtitle);
        textLayout->addWidget(subtitle);
    }
    rowlayout->addLayout(textLayout);

    if (m_arrowOnRight) {
        rowlayout->addStretch();
        QLabel* iconLabel = iconWidget(ICON_TABLE_CHILDARROW, false);
        rowlayout->addWidget(iconLabel);
    }

    row->setLayout(rowlayout);
    return row;
}


void MenuItem::act(CamcopsApp& app)
{
    if (m_notImplemented) {
        alert(tr("Not implemented yet!"));
        return;
    }
    if (m_unsupported) {
        alert(tr("Not supported on this platform!"));
        return;
    }
    if (m_needsPrivilege && !app.m_privileged) {
        alert(tr("You must set Privileged Mode first"));
        return;
    }
    if (m_labelOnly) {
        qDebug() << "Label-only row touched; ignored";
        return;
    }
    if (m_notIfLocked && app.m_patientLocked) {
        alert(tr("Can’t perform this action when CamCOPS is locked"),
              tr("Unlock first"));
        return;
    }
    if (m_menu) {
        MenuWindow* pWindow = m_menu(app);
        app.pushScreen(pWindow);
        return;
    }
    if (m_func) {
        m_func();
        return;
    }
    alert("boo! No other action specified ***");
}
