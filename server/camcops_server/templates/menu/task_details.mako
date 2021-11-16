## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/task_details.mako

===============================================================================

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

</%doc>

<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Icons
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text=_("Task details") + ": " + task_class.tablename
    ) | n }
</h1>

<div>
    ${ req.icon_text(
        icon=Icons.INFO_EXTERNAL,
        url=task_class.help_url(),
        text=task_class.longname(req) + " (" + task_class.shortname + ")"
    ) | n }
</div>

<table>
    <tr>
        <th>${ _("Value") }</th>
        <th>TODO: INSERT MORE CONTENT HERE!</th>
    </tr>
    <tr>
        <td>TODO: INSERT MORE CONTENT HERE!</td>
        <td>TODO: INSERT MORE CONTENT HERE!</td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
