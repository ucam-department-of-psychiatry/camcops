#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"

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
               const QString& icon_filename = "");
signals:
    void backClicked();
    void viewClicked();
    void editClicked();
    void deleteClicked();
    void addClicked();

public slots:
    void offerViewEditDelete(bool offer_view = false,
                             bool offer_edit = false,
                             bool offer_delete = false);
    void offerAdd(bool offer_add = false);
    void lockStateChanged(LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void selectedPatientChanged(bool selected, const QString& details = "");

protected:
    CamcopsApp& m_app;
    QPointer<QLabel> m_icon_whisker_connected;
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
