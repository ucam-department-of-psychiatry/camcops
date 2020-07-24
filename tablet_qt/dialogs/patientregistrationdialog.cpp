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

#include "patientregistrationdialog.h"
#include <QDialogButtonBox>
#include <QColor>
#include <QLabel>
#include <QLineEdit>
#include <QPalette>
#include <QPushButton>
#include <QFormLayout>
#include <QUrl>
#include "common/varconst.h"
#include "lib/uifunc.h"
#include "qobjects/proquintvalidator.h"
#include "qobjects/urlvalidator.h"

PatientRegistrationDialog::PatientRegistrationDialog(
    QWidget* parent) : QDialog(parent),
                       m_url_valid(false),
                       m_proquint_valid(false)
{
    setWindowTitle(tr("Registration"));
    setMinimumSize(uifunc::minimumSizeForTitle(this));

    m_editor_server_url = new QLineEdit();
    QValidator *url_validator = new UrlValidator();
    m_editor_server_url->setValidator(url_validator);
    connect(m_editor_server_url.data(), &QLineEdit::textChanged,
            this, &PatientRegistrationDialog::urlChanged);

    m_editor_patient_proquint = new QLineEdit();
    QValidator *proquint_validator = new ProquintValidator();
    m_editor_patient_proquint->setValidator(proquint_validator);
    connect(m_editor_patient_proquint.data(), &QLineEdit::textChanged,
            this, &PatientRegistrationDialog::proquintChanged);

    m_buttonbox = new QDialogButtonBox(QDialogButtonBox::Ok);

    connect(m_buttonbox, &QDialogButtonBox::accepted, this,
            &PatientRegistrationDialog::accept);

    updateOkButtonEnabledState();

    auto mainlayout = new QFormLayout();
    mainlayout->setRowWrapPolicy(QFormLayout::WrapAllRows);
    mainlayout->addRow(
        tr("<b>CamCOPS server location</b> (e.g. https://server.example.com/camcops/database):"),
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

void PatientRegistrationDialog::urlChanged()
{
    auto validator = new UrlValidator();

    QString url = serverUrlAsString();

    QColor background_color = Qt::red;
    QColor foreground_color = Qt::white;
    m_url_valid = false;

    int pos = 0;
    QValidator::State state = validator->validate(url, pos);
    if (state == QValidator::Acceptable) {
        background_color = Qt::green;
        foreground_color = Qt::black;

        m_url_valid = true;
    }

    QPalette palette;
    palette.setColor(QPalette::Base, background_color);
    palette.setColor(QPalette::Text, foreground_color);

    m_editor_server_url->setPalette(palette);

    updateOkButtonEnabledState();
}

void PatientRegistrationDialog::proquintChanged()
{
    auto validator = new ProquintValidator();

    QString proquint = patientProquint();

    QColor background_color = Qt::red;
    QColor foreground_color = Qt::white;
    m_proquint_valid = false;

    int pos = 0;
    QValidator::State state = validator->validate(proquint, pos);
    if (state == QValidator::Acceptable) {
        background_color = Qt::green;
        foreground_color = Qt::black;

        m_proquint_valid = true;
    }

    QPalette palette;
    palette.setColor(QPalette::Base, background_color);
    palette.setColor(QPalette::Text, foreground_color);

    m_editor_patient_proquint->setPalette(palette);

    updateOkButtonEnabledState();
}

void PatientRegistrationDialog::updateOkButtonEnabledState()
{
    bool enable = m_url_valid && m_proquint_valid;

    m_buttonbox->button(QDialogButtonBox::Ok)->setEnabled(enable);
}
