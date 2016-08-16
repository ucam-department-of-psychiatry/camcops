#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"
#include "lib/uifunc.h"
#include "page.h"

class QVBoxLayout;
class QuestionnaireHeader;


class Questionnaire : public QWidget
{
    Q_OBJECT
public:
    Questionnaire(CamcopsApp& app);
    Questionnaire(CamcopsApp& app, const QList<PagePtr>& pages);
    Questionnaire(CamcopsApp& app, std::initializer_list<PagePtr> pages);
    Questionnaire* setType(PageType type);
    Questionnaire* addPage(const PagePtr& page);
    Questionnaire* setReadOnly(bool read_only = true);
    Questionnaire* setJumpAllowed(bool jump_allowed = true);
    Questionnaire* setWithinChain(bool within_chain = true);

    void open();
    int fontSizePt(FontSize fontsize) const;
protected:
    void commonConstructor();
    void build();
protected:
    CamcopsApp& m_app;
    QList<PagePtr> m_pages;
    PageType m_type;
    bool m_read_only;
    bool m_jump_allowed;
    bool m_within_chain;

    bool m_built;
    QPointer<QWidget> m_background_widget;
    QPointer<QVBoxLayout> m_mainlayout;
    QPointer<QuestionnaireHeader> m_p_header;
    QPointer<QVBoxLayout> m_p_content;
    int m_current_page_zero_based;
};
