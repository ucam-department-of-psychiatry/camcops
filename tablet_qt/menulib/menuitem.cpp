#include <QDebug>
#include <QLabel>
#include <QHBoxLayout>
#include <QPushButton>
#include <QSize>
#include <QUrl>
#include <QVBoxLayout>
#include "menuitem.h"
#include "menuwindow.h"
#include "common/ui_constants.h"
#include "lib/uifunc.h"


MenuItem::MenuItem(QWidget* parent) :
    m_p_parent(parent),
    m_arrow_on_right(false),
    m_copyright_details_pending(false),
    m_implemented(true),
    m_unsupported(false),
    m_crippled(false),
    m_needs_privilege(false),
    m_not_if_locked(false),
    m_menu(nullptr),
    m_func(nullptr),
    m_chain(false),
    m_labelOnly(false)
{
}


void MenuItem::validate() const
{
    // stopApp("test stop");
}


QWidget* MenuItem::getRowWidget() const
{
    QWidget* row = new QWidget();
    QHBoxLayout* rowlayout = new QHBoxLayout();

    if (m_chain) {
        QLabel* iconLabel = ICON_CHAIN(row);
        rowlayout->addWidget(iconLabel);
    } else {
        rowlayout->addSpacing(ICONSIZE);
    }

    QVBoxLayout* textlayout = new QVBoxLayout();
    MenuTitle* title = new MenuTitle(m_title);
    textlayout->addWidget(title);
    if (!m_subtitle.isEmpty()) {
        MenuSubtitle* subtitle = new MenuSubtitle(m_subtitle);
        textlayout->addWidget(subtitle);
    }
    rowlayout->addLayout(textlayout);

    if (m_arrow_on_right) {
        rowlayout->addStretch();
        QLabel* iconLabel = ICON_TABLE_CHILDARROW(nullptr);
        rowlayout->addWidget(iconLabel);
    }

    row->setLayout(rowlayout);
    return row;
}


void MenuItem::act(CamcopsApp& app) const
{
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
    if (m_labelOnly) {
        qDebug() << "Label-only row touched; ignored";
        return;
    }
    if (m_not_if_locked && app.locked()) {
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
    qWarning() << "Menu item selected but no action specified:"
               << m_title;
}


MenuItem MenuItem::makeFuncItem(const QString& title,
                                  const MenuItem::ActionFunction& func)
{
    MenuItem item = MenuItem();
    item.m_title = title;
    item.m_func = func;
    return item;
}


MenuItem MenuItem::makeMenuItem(const QString& title,
                                  const MenuWindowBuilder& menufunc,
                                  const QString& icon)
{
    MenuItem item = MenuItem();
    item.m_title = title;
    item.m_menu = menufunc;
    item.m_icon = icon;
    item.m_arrow_on_right = true;
    return item;
}

bool MenuItem::isImplemented() const
{
    return m_implemented;
}

void MenuItem::setImplemented(bool implemented)
{
    m_implemented = implemented;
}
