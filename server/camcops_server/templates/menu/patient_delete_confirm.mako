## patient_delete_confirm.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Delete patient entirely: FINAL STEP</h1>

<div class="warning">
    This operation is irrevocable!
</div>
<div class="warning">
    IT WILL PERMANENTLY DELETE THE PATIENT AND ALL ASSOCIATED TASKS
    from the group that you specify.
</div>

<div class="important">${ n_patient_instances } patient records (current and/or old) will be deleted.</div>

<div class="warning">
    This is the final step. ARE YOU SURE YOU WANT TO DELETE THE PATIENT
    AND ALL THE FOLLOWING TASKS?
</div>

<%include file="view_tasks_table.mako" args="tasks=tasks"/>

<div class="important">${ len(tasks) } tasks will be deleted.</div>

<h1>Proceed to deletion?</h1>

${ form }

<%include file="to_main_menu.mako"/>
