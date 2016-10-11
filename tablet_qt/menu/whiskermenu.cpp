#include "whiskermenu.h"
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"


WhiskerMenu::WhiskerMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Whisker networked hardware"),
               UiFunc::iconFilename(UiConst::ICON_WHISKER))
{
    m_items = {
        MenuItem(tr("Connect to Whisker server")),  // ***
        MenuItem(tr("Disconnect from Whisker server")),  // ***
        MenuItem(tr("Test network latency to Whisker server")),  // ***
        MenuItem(
            tr("Configure Whisker"),
            std::bind(&WhiskerMenu::configureWhisker, this,
                      std::placeholders::_1)
        ),
    };
}


OpenableWidget* WhiskerMenu::configureWhisker(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    FieldRefPtr address_fr = app.storedVarFieldRef(VarConst::WHISKER_HOST);
    QString address_t = tr("Whisker host");
    QString address_h = tr("host name or IP address; default: localhost");

    FieldRefPtr port_fr = app.storedVarFieldRef(VarConst::WHISKER_PORT);
    QString port_t = tr("Whisker port");
    QString port_h = tr("default 3233");

    FieldRefPtr timeout_fr = app.storedVarFieldRef(VarConst::WHISKER_TIMEOUT_MS);
    QString timeout_t = tr("Network timeout (ms)");
    QString timeout_h = tr("e.g. 5000");

    QuPagePtr page(new QuPage{
        QuestionnaireFunc::defaultGridRawPointer({
            {
                makeTitle(address_t, address_h),
                (new QuLineEdit(address_fr))->setHint(
                    makeHint(address_t, address_h))
            },
            {
                makeTitle(port_t, port_h),
                new QuLineEditInteger(port_fr,
                    UiConst::IP_PORT_MIN, UiConst::IP_PORT_MAX)
            },
            {
                makeTitle(timeout_t, timeout_h),
                new QuLineEditInteger(timeout_fr,
                    UiConst::NETWORK_TIMEOUT_MS_MIN,
                    UiConst::NETWORK_TIMEOUT_MS_MAX)
            },
        }, 1, 1),
    });
    page->setTitle(tr("Configure Whisker"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    connect(questionnaire, &Questionnaire::completed,
            &app, &CamcopsApp::saveCachedVars);
    connect(questionnaire, &Questionnaire::cancelled,
            &app, &CamcopsApp::clearCachedVars);
    return questionnaire;
}


QString WhiskerMenu::makeTitle(const QString& part1,
                               const QString& part2) const
{
    return QString("<b>%1</b> (%2):").arg(part1).arg(part2);
}


QString WhiskerMenu::makeHint(const QString& part1,
                              const QString& part2) const
{
    return QString("%1 (%2)").arg(part1).arg(part2);
}
