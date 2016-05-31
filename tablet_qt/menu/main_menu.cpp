#include "main_menu.h"
#include "menulib/menu_item.h"

MainMenu::MainMenu(QWidget *parent)
    : MenuWindow(parent)
{
    MenuItem first_item = MenuItem();
    first_item.m_title = "hello world";
    first_item.m_icon = ":/images/camcops/camcops.png";

    MenuItem second_item = MenuItem();
    second_item.m_title = "number two";
    second_item.m_arrowOnRight = true;
    second_item.m_needsPrivilege = true;

    m_items
        << first_item
        << second_item;
}

MainMenu::~MainMenu()
{
}
