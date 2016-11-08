#include "menuheader.h"
#include <QAbstractButton>
#include <QLabel>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include "common/cssconst.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
#include "lib/uifunc.h"
#include "widgets/horizontalline.h"
#include "widgets/imagebutton.h"
#include "widgets/labelwordwrapwide.h"


MenuHeader::MenuHeader(QWidget* parent,
                       CamcopsApp& app,
                       bool top,
                       const QString& title,
                       const QString& icon_filename,
                       bool debug_allowed)
    : QWidget(parent),
      m_app(app),
      m_icon_whisker_connected(nullptr),
      m_icon_needs_upload(nullptr),
      m_button_debug(nullptr),
      m_button_view(nullptr),
      m_button_edit(nullptr),
      m_button_delete(nullptr),
      m_button_add(nullptr),
      m_button_locked(nullptr),
      m_button_unlocked(nullptr),
      m_button_privileged(nullptr),
      m_patient_info(nullptr),
      m_no_patient(nullptr)
{
    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------
    QHBoxLayout* toprowlayout = new QHBoxLayout();
    mainlayout->addLayout(toprowlayout);

    Qt::Alignment button_align = Qt::AlignHCenter | Qt::AlignTop;

    // Back button (unless top)
    if (!top) {
        QAbstractButton* back = new ImageButton(UiConst::CBS_BACK);
        toprowlayout->addWidget(back);
        toprowlayout->setAlignment(back, button_align);
        connect(back, &QAbstractButton::clicked,
                this, &MenuHeader::backClicked);
    }

    // Icon
    if (!icon_filename.isEmpty()) {
        QLabel* icon = UiFunc::iconWidget(icon_filename, this);
        toprowlayout->addWidget(icon);
        toprowlayout->setAlignment(icon, button_align);
    }

    // Title
    LabelWordWrapWide* title_label = new LabelWordWrapWide(title);
    title_label->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    title_label->setObjectName(CssConst::MENU_WINDOW_TITLE);
    toprowlayout->addWidget(title_label);

    // Spacing
    toprowlayout->addStretch();

    // Right-hand icons

    // - Debug
    if (debug_allowed) {
        m_button_debug = new QPushButton("Dump layout");
        connect(m_button_debug, &QAbstractButton::clicked,
                this, &MenuHeader::debugLayout);
        toprowlayout->addWidget(m_button_debug);
    }

    // - Task verb buttons
    m_button_view = new ImageButton(UiConst::CBS_ZOOM);
    m_button_edit = new ImageButton(UiConst::CBS_EDIT);
    m_button_delete = new ImageButton(UiConst::CBS_DELETE);
    m_button_add = new ImageButton(UiConst::CBS_ADD);
    toprowlayout->addWidget(m_button_view);
    toprowlayout->addWidget(m_button_edit);
    toprowlayout->addWidget(m_button_delete);
    toprowlayout->addWidget(m_button_add);
    toprowlayout->setAlignment(m_button_view, button_align);
    toprowlayout->setAlignment(m_button_edit, button_align);
    toprowlayout->setAlignment(m_button_delete, button_align);
    toprowlayout->setAlignment(m_button_add, button_align);
    offerView();
    offerEditDelete();
    offerAdd();
    connect(m_button_view, &QAbstractButton::clicked,
            this, &MenuHeader::viewClicked);
    connect(m_button_edit, &QAbstractButton::clicked,
            this, &MenuHeader::editClicked);
    connect(m_button_delete, &QAbstractButton::clicked,
            this, &MenuHeader::deleteClicked);
    connect(m_button_add, &QAbstractButton::clicked,
            this, &MenuHeader::addClicked);

    // - Whisker
    m_icon_whisker_connected = UiFunc::iconWidget(
        UiFunc::iconFilename(UiConst::ICON_WHISKER), this);
    toprowlayout->addWidget(m_icon_whisker_connected);
    toprowlayout->setAlignment(m_icon_whisker_connected, button_align);
    whiskerConnectionStateChanged(m_app.whiskerConnected());

    // - Needs upload
    m_icon_needs_upload = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_UPLOAD), this);
    toprowlayout->addWidget(m_icon_needs_upload);
    toprowlayout->setAlignment(m_icon_needs_upload, button_align);
    needsUploadChanged(m_app.needsUpload());

    // - Locked/unlocked/privileged
    m_button_locked = new ImageButton(UiConst::CBS_LOCKED);
    m_button_unlocked = new ImageButton(UiConst::CBS_UNLOCKED);
    m_button_privileged = new ImageButton(UiConst::CBS_PRIVILEGED);
    toprowlayout->addWidget(m_button_locked);
    toprowlayout->addWidget(m_button_unlocked);
    toprowlayout->addWidget(m_button_privileged);
    toprowlayout->setAlignment(m_button_locked, button_align);
    toprowlayout->setAlignment(m_button_unlocked, button_align);
    toprowlayout->setAlignment(m_button_privileged, button_align);
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
    HorizontalLine* horizline = new HorizontalLine(UiConst::HEADER_HLINE_WIDTH);
    horizline->setObjectName(CssConst::HEADER_HORIZONTAL_LINE);
    mainlayout->addWidget(horizline);

    // ------------------------------------------------------------------------
    // Selected patient
    // ------------------------------------------------------------------------
    m_patient_info = new LabelWordWrapWide();
    m_patient_info->setObjectName(CssConst::MENU_HEADER_PATIENT_INFO);
    mainlayout->addWidget(m_patient_info);
    m_no_patient = new LabelWordWrapWide(tr("No patient selected"));
    m_no_patient->setObjectName(CssConst::MENU_HEADER_NO_PATIENT);
    mainlayout->addWidget(m_no_patient);
    selectedPatientChanged(m_app.selectedPatient());

    // ========================================================================
    // Incoming signals
    // ========================================================================
    connect(&m_app, &CamcopsApp::whiskerConnectionStateChanged,
            this, &MenuHeader::whiskerConnectionStateChanged);
    connect(&m_app, &CamcopsApp::lockStateChanged,
            this, &MenuHeader::lockStateChanged);
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &MenuHeader::selectedPatientChanged);
    connect(&m_app, &CamcopsApp::selectedPatientDetailsChanged,
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


void MenuHeader::needsUploadChanged(bool needs_upload)
{
    m_icon_needs_upload->setVisible(needs_upload);
}


void MenuHeader::selectedPatientChanged(const Patient* patient)
{
    bool selected = patient != nullptr;
    QString info;

    if (selected) {
        info = QString("<b>%1, %2</b> (%3, %4); %5")
                .arg(patient->surname().toUpper())
                .arg(patient->forename())
                .arg(QString("%1y").arg(patient->ageYears()))
                .arg(patient->dobText())
                .arg(patient->shortIdnumSummary());
    }
    qDebug() << Q_FUNC_INFO << info;
    m_patient_info->setText(info);
    m_no_patient->setVisible(!selected);
    m_patient_info->setVisible(selected);
}


void MenuHeader::offerView(bool offer_view)
{
    m_button_view->setVisible(offer_view);
}


void MenuHeader::offerEditDelete(bool offer_edit, bool offer_delete)
{
    m_button_edit->setVisible(offer_edit);
    m_button_delete->setVisible(offer_delete);
}


void MenuHeader::offerAdd(bool offer_add)
{
    m_button_add->setVisible(offer_add);
}
