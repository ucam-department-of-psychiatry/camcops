## view_other_user_info.mako
## <%page args="user: User"/>
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>Information about user ${ user.username | h }</h1>

<%include file="user_info_detail.mako" args="user=user"/>

<%include file="to_view_all_users.mako"/>

<%include file="to_main_menu.mako"/>
