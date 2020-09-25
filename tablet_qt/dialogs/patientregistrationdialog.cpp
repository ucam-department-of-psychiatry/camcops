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
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QFormLayout>
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
    setMinimumSize(uifunc::minimumSizeForTitle(this));

    m_editor_server_url = new ValidatingLineEdit(new UrlValidator());
    connect(m_editor_server_url, &ValidatingLineEdit::validated,
            this, &PatientRegistrationDialog::updateOkButtonEnabledState);

    m_editor_patient_proquint = new ValidatingLineEdit(new ProquintValidator());
    connect(m_editor_patient_proquint, &ValidatingLineEdit::validated,
            this, &PatientRegistrationDialog::updateOkButtonEnabledState);

    m_buttonbox = new QDialogButtonBox(QDialogButtonBox::Ok);

    connect(m_buttonbox, &QDialogButtonBox::accepted, this,
            &PatientRegistrationDialog::accept);

    updateOkButtonEnabledState();

    auto mainlayout = new QFormLayout();
    mainlayout->setRowWrapPolicy(QFormLayout::WrapAllRows);
    mainlayout->addRow(
        tr("<b>CamCOPS server location</b> (e.g. https://server.example.com/camcops/api):"),
        m_editor_server_url
    );

    mainlayout->addRow(
        tr("<b>Access key</b> (e.g. abcde-fghij-klmno-pqrst-uvwxy-zabcd-efghi-jklmn-o):"),
        m_editor_patient_proquint
    );

    mainlayout->addWidget(m_buttonbox);
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
