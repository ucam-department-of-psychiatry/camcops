## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/view_patient_task_schedule.mako

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

</%doc>

<%inherit file="base_web.mako"/>

<%!
from cardinal_pythonlib.datetimefunc import format_datetime

from camcops_server.cc_modules.cc_constants import DateFormat
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Patients")}</h1>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>${_("Patient")}</th>
    </tr>
%for patient in page:
    <tr>
        <td>
            <b>${ patient.get_surname_forename_upper() }</b>
            (${ patient.get_sex_verbose() },
            ${ format_datetime(patient.dob, DateFormat.SHORT_DATE, default="?") })
         </td>
    </tr>
%endfor
</table>

<div>${page.pager()}</div>

<a href="${ req.route_url(Routes.ADD_PATIENT) }">${_("Add a patient")}</a>

<%include file="to_main_menu.mako"/>
