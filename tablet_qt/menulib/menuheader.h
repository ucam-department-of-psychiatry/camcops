/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once
#include <QPointer>
#include <QWidget>
#include "common/camcopsapp.h"  // for LockState

class QAbstractButton;
class QLabel;
class QPushButton;


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
