/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include <QDialogButtonBox>
#include <QGuiApplication>
#include <QLineEdit>
#include <QPushButton>
#include <QFormLayout>
#include <QRect>
#include <QScreen>
#include <QUrl>
#include "common/varconst.h"
#include "lib/uifunc.h"
#include "qobjects/proquintvalidator.h"
#include "qobjects/urlvalidator.h"
#include "widgets/validatinglineedit.h"
#include "patientregistrationdialog.h"


PatientRegistrationDialog::PatientRegistrationDialog(QWidget* parent) :
    QDialog(parent)
{
    setWindowTitle(tr("Registration"));

    m_editor_server_url = new ValidatingLineEdit(new UrlValidator());
    m_editor_server_url->setInputMethodHints(Qt::ImhNoAutoUppercase |
                                             Qt::ImhNoPredictiveText);
    connect(m_editor_server_url, &ValidatingLineEdit::validated,
            this, &PatientRegistrationDialog::updateOkButtonEnabledState);

    m_editor_patient_proquint = new ValidatingLineEdit(new ProquintValidator());
    m_editor_patient_proquint->setInputMethodHints(Qt::ImhSensitiveData |
                                                   Qt::ImhNoAutoUppercase |
                                                   Qt::ImhNoPredictiveText);
    connect(m_editor_patient_proquint, &ValidatingLineEdit::validated,
            this, &PatientRegistrationDialog::updateOkButtonEnabledState);

    m_buttonbox = new QDialogButtonBox(QDialogButtonBox::Ok);

    connect(m_buttonbox, &QDialogButtonBox::accepted, this,
            &PatientRegistrationDialog::accept);

    updateOkButtonEnabledState();

    // If we do this the labels won't wrap properly
    // https://bugreports.qt.io/browse/QTBUG-89805
    // auto mainlayout = new QFormLayout();
    // mainlayout->setRowWrapPolicy(QFormLayout::WrapAllRows);

    // So we do this instead
    auto mainlayout = new QVBoxLayout();

    auto server_url_label = new QLabel(
        tr("<b>CamCOPS server location</b> (e.g. https://server.example.com/camcops/api):")
    );

    auto patient_proquint_label = new QLabel(
        tr("<b>Access key</b> (e.g. abcde-fghij-klmno-pqrst-uvwxy-zabcd-efghi-jklmn-o):")
    );

    // Reinstate when QFormLayout working:
    // mainlayout->addRow(server_url_label, m_editor_server_url);
    // mainlayout->addRow(patient_proquint_label, m_editor_patient_proquint);

    // and remove these lines:
    mainlayout->addWidget(server_url_label);
    mainlayout->addLayout(m_editor_server_url);
    mainlayout->addWidget(patient_proquint_label);
    mainlayout->addLayout(m_editor_patient_proquint);
    mainlayout->setAlignment(Qt::AlignLeft | Qt::AlignTop);

    mainlayout->addWidget(m_buttonbox);

    // https://stackoverflow.com/questions/18975734/how-can-i-find-the-screen-desktop-size-in-qt-so-i-can-display-a-desktop-notific
    QScreen *screen = QGuiApplication::primaryScreen();
    QRect  screenGeometry = screen->geometry();
    int screen_width = screenGeometry.width();

    if (server_url_label->width() > screen_width) {
        server_url_label->setWordWrap(true);
    }

    if (patient_proquint_label->width() > screen_width) {
        patient_proquint_label->setWordWrap(true);
    }

    setLayout(mainlayout);
}


QString PatientRegistrationDialog::patientProquint() const
{
    return m_editor_patient_proquint->getTrimmedText();
}


QString PatientRegistrationDialog::serverUrlAsString() const
{
    return m_editor_server_url->getTrimmedText();
}


QUrl PatientRegistrationDialog::serverUrl() const
{
    return QUrl(serverUrlAsString());
}


void PatientRegistrationDialog::updateOkButtonEnabledState()
{
    const bool enable = m_editor_server_url->isValid() &&
        m_editor_patient_proquint->isValid();

    m_buttonbox->button(QDialogButtonBox::Ok)->setEnabled(enable);
}
