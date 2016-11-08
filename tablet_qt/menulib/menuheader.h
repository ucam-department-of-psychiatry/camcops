#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"  // for LockState

class QAbstractButton;
class QLabel;


class MenuHeader : public QWidget
{
    Q_OBJECT
public:
    MenuHeader(QWidget* parent,
               CamcopsApp& app,
               bool top,
               const QString& title,
               const QString& icon_filename = "",
               bool debug_allowed = false);
signals:
    void backClicked();
    void viewClicked();
    void editClicked();
    void deleteClicked();
    void addClicked();
    void debugLayout();

public slots:
    void offerView(bool offer_view = false);
    void offerEditDelete(bool offer_edit = false, bool offer_delete = false);
    void offerAdd(bool offer_add = false);
    void lockStateChanged(CamcopsApp::LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void needsUploadChanged(bool needs_upload);
    void selectedPatientChanged(const Patient* patient);

protected:
    CamcopsApp& m_app;
    QPointer<QLabel> m_icon_whisker_connected;
    QPointer<QLabel> m_icon_needs_upload;
    QPointer<QPushButton> m_button_debug;
    QPointer<QAbstractButton> m_button_view;
    QPointer<QAbstractButton> m_button_edit;
    QPointer<QAbstractButton> m_button_delete;
    QPointer<QAbstractButton> m_button_add;
    QPointer<QAbstractButton> m_button_locked;
    QPointer<QAbstractButton> m_button_unlocked;
    QPointer<QAbstractButton> m_button_privileged;
    QPointer<QLabel> m_patient_info;
    QPointer<QLabel> m_no_patient;
};
