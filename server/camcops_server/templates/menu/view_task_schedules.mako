## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/view_task_schedules.mako

===============================================================================

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

===============================================================================

</%doc>

<%inherit file="base_web.mako"/>

<%!
from cardinal_pythonlib.datetimefunc import format_datetime

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Task schedules")}</h1>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>${_("Group")}</th>
        <th>${_("Description")}</th>
        <th>${_("Items")}</th>
        <th>${_("Operations")}</th>
    </tr>
%for schedule in page:
    <tr>
        <td>
            ${ schedule.group.name }
        </td>
        <td>
            ${ schedule.description }
        </td>
        <td>
%for item in schedule.items:
            ${ item }<br>
%endfor
        </td>
        <td>
<a href="${ req.route_url(
    Routes.VIEW_TASK_SCHEDULE_ITEMS,
    _query={
        ViewParam.SCHEDULE_ID: schedule.id
    }
) }">${_("View items")}</a>
        </td>
    </tr>
%endfor
</table>

<div>${page.pager()}</div>

<a href="${ req.route_url(Routes.ADD_TASK_SCHEDULE) }">${_("Add a task schedule")}</a>

<%include file="to_main_menu.mako"/>
