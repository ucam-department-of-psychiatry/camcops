## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/exported_task_file_group.mako

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

<%inherit file="base_web.mako"/>

<%!
from markupsafe import escape
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.AUDIT_ITEM,
        text=_("Exported files")
    ) | n }
</h1>

<table>
    <tr>
        <th>File group ID</th>
        <td>${ fg.id }</td>
    </tr>
    <tr>
        <th>Exported task ID</th>
        <td>
            ${ req.icon_text(
                    icon=Icons.EXPORTED_TASK,
                    url=request.route_url(
                        Routes.VIEW_EXPORTED_TASK,
                        _query={
                            ViewParam.ID: fg.exported_task_id
                        }
                    ),
                    text="ExportedTask " + str(fg.exported_task_id)
            ) | n }
        </td>
    </tr>
    <tr>
        <th>Filenames</th>
        <td>${ "<br>".join(escape(filename) for filename in fg.filenames) | n }</td>
    </tr>
    <tr>
        <th>Script called?</th>
        <td>${ fg.script_called }</td>
    </tr>
    <tr>
        <th>Script exit code</th>
        <td>${ fg.script_retcode }</td>
    </tr>
    <tr>
        <th>Script stdout</th>
        <td>${ fg.script_stdout }</td>
    </tr>
    <tr>
        <th>Script stderr</th>
        <td>${ fg.script_stderr }</td>
    </tr>
</table>

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
