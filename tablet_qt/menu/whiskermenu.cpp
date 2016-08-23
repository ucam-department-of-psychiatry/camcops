#include "whiskermenu.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"


WhiskerMenu::WhiskerMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Whisker networked hardware"),
               UiFunc::iconFilename(UiConst::ICON_WHISKER))
{
    m_items = {
        MenuItem(tr("Connect to Whisker server")),  // ***
        MenuItem(tr("Disconnect from Whisker server")),  // ***
        MenuItem(tr("Test network latency to Whisker server")),  // ***
        MenuItem(tr("Configure Whisker")),  // ***
    };
}
