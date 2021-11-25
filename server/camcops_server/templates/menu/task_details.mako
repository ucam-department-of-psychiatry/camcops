## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/task_details.mako

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
from mako.filters import html_escape

from camcops_server.cc_modules.cc_pyramid import Icons, Routes
%>

<%doc>
<%block name="extra_head_end">
    <style nonce="${ request.nonce | n }">
        ${ css | n }
    </style>
</%block>
</%doc>

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

<h2>${ _("Table definitions") }</h2>
<table>
    <colgroup>
        <col style="width:10%">
        <col style="width:20%">
        <col style="width:15%">
        <col style="width:55%">
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Table name") }</th>
            <th>${ _("Column name") }</th>
            <th>${ _("Column type") }</th>
            <th>${ _("Comment") }</th>
        </tr>
        %for table in task_class.all_tables():
            %for column in table.columns:
                <tr>
                    <td>${ table.name }</td>
                    <td>${ column.name }</td>
                    <td>${ str(column.type) }</td>
                    <td>${ column.comment or "" }</td>
                </tr>
            %endfor
        %endfor
    </tbody>
</table>

<h2>${ _("Summary elements") }</h2>
<table>
    <colgroup>
        <col style="width:30%">
        <col style="width:15%">
        <col style="width:55%">
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Name") }</th>
            <th>${ _("Column type") }</th>
            <th>${ _("Comment") }</th>
        </tr>
        %for summary in task_instance.get_summaries(req):
            <tr>
                <td>${ summary.name }</td>
                <td>${ str(summary.coltype) }</td>
                <td>${ summary.comment or "" }</td>
            </tr>
        %endfor
    </tbody>
</table>

<h2>${ _("Tracker elements") }</h2>
<table>
    <colgroup>
        <col style="width:30%">
        <col style="width:70%">
        <%doc>
        <col style="width:25%">
        <col style="width:25%">
        <col style="width:15%">
        <col style="width:15%">
        <col style="width:20%">
        </%doc>
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Plot label") }</th>
            <th>${ _("Axis label") }</th>
            <%doc>
            <th>${ _("Y axis min, max") }</th>
            <th>${ _("Horizontal lines at") }</th>
            <th>${ _("Horizontal line labels") }</th>
            </%doc>
        </tr>
        %for tracker in task_instance.get_trackers(req):
            <tr>
                <td>${ tracker.plot_label }</td>
                <td>${ tracker.axis_label }</td>
                <%doc>
                <td>${ tracker.axis_min }, ${ tracker.axis_max }</td>
                <td>${ tracker.horizontal_lines }</td>
                <td>${ "<br>".join(html_escape(str(x))
                                   for x in tracker.horizontal_labels) | n }</td>
                </%doc>
            </tr>
        %endfor
    </tbody>
</table>

<%doc>
## These only work properly for complete tasks: try PHQ9.
<h2>${ _("Clinical text view (CTV) elements") }</h2>
<table>
    <colgroup>
        <col style="width:25%">
        <col style="width:15%">
        <col style="width:60%">
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Heading") }</th>
            <th>${ _("Subheading") }</th>
            <th>${ _("Description") }</th>
        </tr>
        %for ctvinfo in task_instance.get_clinical_text(req):
            <tr>
                <td>${ ctvinfo.heading or "" }</td>
                <td>${ ctvinfo.subheading or "" }</td>
                <td>${ ctvinfo.description or "" }</td>
            </tr>
        %endfor
    </tbody>
</table>
</%doc>

<h2>${ _("FHIR Questionnaire structure, if applicable") }</h2>
<table>
    <colgroup>
        <col style="width:15%">
        <col style="width:25%">
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
