/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#define OFFER_VIEW_SQL  // debugging only

#include "settingsmenu.h"

#include <QDebug>
#include <QFileDialog>
#include <QTextStream>

#include "common/platform.h"
#include "common/uiconst.h"
#include "common/varconst.h"
#include "core/networkmanager.h"
#include "db/databasemanager.h"
#include "db/dbnestabletransaction.h"
#include "db/dumpsql.h"
#include "db/fieldref.h"
#include "dbobjects/extrastring.h"
#include "dbobjects/idnumdescription.h"
#include "dialogs/logmessagebox.h"
#include "lib/convert.h"
#include "lib/slowguiguard.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "menu/testmenu.h"
#include "menulib/fontsizeanddpiwindow.h"
#include "menulib/menuitem.h"
#include "menulib/serversettingswindow.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"


// For IP settings:
const QString TAG_IP_CLINICAL_WARNING("clinical");

SettingsMenu::SettingsMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETTINGS)),
    m_plaintext_pw_live(false),
    m_ip_questionnaire(nullptr)
{
    m_ip_clinical_fr
        = m_app.storedVarFieldRef(varconst::IP_USE_CLINICAL, false);
}

QString SettingsMenu::title() const
{
    return tr("Settings");
}

void SettingsMenu::makeItems()
{
    const QString PRIVPREFIX("(†) ");
    const QString spanner(uifunc::iconFilename(uiconst::CBS_SPANNER));

    // Safe object lifespan signal: can use std::bind
    m_items = {
        // --------------------------------------------------------------------
        MenuItem(tr("Common user settings")).setLabelOnly(),
        // --------------------------------------------------------------------
        MenuItem(
            tr("Choose language"),
            std::bind(&SettingsMenu::chooseLanguage, this),
            uifunc::iconFilename(uiconst::CBS_LANGUAGE)
        ),
        MenuItem(
            tr("Questionnaire font size and DPI settings"),
            MenuItem::OpenableWidgetMaker(std::bind(
                &SettingsMenu::setQuestionnaireFontSize,
                this,
                std::placeholders::_1
            ))
        ),
        MenuItem(
            tr("User settings"),
            MenuItem::OpenableWidgetMaker(std::bind(
                &SettingsMenu::configureUser, this, std::placeholders::_1
            ))
        )
            .setNotIfLocked(),
        MenuItem(
            tr("Intellectual property (IP) permissions"),
            MenuItem::OpenableWidgetMaker(std::bind(
                &SettingsMenu::configureIntellectualProperty,
                this,
                std::placeholders::_1
            ))
        )
            .setNotIfLocked(),
        MenuItem(
            tr("Change app password"),
            std::bind(&SettingsMenu::changeAppPassword, this)
        )
            .setNotIfLocked(),
        MenuItem(tr("Information")).setLabelOnly(),
        MenuItem(
            tr("Show server information"),
            MenuItem::OpenableWidgetMaker(std::bind(
                &SettingsMenu::viewServerInformation,
                this,
                std::placeholders::_1
            ))
        )
            .setNotIfLocked(),
        // --------------------------------------------------------------------
        MenuItem(tr("Infrequent user functions")).setLabelOnly(),
        // --------------------------------------------------------------------
        MenuItem(
            tr("Change operating mode"),
            std::bind(&SettingsMenu::changeMode, this)
        )
            .setNotIfLocked(),
        MenuItem(
            tr("Fetch all server info"),
            std::bind(&SettingsMenu::fetchAllServerInfo, this)
        )
            .setNotIfLocked(),
        MenuItem(
            tr("Change user agent"),
            std::bind(&SettingsMenu::changeUserAgent, this)
        )
            .setNotIfLocked(),
#if 0
        MenuItem(
            tr("Re-accept ID descriptions from the server"),
            std::bind(&SettingsMenu::fetchIdDescriptions, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Re-fetch extra task strings from the server"),
            std::bind(&SettingsMenu::fetchExtraStrings, this)
        ).setNotIfLocked(),
#endif
        // --------------------------------------------------------------------
        MenuItem(tr("Administrator functions")).setLabelOnly(),
        // --------------------------------------------------------------------
        MenuItem(
            tr("Set privileged mode (for items marked †)"),
            std::bind(&SettingsMenu::setPrivilege, this)
        )
            .setNotIfLocked(),
        // PRIVILEGED FUNCTIONS BELOW HERE
        MenuItem(
            PRIVPREFIX + tr("Configure server settings"),
            MenuItem::OpenableWidgetMaker(std::bind(
                &SettingsMenu::configureServer, this, std::placeholders::_1
            ))
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX + tr("Register this device with the server"),
            std::bind(&SettingsMenu::registerWithServer, this)
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX + tr("Change privileged-mode password"),
            std::bind(&SettingsMenu::changePrivPassword, this)
        )
            .setNeedsPrivilege(),
        // --------------------------------------------------------------------
        MenuItem(tr("Rare functions")).setLabelOnly(),
        // --------------------------------------------------------------------
        MAKE_MENU_MENU_ITEM(TestMenu, m_app),
        MenuItem(
            PRIVPREFIX + tr("Wipe extra strings downloaded from server"),
            [this]() {
                deleteAllExtraStrings();
            }  // alternative lambda syntax
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX + tr("View record counts for all data tables"),
            std::bind(&SettingsMenu::viewDataCounts, this),
            spanner
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX + tr("View record counts for all system tables"),
            std::bind(&SettingsMenu::viewSystemCounts, this),
            spanner
        )
            .setNeedsPrivilege(),
        // --------------------------------------------------------------------
        MenuItem(tr("Rescue operations")).setLabelOnly(),
        // --------------------------------------------------------------------
        MenuItem(
            tr("Drop unknown tables"),
            std::bind(&SettingsMenu::dropUnknownTables, this),
            spanner
        )
            .setNotIfLocked(),
#ifdef OFFER_VIEW_SQL
        MenuItem(
            PRIVPREFIX + tr("View data database as SQL"),
            std::bind(&SettingsMenu::viewDataDbAsSql, this),
            spanner
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX + tr("View system database as SQL"),
            std::bind(&SettingsMenu::viewSystemDbAsSql, this),
            spanner
        )
            .setNeedsPrivilege(),
#endif
        MenuItem(
            PRIVPREFIX
                + tr("Send decrypted data database to debugging stream"),
            std::bind(&SettingsMenu::debugDataDbAsSql, this),
            spanner
        )
            .setNeedsPrivilege(),
        MenuItem(
            PRIVPREFIX
                + tr("Send decrypted system database to debugging stream"),
            std::bind(&SettingsMenu::debugSystemDbAsSql, this),
            spanner
        )
            .setNeedsPrivilege(),
    };
    if (!platform::PLATFORM_IOS) {
        // These options are not supported under iOS.
        m_items.append({
            MenuItem(
                PRIVPREFIX + tr("Dump decrypted data database to SQL file"),
                std::bind(&SettingsMenu::saveDataDbAsSql, this),
                spanner
            )
                .setNeedsPrivilege()
                .setUnsupported(platform::PLATFORM_IOS),
            MenuItem(
                PRIVPREFIX + tr("Dump decrypted system database to SQL file"),
                std::bind(&SettingsMenu::saveSystemDbAsSql, this),
                spanner
            )
                .setNeedsPrivilege()
                .setUnsupported(platform::PLATFORM_IOS),
        });
    }
    connect(
        &m_app,
        &CamcopsApp::fontSizeChanged,
        this,
        &SettingsMenu::reloadStyleSheet
    );
}

OpenableWidget* SettingsMenu::configureServer(CamcopsApp& app)
{
    auto window = new ServerSettingsWindow(app);

    return window->editor();
}

OpenableWidget* SettingsMenu::configureIntellectualProperty(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    const QString label_ip_reason = tr(
        "The settings here influence whether CamCOPS will consider some "
        "third-party tasks “permitted” on your behalf, according to their "
        "published use criteria. They do <b>not</b> remove your "
        "responsibility to ensure that you use them in accordance with their "
        "own requirements."
    );
    const QString label_ip_warning = tr(
        "WARNING. Providing incorrect information here may lead to you "
        "VIOLATING copyright law, by using a task for a purpose that is not "
        "permitted, and being subject to damages and/or prosecution."
    );
    const QString label_ip_disclaimer = tr(
        "The authors of CamCOPS cannot be held responsible or liable for any "
        "consequences of you misusing materials subject to copyright."
    );
    const QString label_ip_preamble
        = tr("Are you using this application for:");

    FieldRefPtr commercial_fr
        = app.storedVarFieldRef(varconst::IP_USE_COMMERCIAL);
    FieldRefPtr educational_fr
        = app.storedVarFieldRef(varconst::IP_USE_EDUCATIONAL);
    FieldRefPtr research_fr = app.storedVarFieldRef(varconst::IP_USE_RESEARCH);

    connect(
        m_ip_clinical_fr.data(),
        &FieldRef::valueChanged,
        this,
        &SettingsMenu::ipClinicalChanged,
        Qt::UniqueConnection
    );

    // I tried putting these in a grid, but when you have just QuMCQ/horizontal
    // on the right, it expands too much vertically. Layout problem,
    // likely to do with FlowLayout (which is Qt code).
    // Probably fixed now; anyway, this is fine.
    QuPagePtr page(new QuPage{
        new QuText(label_ip_reason),
        (new QuText(label_ip_warning))->setBold(true),
        (new QuText(label_ip_disclaimer))->setItalic(true),
        new QuText(label_ip_preamble),

        (new QuText(tr("Clinical use?")))->setBold(true),
        (new QuMcq(m_ip_clinical_fr, CommonOptions::unknownNoYesInteger()))
            ->setHorizontal(true),
        (new QuText(
             tr("WARNING: NOT FOR GENERAL CLINICAL USE; not a Medical Device; "
                "see Terms and Conditions")
         ))
            ->setWarning(true)
            ->addTag(TAG_IP_CLINICAL_WARNING),

        (new QuText(tr("Commercial use?")))->setBold(true),
        (new QuMcq(commercial_fr, CommonOptions::unknownNoYesInteger()))
            ->setHorizontal(true),

        (new QuText(tr("Educational use?")))->setBold(true),
        (new QuMcq(educational_fr, CommonOptions::unknownNoYesInteger()))
            ->setHorizontal(true),

        (new QuText(tr("Research use?")))->setBold(true),
        (new QuMcq(research_fr, CommonOptions::unknownNoYesInteger()))
            ->setHorizontal(true),
    });
    page->setTitle(tr("Intellectual property (IP) permissions"));
    page->setType(QuPage::PageType::Config);

    m_ip_questionnaire = new Questionnaire(m_app, {page});
    m_ip_questionnaire->setFinishButtonIconToTick();
    connect(
        m_ip_questionnaire,
        &Questionnaire::completed,
        this,
        &SettingsMenu::ipSaved
    );
    connect(
        m_ip_questionnaire,
        &Questionnaire::cancelled,
        this,
        &SettingsMenu::ipCancelled
    );
    ipClinicalChanged();  // sets warning visibility
    return m_ip_questionnaire;
}

void SettingsMenu::ipClinicalChanged()
{
    if (!m_ip_questionnaire || !m_ip_clinical_fr) {
        return;
    }
    const bool show = m_ip_clinical_fr->value() != CommonOptions::NO_INT;
    m_ip_questionnaire->setVisibleByTag(TAG_IP_CLINICAL_WARNING, show);
}

void SettingsMenu::ipSaved()
{
    m_app.saveCachedVars();
    m_ip_questionnaire = nullptr;
}

void SettingsMenu::ipCancelled()
{
    m_app.clearCachedVars();
    m_ip_questionnaire = nullptr;
}

OpenableWidget* SettingsMenu::configureUser(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    const bool storing_password = app.storingServerPassword();

    const QString label_server = tr("Interactions with the server");
    FieldRefPtr devicename_fr
        = app.storedVarFieldRef(varconst::DEVICE_FRIENDLY_NAME);
    const QString devicename_t = tr("Device friendly name");
    const QString devicename_h = tr("e.g. “Research tablet 17 (Bob’s)”");
    FieldRefPtr username_fr = app.storedVarFieldRef(varconst::SERVER_USERNAME);
    const QString username_t = tr("Username on server");
    // Safe object lifespan signal: can use std::bind
    FieldRef::GetterFunction getter
        = std::bind(&SettingsMenu::serverPasswordGetter, this);
    FieldRef::SetterFunction setter = std::bind(
        &SettingsMenu::serverPasswordSetter, this, std::placeholders::_1
    );
    FieldRefPtr password_fr = FieldRefPtr(new FieldRef(getter, setter, true));
    const QString password_t = tr("Password on server");
    FieldRefPtr upload_after_edit_fr
        = app.storedVarFieldRef(varconst::OFFER_UPLOAD_AFTER_EDIT);
    const QString upload_after_edit_t
        = tr("Offer to upload every time a task is edited?");

    const QString label_clinician
        = tr("Default clinician/researcher’s details (to save you typing)");
    FieldRefPtr clin_specialty_fr
        = app.storedVarFieldRef(varconst::DEFAULT_CLINICIAN_SPECIALTY, false);
    const QString clin_specialty_t
        = tr("Default clinician/researcher’s specialty");
    const QString clin_specialty_h = tr("e.g. “Liaison Psychiatry”");
    FieldRefPtr clin_name_fr
        = app.storedVarFieldRef(varconst::DEFAULT_CLINICIAN_NAME, false);
    const QString clin_name_t = tr("Default clinician/researcher’s name");
    const QString clin_name_h = tr("e.g. “Dr Bob Smith”");
    FieldRefPtr clin_profreg_fr = app.storedVarFieldRef(
        varconst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION, false
    );
    const QString clin_profreg_t
        = tr("Default clinician/researcher’s professional registration");
    const QString clin_profreg_h = tr("e.g. “GMC# 12345”");
    FieldRefPtr clin_post_fr
        = app.storedVarFieldRef(varconst::DEFAULT_CLINICIAN_POST, false);
    const QString clin_post_t = tr("Default clinician/researcher’s post");
    const QString clin_post_h = tr("e.g. “Specialist registrar”");
    FieldRefPtr clin_service_fr
        = app.storedVarFieldRef(varconst::DEFAULT_CLINICIAN_SERVICE, false);
    const QString clin_service_t
        = tr("Default clinician/researcher’s service");
    const QString clin_service_h = tr("e.g. “Liaison Psychiatry Service”");
    FieldRefPtr clin_contact_fr = app.storedVarFieldRef(
        varconst::DEFAULT_CLINICIAN_CONTACT_DETAILS, false
    );
    const QString clin_contact_t
        = tr("Default clinician/researcher’s contact details");
    const QString clin_contact_h = tr("e.g. “x2167”");

    auto g = new QuGridContainer();
    g->setColumnStretch(0, 1);
    g->setColumnStretch(1, 1);
    int row = 0;
    const Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    g->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(devicename_t, devicename_h, true)))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g->addCell(QuGridCell(
        (new QuLineEdit(devicename_fr))
            ->setHint(stringfunc::makeHint(devicename_t, devicename_h)),
        row,
        1
    ));
    ++row;
    g->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(username_t, "", true)))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g->addCell(QuGridCell(
        (new QuLineEdit(username_fr))
            ->setHint(username_t)
            ->setWidgetInputMethodHints(
                Qt::ImhNoAutoUppercase | Qt::ImhNoPredictiveText
            ),
        row,
        1
    ));
    ++row;
    if (storing_password) {
        g->addCell(QuGridCell(
            (new QuText(stringfunc::makeTitle(password_t, "", true)))
                ->setTextAlignment(labelalign),
            row,
            0
        ));
        g->addCell(QuGridCell(
            (new QuLineEdit(password_fr))
                ->setHint(password_t)
                ->setEchoMode(QLineEdit::Password),
            row,
            1
        ));
        ++row;
    }
    g->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(upload_after_edit_t)))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g->addCell(QuGridCell(
        (new QuMcq(upload_after_edit_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true),
        row,
        1
    ));
    ++row;

    QuPagePtr page(new QuPage{
        (new QuText(label_server))->setItalic(true),
        g,
        new QuHorizontalLine(),
        (new QuText(label_clinician))->setItalic(true),
        questionnairefunc::defaultGridRawPointer(
            {
                {stringfunc::makeTitle(
                     clin_specialty_t, clin_specialty_h, true
                 ),
                 (new QuLineEdit(clin_specialty_fr))
                     ->setHint(stringfunc::makeHint(
                         clin_specialty_t, clin_specialty_h
                     ))},
                {stringfunc::makeTitle(clin_name_t, clin_name_h, true),
                 (new QuLineEdit(clin_name_fr))
                     ->setHint(stringfunc::makeHint(clin_name_t, clin_name_h)
                     )},
                {stringfunc::makeTitle(clin_profreg_t, clin_profreg_h, true),
                 (new QuLineEdit(clin_profreg_fr))
                     ->setHint(
                         stringfunc::makeHint(clin_profreg_t, clin_profreg_h)
                     )},
                {stringfunc::makeTitle(clin_post_t, clin_post_h, true),
                 (new QuLineEdit(clin_post_fr))
                     ->setHint(stringfunc::makeHint(clin_post_t, clin_post_h)
                     )},
                {stringfunc::makeTitle(clin_service_t, clin_service_h, true),
                 (new QuLineEdit(clin_service_fr))
                     ->setHint(
                         stringfunc::makeHint(clin_service_t, clin_service_h)
                     )},
                {stringfunc::makeTitle(clin_contact_t, clin_contact_h, true),
                 (new QuLineEdit(clin_contact_fr))
                     ->setHint(
                         stringfunc::makeHint(clin_contact_t, clin_contact_h)
                     )},
            },
            1,
            1
        ),
    });
    page->setTitle(tr("User settings"));
    page->setType(QuPage::PageType::Config);

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    connect(
        questionnaire,
        &Questionnaire::completed,
        this,
        &SettingsMenu::userSettingsSaved
    );
    connect(
        questionnaire,
        &Questionnaire::cancelled,
        this,
        &SettingsMenu::userSettingsCancelled
    );
    return questionnaire;
}

OpenableWidget* SettingsMenu::setQuestionnaireFontSize(CamcopsApp& app)
{
    auto window = new FontSizeAndDpiWindow(app);

    return window->editor();
}

void SettingsMenu::setPrivilege()
{
    m_app.grantPrivilege();
}

void SettingsMenu::changeAppPassword()
{
    m_app.changeAppPassword();
}

void SettingsMenu::changePrivPassword()
{
    m_app.changePrivPassword();
}

QVariant SettingsMenu::serverPasswordGetter()
{
    if (!m_plaintext_pw_live) {
        m_temp_plaintext_password = m_app.getPlaintextServerPassword();
        m_plaintext_pw_live = true;
    }
    return QVariant(m_temp_plaintext_password);
}

bool SettingsMenu::serverPasswordSetter(const QVariant& value)
{
    const SecureQString value_str = value.toString();
    const bool changed = value_str != m_temp_plaintext_password;
    m_temp_plaintext_password = value_str;
    m_plaintext_pw_live = true;
    return changed;
}

void SettingsMenu::userSettingsSaved()
{
    DbNestableTransaction trans(m_app.sysdb());
    m_app.saveCachedVars();
    if (m_app.storingServerPassword()) {
        m_app.setEncryptedServerPassword(m_temp_plaintext_password);
    } else {
        m_app.setVar(varconst::SERVER_USERPASSWORD_OBSCURED, "");
    }
    m_temp_plaintext_password = "";
    m_plaintext_pw_live = false;
}

void SettingsMenu::userSettingsCancelled()
{
    m_temp_plaintext_password = "";
    m_plaintext_pw_live = false;
    m_app.clearCachedVars();
}

void SettingsMenu::deleteAllExtraStrings()
{
    if (uifunc::confirm(
            tr("<b>Are you sure you want to delete all extra "
               "strings?</b><br>"
               "(To get them back, re-download them "
               "from your server.)"),
            tr("Wipe all extra strings?"),
            tr("Yes, delete them"),
            tr("No! Leave them alone"),
            this
        )) {
        m_app.deleteAllExtraStrings();
    }
}

void SettingsMenu::registerWithServer()
{
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->registerWithServer();
}

void SettingsMenu::fetchAllServerInfo()
{
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->fetchAllServerInfo();
}


#ifdef SETTINGSMENU_OFFER_SPECIFIC_FETCHES
void SettingsMenu::fetchIdDescriptions()
{
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->fetchIdDescriptions();
}

void SettingsMenu::fetchExtraStrings()
{
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->fetchExtraStrings();
}
#endif


OpenableWidget* SettingsMenu::viewServerInformation(CamcopsApp& app)
{
    const QString label_server_address = tr("Server hostname/IP address:");
    const QString label_server_port = tr("Port for HTTPS:");
    const QString label_server_path = tr("Path on server:");
    const QString label_server_timeout = tr("Network timeout (ms):");
    const QString label_last_server_registration
        = tr("Last server registration/ID info acceptance:");
    const QString label_last_successful_upload = tr("Last successful upload:");
    const QString label_dbtitle = tr("Database title (from the server):");
    const QString label_policy_upload = tr("Server’s upload ID policy:");
    const QString label_policy_finalize = tr("Server’s finalizing ID policy:");
    const QString label_server_camcops_version = tr("Server CamCOPS version:");

    const QString data_server_address
        = convert::prettyValue(app.var(varconst::SERVER_ADDRESS));
    const QString data_server_port
        = convert::prettyValue(app.var(varconst::SERVER_PORT));
    const QString data_server_path
        = convert::prettyValue(app.var(varconst::SERVER_PATH));
    const QString data_server_timeout
        = convert::prettyValue(app.var(varconst::SERVER_TIMEOUT_MS));
    const QString data_last_server_registration
        = convert::prettyValue(app.var(varconst::LAST_SERVER_REGISTRATION));
    const QString data_last_successful_upload
        = convert::prettyValue(app.var(varconst::LAST_SUCCESSFUL_UPLOAD));
    const QString data_dbtitle
        = convert::prettyValue(app.var(varconst::SERVER_DATABASE_TITLE));
    const QString data_policy_upload
        = convert::prettyValue(app.var(varconst::ID_POLICY_UPLOAD));
    const QString data_policy_finalize
        = convert::prettyValue(app.var(varconst::ID_POLICY_FINALIZE));
    const QString data_server_camcops_version
        = convert::prettyValue(app.var(varconst::SERVER_CAMCOPS_VERSION));

    const Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    const Qt::Alignment dataalign = Qt::AlignLeft | Qt::AlignTop;

    auto g1 = new QuGridContainer();
    g1->setColumnStretch(0, 1);
    g1->setColumnStretch(1, 1);
    int row = 0;
    g1->addCell(QuGridCell(
        (new QuText(label_server_address))->setTextAlignment(labelalign),
        row,
        0
    ));
    g1->addCell(QuGridCell(
        (new QuText(data_server_address))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;
    g1->addCell(QuGridCell(
        (new QuText(label_server_port))->setTextAlignment(labelalign), row, 0
    ));
    g1->addCell(QuGridCell(
        (new QuText(data_server_port))->setTextAlignment(dataalign)->setBold(),
        row,
        1
    ));
    ++row;
    g1->addCell(QuGridCell(
        (new QuText(label_server_path))->setTextAlignment(labelalign), row, 0
    ));
    g1->addCell(QuGridCell(
        (new QuText(data_server_path))->setTextAlignment(dataalign)->setBold(),
        row,
        1
    ));
    ++row;
    g1->addCell(QuGridCell(
        (new QuText(label_server_timeout))->setTextAlignment(labelalign),
        row,
        0
    ));
    g1->addCell(QuGridCell(
        (new QuText(data_server_timeout))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;

    auto g2 = new QuGridContainer();
    g2->setColumnStretch(0, 1);
    g2->setColumnStretch(1, 1);
    row = 0;
    g2->addCell(QuGridCell(
        (new QuText(label_last_server_registration))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_last_server_registration))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;
    g2->addCell(QuGridCell(
        (new QuText(label_last_successful_upload))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_last_successful_upload))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;
    g2->addCell(QuGridCell(
        (new QuText(label_dbtitle))->setTextAlignment(labelalign), row, 0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_dbtitle))->setTextAlignment(dataalign)->setBold(),
        row,
        1
    ));
    ++row;
    g2->addCell(QuGridCell(
        (new QuText(label_policy_upload))->setTextAlignment(labelalign), row, 0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_policy_upload))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;
    g2->addCell(QuGridCell(
        (new QuText(label_policy_finalize))->setTextAlignment(labelalign),
        row,
        0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_policy_finalize))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;
    g2->addCell(QuGridCell(
        (new QuText(label_server_camcops_version))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    g2->addCell(QuGridCell(
        (new QuText(data_server_camcops_version))
            ->setTextAlignment(dataalign)
            ->setBold(),
        row,
        1
    ));
    ++row;

    auto g3 = new QuGridContainer();
    g3->setColumnStretch(0, 1);
    g3->setColumnStretch(1, 1);
    row = 0;
#ifdef OLD_STYLE_ID_DESCRIPTIONS
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        const QString desc
            = convert::prettyValue(app.var(dbconst::IDDESC_FIELD_FORMAT.arg(n))
            );
        const QString shortdesc = convert::prettyValue(
            app.var(dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n))
        );
#else
    QVector<IdNumDescriptionPtr> descriptions = m_app.getAllIdDescriptions();
    for (const IdNumDescriptionPtr& description : descriptions) {
        const int n = description->whichIdNum();
        const QString desc = description->description();
        const QString shortdesc = description->shortDescription();
#endif
        g3->addCell(QuGridCell(
            (new QuText(
                 tr("Description for patient identifier ") + QString::number(n)
                 + ":"
             ))
                ->setTextAlignment(labelalign),
            row,
            0
        ));
        g3->addCell(QuGridCell(
            (new QuText(desc))->setTextAlignment(dataalign)->setBold(), row, 1
        ));
        ++row;

        g3->addCell(QuGridCell(
            (new QuText(
                 tr("Short description for patient identifier ")
                 + QString::number(n) + ":"
             ))
                ->setTextAlignment(labelalign),
            row,
            0
        ));
        g3->addCell(QuGridCell(
            (new QuText(shortdesc))->setTextAlignment(dataalign)->setBold(),
            row,
            1
        ));
        ++row;
    }

    ExtraString extrastring(m_app, m_app.sysdb());
    QMap<QString, int> count_by_language
        = extrastring.getStringCountByLanguage();
    auto g4 = new QuGridContainer();
    g4->setColumnStretch(0, 1);
    g4->setColumnStretch(1, 1);
    row = 0;
    g4->addCell(QuGridCell(
        (new QuText(tr("Language")))
            ->setTextAlignment(labelalign)
            ->setItalic(),
        row,
        0
    ));
    g4->addCell(QuGridCell(
        (new QuText(tr("Number of strings")))
            ->setTextAlignment(dataalign)
            ->setItalic(),
        row,
        1
    ));
    ++row;
    for (const QString& lang : count_by_language.keys()) {
        const int count = count_by_language[lang];
        g4->addCell(QuGridCell(
            (new QuText(lang.isEmpty() ? "–" : lang))
                ->setTextAlignment(labelalign),
            row,
            0
        ));
        g4->addCell(QuGridCell(
            (new QuText(QString::number(count)))
                ->setTextAlignment(dataalign)
                ->setBold(),
            row,
            1
        ));
        ++row;
    }

    QuPagePtr page(new QuPage{
        g1,
        new QuHorizontalLine(),
        g2,
        new QuHorizontalLine(),
        new QuText(tr("ID number descriptions:")),
        g3,
        new QuHorizontalLine(),
        new QuText(tr("Extra string counts by language:")),
        g4,
    });

    page->setTitle(tr("Show server information"));
    page->setType(QuPage::PageType::Config);

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    questionnaire->setReadOnly(true);
    return questionnaire;
}

void SettingsMenu::dropUnknownTables()
{
    const QString title = tr("Drop unknown tables?");
    DatabaseManager& data_db = m_app.db();
    DatabaseManager& sys_db = m_app.sysdb();
    QStringList data_tables = data_db.tablesNotExplicitlyCreatedByUs();
    QStringList sys_tables = sys_db.tablesNotExplicitlyCreatedByUs();
    data_tables.sort();
    sys_tables.sort();

    if (data_tables.isEmpty() && sys_tables.isEmpty()) {
        uifunc::alert(tr("All is well; no unknown tables."), title);
        return;
    }

    QStringList lines{tr("Delete the following unknown data tables?")};
    lines.append("");
    lines += data_tables;
    lines.append("");
    lines.append(tr("... and the following unknown system tables?"));
    lines.append("");
    lines += sys_tables;
    if (!uifunc::confirm(
            lines.join("\n"), title, tr("Yes, drop"), tr("No, cancel"), this
        )) {
        return;
    }
    data_db.dropTablesNotExplicitlyCreatedByUs();
    sys_db.dropTablesNotExplicitlyCreatedByUs();
    uifunc::alert(tr("Tables dropped."), title);
}

void SettingsMenu::viewDataDbAsSql()
{
#ifdef OFFER_VIEW_SQL
    viewDbAsSql(m_app.db(), tr("Main data database"));
#endif
}

void SettingsMenu::viewSystemDbAsSql()
{
#ifdef OFFER_VIEW_SQL
    viewDbAsSql(m_app.sysdb(), tr("CamCOPS system database"));
#endif
}

void SettingsMenu::viewDbAsSql(DatabaseManager& db, const QString& title)
{
    QString sql;
    {  // block ensures stream is flushed by the time we read the string
        SlowGuiGuard guard = m_app.getSlowGuiGuard();
        QTextStream os(&sql);
        dumpsql::dumpDatabase(os, db);
    }
    LogMessageBox box(this, title, sql);
    box.exec();
}

void SettingsMenu::debugDataDbAsSql()
{
    debugDbAsSql(m_app.db(), tr("Data"));
}

void SettingsMenu::debugSystemDbAsSql()
{
    debugDbAsSql(m_app.sysdb(), tr("System"));
}

void SettingsMenu::debugDbAsSql(DatabaseManager& db, const QString& prefix)
{
    {  // guard block
        SlowGuiGuard guard = m_app.getSlowGuiGuard(
            tr("Sending data..."), TextConst::pleaseWait()
        );
        QString sql;
        {  // block ensures stream is flushed by the time we read the string
            QTextStream os(&sql);
            dumpsql::dumpDatabase(os, db);
        }
        qInfo().noquote().nospace() << sql;
    }
    uifunc::alert(
        prefix + " " + tr("database sent to debugging stream"), tr("Finished")
    );
}

void SettingsMenu::saveDataDbAsSql()
{
    saveDbAsSql(
        m_app.db(),
        tr("Save data database as..."),
        tr("Data database written to:")
    );
}

void SettingsMenu::saveSystemDbAsSql()
{
    saveDbAsSql(
        m_app.sysdb(),
        tr("Save system database as..."),
        tr("System database written to:")
    );
}

void SettingsMenu::saveDbAsSql(
    DatabaseManager& db,
    const QString& save_title,
    const QString& finish_prefix
)
{
    const QString filename = QFileDialog::getSaveFileName(this, save_title);
    if (filename.isEmpty()) {
        return;  // user cancelled
    }
    QFile file(filename);
    file.open(QIODevice::WriteOnly | QIODevice::Text);
    if (!file.isOpen()) {
        uifunc::alert(tr("Unable to open file: ") + filename, tr("Failure"));
        return;
    }
    QTextStream os(&file);
    dumpsql::dumpDatabase(os, db);
    uifunc::alert(
        finish_prefix + " " + filename + "\n"
            + tr("You can import it into SQLite with a command like")
            + " \"sqlite3 newdb.sqlite < mydump.sql\"",
        tr("Success")
    );
}

void SettingsMenu::viewDataCounts()
{
    viewCounts(m_app.db(), tr("Record counts for data database"));
}

void SettingsMenu::viewSystemCounts()
{
    viewCounts(m_app.sysdb(), tr("Record counts for system database"));
}

void SettingsMenu::viewCounts(DatabaseManager& db, const QString& title)
{
    const QStringList tables = db.getAllTables();
    QStringList lines;
    for (const QString& table : tables) {
        const int count = db.count(table);
        lines.append(QString("%1: <b>%2</b>").arg(table).arg(count));
    }
    const QString text = lines.join("<br>");
    LogMessageBox box(this, title, text, true);
    box.exec();
}

void SettingsMenu::chooseLanguage()
{
    uifunc::chooseLanguage(m_app, this);
}

void SettingsMenu::changeMode()
{
    m_app.setModeFromUser();
}

void SettingsMenu::changeUserAgent()
{
    m_app.setUserAgentFromUser();
}
