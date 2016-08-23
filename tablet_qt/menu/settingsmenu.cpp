#include "settingsmenu.h"
#include "common/platform.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "menu/testmenu.h"
#include "menu/whiskermenu.h"


SettingsMenu::SettingsMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Settings"),
               UiFunc::iconFilename(UiConst::ICON_SETTINGS))
{
    m_items = {
        MenuItem(tr("Questionnaire font size")).setNotIfLocked(),  // ***
        MenuItem(tr("User settings")).setNotIfLocked(),  // ***
        MenuItem(tr("Intellectual property (IP) permissions")).setNotIfLocked(),  // ***
        MenuItem(tr("Change app password")).setNotIfLocked(),  // ***
        MenuItem(tr("Show server information")).setNotIfLocked(),  // ***
        MenuItem(tr("Re-accept ID descriptions from the server")).setNotIfLocked(),  // ***
        MenuItem(tr("Re-fetch extra task strings from the server")).setNotIfLocked(),  // ***
        MAKE_MENU_MENU_ITEM(WhiskerMenu, app).setNotIfLocked(),
        MAKE_MENU_MENU_ITEM(TestMenu, app),
        MenuItem(tr("Set privileged mode (for items marked †)")).setNotIfLocked(),  // ***
        // PRIVILEGED FUNCTIONS BELOW HERE
        MenuItem(tr("(†) Configure server settings")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Register this device with the server")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Change privileged-mode password")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Wipe extra strings downloaded from server")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) View local database as SQL")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Send local database to USB debugging stream (tablet "
                    "devices only)")
        ).setNeedsPrivilege().setUnsupported(!Platform::PLATFORM_TABLET),  // ***
        MenuItem(tr("(†) Dump local database to SQL file (Android only)")
        ).setNeedsPrivilege().setUnsupported(!Platform::PLATFORM_ANDROID),  // ***
        MenuItem(tr("(†) Run software unit tests (reporting to debugging "
                    "stream)")
        ).setNeedsPrivilege(),  // ***
    };
}
