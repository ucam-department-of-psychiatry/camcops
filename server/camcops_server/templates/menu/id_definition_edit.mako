## id_definition_edit.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Edit master ID number definition for ID# ${ iddef.which_idnum }</h1>

${ form }

<%include file="to_main_menu.mako"/>
