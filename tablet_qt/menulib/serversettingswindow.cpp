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


#include "serversettingswindow.h"

#include <QString>

#include "common/aliases_camcops.h"
#include "common/varconst.h"
#include "core/camcopsapp.h"
#include "lib/convert.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditint64.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "widgets/openablewidget.h"

// ============================================================================
// Server configuration
// ============================================================================

ServerSettingsWindow::ServerSettingsWindow(CamcopsApp& app) :
    m_app(app)
{
}

OpenableWidget* ServerSettingsWindow::editor()
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

    const QString DEPRECATED("(†) ");

    m_app.clearCachedVars();  // ... in case any are left over

    FieldRefPtr address_fr = m_app.storedVarFieldRef(varconst::SERVER_ADDRESS);
    const QString address_t = tr("Server address");
    const QString address_h = tr("host name or IP address");

    FieldRefPtr port_fr = m_app.storedVarFieldRef(varconst::SERVER_PORT);
    const QString port_t = tr("Server port for HTTPS");
    const QString port_h = tr("default 443");

    FieldRefPtr path_fr = m_app.storedVarFieldRef(varconst::SERVER_PATH);
    const QString path_t = tr("Path on server");
    const QString path_h = tr("no leading /; e.g. camcops/database");

    FieldRefPtr timeout_fr
        = m_app.storedVarFieldRef(varconst::SERVER_TIMEOUT_MS);
    const QString timeout_t = tr("Network timeout (ms)");
    const QString timeout_h = tr("e.g. 50000");

#ifdef DEBUG_OFFER_HTTP_TO_SERVER
    FieldRefPtr https_fr
        = m_app.storedVarFieldRef(varconst::DEBUG_USE_HTTPS_TO_SERVER);
    const QString https_t = tr("Use HTTPS to server?");
    const QString https_h
        = tr("You should <b>only</b> disable this for debugging!");
#endif

    FieldRefPtr ssl_fr
        = m_app.storedVarFieldRef(varconst::VALIDATE_SSL_CERTIFICATES);
    const QString ssl_t = tr("Validate HTTPS (TLS/SSL) certificates?");
    const QString ssl_h = tr(
        "Should always be YES for security-conscious "
        "systems."
    );

    FieldRefPtr ssl_proto_fr = m_app.storedVarFieldRef(varconst::SSL_PROTOCOL);
    const QString ssl_proto_t = tr("HTTPS (TLS/SSL) protocol?");
    const QString ssl_proto_h = tr(
        "Stick with the default unless your server "
        "can’t cope with it."
    );
    const NameValueOptions options_ssl_protocol{
        // https://doc.qt.io/qt-6/qssl.html#SslProtocol-enum
        {tr("Known secure [default]"), convert::SSLPROTODESC_SECUREPROTOCOLS},
        {tr("TLS v1.2"), convert::SSLPROTODESC_TLSV1_2},
        {tr("TLS v1.2 or later"), convert::SSLPROTODESC_TLSV1_2_OR_LATER},
        {tr("TLS v1.3"), convert::SSLPROTODESC_TLSV1_3},
        {tr("TLS v1.3 or later"), convert::SSLPROTODESC_TLSV1_3_OR_LATER},
        {tr("DTLS v1.2"), convert::SSLPROTODESC_DTLSV1_2},
        {tr("DTLS v1.2 or later"), convert::SSLPROTODESC_DTLSV1_2_OR_LATER},
        {DEPRECATED + tr("Any supported protocol"),
         convert::SSLPROTODESC_ANYPROTOCOL},
    };
    const QString ssl_proto_explanation = DEPRECATED + "Insecure, deprecated.";

    FieldRefPtr storepw_fr
        = m_app.storedVarFieldRef(varconst::STORE_SERVER_PASSWORD);
    const QString storepw_t = tr("Store user’s server password?");
    const QString storepw_h = tr(
        "NO = fractionally more secure; YES = more convenient/"
        "fractionally less secure, but still AES-256-encrypted."
    );

    FieldRefPtr uploadmethod_fr
        = m_app.storedVarFieldRef(varconst::UPLOAD_METHOD);
    const QString uploadmethod_t = tr("Upload method");
    const NameValueOptions options_upload_method{
        {tr("Multi-step (original)"), varconst::UPLOAD_METHOD_MULTISTEP},
        {tr("Always one-step (faster)"), varconst::UPLOAD_METHOD_ONESTEP},
        {tr("One-step if small enough (default)"),
         varconst::UPLOAD_METHOD_BYSIZE},
    };

    FieldRefPtr maxsizeonestep_fr
        = m_app.storedVarFieldRef(varconst::MAX_DBSIZE_FOR_ONESTEP_UPLOAD);
    const QString maxsizeonestep_t
        = tr("Maximum (approximate) database size for one-step upload (bytes)"
        );
    const QString maxsizeonestep_h = tr("e.g. 2000000 for ~2Mb");

    QuPagePtr page(new QuPage{
        questionnairefunc::defaultGridRawPointer(
            {
                {stringfunc::makeTitle(address_t, address_h, true),
                 (new QuLineEdit(address_fr))
                     ->setHint(stringfunc::makeHint(address_t, address_h))
                     ->setWidgetInputMethodHints(
                         Qt::ImhNoAutoUppercase | Qt::ImhNoPredictiveText
                     )},
                {stringfunc::makeTitle(port_t, port_h, true),
                 new QuLineEditInteger(
                     port_fr, uiconst::IP_PORT_MIN, uiconst::IP_PORT_MAX
                 )},
                {stringfunc::makeTitle(path_t, path_h, true),
                 (new QuLineEdit(path_fr))
                     ->setHint(stringfunc::makeHint(path_t, path_h))
                     ->setWidgetInputMethodHints(
                         Qt::ImhNoAutoUppercase | Qt::ImhNoPredictiveText
                     )},
                {stringfunc::makeTitle(timeout_t, timeout_h, true),
                 new QuLineEditInteger(
                     timeout_fr,
                     uiconst::NETWORK_TIMEOUT_MS_MIN,
                     uiconst::NETWORK_TIMEOUT_MS_MAX
                 )},
            },
            1,
            1
        ),

#ifdef DEBUG_OFFER_HTTP_TO_SERVER
        new QuText(stringfunc::makeTitle(https_t, https_h)),
        (new QuMcq(https_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true)
            ->setAsTextButton(true),
#endif

        new QuText(stringfunc::makeTitle(ssl_t, ssl_h)),
        (new QuMcq(ssl_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true)
            ->setAsTextButton(true),

        new QuText(stringfunc::makeTitle(ssl_proto_t, ssl_proto_h)),
        (new QuMcq(ssl_proto_fr, options_ssl_protocol))
            ->setHorizontal(true)
            ->setAsTextButton(true),
        new QuText(ssl_proto_explanation),

        new QuHorizontalLine(),

        new QuText(stringfunc::makeTitle(storepw_t, storepw_h)),
        (new QuMcq(storepw_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true)
            ->setAsTextButton(true),

        new QuHorizontalLine(),

        new QuText(stringfunc::makeTitle(uploadmethod_t)),
        (new QuMcq(uploadmethod_fr, options_upload_method))
            ->setHorizontal(true)
            ->setAsTextButton(true),

        questionnairefunc::defaultGridRawPointer(
            {{stringfunc::makeTitle(maxsizeonestep_t, maxsizeonestep_h, true),
              (new QuLineEditInt64(maxsizeonestep_fr))
                  ->setHint(
                      stringfunc::makeHint(maxsizeonestep_t, maxsizeonestep_h)
                  )}},
            1,
            1
        ),
    });
    page->setTitle(tr("Configure server settings"));
    page->setType(QuPage::PageType::Config);
    page->registerValidator(std::bind(
        &ServerSettingsWindow::validateServerSettings,
        this,
        std::placeholders::_1,
        std::placeholders::_2
    ));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setFinishButtonIconToTick();
    connect(
        questionnaire,
        &Questionnaire::completed,
        this,
        &ServerSettingsWindow::serverSettingsSaved
    );
    connect(
        questionnaire,
        &Questionnaire::cancelled,
        &m_app,
        &CamcopsApp::clearCachedVars
    );
    return questionnaire;
}

bool ServerSettingsWindow::validateServerSettings(
    QStringList& errors, const QuPage* page
)
{
    Q_UNUSED(page)
    // Note that we are using cached server variables.
    const QString hostname
        = m_app.getCachedVar(varconst::SERVER_ADDRESS).toString();
    if (hostname.contains("/")) {
        errors.append("No forward slashes ('/') permitted in server hostname");
        return false;
    }
    return true;
}

void ServerSettingsWindow::serverSettingsSaved()
{
    // User has edited server settings and then clicked OK.
    const bool server_details_changed
        = (m_app.cachedVarChanged(varconst::SERVER_ADDRESS)
           || m_app.cachedVarChanged(varconst::SERVER_PORT)
           || m_app.cachedVarChanged(varconst::SERVER_PATH));
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
