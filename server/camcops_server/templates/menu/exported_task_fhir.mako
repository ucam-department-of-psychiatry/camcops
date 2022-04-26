## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/exported_task_fhir.mako

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
from camcops_server.cc_modules.cc_mako_helperfunc import listview
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.EXPORTED_TASK_ENTRY_COLLECTION,
        text=_("FHIR export")
    ) | n }
</h1>

<table>
    <tr>
        <th>FHIR message ID</th>
        <td>${ etf.id }</td>
    </tr>
    <tr>
        <th>Exported task ID</th>
        <td>
            ${ req.icon_text(
                    icon=Icons.EXPORTED_TASK,
                    url=request.route_url(
                        Routes.VIEW_EXPORTED_TASK,
                        _query={
                            ViewParam.ID: etf.exported_task_id
                        }
                    ),
                    text="ExportedTask " + str(etf.exported_task_id)
            ) | n }
        </td>
    </tr>
    <tr>
        <th>Entries</th>
        <td>
            ${ listview(
                    req, etf.entries, Routes.VIEW_EXPORTED_TASK_FHIR_ENTRY,
                    "ExportedTaskFhirEntry", Icons.AUDIT_ITEM
            ) | n }
        </td>
    </tr>
</table>

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
