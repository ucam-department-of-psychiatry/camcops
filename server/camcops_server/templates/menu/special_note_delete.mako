## special_note_delete.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Delete special note?</h1>

You are about to delete this note:

<table>
    <tr><th>note_id</th><td>${ sn.note_id }</td></tr>
    <tr><th>basetable</th><td>${ sn.basetable }</td></tr>
    <tr><th>task_id</th><td>${ sn.task_id }</td></tr>
    <tr><th>device_id</th><td>${ sn.device_id }</td></tr>
    <tr><th>era</th><td>${ sn.era }</td></tr>
    <tr><th>note_at</th><td>${ sn.note_at }</td></tr>
    <tr><th>user_id</th><td>${ sn.user_id }</td></tr>
    <tr><th>note</th><td>${ sn.note }</td></tr>
</table>

<p><i>The special note will vanish (though preserved in the database for auditing).</i></p>

${ form }

<%include file="to_main_menu.mako"/>
