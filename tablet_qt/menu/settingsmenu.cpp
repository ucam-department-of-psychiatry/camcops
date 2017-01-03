/*
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
#include "common/platform.h"
#include "common/uiconstants.h"
#include "common/varconst.h"
#include "db/dbnestabletransaction.h"
#include "db/fieldref.h"
#include "dialogs/logmessagebox.h"
#include "lib/convert.h"
#include "lib/networkmanager.h"
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

const QString TAG_NORMAL("Normal");
const QString TAG_BIG("Big");
const QString TAG_HEADING("Heading");
const QString TAG_TITLE("Title");
const QString TAG_MENUS("Menus");
const QString alphabet("ABCDEFGHIJKLMNOPQRSTUVWXYZ "
                       "abcdefghijklmnopqrstuvwxyz "
                       "0123456789");
const QMap<QString, UiConst::FontSize> FONT_SIZE_MAP{
    {TAG_NORMAL, UiConst::FontSize::Normal},
    {TAG_BIG, UiConst::FontSize::Big},
    {TAG_HEADING, UiConst::FontSize::Heading},
    {TAG_TITLE, UiConst::FontSize::Title},
    {TAG_MENUS, UiConst::FontSize::Menus},
};


SettingsMenu::SettingsMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Settings"),
               UiFunc::iconFilename(UiConst::ICON_SETTINGS)),
    m_plaintext_pw_live(false),
    m_fontsize_questionnaire(nullptr)
{
    m_fontsize_fr = m_app.storedVarFieldRef(
                VarConst::QUESTIONNAIRE_SIZE_PERCENT, true);
    // Safe object lifespan signal: can use std::bind
    m_items = {
        MenuItem(
            tr("Questionnaire font size"),
            std::bind(&SettingsMenu::setQuestionnaireFontSize, this,
                      std::placeholders::_1)
        ).setNotIfLocked(),
        MenuItem(
            tr("User settings"),
            std::bind(&SettingsMenu::configureUser, this,
                      std::placeholders::_1)
        ).setNotIfLocked(),
        MenuItem(
            tr("Intellectual property (IP) permissions"),
            std::bind(&SettingsMenu::configureIntellectualProperty, this,
                      std::placeholders::_1)
        ).setNotIfLocked(),
        MenuItem(
            tr("Change app password"),
            std::bind(&SettingsMenu::changeAppPassword, this)
        ).setNotIfLocked(),
        MenuItem(
            tr("Show server information"),
            std::bind(&SettingsMenu::viewServerInformation, this,
                      std::placeholders::_1)
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
            std::bind(&SettingsMenu::configureServer, this,
                      std::placeholders::_1)
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
            std::bind(&SettingsMenu::viewDataDbAsSql, this)
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) View system database as SQL"),
            std::bind(&SettingsMenu::viewSystemDbAsSql, this)
        ).setNeedsPrivilege(),
#endif
        MenuItem(
            tr("(†) Send data database to debugging stream"),
            std::bind(&SettingsMenu::debugDataDbAsSql, this)
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Send system database to debugging stream"),
            std::bind(&SettingsMenu::debugSystemDbAsSql, this)
        ).setNeedsPrivilege(),
        MenuItem(
            tr("(†) Dump data database to SQL file (not on iOS)"),
            std::bind(&SettingsMenu::saveDataDbAsSql, this)
        ).setNeedsPrivilege().setUnsupported(Platform::PLATFORM_IOS),
        MenuItem(
            tr("(†) Dump system database to SQL file (not on iOS)"),
            std::bind(&SettingsMenu::saveSystemDbAsSql, this)
        ).setNeedsPrivilege().setUnsupported(Platform::PLATFORM_IOS),
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

    FieldRefPtr ssl_fr = app.storedVarFieldRef(VarConst::VALIDATE_SSL_CERTIFICATES);
    QString ssl_t = tr("Validate SSL certificates?");
    QString ssl_h = tr("Should always be YES for security-conscious systems.");

    FieldRefPtr storepw_fr = app.storedVarFieldRef(VarConst::STORE_SERVER_PASSWORD);
    QString storepw_t = tr("Store user’s server password?");
    QString storepw_h = tr("NO = more secure, YES = more convenient/less secure.");

    FieldRefPtr analytics_fr = app.storedVarFieldRef(VarConst::SEND_ANALYTICS);
    QString analytics_t = tr("Send analytics to CamCOPS base?");
    QString analytics_h = tr(
        "We’d very much appreciate you saying yes; it allows us to support "
        "users better. No patient-identifiable information, per-patient "
        "information, or task details are sent. See the documentation for "
        "details.");

    QuPagePtr page(new QuPage{
        QuestionnaireFunc::defaultGridRawPointer({
            {
                makeTitle(address_t, address_h, true),
                (new QuLineEdit(address_fr))->setHint(
                    makeHint(address_t, address_h))
            },
            {
                makeTitle(port_t, port_h, true),
                new QuLineEditInteger(port_fr,
                    UiConst::IP_PORT_MIN, UiConst::IP_PORT_MAX)
            },
            {
                makeTitle(path_t, path_h, true),
                (new QuLineEdit(path_fr))->setHint(makeHint(path_t, path_h))
            },
            {
                makeTitle(timeout_t, timeout_h, true),
                new QuLineEditInteger(timeout_fr,
                    UiConst::NETWORK_TIMEOUT_MS_MIN,
                    UiConst::NETWORK_TIMEOUT_MS_MAX)
            },
        }, 1, 1),

        new QuText(makeTitle(ssl_t, ssl_h)),
        (new QuMCQ(ssl_fr, CommonOptions::yesNoBoolean()))->setHorizontal(true),

        new QuText(makeTitle(storepw_t, storepw_h)),
        (new QuMCQ(storepw_fr, CommonOptions::yesNoBoolean()))->setHorizontal(true),

        new QuHorizontalLine(),

        new QuText(makeTitle(analytics_t, analytics_h)),
        (new QuMCQ(analytics_fr, CommonOptions::yesNoBoolean()))->setHorizontal(true),
    });
    page->setTitle(tr("Configure server settings"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    connect(questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::serverSettingsSaved);
    connect(questionnaire, &Questionnaire::cancelled,
            &app, &CamcopsApp::clearCachedVars);
    return questionnaire;
}


OpenableWidget* SettingsMenu::configureIntellectualProperty(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    QString label_ip_warning = tr(
        "WARNING. Providing incorrect information here may lead to you "
        "VIOLATING copyright law, by using a task for a purpose that is not "
        "permitted, and being subject to damages and/or prosecution.");
    QString label_ip_disclaimer = tr(
        "The authors of CamCOPS cannot be held responsible or liable for any "
        "consequences of you misusing materials subject to copyright."
    );
    QString label_ip_preamble = tr("Are you using this application for:");

    FieldRefPtr clinical_fr = app.storedVarFieldRef(VarConst::IP_USE_CLINICAL);
    FieldRefPtr commercial_fr = app.storedVarFieldRef(VarConst::IP_USE_COMMERCIAL);
    FieldRefPtr educational_fr = app.storedVarFieldRef(VarConst::IP_USE_EDUCATIONAL);
    FieldRefPtr research_fr = app.storedVarFieldRef(VarConst::IP_USE_RESEARCH);

    // I tried putting these in a grid, but when you have just QuMCQ/horizontal
    // on the right, it expands too much vertically. *** Layout problem,
    // likely to do with FlowLayout (which is Qt code).
    QuPagePtr page(new QuPage{
        (new QuText(label_ip_warning))->bold(true),
        (new QuText(label_ip_disclaimer))->italic(true),
        new QuText(label_ip_preamble),

        (new QuText(tr("Clinical use?")))->bold(true),
        (new QuMCQ(clinical_fr, CommonOptions::unknownNoYesInteger()))->setHorizontal(true),

        (new QuText(tr("Commercial use?")))->bold(true),
        (new QuMCQ(commercial_fr, CommonOptions::unknownNoYesInteger()))->setHorizontal(true),

        (new QuText(tr("Educational use?")))->bold(true),
        (new QuMCQ(educational_fr, CommonOptions::unknownNoYesInteger()))->setHorizontal(true),

        (new QuText(tr("Research use?")))->bold(true),
        (new QuMCQ(research_fr, CommonOptions::unknownNoYesInteger()))->setHorizontal(true),
    });
    page->setTitle(tr("Intellectual property (IP) permissions"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    connect(questionnaire, &Questionnaire::completed,
            &app, &CamcopsApp::saveCachedVars);
    connect(questionnaire, &Questionnaire::cancelled,
            &app, &CamcopsApp::clearCachedVars);
    return questionnaire;
}


OpenableWidget* SettingsMenu::configureUser(CamcopsApp& app)
{
    app.clearCachedVars();  // ... in case any are left over

    bool storing_password = app.storingServerPassword();

    QString label_server = tr("Interactions with the server");
    FieldRefPtr devicename_fr = app.storedVarFieldRef(VarConst::DEVICE_FRIENDLY_NAME);
    QString devicename_t = tr("Device friendly name");
    QString devicename_h = tr("e.g. “Research tablet 17 (Bob’s)”");
    FieldRefPtr username_fr = app.storedVarFieldRef(VarConst::SERVER_USERNAME);
    QString username_t = tr("Username on server");
    // Safe object lifespan signal: can use std::bind
    FieldRef::GetterFunction getter = std::bind(&SettingsMenu::serverPasswordGetter, this);
    FieldRef::SetterFunction setter = std::bind(&SettingsMenu::serverPasswordSetter, this, std::placeholders::_1);
    FieldRefPtr password_fr = FieldRefPtr(new FieldRef(getter, setter, true));
    QString password_t = tr("Password on server");
    FieldRefPtr upload_after_edit_fr = app.storedVarFieldRef(VarConst::OFFER_UPLOAD_AFTER_EDIT);
    QString upload_after_edit_t = tr("Offer to upload every time a task is edited?");

    QString label_clinician = tr("Default clinician’s details (to save you typing)");
    FieldRefPtr clin_specialty_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_SPECIALTY, false);
    QString clin_specialty_t = tr("Default clinician’s specialty");
    QString clin_specialty_h = tr("e.g. “Liaison Psychiatry”");
    FieldRefPtr clin_name_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_NAME, false);
    QString clin_name_t = tr("Default clinician’s name");
    QString clin_name_h = tr("e.g. “Dr Bob Smith”");
    FieldRefPtr clin_profreg_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION, false);
    QString clin_profreg_t = tr("Default clinician’s professional registration");
    QString clin_profreg_h = tr("e.g. “GMC# 12345”");
    FieldRefPtr clin_post_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_POST, false);
    QString clin_post_t = tr("Default clinician’s post");
    QString clin_post_h = tr("e.g. “Specialist registrar");
    FieldRefPtr clin_service_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_SERVICE, false);
    QString clin_service_t = tr("Default clinician’s service");
    QString clin_service_h = tr("e.g. “Liaison Psychiatry Service”");
    FieldRefPtr clin_contact_fr = app.storedVarFieldRef(
                VarConst::DEFAULT_CLINICIAN_CONTACT_DETAILS, false);
    QString clin_contact_t = tr("Default clinician’s contact details");
    QString clin_contact_h = tr("e.g. “x2167”");

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
        (new QuMCQ(upload_after_edit_fr,CommonOptions::yesNoBoolean()))
            ->setHorizontal(true),
        row, 1));
    ++row;

    QuPagePtr page(new QuPage{
        (new QuText(label_server))->italic(true),
        g,
        new QuHorizontalLine(),
        (new QuText(label_clinician))->italic(true),
        QuestionnaireFunc::defaultGridRawPointer({
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
    connect(questionnaire, &Questionnaire::completed,
            this, &SettingsMenu::userSettingsSaved);
    connect(questionnaire, &Questionnaire::cancelled,
            this, &SettingsMenu::userSettingsCancelled);
    return questionnaire;
}


QString SettingsMenu::demoText(const QString& text,
                               UiConst::FontSize fontsize_type) const
{
    if (!m_fontsize_fr) {
        return "?";
    }
    double current_pct = m_fontsize_fr->valueDouble();
    int font_size_pt = m_app.fontSizePt(fontsize_type, current_pct);
    return QString("%1 [%2 pt] %3")
            .arg(tr(qPrintable(text)))
            .arg(font_size_pt)
            .arg(alphabet);
}


OpenableWidget* SettingsMenu::setQuestionnaireFontSize(CamcopsApp &app)
{
    int fs_min = 70;
    int fs_max = 300;
    int fs_slider_step = 1;
    int fs_slider_tick_interval = 10;
    QMap<int, QString> ticklabels;
    for (int i = fs_min; i <= fs_max; i += fs_slider_tick_interval) {
        ticklabels[i] = QString("%1").arg(i);
    }

    QString prompt1(tr("Set the font size, as a percentage of the default."));
    QString explan(tr("Changes take effect when a screen is reloaded."));
    QString prompt2(tr("You can type it in:"));
    QString prompt3(tr("... or set it with a slider:"));
    connect(m_fontsize_fr.data(), &FieldRef::valueChanged,
            this, &SettingsMenu::fontSizeChanged,
            Qt::UniqueConnection);

    QuPagePtr page(new QuPage{
        new QuText(makeTitle(prompt1)),
        new QuText(explan),
        QuestionnaireFunc::defaultGridRawPointer({
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
        (new QuText(demoText(TAG_NORMAL, UiConst::FontSize::Normal)))->addTag(TAG_NORMAL),
        (new QuText(demoText(TAG_BIG, UiConst::FontSize::Big)))->addTag(TAG_BIG),
        (new QuText(demoText(TAG_HEADING, UiConst::FontSize::Heading)))->addTag(TAG_HEADING),
        (new QuText(demoText(TAG_TITLE, UiConst::FontSize::Title)))->addTag(TAG_TITLE),
        (new QuText(demoText(TAG_MENUS, UiConst::FontSize::Menus)))->addTag(TAG_MENUS),
    });
    page->setTitle(tr("Set questionnaire font size"));
    page->setType(QuPage::PageType::Config);

    m_fontsize_questionnaire = new Questionnaire(app, {page});
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
    double current_pct = m_fontsize_fr->valueDouble();
    QMapIterator<QString, UiConst::FontSize> i(FONT_SIZE_MAP);
    while (i.hasNext()) {
        i.next();
        QString tag = i.key();
        UiConst::FontSize fontsize_type = i.value();
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
                                bool colon) const
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
    bool server_details_changed = (
        m_app.cachedVarChanged(VarConst::SERVER_ADDRESS)
        || m_app.cachedVarChanged(VarConst::SERVER_PORT)
        || m_app.cachedVarChanged(VarConst::SERVER_PATH)
    );
    if (server_details_changed) {
        UiFunc::alert(
            tr("Server details have changed. You should consider "
               "re-registering with the server."),
            tr("Registration advised")
        );
    }
    if (!m_app.storingServerPassword()) {
        // Wipe the stored password
        m_app.setCachedVar(VarConst::SERVER_USERPASSWORD_OBSCURED, "");
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
    SecureQString value_str = value.toString();
    bool changed = value_str != m_temp_plaintext_password;
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
        m_app.setVar(VarConst::SERVER_USERPASSWORD_OBSCURED, "");
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
    if (UiFunc::confirm(tr("<b>Are you sure you want to delete all extra "
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
    QString label_server_address = tr("Server hostname/IP address:");
    QString label_server_port = tr("Port for HTTPS:");
    QString label_server_path = tr("Path on server:");
    QString label_server_timeout = tr("Network timeout (ms):");
    QString label_last_server_registration = tr("Last server registration/ID info acceptance:");
    QString label_last_successful_upload = tr("Last successful upload:");
    QString label_dbtitle = tr("Database title (from the server):");
    QString label_policy_upload = tr("Server’s upload ID policy:");
    QString label_policy_finalize = tr("Server’s finalizing ID policy:");
    QString label_server_camcops_version = tr("Server CamCOPS version:");

    QString data_server_address = Convert::prettyValue(app.var(VarConst::SERVER_ADDRESS));
    QString data_server_port = Convert::prettyValue(app.var(VarConst::SERVER_PORT));
    QString data_server_path = Convert::prettyValue(app.var(VarConst::SERVER_PATH));
    QString data_server_timeout = Convert::prettyValue(app.var(VarConst::SERVER_TIMEOUT_MS));
    QString data_last_server_registration = Convert::prettyValue(app.var(VarConst::LAST_SERVER_REGISTRATION));
    QString data_last_successful_upload = Convert::prettyValue(app.var(VarConst::LAST_SUCCESSFUL_UPLOAD));
    QString data_dbtitle = Convert::prettyValue(app.var(VarConst::SERVER_DATABASE_TITLE));
    QString data_policy_upload = Convert::prettyValue(app.var(VarConst::ID_POLICY_UPLOAD));
    QString data_policy_finalize = Convert::prettyValue(app.var(VarConst::ID_POLICY_FINALIZE));
    QString data_server_camcops_version = Convert::prettyValue(app.var(VarConst::SERVER_CAMCOPS_VERSION));

    Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    Qt::Alignment dataalign = Qt::AlignLeft | Qt::AlignTop;

    QuGridContainer* g1 = new QuGridContainer();
    g1->setColumnStretch(0, 1);
    g1->setColumnStretch(1, 1);
    int row = 0;
    g1->addCell(QuGridCell((new QuText(label_server_address))->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_address))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_port))->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_port))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_path))->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_path))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g1->addCell(QuGridCell((new QuText(label_server_timeout))->setAlignment(labelalign), row, 0));
    g1->addCell(QuGridCell((new QuText(data_server_timeout))->setAlignment(dataalign)->bold(), row, 1));
    ++row;

    QuGridContainer* g2 = new QuGridContainer();
    g2->setColumnStretch(0, 1);
    g2->setColumnStretch(1, 1);
    row = 0;
    g2->addCell(QuGridCell((new QuText(label_last_server_registration))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_last_server_registration))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_last_successful_upload))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_last_successful_upload))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_dbtitle))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_dbtitle))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_policy_upload))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_policy_upload))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_policy_finalize))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_policy_finalize))->setAlignment(dataalign)->bold(), row, 1));
    ++row;
    g2->addCell(QuGridCell((new QuText(label_server_camcops_version))->setAlignment(labelalign), row, 0));
    g2->addCell(QuGridCell((new QuText(data_server_camcops_version))->setAlignment(dataalign)->bold(), row, 1));
    ++row;

    QuGridContainer* g3 = new QuGridContainer();
    g3->setColumnStretch(0, 1);
    g3->setColumnStretch(1, 1);
    row = 0;
    for (int n = 1; n <= DbConst::NUMBER_OF_IDNUMS; ++n) {
        g3->addCell(QuGridCell(
            (new QuText(tr("Description for patient identifier ") +
                        QString::number(n) + ":")
            )->setAlignment(labelalign), row, 0));
        QString desc = Convert::prettyValue(app.var(DbConst::IDDESC_FIELD_FORMAT.arg(n)));
        g3->addCell(QuGridCell((new QuText(desc))->setAlignment(dataalign)->bold(), row, 1));
        ++row;

        g3->addCell(QuGridCell(
            (new QuText(tr("Short description for patient identifier ") +
                        QString::number(n) + ":")
            )->setAlignment(labelalign), row, 0));
        QString shortdesc = Convert::prettyValue(app.var(DbConst::IDSHORTDESC_FIELD_FORMAT.arg(n)));
        g3->addCell(QuGridCell((new QuText(shortdesc))->setAlignment(dataalign)->bold(), row, 1));
        ++row;
    }

    QuPagePtr page(new QuPage{
        g1,
        new QuHorizontalLine(),
        g2,
        new QuHorizontalLine(),
        g3,
    });

    page->setTitle(tr("Show server information"));
    page->setType(QuPage::PageType::Config);

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setReadOnly(true);
    return questionnaire;
}

void SettingsMenu::viewDataDbAsSql()
{
#ifdef OFFER_VIEW_SQL
    QString sql;
    { // block ensures stream is flushed by the time we read the string
        SlowGuiGuard guard = m_app.getSlowGuiGuard();
        QTextStream os(&sql);
        m_app.dumpDataDatabase(os);
    }
    LogMessageBox box(this, tr("Main data database"), sql);
    box.exec();
#endif
}


void SettingsMenu::viewSystemDbAsSql()
{
#ifdef OFFER_VIEW_SQL
    QString sql;
    {  // as above
        SlowGuiGuard guard = m_app.getSlowGuiGuard();
        QTextStream os(&sql);
        m_app.dumpSystemDatabase(os);
    }
    LogMessageBox box(this, tr("CamCOPS system database"), sql);
    box.exec();
#endif
}


void SettingsMenu::debugDataDbAsSql()
{
    {
        SlowGuiGuard guard = m_app.getSlowGuiGuard(tr("Sending data..."), tr("Please wait"));
        QString sql;
        {  // as above
            QTextStream os(&sql);
            m_app.dumpDataDatabase(os);
        }
        qInfo().noquote().nospace() << sql;
    }
    UiFunc::alert(tr("Data database sent to debugging stream"), tr("Finished"));
}


void SettingsMenu::debugSystemDbAsSql()
{
    {
        SlowGuiGuard guard = m_app.getSlowGuiGuard(tr("Sending data..."), tr("Please wait"));
        QString sql;
        {  // as above
            QTextStream os(&sql);
            m_app.dumpSystemDatabase(os);
        }
        qInfo().noquote().nospace() << sql;
    }
    UiFunc::alert(tr("Data database sent to debugging stream"), tr("Finished"));
}


void SettingsMenu::saveDataDbAsSql()
{
    QString filename = QFileDialog::getSaveFileName(
                this, tr("Save data database as..."));
    if (filename.isEmpty()) {
        return;  // user cancelled
    }
    QFile file(filename);
    file.open(QIODevice::WriteOnly | QIODevice::Text);
    if (!file.isOpen()) {
        UiFunc::alert(tr("Unable to open file: ") + filename, tr("Failure"));
        return;
    }
    QTextStream os(&file);
    m_app.dumpDataDatabase(os);
    UiFunc::alert(tr("Data database written to: ") + filename, tr("Success"));
}


void SettingsMenu::saveSystemDbAsSql()
{
    QString filename = QFileDialog::getSaveFileName(
                this, tr("Save system database as..."));
    if (filename.isEmpty()) {
        return;  // user cancelled
    }
    QFile file(filename);
    file.open(QIODevice::WriteOnly | QIODevice::Text);
    if (!file.isOpen()) {
        UiFunc::alert(tr("Unable to open file: ") + filename, tr("Failure"));
        return;
    }
    QTextStream os(&file);
    m_app.dumpSystemDatabase(os);
    UiFunc::alert(tr("System database written to: ") + filename, tr("Success"));
}
