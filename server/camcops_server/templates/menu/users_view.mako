## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/users_view.mako

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
        icon=Icons.USER_MANAGEMENT,
        text=_("Users")
    ) | n }
</h1>

<div>${ page.pager() | n }</div>

${form | n}

<table>
    <tr>
        <th>${ _("Username") }</th>
        <th>${ _("ID") }</th>
        <th>${ _("Flags") }</th>
        <th>${ _("Full name") }</th>
        <th>${ _("Email") }</th>
        <th>${ _("View details") }</th>
        <th>${ _("Edit") }</th>
        <th>${ _("Groups") }</th>
        <th>${ _("Upload group") }</th>
        <th>${ _("Authentication") }</th>
        <th>${ _("Delete") }</th>
    </tr>
    %for user in page:
        <tr>
            <td>
                ${ user.username }
                %if user.id == req.user.id:
                    ${ req.icon(icon=Icons.YOU, alt=_("You")) | n }
                %endif
            </td>
            <td>${ user.id }</td>
            <td>
                %if user.superuser:
                    <span class="important">
                        ${ req.icon_text(
                            icon=Icons.SUPERUSER,
                            text=_("Superuser.")
                        ) | n }
                    </span>
                %endif
                %if user.is_a_groupadmin:
                    <span class="important">
                        ${ req.icon_text(
                            icon=Icons.GROUP_ADMIN,
                            text=_("Group administrator")
                        ) | n }
                        (${ user.names_of_groups_user_is_admin_for_csv }).
                    </span>
                %endif
                %if user.is_locked_out(request):
                    <span class="warning">
                        ${ _("Locked out;") }
                        ${ req.icon_text(
                            icon=Icons.UNLOCK,
                            url=req.route_url(
                                Routes.UNLOCK_USER,
                                _query={
                                    ViewParam.USER_ID: user.id
                                }
                            ),
                            text=_("unlock")
                        ) | n }.
                    </span>
                %endif
                %if user.auto_generated:
                    <span>${ _("Auto-generated") }</span>
                %endif
            </td>
            <td>${ user.fullname or "" }</td>
            <td>
                %if user.email:
                    ${ req.icon_text(
                        icon=Icons.EMAIL_SEND,
                        url="mailto:" + user.email,
                        text=user.email
                    ) | n }
                %endif
            </td>
            <td>
                ${ req.icon_text(
                    icon=Icons.USER_INFO,
                    url=request.route_url(
                        Routes.VIEW_USER,
                        _query={
                            ViewParam.USER_ID: user.id
                        }
                    ),
                    text=_("View")
                ) | n }
            </td>
            <td>
                ${ req.icon_text(
                    icon=Icons.EDIT,
                    url=request.route_url(
                        Routes.EDIT_USER,
                        _query={
                            ViewParam.USER_ID: user.id
                        }
                    ),
                    text=_("Edit")
                ) | n }
            </td>
            <td>
                %for i, ugm in enumerate(sorted(list(user.user_group_memberships), key=lambda ugm: ugm.group.name)):
                    %if i > 0:
                        <br>
                    %endif
                    ${ ugm.group.name }
                    %if req.user.may_administer_group(ugm.group_id):
                        [${ req.icon_text(
                            icon=Icons.USER_PERMISSIONS,
                            url=request.route_url(
                                Routes.EDIT_USER_GROUP_MEMBERSHIP,
                                _query={
                                    ViewParam.USER_GROUP_MEMBERSHIP_ID: ugm.id
                                }
                            ),
                            text=_("Permissions")
                        ) | n }]
                    %endif
                %endfor
            </td>
            <td>
                ${ (escape(user.upload_group.name) if user.upload_group
                    else "<i>(None)</i>") | n }
                [${ req.icon_text(
                    icon=Icons.UPLOAD,
                    url=request.route_url(
                        Routes.SET_OTHER_USER_UPLOAD_GROUP,
                        _query={
                            ViewParam.USER_ID: user.id
                        }
                    ),
                    text=_("Change")
                ) | n }]
            </td>
            <td class="mini_table">
                <table>
                    <tr>
                        <td>
                            %if user.id == req.user.id:
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
                                ${ req.icon_text(
                                    icon=Icons.PASSWORD_OTHER,
                                    url=request.route_url(
                                        Routes.CHANGE_OTHER_PASSWORD,
                                        _query={
                                            ViewParam.USER_ID: user.id
                                        }
                                    ),
                                    text=_("Change password")
                                ) | n }
                            %endif
                        </td>
                    </tr>
                    <tr>
                        <td>
                            ${ req.icon_text(
                                icon=Icons.MFA,
                                url=request.route_url(
                                    Routes.EDIT_OTHER_USER_MFA,
                                    _query={
                                        ViewParam.USER_ID: user.id
                                    }
                                ),
                                text=_("Change multi-factor authentication")
                            ) | n }
                        </td>
                    </tr>
                </table>
            </td>
            <td>
                ${ req.icon_text(
                    icon=Icons.DELETE,
                    url=request.route_url(
                        Routes.DELETE_USER,
                        _query={
                            ViewParam.USER_ID: user.id
                        }
                    ),
                    text=_("Delete")
                ) | n }
            </td>
        </tr>
    %endfor
</table>

<div>${ page.pager() | n }</div>

<div>
    ${ req.icon_text(
        icon=Icons.USER_ADD,
        url=request.route_url(Routes.ADD_USER),
        text=_("Add a user")
    ) | n }
</div>

<%include file="to_main_menu.mako"/>
