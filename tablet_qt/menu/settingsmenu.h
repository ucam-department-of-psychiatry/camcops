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

#pragma once
#include <QPointer>

#include "crypto/secureqstring.h"
#include "menulib/menuwindow.h"
class Questionnaire;

// #define SETTINGSMENU_OFFER_SPECIFIC_FETCHES


class SettingsMenu : public MenuWindow
{
    Q_OBJECT

public:
    SettingsMenu(CamcopsApp& app);
    virtual QString title() const override;

protected:
    virtual void makeItems() override;
    OpenableWidget* configureServer(CamcopsApp& app);

    OpenableWidget* configureIntellectualProperty(CamcopsApp& app);
    void ipClinicalChanged();
    void ipSaved();
    void ipCancelled();

    OpenableWidget* configureUser(CamcopsApp& app);
    void userSettingsSaved();
    void userSettingsCancelled();

    OpenableWidget* setQuestionnaireFontSize(CamcopsApp& app);
    void setPrivilege();
    void changeAppPassword();
    void changePrivPassword();
    void deleteAllExtraStrings();
    void registerWithServer();
    void fetchAllServerInfo();
#ifdef SETTINGSMENU_OFFER_SPECIFIC_FETCHES
    void fetchIdDescriptions();
    void fetchExtraStrings();
#endif
    OpenableWidget* viewServerInformation(CamcopsApp& app);
    void viewDataCounts();
    void viewSystemCounts();
    void dropUnknownTables();
    void viewDataDbAsSql();
    void viewSystemDbAsSql();
    void debugDataDbAsSql();
    void debugSystemDbAsSql();
    void saveDataDbAsSql();
    void saveSystemDbAsSql();
    void chooseLanguage();
    void changeMode();

    // Internal helpers:
    QVariant serverPasswordGetter();
    bool serverPasswordSetter(const QVariant& value);
    void viewDbAsSql(DatabaseManager& db, const QString& title);
    void debugDbAsSql(DatabaseManager& db, const QString& prefix);
    void saveDbAsSql(
        DatabaseManager& db,
        const QString& save_title,
        const QString& finish_prefix
    );
    void viewCounts(DatabaseManager& db, const QString& title);

protected:
    mutable SecureQString m_temp_plaintext_password;
    bool m_plaintext_pw_live;
    QPointer<Questionnaire> m_ip_questionnaire;
    FieldRefPtr m_ip_clinical_fr;
};
