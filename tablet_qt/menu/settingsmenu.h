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

#pragma once
#include <QPointer>
#include "menulib/menuwindow.h"
#include "crypto/secureqstring.h"
class Questionnaire;


class SettingsMenu : public MenuWindow
{
    Q_OBJECT
public:
    SettingsMenu(CamcopsApp& app);
protected:
    OpenableWidget* configureServer(CamcopsApp& app);
    OpenableWidget* configureIntellectualProperty(CamcopsApp& app);
    OpenableWidget* configureUser(CamcopsApp& app);
    OpenableWidget* setQuestionnaireFontSize(CamcopsApp& app);
    void setPrivilege();
    void changeAppPassword();
    void changePrivPassword();
    void deleteAllExtraStrings();
    void registerWithServer();
    void fetchIdDescriptions();
    void fetchExtraStrings();
    OpenableWidget* viewServerInformation(CamcopsApp& app);

    QString makeTitle(const QString& part1, const QString& part2 = "",
                      bool colon = false) const;
    QString makeHint(const QString& part1, const QString& part2) const;
    void serverSettingsSaved();
    QVariant serverPasswordGetter();
    bool serverPasswordSetter(const QVariant& value);
    void userSettingsSaved();
    void userSettingsCancelled();
    void fontSizeChanged();
    void fontSettingsSaved();
    void fontSettingsCancelled();
    void resetFontSize();
    QString demoText(const QString& text, uiconst::FontSize fontsize_type) const;
    void viewDataDbAsSql();
    void viewSystemDbAsSql();
    void debugDataDbAsSql();
    void debugSystemDbAsSql();
    void saveDataDbAsSql();
    void saveSystemDbAsSql();
protected:
    mutable SecureQString m_temp_plaintext_password;
    bool m_plaintext_pw_live;
    QPointer<Questionnaire> m_fontsize_questionnaire;
    FieldRefPtr m_fontsize_fr;
};
