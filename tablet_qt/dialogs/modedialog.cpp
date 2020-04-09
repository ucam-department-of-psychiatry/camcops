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

#include "modedialog.h"
#include <QButtonGroup>
#include <QDialogButtonBox>
#include <QLabel>
#include <QRadioButton>
#include <QVBoxLayout>
#include "common/varconst.h"
#include "lib/uifunc.h"


ModeDialog::ModeDialog(QWidget* parent) : QDialog(parent)
{
    setWindowTitle(tr("Select clinician or single user mode"));
    setMinimumSize(uifunc::minimumSizeForTitle(this));

    auto prompt = new QLabel(tr("I would like to use CamCOPS as a:"));

    m_mode_selector = new QButtonGroup();
    auto clinician_button = new QRadioButton(tr("clinician"));
    auto single_user_button = new QRadioButton(tr("single user"));
    single_user_button->setChecked(true);
    m_mode_selector->addButton(clinician_button, varconst::MODE_CLINICIAN);
    m_mode_selector->addButton(single_user_button, varconst::MODE_SINGLE_USER);

    auto prompt2 = new QLabel(
        tr("If you are not sure, leave <b>single user</b> selected")
    );

    auto buttonbox = new QDialogButtonBox(QDialogButtonBox::Ok);
    connect(buttonbox, &QDialogButtonBox::accepted, this, &ModeDialog::accept);

    auto mainlayout = new QVBoxLayout();
    mainlayout->addWidget(prompt);
    mainlayout->addWidget(clinician_button);
    mainlayout->addWidget(single_user_button);
    mainlayout->addWidget(prompt2);
    mainlayout->addWidget(buttonbox);
    setLayout(mainlayout);
}

int ModeDialog::mode() const
{
    return m_mode_selector->checkedId();
}
