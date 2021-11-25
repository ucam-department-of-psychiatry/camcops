## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/exported_task.mako

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
from camcops_server.cc_modules.cc_mako_helperfunc import listview
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.EXPORTED_TASK,
        text=_("Individual task export attempt")
    ) | n }
</h1>

<table>
    <tr>
        <th>${ _("Export ID") }</th>
        <td>${ et.id }</td>
    </tr>
    <tr>
        <th>${ _("Export recipient ID") }</th>
        <td>
            ${ req.icon_text(
                    icon=Icons.EXPORT_RECIPIENT,
                    url=request.route_url(
                        Routes.VIEW_EXPORT_RECIPIENT,
                        _query={
                            ViewParam.ID: et.recipient_id
                        }
                    ),
                    text="ExportRecipient " + str(et.recipient_id)
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("Base table") }</th>
        <td>${ et.basetable }</td>
    </tr>
    <tr>
        <th>${ _("Task server PK") }</th>
        <td>
            ${ et.task_server_pk }
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
                    text=_("View task")
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("Start at (UTC)") }</th>
        <td>${ et.start_at_utc }</td>
    </tr>
    <tr>
        <th>${ _("Finish at (UTC)") }</th>
        <td>${ et.finish_at_utc }</td>
    </tr>
    <tr>
        <th>${ _("Success?") }</th>
        <td>${ et.success }</td>
    </tr>
    <tr>
        <th>${ _("Failure reasons") }</th>
        <td>${ "<br>".join(escape(reason) for reason in et.failure_reasons) | n }</td>
    </tr>
    <tr>
        <th>${ _("Cancelled?") }</th>
        <td>${ et.cancelled }</td>
    </tr>
    <tr>
        <th>${ _("Cancelled at (UTC)") }</th>
        <td>${ et.cancelled_at_utc or "" }</td>
    </tr>
    <tr>
        <th>${ _("E-mails") }</th>
        <td>
            ${ listview(
                    req, et.emails, Routes.VIEW_EXPORTED_TASK_EMAIL,
                    "ExportedTaskEmail", Icons.AUDIT_ITEM
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("FHIR exports") }</th>
        <td>
            ${ listview(
                    req, et.fhir_exports, Routes.VIEW_EXPORTED_TASK_FHIR,
                    "ExportedTaskFhir", Icons.EXPORTED_TASK_ENTRY_COLLECTION
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("Files") }</th>
        <td>
            ${ listview(
                    req, et.filegroups, Routes.VIEW_EXPORTED_TASK_FILE_GROUP,
                    "ExportedTaskFileGroup", Icons.AUDIT_ITEM
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("HL7 v2 messages") }</th>
        <td>
            ${ listview(
                    req, et.hl7_messages, Routes.VIEW_EXPORTED_TASK_HL7_MESSAGE,
                    "ExportedTaskHL7Message", Icons.AUDIT_ITEM
            ) | n }
        </td>
    </tr>
    <tr>
        <th>${ _("REDCap exports") }</th>
        <td>
            ${ listview(
                    req, et.redcap_exports, Routes.VIEW_EXPORTED_TASK_REDCAP,
                    "ExportedTaskRedcap", Icons.AUDIT_ITEM
            ) | n }
        </td>
    </tr>
</table>

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
