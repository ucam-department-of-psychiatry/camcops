#include "main_menu.h"
#include <QDebug>
#include "menulib/menu_item.h"
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
    second_item.m_arrowOnRight = true;
    second_item.m_needsPrivilege = true;

    MenuItem test_menu = MenuItem();
    test_menu.m_title = "Testing menu";
    test_menu.m_menu = &buildTestWindow;

    m_items = {first_item, second_item, test_menu};

    buildMenu();
}

MainMenu::~MainMenu()
{
}
