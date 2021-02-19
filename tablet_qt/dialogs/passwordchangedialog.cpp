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

#include "passwordchangedialog.h"
#include <QDialogButtonBox>
#include <QGuiApplication>
#include <QLabel>
#include <QLineEdit>
#include <QResizeEvent>
#include <QScreen>
#include <QVBoxLayout>
#include "lib/uifunc.h"


const int MINIMUM_PASSWORD_LENGTH = 8;

PasswordChangeDialog::PasswordChangeDialog(const QString& text,
                                           const QString& title,
                                           const bool require_old_password,
                                           QWidget* parent) :
    QDialog(parent),
    m_editor_old(nullptr),
    m_editor_new1(nullptr),
    m_editor_new2(nullptr)
{
    setWindowTitle(title);
    setMinimumSize(uifunc::minimumSizeForTitle(this));

    auto mainlayout = new QVBoxLayout();

    m_prompt = new QLabel(text);
    mainlayout->addWidget(m_prompt);

    if (require_old_password) {
        auto prompt_old = new QLabel(tr("Enter old password:"));
#ifdef Q_OS_IOS
        prompt_old->setWordWrap(true);
#endif
        mainlayout->addWidget(prompt_old);
        m_editor_old = new QLineEdit();
        m_editor_old->setEchoMode(QLineEdit::Password);
        mainlayout->addWidget(m_editor_old);
    }

    auto prompt_new1 = new QLabel(tr("Enter new password:"));
    mainlayout->addWidget(prompt_new1);
    m_editor_new1 = new QLineEdit();
    m_editor_new1->setEchoMode(QLineEdit::Password);
    m_editor_new1->setPlaceholderText(
        tr("Must be at least %1 characters").arg(MINIMUM_PASSWORD_LENGTH)
    );
    mainlayout->addWidget(m_editor_new1);

    auto prompt_new2 = new QLabel(tr("Enter new password again for confirmation:"));

    mainlayout->addWidget(prompt_new2);
    m_editor_new2 = new QLineEdit();
    m_editor_new2->setEchoMode(QLineEdit::Password);
    mainlayout->addWidget(m_editor_new2);

    auto buttonbox = new QDialogButtonBox(
                QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttonbox, &QDialogButtonBox::accepted,
            this, &PasswordChangeDialog::okClicked);
    connect(buttonbox, &QDialogButtonBox::rejected,
            this, &PasswordChangeDialog::reject);
    mainlayout->addWidget(buttonbox);

#ifdef Q_OS_IOS
    // Dialogs are full screen on iOS
    m_prompt->setWordWrap(true);
    prompt_new1->setWordWrap(true);
    mainlayout->addStretch(1);
#endif

    setLayout(mainlayout);

    QScreen *screen = QGuiApplication::primaryScreen();
    screen->setOrientationUpdateMask(
        Qt::LandscapeOrientation |
        Qt::PortraitOrientation |
        Qt::InvertedLandscapeOrientation |
        Qt::InvertedPortraitOrientation
    );

    connect(screen, &QScreen::orientationChanged,
            this, &PasswordChangeDialog::orientationChanged);

    orientationChanged(screen->orientation());
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
        uifunc::alert(
            tr("Password must be at least %1 characters long").arg(
                MINIMUM_PASSWORD_LENGTH)
        );
        return;
    }
    if (newpw1 != newpw2) {
        uifunc::alert(tr("New passwords don't match"));
        return;
    }
    accept();
}


void PasswordChangeDialog::orientationChanged(Qt::ScreenOrientation orientation)
{
    QScreen* screen = QGuiApplication::primaryScreen();

    QRect screen_rect = screen->geometry();

    // int new_x = (screen_rect.width() - width()) / 2;
    // int new_y = (screen_rect.height() - height()) / 2;

    Qt::ScreenOrientation screen_orientation = screen->orientation();

    QString label = QString("sw%1 sh%2 dw%3 dh%4 x%5 y%6 o%7 so%8").
        arg(screen_rect.width()).arg(screen_rect.height()).arg(width()).arg(height()).arg(x()).arg(y()).arg(orientation).arg(screen_orientation);
    m_prompt->setText(label);

    // move(new_x, new_y);
}
