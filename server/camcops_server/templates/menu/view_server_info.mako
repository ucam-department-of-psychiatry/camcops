## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/view_server_info.mako

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
from camcops_server.cc_modules.cc_pyramid import Icons, Routes
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text=_("CamCOPS: information about this database/server")
    ) | n }
</h1>

<h2>
    ${ req.icon_text(
        icon=Icons.ID_DEFINITIONS,
        text=_("Identification (ID) numbers")
    ) | n }
</h2>
<table>
    <tr>
        <th>${ _("ID number") }</th>
        <th>${ _("Description") }</th>
        <th>${ _("Short description") }</th>
        <th>${ _("FHIR patient ID system") }</th>
    </tr>
    %for iddef in idnum_definitions:
        <tr>
            <td>${ iddef.which_idnum }</td>
            <td>${ iddef.description }</td>
            <td>${ iddef.short_description }</td>
            <td>
                ${ req.icon_text(
                        icon=Icons.INFO_INTERNAL,
                        url=req.route_url(Routes.FHIR_PATIENT_ID_SYSTEM,
                                          which_idnum=iddef.which_idnum),
                        text=_("FHIR")
                ) | n }
            </td>
        </tr>
    %endfor
</table>

<h2>
    ${ req.icon_text(
        icon=Icons.ACTIVITY,
        text=_("Recent activity")
    ) | n }
</h2>
<table>
    <tr>
        <th>${ _("Time-scale") }</th>
        <th>${ _("Number of active sessions") }</th>
    </tr>
    %for k, v in recent_activity.items():
        <tr>
            <td>${ k }</td>
            <td>${ v }</td>
        </tr>
    %endfor
</table>
<p>
    ${ _("Sessions time out after") } ${ session_timeout_minutes }
    ${ _("minutes; sessions older than this are periodically deleted.") }
</p>

<h2>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text=_("All known tasks")
    ) | n }
</h2>
<p>
    ${ req.icon_text(
            icon=Icons.INFO_INTERNAL,
            url=request.route_url(Routes.TASK_LIST),
            text=_("Task list")
    ) | n }
</p>

<h2>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text=_("Extra string families present")
    ) | n }
</h2>
<ul>
%for sf in string_families:
    <li>
        ${ sf  }
        %if sf in restricted_tasks:
            <b>— restricted to groups: ${ ", ".join(restricted_tasks[sf]) }</b>
        %endif
    </li>
%endfor
</ul>

<%include file="to_main_menu.mako"/>
