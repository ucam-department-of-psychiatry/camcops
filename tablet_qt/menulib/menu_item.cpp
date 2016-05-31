#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPixmap>
#include <QPushButton>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "menu_item.h"
#include "common/gv.h"
#include "common/ui_constants.h"
#include "lib/uifunc.h"


MenuItem::MenuItem() :
    m_arrowOnRight(false),
    m_copyrightDetailsPending(false),
    m_notImplemented(false),
    m_unsupported(false),
    m_crippled(false),
    m_needsPrivilege(false),
    m_notIfLocked(false),
    m_chain(false),
    m_labelOnly(false)
{
}


void MenuItem::validate()
{
    // stop_app("test stop");
}


QWidget* MenuItem::get_row_widget()
{
    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();

    QString iconFilename = m_chain ? ICON_CHAIN : m_icon;
    if (!iconFilename.isEmpty()) {
        QLabel* iconLabel = icon_widget(iconFilename);
        rowlayout->addWidget(iconLabel);
    }

    MenuTitle* title = new MenuTitle(m_title);
    rowlayout->addWidget(title);

    if (m_arrowOnRight) {
        QLabel* iconLabel = icon_widget(ICON_TABLE_CHILDARROW);
        rowlayout->addWidget(iconLabel);
    }

    row->setLayout(rowlayout);
    return row;
}


void MenuItem::act()
{
    if (m_notImplemented) {
        alert(tr("Not implemented yet!"));
        return;
    }
    if (m_unsupported) {
        alert(tr("Not supported on this platform!"));
        return;
    }
    if (m_needsPrivilege && !g_privileged) {
        alert(tr("You must set Privileged Mode first"));
        return;
    }
    if (m_labelOnly) {
        qDebug() << "Label-only row touched; ignored";
        return;
    }
    if (m_notIfLocked && g_patientLocked) {
        alert(tr("Can’t perform this action when CamCOPS is locked"),
              tr("Unlock first"));
        return;
    }

    alert("boo!");
}
