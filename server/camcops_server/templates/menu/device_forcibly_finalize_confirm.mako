## device_forcibly_finalize_confirm.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Forcibly finalize a device</h1>

<h2>Step 2: view affected tasks</h2>

<%include file="view_tasks_table.mako" args="tasks=tasks"/>

<div class="important">${ len(tasks) } tasks will be affected.</div>

<h2>Step 3 (FINAL STEP): proceed to finalize?</h2>

${ form }

<%include file="to_main_menu.mako"/>
