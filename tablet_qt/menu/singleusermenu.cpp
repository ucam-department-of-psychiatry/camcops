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

#include "singleusermenu.h"

#include <QDebug>
#include <QPushButton>
#include <QSharedPointer>

#include "common/uiconst.h"
#include "core/networkmanager.h"
#include "lib/datetime.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "tasklib/taskschedule.h"
#include "tasklib/taskscheduleitem.h"

SingleUserMenu::SingleUserMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_CAMCOPS), true)
{
}

QString SingleUserMenu::title() const
{
    return tr("CamCOPS: Cambridge Cognitive and Psychiatric Assessment Kit");
}

void SingleUserMenu::makeItems()
{
    m_items = {};

    TaskSchedulePtrList schedules = m_app.getTaskSchedules();

    for (const TaskSchedulePtr& schedule : schedules) {
        QVector<MenuItem> started_items = {};
        QVector<MenuItem> due_items = {};
        QVector<MenuItem> completed_items = {};

        auto earliest_future_time = QDateTime();  // invalid

        for (const TaskScheduleItemPtr& schedule_item : schedule->items()) {
            auto state = schedule_item->state();

            switch (state) {

                case TaskScheduleItem::State::Started:
                    started_items.append(TaskScheduleItemMenuItem(schedule_item
                    ));
                    break;

                case TaskScheduleItem::State::Completed:
                    completed_items.append(
                        TaskScheduleItemMenuItem(schedule_item)
                    );
                    break;

                case TaskScheduleItem::State::Due:
                    due_items.append(TaskScheduleItemMenuItem(schedule_item));
                    break;

                case TaskScheduleItem::State::Future: {
                    auto future_time = schedule_item->dueFromLocal();

                    if (!earliest_future_time.isValid()
                        || future_time < earliest_future_time) {

                        earliest_future_time = future_time;
                    }
                } break;

                default:
                    break;
            }
        }

        const int total_items
            = started_items.size() + completed_items.size() + due_items.size();

        const int to_do_items = started_items.size() + due_items.size();

        if (total_items > 0 || earliest_future_time.isValid()) {
            m_items.append(MenuItem(tr("Schedule: %1").arg(schedule->name()))
                               .setLabelOnly());
        }

        if (to_do_items == 0 && earliest_future_time.isValid()) {
            const QString readable_datetime
                = earliest_future_time.toString(datetime::LONG_DATETIME_FORMAT
                );
            m_items.append(
                MenuItem(tr("The next task will be available at: %1")
                             .arg(readable_datetime))
                    .setImplemented(true)
                    .setIcon(uifunc::iconFilename(uiconst::ICON_INFO))
            );
        }

        if (total_items > 0) {
            m_items.append(started_items);
            m_items.append(due_items);
            m_items.append(completed_items);
        }
    }

    if (!m_app.needToRegisterSinglePatient()) {
        if (m_items.size() == 0) {
            m_items.append(MenuItem(tr("You do not have any scheduled tasks"))
                               .setLabelOnly());
        }
    }
}
