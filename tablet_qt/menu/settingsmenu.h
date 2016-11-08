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
    QString demoText(const QString& text, UiConst::FontSize fontsize_type) const;
protected:
    mutable SecureQString m_temp_plaintext_password;
    bool m_plaintext_pw_live;
    QPointer<Questionnaire> m_fontsize_questionnaire;
    FieldRefPtr m_fontsize_fr;
};
