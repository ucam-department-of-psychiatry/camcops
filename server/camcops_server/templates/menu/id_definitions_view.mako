## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/id_definitions_view.mako

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
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.ID_DEFINITIONS,
        text=_("Identification (ID) numbers")
    ) | n }
</h1>

<table>
    <tr>
        <th>${ _("ID number") }</th>
        <th>${ _("Description") }</th>
        <th>${ _("Short description") }</th>
        <th>${ _("Validation method") }</th>
        <th>${ _("HL7 ID Type") }</th>
        <th>${ _("HL7 Assigning Authority") }</th>
        <th>${ _("FHIR ID system") }</th>
        <th>${ _("Edit") }</th>
        <th>${ _("Delete") }</th>
    </tr>
    %for iddef in idnum_definitions:
        <tr>
            <td>${ iddef.which_idnum }</td>
            <td>${ iddef.description }</td>
            <td>${ iddef.short_description }</td>
            <td>${ iddef.validation_method or "" }</td>
            <td>${ iddef.hl7_id_type or "" }</td>
            <td>${ iddef.hl7_assigning_authority or "" }</td>
            <td>
                %if not iddef.fhir_id_system:
                    ${ _("Default:") }
                %endif
                ${ req.icon_text(
                        icon=Icons.INFO_INTERNAL,
                        url=iddef.effective_fhir_id_system(req),
                        text=iddef.effective_fhir_id_system(req)
                ) | n }
            </td>
            <td>
                ${ req.icon_text(
                        icon=Icons.EDIT,
                        url=request.route_url(
                            Routes.EDIT_ID_DEFINITION,
                            _query={
                                ViewParam.WHICH_IDNUM: iddef.which_idnum
                            }
                        ),
                        text=_("Edit")
                ) | n }
            </td>
            <td>
                ${ req.icon_text(
                        icon=Icons.DELETE,
                        url=request.route_url(
                            Routes.DELETE_ID_DEFINITION,
                            _query={
                                ViewParam.WHICH_IDNUM: iddef.which_idnum
                            }
                        ),
                        text=_("Delete")
                ) | n }
            </td>
        </tr>
    %endfor
</table>

<div>
    ${ req.icon_text(
            icon=Icons.ID_DEFINITION_ADD,
            url=request.route_url(Routes.ADD_ID_DEFINITION),
            text=_("Add new ID number definition")
    ) | n }
</div>

<%include file="to_main_menu.mako"/>
