## set_user_upload_group.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Set upload group for user ${ user.username | h }</h1>

<div class="important">A group must be selected for the server to permit uploads.</div>

${ form }

<%include file="to_main_menu.mako"/>
