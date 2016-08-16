#include "questionnaire.h"
#include <QDebug>
#include <QLabel>
#include <QScrollArea>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "questionnaireheader.h"


Questionnaire::Questionnaire(CamcopsApp& app) :
    QWidget(),
    m_app(app)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app, const QList<PagePtr>& pages) :
    QWidget(),
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app,
                             std::initializer_list<PagePtr> pages) :
    QWidget(),
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


void Questionnaire::commonConstructor()
{
    // *** revise: this should just be a placeholder for QuestionnairePage
    // objects, which must supply their own (full-screen-ish) background colour
    // *** or -- one header, lots of pages alternating underneath?

    m_type = PageType::ClinicianWithPatient;
    m_read_only = false;
    m_jump_allowed = false;
    m_within_chain = false;

    m_built = false;
    m_current_page_zero_based = 0;

    setStyleSheet(textfileContents(CSS_CAMCOPS_QUESTIONNAIRE));
    // *** add in CSS for base font size here

    QVBoxLayout* dummy_layout = new QVBoxLayout();
    setLayout(dummy_layout);
    m_background_widget = new QWidget();
    dummy_layout->addWidget(m_background_widget);

    m_mainlayout = new QVBoxLayout();
    m_background_widget->setLayout(m_mainlayout);

    m_p_header = nullptr;
    m_p_content = nullptr;
}


Questionnaire* Questionnaire::setType(PageType type)
{
    if (type == PageType::Inherit) {
        qWarning() << "Can only set PageType::Inherit on Page, not "
                      "Questionnaire";
    } else {
        m_type = type;
    }
    return this;
}


Questionnaire* Questionnaire::addPage(const PagePtr& page)
{
    m_pages.append(page);
    return this;
}


Questionnaire* Questionnaire::setReadOnly(bool read_only)
{
    m_read_only = read_only;
    return this;
}


Questionnaire* Questionnaire::setJumpAllowed(bool jump_allowed)
{
    m_jump_allowed = jump_allowed;
    return this;
}


Questionnaire* Questionnaire::setWithinChain(bool within_chain)
{
    m_within_chain = within_chain;
    return this;
}


void Questionnaire::build()
{
    if (m_p_header) {
        m_p_header->deleteLater();  // later, in case it's currently calling us
    }
    if (m_p_content) {
        m_p_content->deleteLater();
    }

    // Get page
    if (m_current_page_zero_based < 0 ||
            m_current_page_zero_based > m_pages.size()) {
        // Duff page!
        qWarning() << "Bad page number:" << m_current_page_zero_based;
        m_mainlayout->addWidget(new QLabel("BUG! Bad page number"));
        m_built = true;
        return;
    }
    PagePtr page = m_pages.at(m_current_page_zero_based);

    // Background
    PageType page_type = page->type();
    if (page_type == PageType::Inherit) {
        page_type = m_type;
    }
    QString background_css_name;
    switch (page_type) {
    case PageType::Patient:
    case PageType::ClinicianWithPatient:
    default:
        background_css_name = "questionnaire_background_patient";
        break;
    case PageType::Clinician:
        background_css_name = "questionnaire_background_clinician";
        break;
    case PageType::Config:
        background_css_name = "questionnaire_background_config";
        break;
    }
    m_background_widget->setObjectName(background_css_name);

    // Header
    QString header_css_name;
    if (page_type == PageType::ClinicianWithPatient) {
        // Header has "clinician" style; main page has "patient" style
        header_css_name = "questionnaire_background_clinician";
    }
    m_p_header = new QuestionnaireHeader(
        this, page->title(),
        m_read_only, m_jump_allowed, m_within_chain,
        fontSizePt(FontSize::Title), header_css_name);
    m_mainlayout->addWidget(m_p_header);

    // Content
    // The QScrollArea (a) makes text word wrap properly, by setting
    // a horizontal size limit (I presume), and (b) deals with the vertical.
    QScrollArea* scroll = new QScrollArea();
    scroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    scroll->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    scroll->setObjectName(background_css_name);
    scroll->setWidget(page->widget(this));

    m_mainlayout->addWidget(scroll);

    // In case the questionnaire is vertically short:
    // m_mainlayout->addStretch();
    // ... no, not needed with QScrollArea

    m_built = true;
}


void Questionnaire::open()
{
    if (!m_built) {
        build();
    }
    m_app.pushScreen(this);
}


int Questionnaire::fontSizePt(FontSize fontsize) const
{
    return m_app.fontSizePt(fontsize);
}
