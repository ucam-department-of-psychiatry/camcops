## patient_edit.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>${_("Edit details for finalized patient")}</h1>

<div>${_("Server PK:")} ${patient._pk}</div>

${ form }

<div class="warning">${_("The following tasks will be affected:")}</div>

<%include file="view_tasks_table.mako" args="tasks=tasks"/>

<div class="important">${ len(tasks) } ${_("tasks will be affected.")}</div>

<%include file="to_main_menu.mako"/>
