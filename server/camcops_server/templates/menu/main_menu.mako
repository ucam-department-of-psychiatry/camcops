## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/main_menu.mako

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

<%include file="db_user_info.mako" args="offer_main_menu=False"/>

## TRANSLATOR: Mako comment
<h1>
    ${ req.icon_text(
        icon=Icons.HOME,
        text=_("CamCOPS web view: Main menu")
    ) | n }
</h1>

<h3>${ _("Tasks, trackers, and clinical text views") }</h3>
<ul class="menu">
    <li>
        ${ req.icon_text(
            icon=Icons.FILTER,
            url=request.route_url(
                Routes.SET_FILTERS,
                _query={
                    ViewParam.REDIRECT_URL: request.route_url(Routes.HOME)
                }
            ),
            text=_("Filter tasks")
        ) | n }
    </li>
    <li>
        ${ req.icon_text(
            icon=Icons.VIEW_TASKS,
            url=request.route_url(Routes.VIEW_TASKS),
            text=_("View tasks")
        ) | n }
    <li>
        ${ req.icon_text(
            icon=Icons.TRACKERS,
            url=request.route_url(Routes.CHOOSE_TRACKER),
            text=_("Trackers for numerical information")
        ) | n }
    </li>
    <li>
        ${ req.icon_text(
            icon=Icons.CTV,
            url=request.route_url(Routes.CHOOSE_CTV),
            text=_("Clinical text views")
        ) | n }
    </li>
</ul>

%if authorized_to_manage_patients:
    <h3>${ _("Patients") }</h3>
    <ul class="menu">
        <li>
            ${ req.icon_text(
                icon=Icons.PATIENTS,
                url=request.route_url(Routes.VIEW_PATIENT_TASK_SCHEDULES),
                text=_("Manage patients and their task schedules")
            ) | n }
        </li>
    </ul>
%endif

%if authorized_to_dump:
    <h3>${ _("Research views") }</h3>
    <ul class="menu">
        <li>
            ${ req.icon_text(
                    icon=Icons.DUMP_BASIC,
                    url=request.route_url(Routes.OFFER_BASIC_DUMP),
                    text=_("Basic research dump (fields and summaries)")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.DUMP_SQL,
                    url=request.route_url(Routes.OFFER_SQL_DUMP),
                    text=_("Advanced research dump (SQL or database)")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.DOWNLOAD,
                    url=request.route_url(Routes.DOWNLOAD_AREA),
                    text=_("Download area")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.INFO_INTERNAL,
                    url=request.route_url(Routes.TASK_LIST),
                    text=_("Task list")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.INFO_INTERNAL,
                    url=request.route_url(Routes.VIEW_DDL),
                    text=_("Inspect table definitions")
            ) | n }
        </li>
    </ul>
%endif

%if authorized_for_reports:
    <h3>${ _("Reports") }</h3>
    <ul class="menu">
        <li>
            ${ req.icon_text(
                    icon=Icons.REPORTS,
                    url=request.route_url(Routes.REPORTS_MENU),
                    text=_("Run reports")
            ) | n }
        </li>
    </ul>
%endif

%if authorized_as_groupadmin:
    <h3>${ _("Group administrator options") }</h3>
    <ul class="menu">
        <li>
            ${ req.icon_text(
                    icon=Icons.USER_MANAGEMENT,
                    url=request.route_url(Routes.VIEW_ALL_USERS),
                    text=_("User management")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.EMAIL_CONFIGURE,
                    url=request.route_url(Routes.VIEW_USER_EMAIL_ADDRESSES),
                    text=_("E-mail addresses of your users")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.FORCE_FINALIZE,
                    url=request.route_url(Routes.FORCIBLY_FINALIZE),
                    text=_("Forcibly finalize records for a device")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.DELETE_MAJOR,
                    url=request.route_url(Routes.DELETE_PATIENT),
                    text=_("Delete patient entirely")
            ) | n }
        </li>
    </ul>
%endif

%if authorized_as_superuser:
    <h3>${ _("Superuser options") }</h3>
    <ul class="menu">
        <li>
            ${ req.icon_text(
                    icon=Icons.GROUPS,
                    url=request.route_url(Routes.VIEW_GROUPS),
                    text=_("Group management")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.AUDIT_MENU,
                    url=request.route_url(Routes.AUDIT_MENU),
                    text=_("Audit menu")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.ID_DEFINITIONS,
                    url=request.route_url(Routes.VIEW_ID_DEFINITIONS),
                    text=_("ID number definition management")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.SETTINGS,
                    url=request.route_url(Routes.EDIT_SERVER_SETTINGS),
                    text=_("Edit server settings")
            ) | n }
        </li>
        <li>
            ${ req.icon_text(
                    icon=Icons.DEVELOPER,
                    url=request.route_url(Routes.DEVELOPER),
                    text=_("Developer test pages")
            ) | n }
        </li>
    </ul>
%endif

<h3>${ _("Settings") }</h3>
<ul class="menu">
    <li>
        ${ req.icon_text(
                icon=Icons.UPLOAD,
                url=request.route_url(Routes.SET_OWN_USER_UPLOAD_GROUP),
                text=_("Choose group into which to upload data")
        ) | n }
    </li>
    <li>
        ${ req.icon_text(
                icon=Icons.INFO_INTERNAL,
                url=request.route_url(Routes.VIEW_OWN_USER_INFO),
                text=_("View your user settings")
        ) | n }
    </li>
    <li>
        ${ req.icon_text(
                icon=Icons.INFO_INTERNAL,
                url=request.route_url(Routes.VIEW_SERVER_INFO),
                text=_("View server information")
        ) | n }
    </li>
    %if request.camcops_session.username:
        <li>
            ${ req.icon_text(
                    icon=Icons.PASSWORD_OWN,
                    url=request.route_url(
                        Routes.CHANGE_OWN_PASSWORD,
                        _query={
                            ViewParam.USERNAME: request.camcops_session.username
                        }
                    ),
                    text=_("Change password")
            ) | n }
    %else:
        <li class="warning">${ _("No username!") }</li>
    %endif
    <li>
        ${ req.icon_text(
            icon=Icons.MFA,
            url=request.route_url(Routes.EDIT_OWN_USER_MFA),
            text=_("Multi-factor authentication settings")
        ) | n }
    </li>
</ul>

<h3>${ _("Help") }</h3>
<ul class="menu">
    <li>
        ${ req.icon_text(
                icon=Icons.INFO_EXTERNAL,
                url=request.url_camcops_docs,
                text=_("CamCOPS documentation")
        ) | n }
    </li>
</ul>

<div class="office">
    ${ _("The time is") } ${ now }.
    ${ _("Server version:") } ${ server_version }.
    ${ _("See") } <a href="${ camcops_url | n }">${ camcops_url }</a>
    ${ _("for more information on CamCOPS.") }
    ${ _("Clicking on the CamCOPS logo will return you to the main menu.") }
</div>
