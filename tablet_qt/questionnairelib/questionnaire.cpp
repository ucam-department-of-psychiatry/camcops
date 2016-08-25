#include "questionnaire.h"
#include <functional>
#include <QDebug>
#include <QMessageBox>
#include <QLabel>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "questionnaireheader.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/openablewidget.h"
#include "widgets/verticalscrollarea.h"


Questionnaire::Questionnaire(CamcopsApp& app) :
    m_app(app)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app, const QList<QuPagePtr>& pages) :
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


Questionnaire::Questionnaire(CamcopsApp& app,
                             std::initializer_list<QuPagePtr> pages) :
    m_app(app),
    m_pages(pages)
{
    commonConstructor();
}


void Questionnaire::commonConstructor()
{
    m_type = QuPage::PageType::ClinicianWithPatient;
    m_read_only = false;
    m_jump_allowed = false;
    m_within_chain = false;

    m_built = false;
    m_current_pagenum_zero_based = 0;

    setStyleSheet(m_app.getQuestionnaireCss());

    m_outer_layout = new QVBoxLayout();
    setLayout(m_outer_layout);

    m_p_header = nullptr;
    m_p_content = nullptr;
}


void Questionnaire::setType(QuPage::PageType type)
{
    if (type == QuPage::PageType::Inherit) {
        qWarning() << "Can only set PageType::Inherit on Page, not "
                      "Questionnaire";
    } else {
        m_type = type;
    }
}


void Questionnaire::addPage(const QuPagePtr& page)
{
    m_pages.append(page);
}


void Questionnaire::setReadOnly(bool read_only)
{
    m_read_only = read_only;
}


void Questionnaire::setJumpAllowed(bool jump_allowed)
{
    m_jump_allowed = jump_allowed;
}


void Questionnaire::setWithinChain(bool within_chain)
{
    m_within_chain = within_chain;
}


void Questionnaire::build()
{
    // ========================================================================
    // Clean up any old page widgets
    // ========================================================================
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

    // ========================================================================
    // Create new
    // ========================================================================
    m_background_widget = new QWidget();
    m_outer_layout->addWidget(m_background_widget);
    m_outer_layout->setContentsMargins(UiConst::NO_MARGINS);
    m_mainlayout = new QVBoxLayout();
    m_mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    m_background_widget->setLayout(m_mainlayout);

    // Get page
    if (m_current_pagenum_zero_based < 0 ||
            m_current_pagenum_zero_based > m_pages.size()) {
        // Duff page!
        qWarning() << "Bad page number:" << m_current_pagenum_zero_based;
        m_mainlayout->addWidget(new LabelWordWrapWide("BUG! Bad page number"));
        m_built = true;
        return;
    }
    QuPagePtr page = currentPagePtr();

    // Background
    QuPage::PageType page_type = page->type();
    if (page_type == QuPage::PageType::Inherit) {
        page_type = m_type;
    }
    QString background_css_name;
    switch (page_type) {
    case QuPage::PageType::Patient:
    case QuPage::PageType::ClinicianWithPatient:
    default:
        background_css_name = "questionnaire_background_patient";
        break;
    case QuPage::PageType::Clinician:
        background_css_name = "questionnaire_background_clinician";
        break;
    case QuPage::PageType::Config:
        background_css_name = "questionnaire_background_config";
        break;
    }
    m_background_widget->setObjectName(background_css_name);

    // Header
    QString header_css_name;
    if (page_type == QuPage::PageType::ClinicianWithPatient) {
        // Header has "clinician" style; main page has "patient" style
        header_css_name = "questionnaire_background_clinician";
    }
    m_p_header = new QuestionnaireHeader(
        this, page->title(),
        m_read_only, m_jump_allowed, m_within_chain,
        header_css_name);
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
    scroll->setWidget(page->widget(this));  // adds the content
    connect(page.data(), &QuPage::elementValueChanged,
            this, &Questionnaire::resetButtons,
            Qt::UniqueConnection);

    m_mainlayout->addWidget(scroll);

    // In case the questionnaire is vertically short:
    m_mainlayout->addStretch();

    m_built = true;

    resetButtons();

    // *** deal with multiple pages
}


void Questionnaire::resetButtons()
{
    QuPagePtr page = currentPagePtr();
    if (!page || !m_p_header) {
        return;
    }
    bool on_last_page = currentPageNumOneBased() == nPages();
    bool allow_progression = readOnly() || !page->missingInput();
    m_p_header->setButtons(
        m_current_pagenum_zero_based > 0,  // previous
        !on_last_page && allow_progression,  // next
        on_last_page && allow_progression  // finish
    );
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
    if (m_current_pagenum_zero_based < 0 ||
            m_current_pagenum_zero_based >= m_pages.size()) {
        return QuPagePtr(nullptr);
    }
    return m_pages.at(m_current_pagenum_zero_based);
}


bool Questionnaire::readOnly() const
{
    return m_read_only;
}


int Questionnaire::fontSizePt(UiConst::FontSize fontsize) const
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
    if (m_read_only) {
        doCancel();
        return;
    }
    QMessageBox msgbox(QMessageBox::Question,  // icon
                       tr("Abort"),  // title
                       tr("Abort this questionnaire?"),  // text
                       QMessageBox::Yes | QMessageBox::No,  // buttons
                       this);  // parent
    msgbox.setButtonText(QMessageBox::Yes, tr("Yes, abort"));
    msgbox.setButtonText(QMessageBox::No, tr("No, go back"));
    int reply = msgbox.exec();
    if (reply == QMessageBox::Yes) {
        doCancel();
    }
}


void Questionnaire::jumpClicked()
{
    UiFunc::alert("*** jump");
}


void Questionnaire::previousClicked()
{
    if (m_current_pagenum_zero_based <= 0) {
        // On the first page already
        return;
    }
    pageClosing();
    --m_current_pagenum_zero_based;
    build();
}


void Questionnaire::nextClicked()
{
    if (currentPageNumOneBased() >= nPages()) {
        // On the last page; use finish rather than next
        return;
    }
    QuPagePtr page = currentPagePtr();
    if (!readOnly() && page->missingInput()) {
        // Can't progress
        return;
    }
    pageClosing();
    ++m_current_pagenum_zero_based;
    build();
}


void Questionnaire::finishClicked()
{
    if (currentPageNumOneBased() != nPages()) {
        // Not on the last page; can't finish here
        return;
    }
    QuPagePtr page = currentPagePtr();
    if (!readOnly() && page->missingInput()) {
        // Can't progress
        return;
    }
    doFinish();
}


void Questionnaire::pageClosing()
{
    QuPagePtr page = currentPagePtr();
    if (!page) {
        return;
    }
    page->closing();
}


void Questionnaire::doCancel()
{
    if (!readOnly()) {
        // *** mark task as cancelled, or whatever
    }
    emit finished();
}


void Questionnaire::doFinish()
{
    if (!readOnly()) {
        // *** mark task as finished, or whatever
    }
    emit finished();
}
