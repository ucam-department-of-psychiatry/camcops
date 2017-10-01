## users_view.mako
<%inherit file="base_web.mako"/>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<%!
from markupsafe import escape
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Users</h1>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>Username</th>
        <th>ID</th>
        <th>Flags</th>
        <th>Full name</th>
        <th>Email</th>
        <th>View details</th>
        <th>Edit</th>
        <th>Groups</th>
        %if as_superuser:
            <th>Upload group</th>
        %endif
        <th>Change password</th>
        <th>Delete</th>
    </tr>
    %for user in page:
        <tr>
            <td>${ user.username | h }</td>
            <td>${ user.id }</td>
            <td>
                %if user.superuser:
                    <span class="important">Superuser.</span>
                %endif
                %if user.is_a_groupadmin:
                    <span class="important">Group administrator.</span>
                %endif
                %if user.is_locked_out(request):
                    <span class="warning">Locked out; <a href="${ req.route_url(Routes.UNLOCK_USER, _query={ViewParam.USER_ID: user.id}) }">unlock</a>.</span>
                %endif
            </td>
            <td>${ (user.fullname or "") | h }</td>
            <td>${ (user.email or "") | h }</td>
            <td><a href="${ req.route_url(Routes.VIEW_USER, _query={ViewParam.USER_ID: user.id}) }">View</a></td>
            <td><a href="${ req.route_url(Routes.EDIT_USER, _query={ViewParam.USER_ID: user.id}) }">Edit</a></td>
            <td>
                ${ one_per_line(
                ['{} [<a href="{}">Permissions</a>]'.format(
                    ugm.group.name,
                    req.route_url(Routes.EDIT_USER_GROUP_MEMBERSHIP, _query={ViewParam.USER_GROUP_MEMBERSHIP_ID: ugm.id})
                )
                for ugm in sorted(list(user.user_group_memberships), key=lambda ugm: ugm.group.name)],
                escape=False) }
            </td>
            %if as_superuser:
                <td>
                    ${ (escape(user.upload_group.name) if user.upload_group else "<i>(None)</i>") }
                    [<a href="${request.route_url(Routes.SET_OTHER_USER_UPLOAD_GROUP, _query={ViewParam.USER_ID: user.id})}">change</a>]
                </td>
            %endif
            <td><a href="${ req.route_url(Routes.CHANGE_OTHER_PASSWORD, _query={ViewParam.USER_ID: user.id}) }">Change password</a></td>
            <td><a href="${ req.route_url(Routes.DELETE_USER, _query={ViewParam.USER_ID: user.id}) }">Delete</a></td>
        </tr>
    %endfor
</table>

<div>${page.pager()}</div>

<td><a href="${ req.route_url(Routes.ADD_USER) }">Add a user</a></td>

<%include file="to_main_menu.mako"/>
