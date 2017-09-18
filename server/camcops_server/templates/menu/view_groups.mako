## view_groups.mako
<%inherit file="base_web.mako"/>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Groups</h1>

<div>${page.pager()}</div>

<table>
    <tr>
        <th>Group name</th>
        <th>Group ID</th>
        <th>Description</th>
        <th>Groups this group is allowed to see, in addition to itself</th>
        <th>Edit</th>
        <th>Delete</th>
    </tr>
    %for group in page:
        <tr>
            <td>${ group.name | h }</td>
            <td>${ group.id }</td>
            <td>${ (group.description or "") | h }</td>
            <td>
                ${ one_per_line(g.name for g in group.can_see_other_groups) }
            </td>
            <td><a href="${ req.route_url(Routes.EDIT_GROUP, _query={ViewParam.GROUP_ID: group.id}) }">Edit</a></td>
            <td><a href="${ req.route_url(Routes.DELETE_GROUP, _query={ViewParam.GROUP_ID: group.id}) }">Delete</a></td>
        </tr>
    %endfor
</table>

<div>${page.pager()}</div>

<td><a href="${ req.route_url(Routes.ADD_GROUP) }">Add a group</a></td>

<%include file="to_main_menu.mako"/>
