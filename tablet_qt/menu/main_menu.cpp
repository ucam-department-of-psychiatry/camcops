#include "main_menu.h"
#include <QDebug>
#include "menulib/menuitem.h"
#include "menu/test_menu.h"


MainMenu::MainMenu(CamcopsApp& app)
    : MenuWindow(app, true)
{
    qDebug() << "Creating MainMenu";
    MenuItem first_item = MenuItem();
    first_item.m_title = "hello world";
    first_item.m_icon = ":/images/camcops/camcops.png";

    MenuItem second_item = MenuItem();
    second_item.m_title = "number two";
    second_item.m_subtitle = "subtitle";
    second_item.m_needs_privilege = true;

    m_items = {
        first_item,
        second_item,
        MenuItem::makeMenuItem(
            "Testing menu",
            &MainMenu::makeTestMenu)
    };

    buildMenu();
}


MainMenu::~MainMenu()
{
}


MenuWindow* MainMenu::makeTestMenu(CamcopsApp& app)
{
    return new TestMenu(app);
}
