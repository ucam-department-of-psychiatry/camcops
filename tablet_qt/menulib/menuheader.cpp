#include "menuheader.h"
#include <QAbstractButton>
#include <QFrame>
#include <QLabel>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/imagebutton.h"
#include "widgets/labelwordwrapwide.h"


MenuHeader::MenuHeader(QWidget* parent,
                       CamcopsApp& app,
                       bool top,
                       const QString& title,
                       const QString& icon_filename)
    : QWidget(parent),
      m_app(app),
      m_button_add(nullptr)
{
    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------
    QHBoxLayout* toprowlayout = new QHBoxLayout();
    mainlayout->addLayout(toprowlayout);

    // Back button (unless top)
    if (!top) {
        QAbstractButton* back = new ImageButton(UiConst::CBS_BACK);
        toprowlayout->addWidget(back);
        connect(back, &QAbstractButton::clicked,
                this, &MenuHeader::backClicked);
    }

    // Icon
    if (!icon_filename.isEmpty()) {
        QLabel* icon = UiFunc::iconWidget(icon_filename, this);
        toprowlayout->addWidget(icon);
    }

    // Title
    LabelWordWrapWide* title_label = new LabelWordWrapWide(title);
    title_label->setObjectName("menu_window_title");
    toprowlayout->addWidget(title_label);

    // Spacing
    toprowlayout->addStretch();

    // Right-hand icons

    // (a) Task verb buttons
    m_button_view = new ImageButton(UiConst::CBS_ZOOM);
    m_button_edit = new ImageButton(UiConst::CBS_EDIT);
    m_button_delete = new ImageButton(UiConst::CBS_DELETE);
    m_button_add = new ImageButton(UiConst::CBS_ADD);
    toprowlayout->addWidget(m_button_view);
    toprowlayout->addWidget(m_button_edit);
    toprowlayout->addWidget(m_button_delete);
    toprowlayout->addWidget(m_button_add);
    offerViewEditDelete();
    offerAdd();
    connect(m_button_view, &QAbstractButton::clicked,
            this, &MenuHeader::viewClicked);
    connect(m_button_edit, &QAbstractButton::clicked,
            this, &MenuHeader::editClicked);
    connect(m_button_delete, &QAbstractButton::clicked,
            this, &MenuHeader::deleteClicked);
    connect(m_button_add, &QAbstractButton::clicked,
            this, &MenuHeader::addClicked);

    // (b) Whisker
    m_icon_whisker_connected = UiFunc::iconWidget(
        UiFunc::iconFilename(UiConst::ICON_WHISKER), this);
    toprowlayout->addWidget(m_icon_whisker_connected);
    whiskerConnectionStateChanged(m_app.whiskerConnected());

    // (c) Locked/unlocked/privileged
    m_button_locked = new ImageButton(UiConst::CBS_LOCKED);
    m_button_unlocked = new ImageButton(UiConst::CBS_UNLOCKED);
    m_button_privileged = new ImageButton(UiConst::CBS_PRIVILEGED);
    toprowlayout->addWidget(m_button_locked);
    toprowlayout->addWidget(m_button_unlocked);
    toprowlayout->addWidget(m_button_privileged);
    lockStateChanged(m_app.lockstate());
    connect(m_button_locked, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::unlock);
    connect(m_button_unlocked, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::lock);
    connect(m_button_privileged, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::unlock);

    // ------------------------------------------------------------------------
    // Horizontal line
    // ------------------------------------------------------------------------
    QFrame* horizline = new QFrame();
    horizline->setObjectName("header_horizontal_line");
    horizline->setFrameShape(QFrame::HLine);
    horizline->setFrameShadow(QFrame::Plain);
    horizline->setLineWidth(UiConst::HEADER_HLINE_WIDTH);
    mainlayout->addWidget(horizline);

    // ------------------------------------------------------------------------
    // Selected patient
    // ------------------------------------------------------------------------
    m_patient_info = new LabelWordWrapWide(); // *** patient info
    m_patient_info->setObjectName("menu_header_patient_info");
    mainlayout->addWidget(m_patient_info);
    m_no_patient = new LabelWordWrapWide(tr("No patient selected"));
    m_no_patient->setObjectName("menu_header_no_patient");
    mainlayout->addWidget(m_no_patient);
    selectedPatientChanged(m_app.patientSelected(),
                           m_app.patientDetails());

    // ========================================================================
    // Incoming signals
    // ========================================================================
    connect(&m_app, &CamcopsApp::whiskerConnectionStateChanged,
            this, &MenuHeader::whiskerConnectionStateChanged);
    connect(&m_app, &CamcopsApp::lockStateChanged,
            this, &MenuHeader::lockStateChanged);
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &MenuHeader::selectedPatientChanged);
}


void MenuHeader::lockStateChanged(CamcopsApp::LockState lockstate)
{
    m_button_locked->setVisible(lockstate == CamcopsApp::LockState::Locked);
    m_button_unlocked->setVisible(lockstate == CamcopsApp::LockState::Unlocked);
    m_button_privileged->setVisible(lockstate == CamcopsApp::LockState::Privileged);
}


void MenuHeader::whiskerConnectionStateChanged(bool connected)
{
    m_icon_whisker_connected->setVisible(connected);
}


void MenuHeader::selectedPatientChanged(bool selected, const QString& details)
{
    m_no_patient->setVisible(!selected);
    m_patient_info->setVisible(selected);
    m_patient_info->setText(details);
}


void MenuHeader::offerViewEditDelete(bool offer_view, bool offer_edit,
                                     bool offer_delete)
{
    m_button_view->setVisible(offer_view);
    m_button_edit->setVisible(offer_edit);
    m_button_delete->setVisible(offer_delete);
}


void MenuHeader::offerAdd(bool offer_add)
{
    m_button_add->setVisible(offer_add);
}
