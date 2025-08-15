/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "patientregistrationdialog.h"

#include <QDialogButtonBox>
#include <QFormLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QScreen>
#include <QUrl>

#include "qobjects/urlvalidator.h"
#include "qobjects/widgetpositioner.h"
#include "widgets/proquintlineedit.h"
#include "widgets/validatinglineedit.h"

const int MIN_WIDTH = 500;
const int MIN_HEIGHT = 500;

PatientRegistrationDialog::PatientRegistrationDialog(
    QWidget* parent, const QUrl& server_url, const QString& patient_proquint
) :
    QDialog(parent)
{
    setWindowTitle(tr("Registration"));

    const int min_width
        = qMin(screen()->availableGeometry().width(), MIN_WIDTH);
    const int min_height
        = qMin(screen()->availableGeometry().height(), MIN_HEIGHT);
    const int min_size = qMin(min_width, min_height);

    setMinimumWidth(min_size);

    m_editor_server_url = new ValidatingLineEdit(new UrlValidator());
    m_editor_server_url->addInputMethodHints(
        Qt::ImhNoAutoUppercase | Qt::ImhNoPredictiveText
    );
    connect(
        m_editor_server_url,
        &ValidatingLineEdit::validated,
        this,
        &PatientRegistrationDialog::updateOkButtonEnabledState
    );

    m_editor_patient_proquint = new ProquintLineEdit();
    connect(
        m_editor_patient_proquint,
        &ValidatingLineEdit::validated,
        this,
        &PatientRegistrationDialog::updateOkButtonEnabledState
    );

    m_buttonbox = new QDialogButtonBox(QDialogButtonBox::Ok);

    connect(
        m_buttonbox,
        &QDialogButtonBox::accepted,
        this,
        &PatientRegistrationDialog::accept
    );

    // If we do this the labels won't wrap properly
    // https://bugreports.qt.io/browse/QTBUG-89805
    // auto mainlayout = new QFormLayout();
    // mainlayout->setRowWrapPolicy(QFormLayout::WrapAllRows);

    // So we do this instead
    auto mainlayout = new QVBoxLayout();
    auto server_url_label
        = new QLabel(tr("<b>CamCOPS server location</b> (e.g. "
                        "https://server.example.com/camcops/api):"));

    auto patient_proquint_label
        = new QLabel(tr("<b>Access key</b> (e.g. "
                        "abcde-fghij-klmno-pqrst-uvwxy-zabcd-efghi-jklmn-o):")
        );

    // Reinstate when QFormLayout working:
    // mainlayout->addRow(server_url_label, m_editor_server_url);
    // mainlayout->addRow(patient_proquint_label, m_editor_patient_proquint);

    // and remove these lines:
    mainlayout->addWidget(server_url_label);
    mainlayout->addWidget(m_editor_server_url);
    mainlayout->addWidget(patient_proquint_label);
    mainlayout->addWidget(m_editor_patient_proquint);

    mainlayout->addStretch(1);
    mainlayout->addWidget(m_buttonbox);

    server_url_label->setWordWrap(true);
    patient_proquint_label->setWordWrap(true);

    new WidgetPositioner(this);

    setLayout(mainlayout);

    // If the text boxes are empty, validation won't happen and
    // updateOkButtonEnabledState() won't get called because the text hasn't
    // changed. So disable the button first.
    m_buttonbox->button(QDialogButtonBox::Ok)->setEnabled(false);
    m_editor_server_url->setText(server_url.url());
    m_editor_patient_proquint->setText(patient_proquint);
}

QString PatientRegistrationDialog::patientProquint() const
{
    return m_editor_patient_proquint->text().trimmed();
}

QString PatientRegistrationDialog::serverUrlAsString() const
{
    return m_editor_server_url->text().trimmed();
}

QUrl PatientRegistrationDialog::serverUrl() const
{
    return QUrl(serverUrlAsString());
}

void PatientRegistrationDialog::updateOkButtonEnabledState()
{
    auto url_state = m_editor_server_url->getState();
    auto proquint_state = m_editor_patient_proquint->getState();

    const bool enable = url_state == QValidator::Acceptable
        && proquint_state == QValidator::Acceptable;

    m_buttonbox->button(QDialogButtonBox::Ok)->setEnabled(enable);
}
