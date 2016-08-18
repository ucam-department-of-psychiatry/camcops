#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"
#include "lib/uifunc.h"
#include "qupage.h"

class QVBoxLayout;
class QuestionnaireHeader;


class Questionnaire : public QWidget
{
    Q_OBJECT
public:
    Questionnaire(CamcopsApp& app);
    Questionnaire(CamcopsApp& app, const QList<QuPagePtr>& pages);
    Questionnaire(CamcopsApp& app, std::initializer_list<QuPagePtr> pages);
    Questionnaire* setType(QuPageType type);
    Questionnaire* addPage(const QuPagePtr& page);
    Questionnaire* setReadOnly(bool read_only = true);
    Questionnaire* setJumpAllowed(bool jump_allowed = true);
    Questionnaire* setWithinChain(bool within_chain = true);

    void open();
    int fontSizePt(FontSize fontsize) const;
protected:
    void commonConstructor();
    void rebuild();
    int currentPageNumOneBased() const;
    int nPages() const;
    QuPagePtr currentPagePtr() const;
    void doFinish();
    void doCancel();
protected slots:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();
protected:
    CamcopsApp& m_app;
    QList<QuPagePtr> m_pages;
    QuPageType m_type;
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
