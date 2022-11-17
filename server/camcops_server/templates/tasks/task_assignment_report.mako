## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/tasks/task_assignment_report.mako

===============================================================================

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

===============================================================================

</%doc>

<%inherit file="report.mako"/>

<%block name="additional_report_below_results">
    <ul>
        <li>
            ${ req.gettext("This report counts patients created directly on the server, and scheduled tasks assigned to them.") }
        </li>
        <li>
            ${ req.gettext("Unless a specific start time was set by the administrator when assigining a patient to a task schedule, the count of 'tasks_assigned' is for the month/year the patients registered themselves on the CamCOPS app.") }
        </li>
        <li>
            ${ req.gettext("Tasks for patients who are yet to register appear in the count of 'tasks_assigned' for the date 'None'.") }
        </li>
    </ul>
</%block>
