## groups_view.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Groups")}</h1>

<%include file="groups_table.mako" args="groups_page=groups_page, valid_which_idnums=valid_which_idnums, with_edit=True"/>

<td><a href="${ req.route_url(Routes.ADD_GROUP) }">${_("Add a group")}</a></td>

<%include file="to_main_menu.mako"/>
