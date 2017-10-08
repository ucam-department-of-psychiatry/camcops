## patient_edit.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Edit details for finalized patient</h1>

<div>Server PK: ${patient._pk}</div>

${ form }

<div class="warning">The following tasks will be affected:</div>

<%include file="view_tasks_table.mako" args="tasks=tasks"/>

<div class="important">${ len(tasks) } tasks will be affected.</div>

<%include file="to_main_menu.mako"/>
