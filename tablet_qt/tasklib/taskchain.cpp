/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "taskchain.h"
#include "core/camcopsapp.h"
#include "tasklib/taskfactory.h"


TaskChain::TaskChain(CamcopsApp& app,
                     const QStringList& task_tablenames,
                     CreationMethod creation_method,
                     const QString& title,
                     const QString& subtitle) :
    m_app(app),
    m_task_tablenames(task_tablenames),
    m_creation_method(creation_method),
    m_title(title),
    m_subtitle(subtitle)
{
}


QString TaskChain::title() const
{
    return m_title.isEmpty() ? tr("Task chain") : m_title;
}


QString TaskChain::subtitle() const
{
    return m_subtitle.isEmpty() ? description() : m_subtitle;
}


QString TaskChain::description(const bool longname) const
{
    QStringList tasknames;
    TaskFactory* factory = m_app.taskFactory();
    for (int i = 0; i < m_task_tablenames.length(); ++i) {
        const int pos = i + 1;
        const auto& tablename = m_task_tablenames[i];
        const QString taskname = longname ? factory->longname(tablename)
                                          : factory->shortname(tablename);
        tasknames.append(QString("%1. %2").arg(QString::number(pos),
                                               taskname));
    }
    return tasknames.join(" → ");
}


int TaskChain::nTasks() const
{
    return m_task_tablenames.length();
}


TaskChain::CreationMethod TaskChain::creationMethod() const
{
    return m_creation_method;
}


TaskPtr TaskChain::makeTask(int index) const
{
    if (index < 0 || index >= nTasks()) {
        return nullptr;
    }
    return m_app.taskFactory()->create(m_task_tablenames[index]);
}
