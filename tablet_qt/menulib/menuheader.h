#pragma once
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
               const QString& icon_filename = "",
               bool offer_add = false);
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

protected slots:
    void lockStateChanged(LockState lockstate);
    void whiskerConnectionStateChanged(bool connected);
    void selectedPatientChanged(bool selected, const QString& details = "");

protected:
    CamcopsApp& m_app;
    QLabel* m_icon_whisker_connected;
    QAbstractButton* m_button_view;
    QAbstractButton* m_button_edit;
    QAbstractButton* m_button_delete;
    QAbstractButton* m_button_add;
    QAbstractButton* m_button_locked;
    QAbstractButton* m_button_unlocked;
    QAbstractButton* m_button_privileged;
    QLabel* m_patient_info;
    QLabel* m_no_patient;
};
