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

#include "useragentdialog.h"

#include <QButtonGroup>
#include <QDialog>
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QVBoxLayout>

#include "lib/widgetfunc.h"
#include "qobjects/widgetpositioner.h"

UserAgentDialog::UserAgentDialog(
    const QString default_user_agent,
    const QString current_user_agent,
    QWidget* parent
) :
    QDialog(parent)
{
    setWindowTitle(tr("Change user agent"));
    setMinimumSize(widgetfunc::minimumSizeForTitle(this));

    auto warning = new QLabel(
        tr("WARNING: Changing the user agent could stop CamCOPS from "
           "connecting to the server. Do not change this unless there are "
           "problems connecting to the server.")
    );
    m_default_user_agent = default_user_agent;
    m_user_agent_edit = new QLineEdit();
    m_user_agent_edit->setText(current_user_agent);

    QDialogButtonBox::StandardButtons buttons
        = QDialogButtonBox::RestoreDefaults | QDialogButtonBox::Ok
        | QDialogButtonBox::Cancel;
    m_buttonbox = new QDialogButtonBox(buttons);
    connect(
        m_buttonbox,
        &QDialogButtonBox::accepted,
        this,
        &UserAgentDialog::accept
    );
    connect(
        m_buttonbox,
        &QDialogButtonBox::rejected,
        this,
        &UserAgentDialog::reject
    );
    connect(
        m_buttonbox,
        &QDialogButtonBox::clicked,
        this,
        &UserAgentDialog::handleButtonClicked
    );

    auto mainlayout = new QVBoxLayout();

    mainlayout->addWidget(warning);
    mainlayout->addWidget(m_user_agent_edit);
    mainlayout->addStretch(1);
    mainlayout->addWidget(m_buttonbox);

    warning->setWordWrap(true);

    new WidgetPositioner(this);

    setLayout(mainlayout);
}

QString UserAgentDialog::userAgent() const
{
    return m_user_agent_edit->text();
}

void UserAgentDialog::handleButtonClicked(QAbstractButton* button)
{
    if (m_buttonbox->buttonRole(button) == QDialogButtonBox::ResetRole) {
        m_user_agent_edit->setText(m_default_user_agent);
    }
}
