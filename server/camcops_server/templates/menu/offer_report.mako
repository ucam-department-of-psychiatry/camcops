## offer_report.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Configure report: ${ report.title | h }</h1>

${ form }

<%include file="to_main_menu.mako"/>
