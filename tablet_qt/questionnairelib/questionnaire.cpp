#include "questionnaire.h"
#include <QDebug>
#include <QMessageBox>
#include <QLabel>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/filefunc.h"
#include "questionnaireheader.h"
#include "widgets/verticalscrollarea.h"


Questionnaire::Questionnaire(CamcopsApp& app) :
    QWidget(),
    m_app(app)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app, const QList<QuPagePtr>& pages) :
    QWidget(),
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app,
                             std::initializer_list<QuPagePtr> pages) :
    QWidget(),
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


void Questionnaire::commonConstructor()
{
    m_type = QuPageType::ClinicianWithPatient;
    m_read_only = false;
    m_jump_allowed = false;
    m_within_chain = false;

    m_built = false;
    m_current_pagenum_zero_based = 0;

    setStyleSheet(textfileContents(CSS_CAMCOPS_QUESTIONNAIRE));

    m_outer_layout = new QVBoxLayout();
    setLayout(m_outer_layout);

    m_p_header = nullptr;
    m_p_content = nullptr;
}


Questionnaire* Questionnaire::setType(QuPageType type)
{
    if (type == QuPageType::Inherit) {
        qWarning() << "Can only set PageType::Inherit on Page, not "
                      "Questionnaire";
    } else {
        m_type = type;
    }
    return this;
}


Questionnaire* Questionnaire::addPage(const QuPagePtr& page)
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


void Questionnaire::rebuild()
{
    if (m_p_header) {
        m_p_header->deleteLater();  // later, in case it's currently calling us
    }
    if (m_p_content) {
        m_p_content->deleteLater();
    }
    if (m_mainlayout) {
        m_mainlayout->deleteLater();
    }
    if (m_background_widget) {
        m_background_widget->deleteLater();
    }

    m_background_widget = new QWidget();
    m_outer_layout->addWidget(m_background_widget);
    m_mainlayout = new QVBoxLayout();
    m_background_widget->setLayout(m_mainlayout);

    // Get page
    if (m_current_pagenum_zero_based < 0 ||
            m_current_pagenum_zero_based > m_pages.size()) {
        // Duff page!
        qWarning() << "Bad page number:" << m_current_pagenum_zero_based;
        m_mainlayout->addWidget(new QLabel("BUG! Bad page number"));
        m_built = true;
        return;
    }
    QuPagePtr page = currentPagePtr();

    // Background
    QuPageType page_type = page->type();
    if (page_type == QuPageType::Inherit) {
        page_type = m_type;
    }
    QString background_css_name;
    switch (page_type) {
    case QuPageType::Patient:
    case QuPageType::ClinicianWithPatient:
    default:
        background_css_name = "questionnaire_background_patient";
        break;
    case QuPageType::Clinician:
        background_css_name = "questionnaire_background_clinician";
        break;
    case QuPageType::Config:
        background_css_name = "questionnaire_background_config";
        break;
    }
    m_background_widget->setObjectName(background_css_name);

    // Header
    QString header_css_name;
    if (page_type == QuPageType::ClinicianWithPatient) {
        // Header has "clinician" style; main page has "patient" style
        header_css_name = "questionnaire_background_clinician";
    }
    m_p_header = new QuestionnaireHeader(
        this, page->title(),
        m_read_only, m_jump_allowed, m_within_chain,
        fontSizePt(FontSize::Title), header_css_name);
    m_mainlayout->addWidget(m_p_header);
    connect(m_p_header, &QuestionnaireHeader::cancelClicked,
            this, &Questionnaire::cancelClicked);
    connect(m_p_header, &QuestionnaireHeader::jumpClicked,
            this, &Questionnaire::jumpClicked);
    connect(m_p_header, &QuestionnaireHeader::previousClicked,
            this, &Questionnaire::previousClicked);
    connect(m_p_header, &QuestionnaireHeader::nextClicked,
            this, &Questionnaire::nextClicked);
    connect(m_p_header, &QuestionnaireHeader::finishClicked,
            this, &Questionnaire::finishClicked);

    // Content
    // The QScrollArea (a) makes text word wrap, by setting a horizontal size
    // limit (I presume), and (b) deals with the vertical.
    // But it doesn't get the horizontal widths right. So we use a substitute.
    VerticalScrollArea* scroll = new VerticalScrollArea();
    scroll->setObjectName(background_css_name);
    scroll->setWidget(page->widget(this));

    m_mainlayout->addWidget(scroll);

    // In case the questionnaire is vertically short:
    m_mainlayout->addStretch();

    m_built = true;

    bool on_last_page = currentPageNumOneBased() == nPages();
    bool missing_input = page->missingInput();
    m_p_header->setButtons(
        m_current_pagenum_zero_based > 0,  // previous
        !on_last_page && !missing_input,  // next
        on_last_page && !missing_input  // finish
    );

    // *** deal with multiple pages
}


void Questionnaire::open()
{
    if (!m_built) {
        rebuild();
    }
    m_app.pushScreen(this);
}


int Questionnaire::currentPageNumOneBased() const
{
    return m_current_pagenum_zero_based + 1;
}


int Questionnaire::nPages() const
{
    return m_pages.size();
}


QuPagePtr Questionnaire::currentPagePtr() const
{
    return m_pages.at(m_current_pagenum_zero_based);
}


int Questionnaire::fontSizePt(FontSize fontsize) const
{
    return m_app.fontSizePt(fontsize);
}


void Questionnaire::cancelClicked()
{
    /*
    QMessageBox::StandardButton reply;
    reply = QMessageBox::question(
        this,
        tr("Abort"),
        tr("Abort this questionnaire?"),
        QMessageBox::Yes | QMessageBox::No);
    if (reply == QMessageBox::Yes) {
        doCancel();
    }
    */
    QMessageBox msgbox(QMessageBox::Question,
                       tr("Abort"),
                       tr("Abort this questionnaire?"),
                       QMessageBox::Yes | QMessageBox::No);
    msgbox.setButtonText(QMessageBox::Yes, "Yes, abort");
    msgbox.setButtonText(QMessageBox::No, "No, go back");
    int reply = msgbox.exec();
    if (reply == QMessageBox::Yes) {
        doCancel();
    }
}


void Questionnaire::jumpClicked()
{
    alert("*** jump");
}


void Questionnaire::previousClicked()
{
    if (m_current_pagenum_zero_based <= 0) {
        // On the first page already
        return;
    }
    --m_current_pagenum_zero_based;
    rebuild();
}


void Questionnaire::nextClicked()
{
    if (currentPageNumOneBased() >= nPages()) {
        // On the last page; use finish rather than next
        return;
    }
    QuPagePtr page = currentPagePtr();
    if (page->missingInput()) {
        // Can't progress
        return;
    }
    ++m_current_pagenum_zero_based;
    rebuild();
}


void Questionnaire::finishClicked()
{
    if (currentPageNumOneBased() != nPages()) {
        // Not on the last page; can't finish here
        return;
    }
    QuPagePtr page = currentPagePtr();
    if (page->missingInput()) {
        // Can't progress
        return;
    }
    doFinish();
}


void Questionnaire::doCancel()
{
    // *** mark task as cancelled, or whatever
    m_app.popScreen();
}


void Questionnaire::doFinish()
{
    // *** mark task as finished, or whatever
    m_app.popScreen();
}
