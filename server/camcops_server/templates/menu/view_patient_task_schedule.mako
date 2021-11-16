## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/view_patient_task_schedule.mako

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
from cardinal_pythonlib.datetimefunc import format_datetime

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_html import get_yes_no
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.PATIENT,
        text=_("{patient} on schedule: {schedule}").format(
            patient=patient_descriptor,
            schedule=schedule_name
        )
    ) | n }
</h1>

<h2>${ _("Scheduled tasks") }</h2>

<table class="scheduled_tasks_table">
    <tr>
        <th>${ _("Task") }</th>
        <th>${ _("Due from") }</th>
        <th>${ _("Due by") }</th>
        <th>${ _("Created") }</th>
        <th>${ _("Complete") }</th>
        <th>${ _("View") }</th>
        <th>${ _("Print, save") }</th>
    </tr>
    %for task_info in task_list:
        <%
            td_attributes = ""
            if task_info.task and not task_info.task.is_complete():
                td_attributes = "class='incomplete'"
        %>
        <tr>
            <td>
                ${ task_info.shortname }
            </td>
            <td>
                %if task_info.start_datetime:
                    ${ format_datetime(task_info.start_datetime, DateFormat.SHORT_DATETIME_NO_TZ) }
                %endif
            </td>
            <td>
                %if task_info.end_datetime:
                    ${ format_datetime(task_info.end_datetime, DateFormat.SHORT_DATETIME_NO_TZ) }
                %endif
            </td>
            <td>
                %if task_info.is_anonymous:
                   —
                %elif task_info.task:
                   ${ format_datetime(task_info.task.when_created, DateFormat.SHORT_DATETIME_NO_TZ) }
                %endif
            </td>
            <td>
                %if task_info.is_anonymous:
                   —
                %elif task_info.task:
                   ${ task_info.task.is_complete() }
                %endif
            </td>
            <td ${ td_attributes | n }>
                %if task_info.is_anonymous:
                   —
                %elif task_info.task:
                    ${ req.icon_text(
                        icon=Icons.HTML_IDENTIFIABLE,
                        url=request.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task_info.task.tablename,
                                ViewParam.SERVER_PK: task_info.task.pk,
                                ViewParam.VIEWTYPE: ViewArg.HTML,
                            }
                        ),
                        text="HTML"
                    ) | n }
                %endif
            </td>
            <td ${ td_attributes }>
                %if task_info.is_anonymous:
                   —
                %elif task_info.task:
                    ${ req.icon_text(
                        icon=Icons.PDF_IDENTIFIABLE,
                        url=request.route_url(
                            Routes.TASK,
                            _query={
                                ViewParam.TABLE_NAME: task_info.task.tablename,
                                ViewParam.SERVER_PK: task_info.task.pk,
                                ViewParam.VIEWTYPE: ViewArg.PDF,
                            }
                        ),
                        text="PDF"
                    ) | n }
                %endif
            </td>
        </tr>
    %endfor
</table>

%if req.user.authorized_to_email_patients:
    <h2>${ _("Emails") }</h2>

    <table>
        <tr>
            <th>${ _("Subject") }</th>
            <th>${ _("Date") }</th>
            <th>${ _("Sent") }</th>
            <th>${ _("Sending failure reason") }</th>
        </tr>
        %for pts_email in pts.emails:
            <%
                tr_attributes = ""
                failure_reason = ""
                if not pts_email.email.sent:
                    failure_reason = pts_email.email.sending_failure_reason
                    tr_attributes = "class='error'"
            %>
            <tr ${ tr_attributes | n }>
                <td>
                    %if req.user.superuser:
                        ${ req.icon_text(
                            icon=Icons.EMAIL_VIEW,
                            url=req.route_url(
                                Routes.VIEW_EMAIL,
                                _query={
                                    ViewParam.ID: pts_email.email_id
                                }
                            ),
                            text=pts_email.email.subject
                        ) | n }
                    %else:
                        ${ pts_email.email.subject }
                    %endif
                </td>
                <td>${ pts_email.email.date }</td>
                <td>${ get_yes_no(req, pts_email.email.sent) }</td>
                <td>${ failure_reason }</td>
            </tr>
        %endfor
    </table>
    %if pts.patient.email and pts.task_schedule.email_from:
        <div>
            ${ req.icon_text(
                icon=Icons.EMAIL_SEND,
                url=req.route_url(
                    Routes.SEND_EMAIL_FROM_PATIENT_TASK_SCHEDULE,
                    _query={
                        ViewParam.PATIENT_TASK_SCHEDULE_ID: pts.id
                    }
                ),
                text=_("Email this patient")
            ) | n }
        </div>
    %endif
%endif

<%include file="to_view_patient_task_schedules.mako"/>
<%include file="to_main_menu.mako"/>
