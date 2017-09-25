## id_definition_delete.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Delete master ID definition number ${ iddef.which_idnum } (${ iddef.description | h })</h1>

%if error:
    <div class="error">${ error | h }</div>
%endif

${ form }

<%include file="to_main_menu.mako"/>
