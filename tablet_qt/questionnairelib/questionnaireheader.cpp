#include "questionnaireheader.h"
#include <QAbstractButton>
#include <QDebug>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/labelwordwrapwide.h"


QuestionnaireHeader::QuestionnaireHeader(QWidget* parent,
                                         const QString& title,
                                         bool read_only,
                                         bool jump_allowed,
                                         bool within_chain,
                                         int fontsize,
                                         const QString& css_name) :
    QWidget(parent),
    m_title(title)
{
    if (!css_name.isEmpty()) {
        setObjectName(css_name);  // *** not working! But works for e.g. cancel widget below
    }
    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------
    QHBoxLayout* toprowlayout = new QHBoxLayout();
    mainlayout->addLayout(toprowlayout);

    // Cancel button
    QAbstractButton* cancel = CAMCOPS_BUTTON_CANCEL(this);
    toprowlayout->addWidget(cancel);
    connect(cancel, &QAbstractButton::clicked,
            this, &QuestionnaireHeader::cancelClicked);

    // Read-only icon
    if (read_only) {
        QLabel* read_only_icon = iconWidget(ICON_READ_ONLY, this);
        toprowlayout->addWidget(read_only_icon);
    }

    // Title
    LabelWordWrapWide* title_label = new LabelWordWrapWide(title);
    title_label->setAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    title_label->setObjectName("questionnaire_title");
    QString title_css = textCSS(fontsize);
    title_label->setStyleSheet(title_css);
    toprowlayout->addWidget(title_label);

    // Right-hand icons
    if (jump_allowed) {
        m_button_jump = CAMCOPS_BUTTON_CHOOSE_PAGE(this);
        toprowlayout->addWidget(m_button_jump);
        connect(m_button_jump, &QAbstractButton::clicked,
                this, &QuestionnaireHeader::jumpClicked);
    }
    m_button_previous = CAMCOPS_BUTTON_BACK(this);
    m_button_next = CAMCOPS_BUTTON_NEXT(this);
    if (within_chain) {
        m_button_finish = CAMCOPS_BUTTON_FAST_FORWARD(this);
    } else {
        m_button_finish = CAMCOPS_BUTTON_FINISH(this);
    }
    toprowlayout->addWidget(m_button_previous);
    toprowlayout->addWidget(m_button_next);
    toprowlayout->addWidget(m_button_finish);
    setButtons(false, false, false);
    connect(m_button_previous, &QAbstractButton::clicked,
            this, &QuestionnaireHeader::previousClicked);
    connect(m_button_next, &QAbstractButton::clicked,
            this, &QuestionnaireHeader::nextClicked);
    connect(m_button_finish, &QAbstractButton::clicked,
            this, &QuestionnaireHeader::finishClicked);

    // ------------------------------------------------------------------------
    // Horizontal line
    // ------------------------------------------------------------------------
    QFrame* horizline = new QFrame();
    horizline->setObjectName("header_horizontal_line");
    horizline->setFrameShape(QFrame::HLine);
    horizline->setFrameShadow(QFrame::Plain);
    horizline->setLineWidth(HEADER_HLINE_WIDTH);
    mainlayout->addWidget(horizline);
}


void QuestionnaireHeader::setButtons(bool previous, bool next, bool finish)
{
    m_button_previous->setVisible(previous);
    m_button_next->setVisible(next);
    m_button_finish->setVisible(finish);
}
