## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/fhir_questionnaire_id.mako

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
from camcops_server.cc_modules.cc_pyramid import Routes
%>

<%include file="db_user_info.mako"/>

<h1>${ _("All tasks") }</h1>

<table>
    <tr>
        <th>${ _("Code") }</th>
        <th>${ _("Short name") }</th>
        <th>${ _("Full name, with link to help") }</th>
        <th>${ _("Elements") }</th>
    </tr>
    %for tc in all_task_classes:
        <tr>
            <td>${ tc.tablename }</td>
            <td>${ tc.shortname }</td>
            <td>
                <a href="${ tc.help_url() }">
                    ${ tc.longname(req) }
                </a>
            </td>
            <td>
                <a href="${ req.route_url(Routes.FHIR_QUESTIONNAIRE_RESPONSE_ID,
                                          table_name=tc.tablename) }">
                    ${ _("Elements") }
                </a>
            </td>
        </tr>
    %endfor
</table>

<p>${ _(
    "This is also the FHIR Questionnaire system. The code is the FHIR value. "
    "The elements make up the FHIR QuestionnaireResponse system for each task."
) }</p>

<%include file="to_main_menu.mako"/>
