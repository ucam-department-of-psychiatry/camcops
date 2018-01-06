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

#include "patientsummarymenu.h"
#include "common/uiconst.h"
#include "dbobjects/patient.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskfactory.h"


PatientSummaryMenu::PatientSummaryMenu(CamcopsApp& app) :
    MenuWindow(app, tr("Patient summary"),
               uifunc::iconFilename(uiconst::ICON_PATIENT_SUMMARY))
{
    // m_items is EXPENSIVE (and depends on security), so leave it to build()

    // Signals
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &PatientSummaryMenu::selectedPatientChanged,
            Qt::UniqueConnection);
    connect(&m_app, &CamcopsApp::taskAlterationFinished,
            this, &PatientSummaryMenu::taskFinished,
            Qt::UniqueConnection);
}


void PatientSummaryMenu::build()
{
    TaskFactory* factory = m_app.taskFactory();

    // Common items
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
        MAKE_CHANGE_PATIENT(m_app),
        MenuItem(tr("Task instances")).setLabelOnly(),
    };

    // Task items
    const TaskPtrList tasklist = factory->fetch();
    qDebug() << Q_FUNC_INFO << "-" << tasklist.size() << "task(s)";
    for (auto task : tasklist) {
        m_items.append(MenuItem(task, true, false));
    }

    // Call parent build()
    MenuWindow::build();
}


void PatientSummaryMenu::selectedPatientChanged(const Patient* patient)
{
    Q_UNUSED(patient);
    build();  // refresh task list
}


void PatientSummaryMenu::taskFinished()
{
    build();  // refresh task list
}
