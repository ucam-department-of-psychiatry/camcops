## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/exported_task_list.mako

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
        icon=Icons.AUDIT_REPORT,
        text=_("Exported task log")
    ) | n }
</h1>

%if conditions:
    <h2>${ _("Conditions") }</h2>
    ${ conditions }
%endif

<h2>${ _("Results") }</h2>

<div>${ page.pager() | n }</div>

<table>
    <tr>
        <th>ExportedTask</th>
        <th>Recipient</th>
        <th>Task</th>
        <th>Started at (UTC)</th>
        <th>Finished at (UTC)</th>
        <th>Success?</th>
        <th>Failure reasons</th>
        <th>Cancelled?</th>
        <th>Cancelled at (UTC)</th>
    </tr>

    %for et in page:
        <tr>
            <td>
                ${ req.icon_text(
                        icon=Icons.EXPORTED_TASK,
                        url=request.route_url(
                            Routes.VIEW_EXPORTED_TASK,
                            _query={
                                ViewParam.ID: et.id
                            }
                        ),
                        text="ExportedTask " + str(et.id)
                ) | n }
            </td>
            <td>
                ${ req.icon_text(
                        icon=Icons.EXPORT_RECIPIENT,
                        url=request.route_url(
                            Routes.VIEW_EXPORT_RECIPIENT,
                            _query={
                                ViewParam.ID: et.recipient_id
                            }
                        ),
                        text=et.recipient.recipient_name
                ) | n }
            </td>
            <td>
                ${ req.icon_text(
                        icon=Icons.HTML_IDENTIFIABLE,
                        url=request.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: et.basetable,
                                ViewParam.SERVER_PK: et.task_server_pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML
                            }
                        ),
                        text=et.basetable + " #" + str(et.task_server_pk)
                ) | n }
            </td>
            <td>${ et.start_at_utc }</td>
            <td>${ et.finish_at_utc }</td>
            <td>${ et.success }</td>
            <td>${ "<br>".join(escape(reason) for reason in et.failure_reasons) | n }</td>
            <td>${ et.cancelled }</td>
            <td>${ et.cancelled_at_utc }</td>
        </tr>
    %endfor
</table>

<div>${ page.pager() | n }</div>

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
