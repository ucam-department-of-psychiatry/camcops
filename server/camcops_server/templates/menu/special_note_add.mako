## special_note_add.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>${_("Add special note to task instance irrevocably?")}</h1>

<%include file="task_descriptive_header.mako" args="task=task, anonymise=False"/>

<div class="warning">
    <b>${_("Be very sure you want to apply a note.")}</b>
</div>

<p><i>${_("Your note will be appended to any existing note.")}</i></p>

${ form }

<%include file="to_main_menu.mako"/>
