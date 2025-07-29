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

#include "dangerousconfirmationdialog.h"

#include <QDialog>
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QVBoxLayout>

#include "common/textconst.h"
#include "lib/widgetfunc.h"
#include "qobjects/widgetpositioner.h"

DangerousConfirmationDialog::DangerousConfirmationDialog(
    const QString& text, const QString& title, QWidget* parent
) :
    QDialog(parent)
{
    setWindowTitle(title);
    setMinimumSize(widgetfunc::minimumSizeForTitle(this));

    auto prompt = new QLabel(text);
    prompt->setWordWrap(true);
    auto prompt2 = new QLabel(
        //: This will expand to: If you are sure, enter *Yes* here
        tr("If you are sure, enter <b>%1</b> here").arg(TextConst::yes())
    );
    prompt2->setWordWrap(true);

    m_editor = new QLineEdit();

    auto buttonbox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel
    );
    connect(
        buttonbox,
        &QDialogButtonBox::accepted,
        this,
        &DangerousConfirmationDialog::accept
    );
    connect(
        buttonbox,
        &QDialogButtonBox::rejected,
        this,
        &DangerousConfirmationDialog::reject
    );

    auto mainlayout = new QVBoxLayout();

    mainlayout->addWidget(prompt);
    mainlayout->addWidget(prompt2);
    mainlayout->addWidget(m_editor);
    mainlayout->addWidget(buttonbox);
    mainlayout->addStretch(1);

    new WidgetPositioner(this);

    setLayout(mainlayout);
}

bool DangerousConfirmationDialog::confirmed()
{
    const int reply = exec();
    if (reply != QDialog::Accepted) {
        return false;
    }

    return (m_editor->text() == TextConst::yes());
}
