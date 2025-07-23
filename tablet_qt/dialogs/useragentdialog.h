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

#pragma once
#include <QAbstractButton>
#include <QDialog>
#include <QDialogButtonBox>
#include <QLineEdit>
#include <QPointer>

class UserAgentDialog : public QDialog
{
    Q_OBJECT

public:
    UserAgentDialog(
        const QString default_user_agent,
        const QString current_user_agent,
        QWidget* parent = nullptr
    );
    QString userAgent() const;

protected:
    QString m_default_user_agent;
    QPointer<QLineEdit> m_user_agent_edit;
    QPointer<QDialogButtonBox> m_buttonbox;

private slots:
    void handleButtonClicked(QAbstractButton* button);
};
