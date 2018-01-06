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

#pragma once
#include <QDialog>
#include <QString>
#include "questionnairelib/namevalueoptions.h"

class QVariant;


class NvpChoiceDialog : public QDialog
{
    // Dialog to choose between a set of name/value pairs (offering the names,
    // returning the chosen value via a pointer).
    // MODAL and BLOCKING.

    Q_OBJECT
public:
    NvpChoiceDialog(QWidget* parent, const NameValueOptions& options,
                    const QString& title = "");
    virtual int choose(QVariant* new_value);
    virtual bool event(QEvent* e) override;
protected slots:
    void itemClicked(int index);
protected:
    NameValueOptions m_options;
    QString m_title;
    QVariant* m_new_value;
};
