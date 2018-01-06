/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "passwordentrydialog.h"
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QVBoxLayout>


PasswordEntryDialog::PasswordEntryDialog(const QString& text,
                                         const QString& title,
                                         QWidget* parent) :
    QDialog(parent)
{
    setWindowTitle(title);

    QLabel* prompt = new QLabel(text);

    m_editor = new QLineEdit();
    m_editor->setEchoMode(QLineEdit::Password);

    QDialogButtonBox* buttonbox = new QDialogButtonBox(
                QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttonbox, &QDialogButtonBox::accepted,
            this, &PasswordEntryDialog::accept);
    connect(buttonbox, &QDialogButtonBox::rejected,
            this, &PasswordEntryDialog::reject);

    QVBoxLayout* mainlayout = new QVBoxLayout();
    mainlayout->addWidget(prompt);
    mainlayout->addWidget(m_editor);
    mainlayout->addWidget(buttonbox);
    setLayout(mainlayout);
}


QString PasswordEntryDialog::password() const
{
    if (!m_editor) {
        return "";
    }
    return m_editor->text();
}
