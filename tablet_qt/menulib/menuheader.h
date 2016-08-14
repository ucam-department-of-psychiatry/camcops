#pragma once
#include <QLabel>
#include <QWidget>
#include "common/camcopsapp.h"

class QAbstractButton;
class MenuHeaderPatientInfo;
class MenuHeaderNoPatient;


class MenuHeader : public QWidget
{
    Q_OBJECT
public:
    MenuHeader(QWidget* parent,
               CamcopsApp& app,
               bool top,
               const QString& title,
               const QString& icon_filename = "",
               bool offer_add_task = false);
signals:
    void back();
    void viewTask();
    void editTask();
    void deleteTask();
    void addTask();

public Q_SLOTS:
    void taskSelectionChanged(Task* p_task = nullptr);

protected Q_SLOTS:
    void backClicked();
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
    MenuHeaderPatientInfo* m_patient_info;
    MenuHeaderNoPatient* m_no_patient;
};


// ============================================================================
// The following classes exist just for CSS.
// ============================================================================

class MenuWindowTitle : public QLabel
{
    Q_OBJECT
public:
    MenuWindowTitle(QWidget* parent = nullptr, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuWindowTitle(const QString& text, QWidget* parent = nullptr,
                    Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuWindowTitle() {}
};


class MenuHeaderPatientInfo : public QLabel
{
    Q_OBJECT
public:
    MenuHeaderPatientInfo(QWidget* parent = nullptr, Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuHeaderPatientInfo(const QString& text, QWidget* parent = nullptr,
                          Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuHeaderPatientInfo() {}
};


class MenuHeaderNoPatient : public QLabel
{
    Q_OBJECT
public:
    MenuHeaderNoPatient(QWidget* parent = nullptr,
                                Qt::WindowFlags f = 0) :
        QLabel(parent, f)
    {}
    MenuHeaderNoPatient(const QString& text, QWidget* parent = nullptr,
                        Qt::WindowFlags f = 0) :
        QLabel(text, parent, f)
    {}
    virtual ~MenuHeaderNoPatient() {}
};
