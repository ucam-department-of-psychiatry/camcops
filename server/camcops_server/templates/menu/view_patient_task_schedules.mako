## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/view_patient_task_schedules.mako

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
from urllib.parse import quote, urlencode

from cardinal_pythonlib.datetimefunc import format_datetime

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>
<h2>
    ${ req.icon_text(
        icon=Icons.INFO_INTERNAL,
        text= _("CamCOPS server location:")
    ) | n }
</h2>
<div>
    ${ req.icon_text(
        icon=Icons.INFO_EXTERNAL,
        url=req.route_url(Routes.CLIENT_API),
        text=req.route_url(Routes.CLIENT_API),
    ) | n }
</div>

<h1>
    ${ req.icon_text(
        icon=Icons.PATIENTS,
        text=_("Patients and their task schedules")
    ) | n }
</h1>

<div>${ page.pager() | n }</div>

<table>
    <colgroup>
        <col style="width:20%">
        <col style="width:15%">
        <col style="width:20%">
        <col style="width:25%">
        <col style="width:10%">
        <col style="width:10%">
    </colgroup>
    <tbody>
        <tr>
            <th>${ _("Patient") }</th>
            <th>${ _("Identifiers") }</th>
            <th>${ _("Access key") }</th>
            <th>${ _("Task schedules") }</th>
            <th>${ _("Edit patient, assign schedules") }</th>
            <th>${ _("Delete patient") }</th>
        </tr>
        %for patient in page:
            <tr>
                <td>
                    ${ req.icon(
                        icon=Icons.PATIENT,
                        alt=_("Patient")
                    ) | n }
                    <b>${ patient.get_surname_forename_upper() }</b>
                    (${ patient.get_sex_verbose() },
                    ${ format_datetime(patient.dob, DateFormat.SHORT_DATE, default="?") })
                </td>
                <td>
                    %for idobj in patient.idnums:
                        ${ idobj.short_description(request) }:&nbsp;${ idobj.idnum_value }.
                        <br>
                    %endfor
                </td>
                <td>
                    ${ patient.uuid_as_proquint }
                </td>
                <td class="mini_table">
                    <table>
                    %for pts in patient.task_schedules:
                    <%
                        if patient.email:
                            email_text = _("Send email")
                            button_class = "btn btn-success"
                            if pts.email_sent:
                                email_text = _("Resend email")
                                button_class = "btn btn-primary"
                    %>
                        <tr>
                            <td>
                                ${ req.icons_text(
                                    icons=[Icons.PATIENT, Icons.TASK_SCHEDULE],
                                    url=request.route_url(
                                        Routes.VIEW_PATIENT_TASK_SCHEDULE,
                                        _query={
                                            ViewParam.PATIENT_TASK_SCHEDULE_ID: pts.id
                                        }
                                    ),
                                    text=pts.task_schedule.name
                                ) | n }
                            </td>
                            <td>
                                %if req.user.authorized_to_email_patients and patient.email and pts.task_schedule.email_from:
                                    ${ req.icon_text(
                                        icon=Icons.EMAIL_SEND,
                                        url=request.route_url(
                                            Routes.SEND_EMAIL_FROM_PATIENT_LIST,
                                            _query={
                                                ViewParam.PATIENT_TASK_SCHEDULE_ID: pts.id
                                            }
                                        ),
                                        extra_a_classes=[button_class],
                                        text=email_text,
                                        hyperlink_together=True,
                                    ) | n }
                                %endif
                            </td>
                        </tr>
                    %endfor
                    </table>
                </td>
                <td>
                    ${ req.icon_text(
                        icon=Icons.PATIENT_EDIT,
                        url=request.route_url(
                            Routes.EDIT_SERVER_CREATED_PATIENT,
                            _query={
                                ViewParam.SERVER_PK: patient.pk
                            }
                        ),
                        text=_("Edit")
                    ) | n }
                </td>
                <td>
                    ${ req.icon_text(
                        icon=Icons.DELETE,
                        url=request.route_url(
                            Routes.DELETE_SERVER_CREATED_PATIENT,
                            _query={
                                ViewParam.SERVER_PK: patient.pk
                            }
                        ),
                        text=_("Delete")
                    ) | n }
                </td>
            </tr>
        %endfor
    </tbody>
</table>

<div>${ page.pager() | n }</div>

<div>
    ${ req.icon_text(
        icon=Icons.PATIENT_ADD,
        url=request.route_url(Routes.ADD_PATIENT),
        text=_("Add a patient")
    ) | n }
</div>
%if request.user.authorized_as_groupadmin:
    <%include file="to_view_task_schedules.mako"/>
%endif

<%include file="to_main_menu.mako"/>
