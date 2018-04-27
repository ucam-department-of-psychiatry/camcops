/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "whiskermenu.h"
#include "common/uiconst.h"
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
               uifunc::iconFilename(uiconst::ICON_WHISKER))
{
    m_items = {
        MenuItem(tr("Connect to Whisker server")),  // ***
        MenuItem(tr("Disconnect from Whisker server")),  // ***
        MenuItem(tr("Test network latency to Whisker server")),  // ***
        MenuItem(
            tr("Configure Whisker"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&WhiskerMenu::configureWhisker, this,
                          std::placeholders::_1)
            )
        ),
    };
}


OpenableWidget* WhiskerMenu::configureWhisker(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    FieldRefPtr address_fr = app.storedVarFieldRef(varconst::WHISKER_HOST);
    const QString address_t = tr("Whisker host");
    const QString address_h = tr("host name or IP address; default: localhost");

    FieldRefPtr port_fr = app.storedVarFieldRef(varconst::WHISKER_PORT);
    const QString port_t = tr("Whisker port");
    const QString port_h = tr("default 3233");

    FieldRefPtr timeout_fr = app.storedVarFieldRef(varconst::WHISKER_TIMEOUT_MS);
    const QString timeout_t = tr("Network timeout (ms)");
    const QString timeout_h = tr("e.g. 5000");

    QuPagePtr page(new QuPage{
        questionnairefunc::defaultGridRawPointer({
            {
                makeTitle(address_t, address_h),
                (new QuLineEdit(address_fr))->setHint(
                    makeHint(address_t, address_h))
            },
            {
                makeTitle(port_t, port_h),
                new QuLineEditInteger(port_fr,
                    uiconst::IP_PORT_MIN, uiconst::IP_PORT_MAX)
            },
            {
                makeTitle(timeout_t, timeout_h),
                new QuLineEditInteger(timeout_fr,
                    uiconst::NETWORK_TIMEOUT_MS_MIN,
                    uiconst::NETWORK_TIMEOUT_MS_MAX)
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
