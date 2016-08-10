#include "menuheader.h"
#include <QAbstractButton>
#include <QFrame>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include "lib/uifunc.h"


MenuHeader::MenuHeader(QWidget* parent,
                       CamcopsApp& app,
                       bool top,
                       const QString& title)
    : QWidget(parent),
      m_app(app)
{
    QVBoxLayout* mainlayout = new QVBoxLayout();
    setLayout(mainlayout);

    // ------------------------------------------------------------------------
    // Main row
    // ------------------------------------------------------------------------
    QHBoxLayout* toprowlayout = new QHBoxLayout();
    mainlayout->addLayout(toprowlayout);
    // Back button, or CamCOPS icon
    if (top) {
        QLabel* logo = ICON_CAMCOPS(this);
        toprowlayout->addWidget(logo);
    } else {
        QAbstractButton* back = CAMCOPS_BUTTON_BACK(this);
        toprowlayout->addWidget(back);
        connect(back, &QAbstractButton::clicked,
                this, &MenuHeader::backClicked);
    }
    // Title
    QLabel* title_label = new QLabel(title);
    toprowlayout->addWidget(title_label);
    // Spacing
    toprowlayout->addStretch();
    // Right-hand icons
    m_button_locked = CAMCOPS_BUTTON_LOCKED(this);
    m_button_unlocked = CAMCOPS_BUTTON_UNLOCKED(this);
    m_button_privileged = CAMCOPS_BUTTON_PRIVILEGED(this);
    toprowlayout->addWidget(m_button_locked);
    toprowlayout->addWidget(m_button_unlocked);
    toprowlayout->addWidget(m_button_privileged);
    connect(m_button_locked, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::unlock);
    connect(m_button_unlocked, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::lock);
    connect(m_button_privileged, &QAbstractButton::clicked,
            &m_app, &CamcopsApp::unlock);
    lockStateChanged(m_app.lockstate());

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
    QLabel* patient_label = new QLabel("dummy patient line");
    mainlayout->addWidget(patient_label);

    connect(&m_app, &CamcopsApp::lockStateChanged,
            this, &MenuHeader::lockStateChanged);
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
