## groups_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>View/edit groups</h1>

<%include file="groups_table.mako" args="groups_page=groups_page, with_edit=True"/>

<td><a href="${ req.route_url(Routes.ADD_GROUP) }">Add a group</a></td>

<%include file="to_main_menu.mako"/>
