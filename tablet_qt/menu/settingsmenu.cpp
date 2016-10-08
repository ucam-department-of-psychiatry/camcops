#include "settingsmenu.h"
#include "common/platform.h"
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "lib/fieldref.h"
#include "lib/uifunc.h"
#include "menu/testmenu.h"
#include "menu/whiskermenu.h"
#include "menulib/menuitem.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"

const int IP_PORT_MIN = 0;
const int IP_PORT_MAX = 65536;
const int TIMEOUT_MS_MIN = 100;
const int TIMEOUT_MS_MAX = 5 * 60 * 1000;


SettingsMenu::SettingsMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Settings"),
               UiFunc::iconFilename(UiConst::ICON_SETTINGS)),
    m_app(app)
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
        MenuItem(
            tr("Set privileged mode (for items marked †)"),
            std::bind(&SettingsMenu::setPrivilege, this)
        ).setNotIfLocked(),
        // PRIVILEGED FUNCTIONS BELOW HERE
        MenuItem(
            tr("(†) Configure server settings"),
            std::bind(&SettingsMenu::configureServerSettings, this,
                      std::placeholders::_1)
        ).setNeedsPrivilege(),
        MenuItem(tr("(†) Register this device with the server")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Change privileged-mode password")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Wipe extra strings downloaded from server")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) View local database as SQL")).setNeedsPrivilege(),  // ***
        MenuItem(tr("(†) Send local database to USB debugging stream (tablet "
                    "devices only)")
        ).setNeedsPrivilege().setUnsupported(!Platform::PLATFORM_TABLET),  // ***
        MenuItem(tr("(†) Dump local database to SQL file (Android only)")
        ).setNeedsPrivilege().setUnsupported(!Platform::PLATFORM_ANDROID),  // ***
        MenuItem(
            tr("(†) Run software unit tests (reporting to debugging stream)")
        ).setNeedsPrivilege(),  // ***
    };
}


OpenableWidget* SettingsMenu::configureServerSettings(CamcopsApp& app)
{
    // The general options here: have the Questionnaire save directly to the
    // StoredVar but in a way that's not permanent and allows "recall/reload"
    // upon cancel; or temporary local storage with writing to the StoredVar
    // on OK. The latter is a generally better principle. Since C++ lambda
    // functions don't extend the life of things they reference (see "dangling
    // references" in the spec), the best way is by having the CamcopsApp
    // (whose lifespan is guaranteed to be long enough) to do the storage,
    // and having a fieldref to a cached storedvar.

    qDebug() << Q_FUNC_INFO;
    app.clearCachedVars();  // ... in case any are left over

    FieldRefPtr address_fr = app.storedVarFieldRef(VarConst::SERVER_ADDRESS);
    QString address_t = tr("Server address");
    QString address_h = tr("host name or IP address");

    FieldRefPtr port_fr = app.storedVarFieldRef(VarConst::SERVER_PORT);
    QString port_t = tr("Server port for HTTPS");
    QString port_h = tr("default 443");

    FieldRefPtr path_fr = app.storedVarFieldRef(VarConst::SERVER_PATH);
    QString path_t = tr("Path on server");
    QString path_h = tr("no leading /; e.g. camcops/database");

    FieldRefPtr timeout_fr = app.storedVarFieldRef(VarConst::SERVER_TIMEOUT_MS);
    QString timeout_t = tr("Network timeout (ms)");
    QString timeout_h = tr("e.g. 50000");

    QuPagePtr page(new QuPage{
        QuestionnaireFunc::defaultGridRawPointer({
            {
                makeTitle(address_t, address_h),
                (new QuLineEdit(address_fr))->setHint(
                    makeHint(address_t, address_h))
            },
            {
                makeTitle(port_t, port_h),
                (new QuLineEditInteger(port_fr,
                    IP_PORT_MIN, IP_PORT_MAX))->setHint(
                        makeHint(port_t, port_h))
            },
            {
                makeTitle(path_t, path_h),
                (new QuLineEdit(path_fr))->setHint(makeHint(path_t, path_h))
            },
            {
                makeTitle(timeout_t, timeout_h),
                (new QuLineEditInteger(timeout_fr,
                    TIMEOUT_MS_MIN, TIMEOUT_MS_MAX))->setHint(
                        makeHint(timeout_t, timeout_h))
            },
        }, 1, 1),
    });
    // *** add others
    page->setTitle(tr("Configure server settings"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    connect(questionnaire, &Questionnaire::completed,
            &app, &CamcopsApp::saveCachedVars);
    connect(questionnaire, &Questionnaire::cancelled,
            &app, &CamcopsApp::clearCachedVars);
    return questionnaire;
}


void SettingsMenu::setPrivilege()
{
    m_app.grantPrivilege();  // *** make secure!
}


QString SettingsMenu::makeTitle(const QString& part1, const QString& part2) const
{
    return QString("<b>%1</b> (%2):").arg(part1).arg(part2);
}

QString SettingsMenu::makeHint(const QString& part1, const QString& part2) const
{
    return QString("%1 (%2)").arg(part1).arg(part2);
}
