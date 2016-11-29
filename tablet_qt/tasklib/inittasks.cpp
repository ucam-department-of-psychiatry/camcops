/*
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

#include "tasklib/inittasks.h"

#include "tasks/demoquestionnaire.h"
#include "tasks/phq9.h"


void InitTasks(TaskFactory& factory)
{
    // Change these lines to determine which tasks are available:

    initializeDemoQuestionnaire(factory);
    initializePhq9(factory);
}
