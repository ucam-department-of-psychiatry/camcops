## edit_group.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Edit group ${ group.name | h }</h1>

${ form }

<%include file="to_main_menu.mako"/>
