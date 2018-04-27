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

#define OFFER_VIEW_SQL  // debugging only

#include "settingsmenu.h"
#include <QDebug>
#include <QFileDialog>
#include <QTextStream>
#include "common/design_defines.h"
#include "common/platform.h"
#include "common/uiconst.h"
#include "common/varconst.h"
#include "core/networkmanager.h"
#include "db/databasemanager.h"
#include "db/dbnestabletransaction.h"
#include "db/dumpsql.h"
#include "db/fieldref.h"
#include "dbobjects/idnumdescription.h"
#include "dialogs/logmessagebox.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "menu/testmenu.h"
#include "menu/whiskermenu.h"
#include "menulib/menuitem.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/qutext.h"
#include "widgets/labelwordwrapwide.h"
#include "lib/slowguiguard.h"

// For font size settings:
const QString TAG_NORMAL("Normal");
const QString TAG_BIG("Big");
const QString TAG_HEADING("Heading");
const QString TAG_TITLE("Title");
const QString TAG_MENUS("Menus");
const QString alphabet("ABCDEFGHIJKLMNOPQRSTUVWXYZ "
                       "abcdefghijklmnopqrstuvwxyz "
                       "0123456789");
const QMap<QString, uiconst::FontSize> FONT_SIZE_MAP{
    {TAG_NORMAL, uiconst::FontSize::Normal},
    {TAG_BIG, uiconst::FontSize::Big},
    {TAG_HEADING, uiconst::FontSize::Heading},
    {TAG_TITLE, uiconst::FontSize::Title},
    {TAG_MENUS, uiconst::FontSize::Menus},
};

// For IP settings:
const QString TAG_IP_CLINICAL_WARNING("clinical");


SettingsMenu::SettingsMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Settings"),
               uifunc::iconFilename(uiconst::ICON_SETTINGS)),
    m_plaintext_pw_live(false),
    m_fontsize_questionnaire(nullptr),
    m_ip_questionnaire(nullptr)
{
    m_fontsize_fr = m_app.storedVarFieldRef(
                varconst::QUESTIONNAIRE_SIZE_PERCENT, true);
    m_ip_clinical_fr = m_app.storedVarFieldRef(
                varconst::IP_USE_CLINICAL, false);
    const QString spanner(uifunc::iconFilename(uiconst::CBS_SPANNER));

    // Safe object lifespan signal: can use std::bind
    m_items = {
        MenuItem(
            tr("Questionnaire font size"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SettingsMenu::setQuestionnaireFontSize, this,
                          std::placeholders::_1)
            )
        ).setNotIfLocked(),
        MenuItem(
            tr("User settings"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SettingsMenu::configureUser, this,
                          std::placeholders::_1)
            )
        ).setNotIfLocked(),
        MenuItem(
            tr("Intellectual property (IP) permissions"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SettingsMenu::configureIntellectualProperty, this,
                          std::placeholders::_1)
            )
        ).setNotIfLocked(),
        MenuItem(
            tr("Change app password"),
            std::bind(&SettingsMenu::changeAppPassword, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Show server information"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SettingsMenu::viewServerInformation, this,
                          std::placeholders::_1)
            )
        ).setNotIfLocked(),
        MenuItem(
            tr("Re-accept ID descriptions from the server"),
            std::bind(&SettingsMenu::fetchIdDescriptions, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Re-fetch extra task strings from the server"),
            std::bind(&SettingsMenu::fetchExtraStrings, this)
        ).setNotIfLocked(),
        MAKE_MENU_MENU_ITEM(WhiskerMenu, app).setNotIfLocked(),
        MAKE_MENU_MENU_ITEM(TestMenu, app),
        MenuItem(
            tr("Set privileged mode (for items marked †)"),
            std::bind(&SettingsMenu::setPrivilege, this)
        ).setNotIfLocked(),
        // PRIVILEGED FUNCTIONS BELOW HERE
        MenuItem(
            tr("(†) Configure server settings"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SettingsMenu::configureServer, this,
                          std::placeholders::_1)
            )
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Register this device with the server"),
            std::bind(&SettingsMenu::registerWithServer, this)
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Change privileged-mode password"),
            std::bind(&SettingsMenu::changePrivPassword, this)
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Wipe extra strings downloaded from server"),
            [this](){ deleteAllExtraStrings(); }  // alternative lambda syntax
        ).setNeedsPrivilege(),
#ifdef OFFER_VIEW_SQL
        MenuItem(
            tr("(†) View data database as SQL"),
            std::bind(&SettingsMenu::viewDataDbAsSql, this),
            spanner
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) View system database as SQL"),
            std::bind(&SettingsMenu::viewSystemDbAsSql, this),
            spanner
        ).setNeedsPrivilege(),
#endif
        MenuItem(
            tr("(†) View record counts for all data tables"),
            std::bind(&SettingsMenu::viewDataCounts, this),
            spanner
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) View record counts for all system tables"),
            std::bind(&SettingsMenu::viewSystemCounts, this),
            spanner
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Send decrypted data database to debugging stream"),
            std::bind(&SettingsMenu::debugDataDbAsSql, this),
            spanner
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Send decrypted system database to debugging stream"),
            std::bind(&SettingsMenu::debugSystemDbAsSql, this),
            spanner
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Dump decrypted data database to SQL file (not on iOS)"),
            std::bind(&SettingsMenu::saveDataDbAsSql, this),
            spanner
        ).setNeedsPrivilege().setUnsupported(platform::PLATFORM_IOS),
        MenuItem(
            tr("(†) Dump decrypted system database to SQL file (not on iOS)"),
            std::bind(&SettingsMenu::saveSystemDbAsSql, this),
            spanner
        ).setNeedsPrivilege().setUnsupported(platform::PLATFORM_IOS),
    };
    connect(&m_app, &CamcopsApp::fontSizeChanged,
            this, &SettingsMenu::reloadStyleSheet);
}


OpenableWidget* SettingsMenu::configureServer(CamcopsApp& app)
{
    // The general options here: have the Questionnaire save directly to the
    // StoredVar but in a way that's not permanent and allows "recall/reload"
    // upon cancel; or temporary local storage with writing to the StoredVar
    // on OK. The latter is a generally better principle. Since C++ lambda
    // functions don't extend the life of things they reference (see "dangling
    // references" in the spec), the best way is by having the CamcopsApp
    // (whose lifespan is guaranteed to be long enough) to do the storage,
    // and having a fieldref to a cached storedvar.
    // A third option is to use a database transaction (and forgo or invalidate
    // any copies of storedvars maintained in memory).

    app.clearCachedVars();  // ... in case any are left over

    FieldRefPtr address_fr = app.storedVarFieldRef(varconst::SERVER_ADDRESS);
    const QString address_t = tr("Server address");
    const QString address_h = tr("host name or IP address");

    FieldRefPtr port_fr = app.storedVarFieldRef(varconst::SERVER_PORT);
    const QString port_t = tr("Server port for HTTPS");
    const QString port_h = tr("default 443");

    FieldRefPtr path_fr = app.storedVarFieldRef(varconst::SERVER_PATH);
    const QString path_t = tr("Path on server");
    const QString path_h = tr("no leading /; e.g. camcops/database");

    FieldRefPtr timeout_fr = app.storedVarFieldRef(varconst::SERVER_TIMEOUT_MS);
    const QString timeout_t = tr("Network timeout (ms)");
    const QString timeout_h = tr("e.g. 50000");

#ifdef DEBUG_OFFER_HTTP_TO_SERVER
    FieldRefPtr https_fr = app.storedVarFieldRef(varconst::DEBUG_USE_HTTPS_TO_SERVER);
    const QString https_t = tr("Use HTTPS to server?");
    const QString https_h = tr("You should <b>only</b> disable this for debugging!");
#endif

    FieldRefPtr ssl_fr = app.storedVarFieldRef(
                varconst::VALIDATE_SSL_CERTIFICATES);
    const QString ssl_t = tr("Validate HTTPS (TLS/SSL) certificates?");
    const QString ssl_h = tr("Should always be YES for security-conscious "
                             "systems.");

    FieldRefPtr ssl_proto_fr = app.storedVarFieldRef(varconst::SSL_PROTOCOL);
    const QString ssl_proto_t = tr("HTTPS (TLS/SSL) protocol?");
    const QString ssl_proto_h = tr("Stick with the default unless your server "
                                   "can’t cope with it.");

    FieldRefPtr storepw_fr = app.storedVarFieldRef(varconst::STORE_SERVER_PASSWORD);
    const QString storepw_t = tr("Store user’s server password?");
    const QString storepw_h = tr(
                "NO = fractionally more secure; YES = more convenient/"
                "fractionally less secure, but still AES-256-encrypted.");

#ifdef ALLOW_SEND_ANALYTICS
    FieldRefPtr analytics_fr = app.storedVarFieldRef(varconst::SEND_ANALYTICS);
    const QString analytics_t = tr("Send analytics to CamCOPS base?");
    const QString analytics_h = tr(
        "We’d very much appreciate you saying yes; it allows us to support "
        "users better. No patient-identifiable information, per-patient "
        "information, or task details are sent. See the documentation for "
        "details.");
#endif

    const NameValueOptions options_ssl_protocol{
        // http://doc.qt.io/qt-5/qssl.html#SslProtocol-enum
        {"Known secure [default]", convert::SSLPROTODESC_SECUREPROTOCOLS},
        {"(†) SSL v3", convert::SSLPROTODESC_SSLV3},
        {"(†) SSL v2", convert::SSLPROTODESC_SSLV2},
        {"(†) TLS v1.0", convert::SSLPROTODESC_TLSV1_0},
        {"(†) TLS v1.0 or later", convert::SSLPROTODESC_TLSV1_0_OR_LATER},
        {"TLS v1.1", convert::SSLPROTODESC_TLSV1_1},
        {"TLS v1.1 or later", convert::SSLPROTODESC_TLSV1_1_OR_LATER},
        {"TLS v1.2", convert::SSLPROTODESC_TLSV1_2},
        {"TLS v1.2 or later", convert::SSLPROTODESC_TLSV1_2_OR_LATER},
        {"(†) SSLv2, SSLv3, or TLSv1.0", convert::SSLPROTODESC_ANYPROTOCOL},
        {"(†) TLS v1.0 or SSL v3", convert::SSLPROTODESC_TLSV1_SSLV3},
    };
    const QString ssl_proto_explanation = "(†) Insecure, deprecated.";

    QuPagePtr page(new QuPage{
        questionnairefunc::defaultGridRawPointer({
            {
                makeTitle(address_t, address_h, true),
                (new QuLineEdit(address_fr))->setHint(
                    makeHint(address_t, address_h))
            },
            {
                makeTitle(port_t, port_h, true),
                new QuLineEditInteger(port_fr,
                    uiconst::IP_PORT_MIN, uiconst::IP_PORT_MAX)
            },
            {
                makeTitle(path_t, path_h, true),
                (new QuLineEdit(path_fr))->setHint(makeHint(path_t, path_h))
            },
            {
                makeTitle(timeout_t, timeout_h, true),
                new QuLineEditInteger(timeout_fr,
                    uiconst::NETWORK_TIMEOUT_MS_MIN,
                    uiconst::NETWORK_TIMEOUT_MS_MAX)
            },
        }, 1, 1),

#ifdef DEBUG_OFFER_HTTP_TO_SERVER
       new QuText(makeTitle(https_t, https_h)),
       (new QuMcq(https_fr, CommonOptions::yesNoBoolean()))
                       ->setHorizontal(true)
                       ->setAsTextButton(true),
#endif

        new QuText(makeTitle(ssl_t, ssl_h)),
        (new QuMcq(ssl_fr, CommonOptions::yesNoBoolean()))
                       ->setHorizontal(true)
                       ->setAsTextButton(true),

        new QuText(makeTitle(ssl_proto_t, ssl_proto_h)),
        (new QuMcq(ssl_proto_fr, options_ssl_protocol))
                       ->setHorizontal(true)
                       ->setAsTextButton(true),
        new QuText(ssl_proto_explanation),

        new QuHorizontalLine(),

        new QuText(makeTitle(storepw_t, storepw_h)),
        (new QuMcq(storepw_fr, CommonOptions::yesNoBoolean()))
                       ->setHorizontal(true)
                       ->setAsTextButton(true),

#ifdef ALLOW_SEND_ANALYTICS
        new QuHorizontalLine(),

        new QuText(makeTitle(analytics_t, analytics_h)),
        (new QuMcq(analytics_fr, CommonOptions::yesNoBoolean()))
                       ->setHorizontal(true)
                       ->setAsTextButton(true),
#endif
    });
    page->setTitle(tr("Configure server settings"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    connect(questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::serverSettingsSaved);
    connect(questionnaire, &Questionnaire::cancelled,
            &app, &CamcopsApp::clearCachedVars);
    return questionnaire;
}


OpenableWidget* SettingsMenu::configureIntellectualProperty(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    const QString label_ip_reason = tr(
        "The settings here influence whether CamCOPS will consider some "
        "third-party tasks “permitted” on your behalf, according to their "
        "published use criteria. They do <b>not</b> remove your "
        "responsibility to ensure that you use them in accordance with their "
        "own requirements.");
    const QString label_ip_warning = tr(
        "WARNING. Providing incorrect information here may lead to you "
        "VIOLATING copyright law, by using a task for a purpose that is not "
        "permitted, and being subject to damages and/or prosecution.");
    const QString label_ip_disclaimer = tr(
        "The authors of CamCOPS cannot be held responsible or liable for any "
        "consequences of you misusing materials subject to copyright."
    );
    const QString label_ip_preamble = tr("Are you using this application for:");

    FieldRefPtr commercial_fr = app.storedVarFieldRef(varconst::IP_USE_COMMERCIAL);
    FieldRefPtr educational_fr = app.storedVarFieldRef(varconst::IP_USE_EDUCATIONAL);
    FieldRefPtr research_fr = app.storedVarFieldRef(varconst::IP_USE_RESEARCH);

    connect(m_ip_clinical_fr.data(), &FieldRef::valueChanged,
            this, &SettingsMenu::ipClinicalChanged,
            Qt::UniqueConnection);

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
        (new QuMcq(m_ip_clinical_fr,
                   CommonOptions::unknownNoYesInteger()))->setHorizontal(true),
        (new QuText(tr("WARNING: NOT FOR GENERAL CLINICAL USE; not a Medical Device; "
                       "see Terms and Conditions")))
                       ->setWarning(true)
                       ->addTag(TAG_IP_CLINICAL_WARNING),

        (new QuText(tr("Commercial use?")))->setBold(true),
        (new QuMcq(commercial_fr,
                   CommonOptions::unknownNoYesInteger()))->setHorizontal(true),

        (new QuText(tr("Educational use?")))->setBold(true),
        (new QuMcq(educational_fr,
                   CommonOptions::unknownNoYesInteger()))->setHorizontal(true),

        (new QuText(tr("Research use?")))->setBold(true),
        (new QuMcq(research_fr,
                   CommonOptions::unknownNoYesInteger()))->setHorizontal(true),
    });
    page->setTitle(tr("Intellectual property (IP) permissions"));
    page->setType(QuPage::PageType::Config);

    m_ip_questionnaire = new Questionnaire(m_app, {page});
    m_ip_questionnaire->setFinishButtonIconToTick();
    connect(m_ip_questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::ipSaved);
    connect(m_ip_questionnaire, &Questionnaire::cancelled,
            this, &SettingsMenu::ipCancelled);
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
    FieldRefPtr devicename_fr = app.storedVarFieldRef(varconst::DEVICE_FRIENDLY_NAME);
    const QString devicename_t = tr("Device friendly name");
    const QString devicename_h = tr("e.g. “Research tablet 17 (Bob’s)”");
    FieldRefPtr username_fr = app.storedVarFieldRef(varconst::SERVER_USERNAME);
    const QString username_t = tr("Username on server");
    // Safe object lifespan signal: can use std::bind
    FieldRef::GetterFunction getter = std::bind(
                &SettingsMenu::serverPasswordGetter, this);
    FieldRef::SetterFunction setter = std::bind(
                &SettingsMenu::serverPasswordSetter, this, std::placeholders::_1);
    FieldRefPtr password_fr = FieldRefPtr(new FieldRef(getter, setter, true));
    const QString password_t = tr("Password on server");
    FieldRefPtr upload_after_edit_fr = app.storedVarFieldRef(varconst::OFFER_UPLOAD_AFTER_EDIT);
    const QString upload_after_edit_t = tr("Offer to upload every time a task is edited?");

    const QString label_clinician = tr("Default clinician’s details (to save you typing)");
    FieldRefPtr clin_specialty_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_SPECIALTY, false);
    const QString clin_specialty_t = tr("Default clinician’s specialty");
    const QString clin_specialty_h = tr("e.g. “Liaison Psychiatry”");
    FieldRefPtr clin_name_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_NAME, false);
    const QString clin_name_t = tr("Default clinician’s name");
    const QString clin_name_h = tr("e.g. “Dr Bob Smith”");
    FieldRefPtr clin_profreg_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION, false);
    const QString clin_profreg_t = tr("Default clinician’s professional registration");
    const QString clin_profreg_h = tr("e.g. “GMC# 12345”");
    FieldRefPtr clin_post_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_POST, false);
    const QString clin_post_t = tr("Default clinician’s post");
    const QString clin_post_h = tr("e.g. “Specialist registrar");
    FieldRefPtr clin_service_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_SERVICE, false);
    const QString clin_service_t = tr("Default clinician’s service");
    const QString clin_service_h = tr("e.g. “Liaison Psychiatry Service”");
    FieldRefPtr clin_contact_fr = app.storedVarFieldRef(
                varconst::DEFAULT_CLINICIAN_CONTACT_DETAILS, false);
    const QString clin_contact_t = tr("Default clinician’s contact details");
    const QString clin_contact_h = tr("e.g. “x2167”");

    QuGridContainer* g = new QuGridContainer();
    g->setColumnStretch(0, 1);
    g->setColumnStretch(1, 1);
    int row = 0;
    Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    g->addCell(QuGridCell(
        (new QuText(makeTitle(devicename_t, devicename_h, true)))
            ->setAlignment(labelalign),
        row, 0));
    g->addCell(QuGridCell(
        (new QuLineEdit(devicename_fr))
            ->setHint(makeHint(devicename_t, devicename_h)),
        row, 1));
    ++row;
    g->addCell(QuGridCell(
        (new QuText(makeTitle(username_t, "", true)))
            ->setAlignment(labelalign),
        row, 0));
    g->addCell(QuGridCell(
        (new QuLineEdit(username_fr))
            ->setHint(username_t),
        row, 1));
    ++row;
    if (storing_password) {
        g->addCell(QuGridCell(
            (new QuText(makeTitle(password_t, "", true)))
                ->setAlignment(labelalign),
            row, 0));
        g->addCell(QuGridCell(
            (new QuLineEdit(password_fr))
                ->setHint(password_t)
                ->setEchoMode(QLineEdit::Password),
            row, 1));
        ++row;
    }
    g->addCell(QuGridCell(
        (new QuText(makeTitle(upload_after_edit_t)))
            ->setAlignment(labelalign),
        row, 0));
    g->addCell(QuGridCell(
        (new QuMcq(upload_after_edit_fr,CommonOptions::yesNoBoolean()))
            ->setHorizontal(true),
        row, 1));
    ++row;

    QuPagePtr page(new QuPage{
        (new QuText(label_server))->setItalic(true),
        g,
        new QuHorizontalLine(),
        (new QuText(label_clinician))->setItalic(true),
        questionnairefunc::defaultGridRawPointer({
            {
                makeTitle(clin_specialty_t, clin_specialty_h, true),
                (new QuLineEdit(clin_specialty_fr))->setHint(
                    makeHint(clin_specialty_t, clin_specialty_h))
            },
            {
                makeTitle(clin_name_t, clin_name_h, true),
                (new QuLineEdit(clin_name_fr))->setHint(
                    makeHint(clin_name_t, clin_name_h))
            },
            {
                makeTitle(clin_profreg_t, clin_profreg_h, true),
                (new QuLineEdit(clin_profreg_fr))->setHint(
                    makeHint(clin_profreg_t, clin_profreg_h))
            },
            {
                makeTitle(clin_post_t, clin_post_h, true),
                (new QuLineEdit(clin_post_fr))->setHint(
                    makeHint(clin_post_t, clin_post_h))
            },
            {
                makeTitle(clin_service_t, clin_service_h, true),
                (new QuLineEdit(clin_service_fr))->setHint(
                    makeHint(clin_service_t, clin_service_h))
            },
            {
                makeTitle(clin_contact_t, clin_contact_h, true),
                (new QuLineEdit(clin_contact_fr))->setHint(
                    makeHint(clin_contact_t, clin_contact_h))
            },
        }, 1, 1),
    });
    page->setTitle(tr("User settings"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    connect(questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::userSettingsSaved);
    connect(questionnaire, &Questionnaire::cancelled,
            this, &SettingsMenu::userSettingsCancelled);
    return questionnaire;
}


QString SettingsMenu::demoText(const QString& text,
                               const uiconst::FontSize fontsize_type) const
{
    if (!m_fontsize_fr) {
        return "?";
    }
    const double current_pct = m_fontsize_fr->valueDouble();
    const int font_size_pt = m_app.fontSizePt(fontsize_type, current_pct);
    return QString("%1 [%2 pt] %3")
            .arg(tr(qPrintable(text)))
            .arg(font_size_pt)
            .arg(alphabet);
}


OpenableWidget* SettingsMenu::setQuestionnaireFontSize(CamcopsApp& app)
{
    const int fs_min = 70;
    const int fs_max = 300;
    const int fs_slider_step = 1;
    const int fs_slider_tick_interval = 10;
    QMap<int, QString> ticklabels;
    for (int i = fs_min; i <= fs_max; i += fs_slider_tick_interval) {
        ticklabels[i] = QString("%1").arg(i);
    }

    const QString prompt1(tr("Set the font size, as a percentage of the default."));
    const QString explan(tr("Changes take effect when a screen is reloaded."));
    const QString prompt2(tr("You can type it in:"));
    const QString prompt3(tr("... or set it with a slider:"));
    connect(m_fontsize_fr.data(), &FieldRef::valueChanged,
            this, &SettingsMenu::fontSizeChanged,
            Qt::UniqueConnection);

    QuPagePtr page(new QuPage{
        new QuText(makeTitle(prompt1)),
        new QuText(explan),
        questionnairefunc::defaultGridRawPointer({
            {
                prompt2,
                new QuLineEditInteger(m_fontsize_fr, fs_min, fs_max)
            },
        }, 1, 1),
        new QuText(prompt3),
        (new QuSlider(m_fontsize_fr, fs_min, fs_max, fs_slider_step))
            ->setTickInterval(fs_slider_tick_interval)
            ->setTickPosition(QSlider::TicksBothSides)
            ->setTickLabels(ticklabels)
            ->setTickLabelPosition(QSlider::TicksAbove),
        new QuButton(tr("Reset to 100%"),
                       [this](){ resetFontSize(); }),
        (new QuText(demoText(TAG_NORMAL,
                             uiconst::FontSize::Normal)))->addTag(TAG_NORMAL),
        (new QuText(demoText(TAG_BIG,
                             uiconst::FontSize::Big)))->addTag(TAG_BIG),
        (new QuText(demoText(TAG_HEADING,
                             uiconst::FontSize::Heading)))->addTag(TAG_HEADING),
        (new QuText(demoText(TAG_TITLE,
                             uiconst::FontSize::Title)))->addTag(TAG_TITLE),
        (new QuText(demoText(TAG_MENUS,
                             uiconst::FontSize::Menus)))->addTag(TAG_MENUS),
    });
    page->setTitle(tr("Set questionnaire font size"));
    page->setType(QuPage::PageType::Config);

    m_fontsize_questionnaire = new Questionnaire(app, {page});
    m_fontsize_questionnaire->setFinishButtonIconToTick();
    connect(m_fontsize_questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::fontSettingsSaved);
    connect(m_fontsize_questionnaire, &Questionnaire::cancelled,
            this, &SettingsMenu::fontSettingsCancelled);
    connect(m_fontsize_questionnaire, &Questionnaire::pageAboutToOpen,
            this, &SettingsMenu::fontSizeChanged);
    return m_fontsize_questionnaire;
}


void SettingsMenu::resetFontSize()
{
    if (!m_fontsize_fr) {
        return;
    }
    m_fontsize_fr->setValue(100);
}


void SettingsMenu::fontSizeChanged()
{
    // Slightly nasty code.
    if (!m_fontsize_questionnaire || !m_fontsize_fr) {
        return;
    }
    QuPage* page = m_fontsize_questionnaire->currentPagePtr();
    if (!page) {
        return;
    }
    const double current_pct = m_fontsize_fr->valueDouble();
    QMapIterator<QString, uiconst::FontSize> i(FONT_SIZE_MAP);
    while (i.hasNext()) {
        i.next();
        QString tag = i.key();
        uiconst::FontSize fontsize_type = i.value();
        for (auto e : page->elementsWithTag(tag)) {
            int fontsize_pt = m_app.fontSizePt(fontsize_type, current_pct);
            QString text = demoText(tag, fontsize_type);
            // Here's the slightly nasty bit:
            QuText* textelement = dynamic_cast<QuText*>(e);
            if (!textelement) {
                continue;
            }
            textelement->forceFontSize(fontsize_pt, false);
            textelement->setText(text);
        }
    }
}


void SettingsMenu::fontSettingsSaved()
{
    m_app.saveCachedVars();
    m_fontsize_questionnaire = nullptr;
    // Trigger reloading of reload CSS to SettingsMenu and MainMenu:
    m_app.fontSizeChanged();
}


void SettingsMenu::fontSettingsCancelled()
{
    m_app.clearCachedVars();
    m_fontsize_questionnaire = nullptr;
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


QString SettingsMenu::makeTitle(const QString& part1,
                                const QString& part2,
                                const bool colon) const
{
    QString result;
    if (part2.isEmpty()) {
        result = QString("<b>%1%2</b>").arg(part1).arg(colon ? ":" : "");
    } else {
        result = QString("<b>%1</b> (%2)").arg(part1).arg(part2);
        if (colon) {
            result += ":";
        }
    }
    return result;
}


QString SettingsMenu::makeHint(const QString& part1,
                               const QString& part2) const
{
    return QString("%1 (%2)").arg(part1).arg(part2);
}


void SettingsMenu::serverSettingsSaved()
{
    // User has edited server settings and then clicked OK.
    const bool server_details_changed = (
        m_app.cachedVarChanged(varconst::SERVER_ADDRESS)
        || m_app.cachedVarChanged(varconst::SERVER_PORT)
        || m_app.cachedVarChanged(varconst::SERVER_PATH)
    );
    if (server_details_changed) {
        uifunc::alert(
            tr("Server details have changed. You should consider "
               "re-registering with the server."),
            tr("Registration advised")
        );
    }
    if (!m_app.storingServerPassword()) {
        // Wipe the stored password
        m_app.setCachedVar(varconst::SERVER_USERPASSWORD_OBSCURED, "");
    }
    m_app.saveCachedVars();
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
    if (uifunc::confirm(tr("<b>Are you sure you want to delete all extra "
                           "strings?</b><br>"
                           "(To get them back, re-download them "
                           "from your server.)"),
                        tr("Wipe all extra strings?"),
                        tr("Yes, delete them"),
                        tr("No! Leave them alone"),
                        this)) {
        m_app.deleteAllExtraStrings();
    }
}


void SettingsMenu::registerWithServer()
{
    NetworkManager* netmgr = m_app.networkManager();
    netmgr->registerWithServer();
}


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


OpenableWidget* SettingsMenu::viewServerInformation(CamcopsApp& app)
{
    const QString label_server_address = tr("Server hostname/IP address:");
    const QString label_server_port = tr("Port for HTTPS:");
    const QString label_server_path = tr("Path on server:");
    const QString label_server_timeout = tr("Network timeout (ms):");
    const QString label_last_server_registration = tr(
                "Last server registration/ID info acceptance:");
    const QString label_last_successful_upload = tr("Last successful upload:");
    const QString label_dbtitle = tr("Database title (from the server):");
    const QString label_policy_upload = tr("Server’s upload ID policy:");
    const QString label_policy_finalize = tr("Server’s finalizing ID policy:");
    const QString label_server_camcops_version = tr("Server CamCOPS version:");

    const QString data_server_address = convert::prettyValue(
                app.var(varconst::SERVER_ADDRESS));
    const QString data_server_port = convert::prettyValue(
                app.var(varconst::SERVER_PORT));
    const QString data_server_path = convert::prettyValue(
                app.var(varconst::SERVER_PATH));
    const QString data_server_timeout = convert::prettyValue(
                app.var(varconst::SERVER_TIMEOUT_MS));
    const QString data_last_server_registration = convert::prettyValue(
                app.var(varconst::LAST_SERVER_REGISTRATION));
    const QString data_last_successful_upload = convert::prettyValue(
                app.var(varconst::LAST_SUCCESSFUL_UPLOAD));
    const QString data_dbtitle = convert::prettyValue(
                app.var(varconst::SERVER_DATABASE_TITLE));
    const QString data_policy_upload = convert::prettyValue(
                app.var(varconst::ID_POLICY_UPLOAD));
    const QString data_policy_finalize = convert::prettyValue(
                app.var(varconst::ID_POLICY_FINALIZE));
    const QString data_server_camcops_version = convert::prettyValue(
                app.var(varconst::SERVER_CAMCOPS_VERSION));

    const Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    const Qt::Alignment dataalign = Qt::AlignLeft | Qt::AlignTop;

    QuGridContainer* g1 = new QuGridContainer();
    g1->setColumnStretch(0, 1);
    g1->setColumnStretch(1, 1);
    int row = 0;
    g1->addCell(QuGridCell((new QuText(label_server_address))
                           ->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_address))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_port))
                           ->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_port))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_path))
                           ->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_path))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_timeout))
                           ->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_timeout))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;

    QuGridContainer* g2 = new QuGridContainer();
    g2->setColumnStretch(0, 1);
    g2->setColumnStretch(1, 1);
    row = 0;
    g2->addCell(QuGridCell((new QuText(label_last_server_registration))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_last_server_registration))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_last_successful_upload))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_last_successful_upload))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_dbtitle))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_dbtitle))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_policy_upload))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_policy_upload))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_policy_finalize))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_policy_finalize))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_server_camcops_version))
                           ->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_server_camcops_version))
                           ->setAlignment(dataalign)->setBold(), row, 1));
    ++row;

    QuGridContainer* g3 = new QuGridContainer();
    g3->setColumnStretch(0, 1);
    g3->setColumnStretch(1, 1);
    row = 0;
#if OLD_STYLE_ID_DESCRIPTIONS
    for (int n = 1; n <= dbconst::NUMBER_OF_IDNUMS; ++n) {
        const QString desc = convert::prettyValue(
                    app.var(dbconst::IDDESC_FIELD_FORMAT.arg(n)));
        const QString shortdesc = convert::prettyValue(
                    app.var(dbconst::IDSHORTDESC_FIELD_FORMAT.arg(n)));
#else
    QVector<IdNumDescriptionPtr> descriptions = m_app.getAllIdDescriptions();
    for (IdNumDescriptionPtr description : descriptions) {
        const int n = description->whichIdNum();
        const QString desc = description->description();
        const QString shortdesc = description->shortDescription();
#endif
        g3->addCell(QuGridCell(
            (new QuText(tr("Description for patient identifier ") +
                        QString::number(n) + ":")
            )->setAlignment(labelalign), row, 0));
        g3->addCell(QuGridCell((new QuText(desc))
                               ->setAlignment(dataalign)->setBold(), row, 1));
        ++row;

        g3->addCell(QuGridCell(
            (new QuText(tr("Short description for patient identifier ") +
                        QString::number(n) + ":")
            )->setAlignment(labelalign), row, 0));
        g3->addCell(QuGridCell((new QuText(shortdesc))
                               ->setAlignment(dataalign)->setBold(), row, 1));
        ++row;
    }

    QuPagePtr page(new QuPage{
        g1,
        new QuHorizontalLine(),
        g2,
        new QuHorizontalLine(),
        new QuText(tr("ID number descriptions:")),
        g3,
    });

    page->setTitle(tr("Show server information"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    questionnaire->setReadOnly(true);
    return questionnaire;
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
    { // guard block
        SlowGuiGuard guard = m_app.getSlowGuiGuard(tr("Sending data..."),
                                                   tr("Please wait"));
        QString sql;
        { // block ensures stream is flushed by the time we read the string
            QTextStream os(&sql);
            dumpsql::dumpDatabase(os, db);
        }
        qInfo().noquote().nospace() << sql;
    }
    uifunc::alert(prefix + " "  + tr("database sent to debugging stream"),
                  tr("Finished"));
}


void SettingsMenu::saveDataDbAsSql()
{
    saveDbAsSql(m_app.db(),
                tr("Save data database as..."),
                tr("Data database written to:"));
}


void SettingsMenu::saveSystemDbAsSql()
{
    saveDbAsSql(m_app.sysdb(),
                tr("Save system database as..."),
                tr("System database written to:"));
}


void SettingsMenu::saveDbAsSql(DatabaseManager& db, const QString& save_title,
                               const QString& finish_prefix)
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
    uifunc::alert(finish_prefix + " " + filename + "\n" +
                    tr("You can import it into SQLite with a command like") +
                    " \"sqlite3 newdb.sqlite < mydump.sql\"",
                  tr("Success"));
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
