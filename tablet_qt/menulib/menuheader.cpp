#include "menuheader.h"
#include <QAbstractButton>
#include <QFrame>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include "lib/uifunc.h"


MenuHeader::MenuHeader(QWidget* parent,
                       CamcopsApp& app,
                       bool top,
                       const QString& title,
                       const QString& icon_filename,
                       bool offer_add_task)
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
        QAbstractButton* back = CAMCOPS_BUTTON_BACK(this);
        toprowlayout->addWidget(back);
        connect(back, &QAbstractButton::clicked,
                this, &MenuHeader::backClicked);
    }

    // Icon
    if (!icon_filename.isEmpty()) {
        QLabel* icon = iconWidget(icon_filename, this);
        toprowlayout->addWidget(icon);
    }

    // Title
    MenuWindowTitle* title_label = new MenuWindowTitle(title);
    toprowlayout->addWidget(title_label);

    // Spacing
    toprowlayout->addStretch();

    // Right-hand icons

    // (a) Task verb buttons
    m_button_view = CAMCOPS_BUTTON_ZOOM(this);
    m_button_edit = CAMCOPS_BUTTON_EDIT(this);
    m_button_delete = CAMCOPS_BUTTON_DELETE(this);
    toprowlayout->addWidget(m_button_view);
    toprowlayout->addWidget(m_button_edit);
    toprowlayout->addWidget(m_button_delete);
    taskSelectionChanged();
    connect(m_button_view, &QAbstractButton::clicked,
            this, &MenuHeader::viewTask);
    connect(m_button_edit, &QAbstractButton::clicked,
            this, &MenuHeader::editTask);
    connect(m_button_delete, &QAbstractButton::clicked,
            this, &MenuHeader::deleteTask);
    if (offer_add_task) {
        m_button_add = CAMCOPS_BUTTON_ADD(this);
        toprowlayout->addWidget(m_button_add);
        connect(m_button_add, &QAbstractButton::clicked,
                this, &MenuHeader::addTask);
    }

    // (b) Whisker
    m_icon_whisker_connected = iconWidget(ICON_WHISKER, this);
    toprowlayout->addWidget(m_icon_whisker_connected);
    whiskerConnectionStateChanged(m_app.whiskerConnected());

    // (c) Locked/unlocked/privileged
    m_button_locked = CAMCOPS_BUTTON_LOCKED(this);
    m_button_unlocked = CAMCOPS_BUTTON_UNLOCKED(this);
    m_button_privileged = CAMCOPS_BUTTON_PRIVILEGED(this);
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
    horizline->setFrameShape(QFrame::HLine);
    horizline->setFrameShadow(QFrame::Sunken);
    mainlayout->addWidget(horizline);

    // ------------------------------------------------------------------------
    // Selected patient
    // ------------------------------------------------------------------------
    m_patient_info = new MenuHeaderPatientInfo();
    mainlayout->addWidget(m_patient_info);
    m_no_patient = new MenuHeaderNoPatient(tr("No patient selected"));
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


void MenuHeader::backClicked()
{
    emit back();
}


void MenuHeader::lockStateChanged(LockState lockstate)
{
    m_button_locked->setVisible(lockstate == LockState::Locked);
    m_button_unlocked->setVisible(lockstate == LockState::Unlocked);
    m_button_privileged->setVisible(lockstate == LockState::Privileged);
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


void MenuHeader::taskSelectionChanged(Task* p_task)
{
    bool selected = p_task != nullptr;
    m_button_view->setVisible(selected);
    m_button_edit->setVisible(selected && p_task->isEditable());
    m_button_delete->setVisible(selected);
}
