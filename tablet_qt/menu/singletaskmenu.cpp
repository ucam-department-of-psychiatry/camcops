/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "singletaskmenu.h"
#include "common/uiconstants.h"
#include "dbobjects/patient.h"
#include "lib/filefunc.h"
#include "lib/uifunc.h"
#include "lib/stringfunc.h"
#include "menulib/menuheader.h"
#include "menulib/menuitem.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


SingleTaskMenu::SingleTaskMenu(const QString& tablename, CamcopsApp& app) :
    MenuWindow(app, ""),  // start with a blank title
    m_tablename(tablename)
{
    // Title
    TaskFactory* factory = app.taskFactory();
    TaskPtr specimen = factory->create(m_tablename);
    m_title = specimen->menutitle();
    m_p_header->setTitle(m_title);
    m_anonymous = specimen->isAnonymous();
    if (m_anonymous) {
        setIcon(uifunc::iconFilename(uiconst::ICON_ANONYMOUS));
    }
    bool crippled = specimen->isCrippled();
    m_p_header->setCrippled(crippled);

    // m_items is EXPENSIVE (and depends on security), so leave it to build()

    // Signals
    connect(&m_app, &CamcopsApp::selectedPatientChanged,
            this, &SingleTaskMenu::selectedPatientChanged,
            Qt::UniqueConnection);
    connect(&m_app, &CamcopsApp::taskAlterationFinished,
            this, &SingleTaskMenu::taskFinished,
            Qt::UniqueConnection);

    connect(m_p_header, &MenuHeader::addClicked,
            this, &SingleTaskMenu::addTask,
            Qt::UniqueConnection);
}


void SingleTaskMenu::build()
{
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr specimen = factory->create(m_tablename);

    // Common items
    QString info_icon_filename = uifunc::iconFilename(uiconst::ICON_INFO);
    m_items = {
        MenuItem(tr("Options")).setLabelOnly(),
    };
    if (!m_anonymous) {
        m_items.append(MAKE_CHANGE_PATIENT(m_app));
    }
    m_items.append(
        MenuItem(
            tr("Task information"),
            HtmlMenuItem(
                m_title,
                filefunc::taskHtmlFilename(specimen->infoFilenameStem()),
                info_icon_filename),
            info_icon_filename
        )
    );
    m_items.append(MenuItem(tr("Task status"),
                            std::bind(&SingleTaskMenu::showTaskStatus, this),
                            info_icon_filename));
    m_items.append(
        MenuItem(tr("Task instances") + ": " + m_title).setLabelOnly()
    );

    // Task items
    TaskPtrList tasklist = factory->fetch(m_tablename);
    qDebug() << Q_FUNC_INFO << "-" << tasklist.size() << "tasks";
    bool show_patient_name = specimen->isAnonymous() || !m_app.isPatientSelected();
    for (auto task : tasklist) {
        m_items.append(MenuItem(task, false, show_patient_name));
    }

    // Call parent buildMenu()
    MenuWindow::build();

    emit offerAdd(m_anonymous || m_app.isPatientSelected());
}


void SingleTaskMenu::addTask()
{
    // The task we create here needs to stay in scope for the duration of the
    // editing! The simplest way is to use a member object to hold the pointer.
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr task = factory->create(m_tablename);
    if (!task->isTaskPermissible()) {
        QString reason = QString("%1<br><br>%2: %3")
                .arg(tr("You cannot add this task with your current settings."),
                     tr("Current reason"),
                     stringfunc::bold(task->whyNotPermissible()));
        uifunc::alert(reason, tr("Not permitted to add task"));
        return;
    }
    if (!task->isAnonymous()) {
        int patient_id = m_app.selectedPatientId();
        if (patient_id == dbconst::NONEXISTENT_PK) {
            qCritical() << Q_FUNC_INFO << "- no patient selected";
            return;
        }
        task->setPatient(m_app.selectedPatientId());
    }
    task->setDefaultClinicianVariablesAtFirstUse();
    task->setDefaultsAtFirstUse();
    task->save();
    editTaskConfirmed(task);
}


void SingleTaskMenu::selectedPatientChanged(const Patient* patient)
{
    build();  // refresh task list
    emit offerAdd(m_anonymous || patient);
}


void SingleTaskMenu::taskFinished()
{
    build();  // refresh task list
}


void SingleTaskMenu::showTaskStatus() const
{
    TaskFactory* factory = m_app.taskFactory();
    TaskPtr specimen = factory->create(m_tablename);
    QStringList info;
    auto add = [this, &info](const char* desc, const QString& value) -> void {
        info.append(QString("%1: %2")
                    .arg(tr(desc),
                         stringfunc::bold(value)));
    };
    add("Long name", specimen->longname());
    add("Short name", specimen->shortname());
    add("Main database table name", specimen->tablename());
    add("Anonymous", uifunc::yesNo(specimen->isAnonymous()));
    add("Has a clinician", uifunc::yesNo(specimen->hasClinician()));
    add("Has a respondent", uifunc::yesNo(specimen->hasRespondent()));
    add("Prohibits clinical use", uifunc::yesNo(specimen->prohibitsClinical()));
    add("Prohibits commercial use", uifunc::yesNo(specimen->prohibitsCommercial()));
    add("Prohibits educational use", uifunc::yesNo(specimen->prohibitsEducational()));
    add("Prohibits research use", uifunc::yesNo(specimen->prohibitsResearch()));
    add("Permissible (creatable) with current settings", uifunc::yesNo(specimen->isTaskPermissible()));
    add("If not, why not permissible", specimen->whyNotPermissible());
    add("Fully functional", uifunc::yesNo(!specimen->isCrippled()));
    add("Extra strings present from server", uifunc::yesNo(specimen->hasExtraStrings()));
    add("Editable once created", uifunc::yesNo(specimen->isEditable()));
    uifunc::alert(info.join("<br>"), tr("Task status"));
}
