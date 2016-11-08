#include "questionnaireheader.h"
#include <QAbstractButton>
#include <QDebug>
#include <QHBoxLayout>
#include <QPushButton>
#include <QVBoxLayout>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/horizontalline.h"
#include "widgets/imagebutton.h"
#include "widgets/labelwordwrapwide.h"


QuestionnaireHeader::QuestionnaireHeader(QWidget* parent,
                                         const QString& title,
                                         bool read_only,
                                         bool jump_allowed,
                                         bool within_chain,
                                         const QString& css_name,
                                         bool debug_allowed) :
    QWidget(parent),
    m_title(title),
    m_button_debug(nullptr),
    m_button_jump(nullptr),
    m_button_previous(nullptr),
    m_button_next(nullptr),
    m_button_finish(nullptr),
    m_icon_no_next(nullptr)
{
    if (!css_name.isEmpty()) {
        setObjectName(css_name);  // was not working! But works for e.g. cancel button below
        // Problem appears to be that WA_StyledBackground is not set.
        setAttribute(Qt::WidgetAttribute::WA_StyledBackground, true);

        // Following which discovery...
        // http://stackoverflow.com/questions/24653405/why-is-qwidget-with-border-and-background-image-styling-behaving-different-to-ql
        // ... suggests using QFrame
        // http://stackoverflow.com/questions/12655538/how-to-set-qwidget-background-color
        // ... suggests using setAutoFillBackground(true)
        // http://doc.qt.io/qt-5.7/qwidget.html#autoFillBackground-prop
        // ... advises caution with setAutoFillBackground() and stylesheets
    }
    setSizePolicy(UiFunc::expandingFixedHFWPolicy());

    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------
    QHBoxLayout* toprowlayout = new QHBoxLayout();
    mainlayout->addLayout(toprowlayout);

    Qt::Alignment button_align = Qt::AlignHCenter | Qt::AlignTop;

    // Cancel button
    QAbstractButton* cancel = new ImageButton(UiConst::CBS_CANCEL);
    toprowlayout->addWidget(cancel);
    toprowlayout->setAlignment(cancel, button_align);
    connect(cancel, &QAbstractButton::clicked,
            this, &QuestionnaireHeader::cancelClicked);

    // Read-only icon
    if (read_only) {
        QLabel* read_only_icon = UiFunc::iconWidget(
            UiFunc::iconFilename(UiConst::ICON_READ_ONLY));
        toprowlayout->addWidget(read_only_icon);
        toprowlayout->setAlignment(read_only_icon, button_align);
    }

    // Spacing
    toprowlayout->addStretch();

    // Title
    LabelWordWrapWide* title_label = new LabelWordWrapWide(title);
    title_label->setAlignment(Qt::AlignHCenter | Qt::AlignTop);
    toprowlayout->addWidget(title_label);  // default alignment fills whole cell

    // Spacing
    toprowlayout->addStretch();

    // Right-hand icons/buttons
    if (debug_allowed) {
        m_button_debug = new QPushButton("Dump layout");
        connect(m_button_debug, &QAbstractButton::clicked,
                this, &QuestionnaireHeader::debugLayout);
        toprowlayout->addWidget(m_button_debug);
    }

    m_button_previous = new ImageButton(UiConst::CBS_BACK);
    toprowlayout->addWidget(m_button_previous);
    toprowlayout->setAlignment(m_button_previous, button_align);

    if (jump_allowed) {
        m_button_jump = new ImageButton(UiConst::CBS_CHOOSE_PAGE);
        connect(m_button_jump, &QAbstractButton::clicked,
                this, &QuestionnaireHeader::jumpClicked);
        toprowlayout->addWidget(m_button_jump);
        toprowlayout->setAlignment(m_button_jump, button_align);
    }

    m_button_next = new ImageButton(UiConst::CBS_NEXT);
    toprowlayout->addWidget(m_button_next);
    toprowlayout->setAlignment(m_button_next, button_align);

    if (within_chain) {
        m_button_finish = new ImageButton(UiConst::CBS_FAST_FORWARD);
    } else {
        m_button_finish = new ImageButton(UiConst::CBS_FINISH);
    }
    toprowlayout->addWidget(m_button_finish);
    toprowlayout->setAlignment(m_button_finish, button_align);

    m_icon_no_next = UiFunc::iconWidget(
        UiFunc::iconFilename(UiConst::ICON_WARNING));
    toprowlayout->addWidget(m_icon_no_next);
    toprowlayout->setAlignment(m_icon_no_next, button_align);

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
    HorizontalLine* horizline = new HorizontalLine(UiConst::HEADER_HLINE_WIDTH);
    horizline->setObjectName(CssConst::QUESTIONNAIRE_HORIZONTAL_LINE);
    mainlayout->addWidget(horizline);

}


void QuestionnaireHeader::setButtons(bool previous, bool next, bool finish)
{
    m_button_previous->setVisible(previous);
    m_button_next->setVisible(next);
    m_button_finish->setVisible(finish);
    m_icon_no_next->setVisible(!next && !finish);
}
