## device_forcibly_finalize_confirm.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>${_("Forcibly finalize a device")}</h1>

<h2>${_("Step 2: view affected tasks")}</h2>

<%include file="view_tasks_table.mako" args="tasks=tasks"/>

<div class="important">${ len(tasks) } ${_("tasks will be affected (plus any uploaded while you watch this message).")}</div>

<h2>${_("Step 3 (FINAL STEP): proceed to finalize?")}</h2>

${ form }

<%include file="to_main_menu.mako"/>
