## user_add.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Add user</h1>

<div class="important">Once created, you can set permissions.</div>

${ form }

<%include file="to_main_menu.mako"/>
