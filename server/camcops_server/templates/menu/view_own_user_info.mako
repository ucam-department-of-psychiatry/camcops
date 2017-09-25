## view_own_user_info.mako
## <%page args="user: User"/>
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>Information about user ${ user.username | h }</h1>

<%include file="user_info_detail.mako" args="user=user"/>

<h1>Groups that user ${ user.username | h } is a member of</h1>

<%include file="groups_table.mako" args="groups_page=groups_page, with_edit=False"/>

<%include file="to_main_menu.mako"/>
