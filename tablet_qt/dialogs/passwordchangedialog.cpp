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

#include "passwordchangedialog.h"

#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QVBoxLayout>

#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "qobjects/widgetpositioner.h"


const int MINIMUM_PASSWORD_LENGTH = 10;
const QString PROHIBITED_PASSWORDS_FILE(
    ":/resources/camcops/prohibited_passwords/PwnedPasswordsTop100k.txt"
);

bool passwordProhibited(const QString& password)
{
    return filefunc::fileContainsLine(PROHIBITED_PASSWORDS_FILE, password);
}

PasswordChangeDialog::PasswordChangeDialog(
    const QString& text,
    const QString& title,
    const bool require_old_password,
    QWidget* parent
) :
    QDialog(parent),
    m_editor_old(nullptr),
    m_editor_new1(nullptr),
    m_editor_new2(nullptr)
{
    setWindowTitle(title);
    setMinimumSize(uifunc::minimumSizeForTitle(this));

    auto mainlayout = new QVBoxLayout();

    auto prompt = new QLabel(text);
    prompt->setWordWrap(true);
    mainlayout->addWidget(prompt);

    if (require_old_password) {
        auto prompt_old = new QLabel(tr("Enter old password:"));
        prompt_old->setWordWrap(true);
        mainlayout->addWidget(prompt_old);
        m_editor_old = new QLineEdit();
        m_editor_old->setEchoMode(QLineEdit::Password);
        mainlayout->addWidget(m_editor_old);

        // Work around https://bugreports.qt.io/browse/QTBUG-125337
        setFocusProxy(m_editor_old);
    }

    auto prompt_new1 = new QLabel(tr("Enter new password:"));
    prompt_new1->setWordWrap(true);
    mainlayout->addWidget(prompt_new1);
    m_editor_new1 = new QLineEdit();
    m_editor_new1->setEchoMode(QLineEdit::Password);
    m_editor_new1->setPlaceholderText(
        tr("Must be at least %1 characters").arg(MINIMUM_PASSWORD_LENGTH)
    );
    if (!require_old_password) {
        // Work around https://bugreports.qt.io/browse/QTBUG-125337
        setFocusProxy(m_editor_new1);
    }
    mainlayout->addWidget(m_editor_new1);

    auto prompt_new2
        = new QLabel(tr("Enter new password again for confirmation:"));
    prompt_new2->setWordWrap(true);

    mainlayout->addWidget(prompt_new2);
    m_editor_new2 = new QLineEdit();
    m_editor_new2->setEchoMode(QLineEdit::Password);
    mainlayout->addWidget(m_editor_new2);

    auto buttonbox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel
    );
    connect(
        buttonbox,
        &QDialogButtonBox::accepted,
        this,
        &PasswordChangeDialog::okClicked
    );
    connect(
        buttonbox,
        &QDialogButtonBox::rejected,
        this,
        &PasswordChangeDialog::reject
    );
    mainlayout->addWidget(buttonbox);
    mainlayout->addStretch(1);

    new WidgetPositioner(this);

    setLayout(mainlayout);
}

QString PasswordChangeDialog::oldPassword() const
{
    if (!m_editor_old) {
        return "";
    }
    return m_editor_old->text();
}

QString PasswordChangeDialog::newPassword() const
{
    if (!m_editor_new1) {
        return "";
    }
    return m_editor_new1->text();
}

void PasswordChangeDialog::okClicked()
{
    if (!m_editor_new1 || !m_editor_new2) {
        return;
    }
    const QString newpw1 = m_editor_new1->text();
    const QString newpw2 = m_editor_new2->text();
    if (newpw1.isEmpty()) {
        uifunc::alert(tr("Can't set an empty password"));
        return;
    }
    if (newpw1.size() < MINIMUM_PASSWORD_LENGTH) {
        uifunc::alert(tr("Password must be at least %1 characters long")
                          .arg(MINIMUM_PASSWORD_LENGTH));
        return;
    }
    if (newpw1 != newpw2) {
        uifunc::alert(tr("New passwords don't match"));
        return;
    }
    if (passwordProhibited(newpw1)) {
        uifunc::alert(
            tr("That password is used too commonly. Please pick another.")
        );
        return;
    }
    accept();
}
