## user_edit.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Edit user ${ user.username | h }</h1>

${ form }

<%include file="to_main_menu.mako"/>
