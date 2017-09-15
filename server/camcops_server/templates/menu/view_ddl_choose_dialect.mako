## view_ddl_choose_dialect.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>View data definition language (DDL), in SQL</h1>

<div>
    The server’s database is using dialect <code>${ current_dialect }</code>
    (${ current_dialect_description }).
</div>

${ form }

<%include file="to_main_menu.mako"/>
