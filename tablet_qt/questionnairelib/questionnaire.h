#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include "common/uiconstants.h"  // for FontSize
#include "widgets/openablewidget.h"
#include "qupage.h"

class QVBoxLayout;
class QWidget;

class CamcopsApp;
class Questionnaire;
using QuestionnairePtr = QSharedPointer<Questionnaire>;
class QuestionnaireHeader;


class Questionnaire : public OpenableWidget
{
    // Master class controlling a questionnaire.

    Q_OBJECT
public:
    Questionnaire(CamcopsApp& app);
    Questionnaire(CamcopsApp& app, const QList<QuPagePtr>& pages);
    Questionnaire(CamcopsApp& app, std::initializer_list<QuPagePtr> pages);

    virtual void build() override;

    void setType(QuPage::PageType type);
    void addPage(const QuPagePtr& page);
    void setReadOnly(bool read_only = true);
    void setJumpAllowed(bool jump_allowed = true);
    void setWithinChain(bool within_chain = true);

    bool readOnly() const;
    int fontSizePt(UiConst::FontSize fontsize) const;

    void openSubWidget(OpenableWidget* widget);
    CamcopsApp& app() const;
    QString getSubstitutedCss(const QString& filename) const;
protected:
    void commonConstructor();
    int currentPageNumOneBased() const;
    int nPages() const;
    QuPagePtr currentPagePtr() const;
    void doFinish();
    void doCancel();
    void pageClosing();
protected slots:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
    void resetButtons();
protected:
    CamcopsApp& m_app;
    QList<QuPagePtr> m_pages;
    QuPage::PageType m_type;
    bool m_read_only;
    bool m_jump_allowed;
    bool m_within_chain;

    bool m_built;
    QPointer<QVBoxLayout> m_outer_layout;
    QPointer<QWidget> m_background_widget;
    QPointer<QVBoxLayout> m_mainlayout;
    QPointer<QuestionnaireHeader> m_p_header;
    QPointer<QVBoxLayout> m_p_content;
    int m_current_pagenum_zero_based;
};
