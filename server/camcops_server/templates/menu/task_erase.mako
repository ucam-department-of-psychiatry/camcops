## task_erase.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Erase task irrevocably?</h1>

<%include file="task_descriptive_header.mako" args="task=task, anonymise=False"/>

<div class="warning">
    <b>ARE YOU REALLY SURE YOU WANT TO ERASE THIS TASK?</b>
</div>

<p><i>Data will be erased; the task structure itself will remain as a placeholder.</i></p>

${ form }

<%include file="to_main_menu.mako"/>
