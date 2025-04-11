## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/server_created_patient_edit.mako

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

<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.PATIENT_EDIT,
        text=_("Edit details for patient")
    ) | n }
</h1>

<%
    duplicates = object.duplicates
%>

%if duplicates:
<div class="warning">
${ _("Other patients exist with identifiers that match this patient. CamCOPS can handle this but it is probably due to a data entry mistake:") }

<ul class="duplicates">
%for duplicate in duplicates:
<li>
     ${ req.icon_text(
     icon=Icons.PATIENT_EDIT,
     url=request.route_url(
         Routes.EDIT_SERVER_CREATED_PATIENT,
         _query={
             ViewParam.SERVER_PK: duplicate.pk
         }
     ),
     text=duplicate
 ) | n }
</li>
%endfor
</ul>

</div>
%endif


<div>${ _("Server PK:") } ${ object.pk }</div>

${ form | n }

<%include file="to_main_menu.mako"/>
