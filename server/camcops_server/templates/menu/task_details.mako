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
from camcops_server.cc_modules.cc_pyramid import Icons, Routes
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text=_("Task details") + ": " + task_class.tablename
    ) | n }
</h1>

<h2>${ _("Help") }</h2>
<div>
    ${ req.icon_text(
        icon=Icons.INFO_EXTERNAL,
        url=task_class.help_url(),
        text=task_class.longname(req) + " (" + task_class.shortname + ")"
    ) | n }
</div>

<h2>${ _("FHIR Questionnaire structure, if applicable") }</h2>
<table>
    <colgroup>
        <col style="width:10%">
        <col style="width:30%">
        <col style="width:10%">
        <col style="width:10%">
        <col style="width:40%">
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Item") }</th>
            <th>${ _("Question") }</th>
            <th>${ _("Question type") }</th>
            <th>${ _("Answer type") }</th>
            <th>${ _("Answer options, if applicable") }</th>
        </tr>
        %for aq in fhir_aq_items:
            <tr>
                <td>${ aq.qname }</td>
                <td>${ aq.qtext }</td>
                <td>${ aq.qtype.value }</td>
                <td>${ aq.answer_type.value }</td>
                <td>
                    %if aq.is_mcq:
                        %if aq.answer_options:
                            %for code, display in aq.answer_options.items():
                                ${ code }: ${ display }<br>
                            %endfor
                        %else:
                            ${ ", ".join(str(x) for x in aq.answer_valueset) }
                        %endif
                    %endif
                </td>
            </tr>
        %endfor
    </tbody>
</table>

<div>
    ${ req.icon_text(
            icon=Icons.ZOOM_OUT,
            url=request.route_url(Routes.TASK_LIST),
            text=_("Task list")
    ) | n }
</div>
<%include file="to_main_menu.mako"/>
