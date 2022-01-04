## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/exported_task_fhir_entry.mako

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
        icon=Icons.AUDIT_ITEM,
        text=_("Individual FHIR export entry")
    ) | n }
</h1>

<table>
    <tr>
        <th>ExportedTaskFhirEntry ID</th>
        <td>${ etfe.id }</td>
    </tr>
    <tr>
        <th>ExportedTaskFhir</th>
        <td>
            ${ req.icon_text(
                    icon=Icons.EXPORTED_TASK_ENTRY_COLLECTION,
                    url=request.route_url(
                        Routes.VIEW_EXPORTED_TASK_FHIR,
                        _query={
                            ViewParam.ID: etfe.exported_task_fhir_id
                        }
                    ),
                    text="ExportedTaskFhir " + str(etfe.exported_task_fhir_id)
            ) | n }
        </td>
    </tr>
    <tr>
        <th>ETag</th>
        <td>
            ${ etfe.etag or "" }
        </td>
    </tr>
    <tr>
        <th>Server's date/time modified</th>
        <td>
            ${ etfe.last_modified }
        </td>
    </tr>
    <tr>
        <th>Location (if the operation returns one)</th>
        <td>
            %if etfe.location:
                ${ req.icon_text(
                        icon=Icons.INFO_EXTERNAL,
                        url=etfe.location_url,
                        text=etfe.location
                ) | n }
            %endif
        </td>
    </tr>
    <tr>
        <th>Status</th>
        <td>
            ${ etfe.status or "" }
        </td>
    </tr>
</table>

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
