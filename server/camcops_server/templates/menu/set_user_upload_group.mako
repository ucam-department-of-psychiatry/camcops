## set_user_upload_group.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Set upload group for user ${ user.username | h }</h1>

<div class="important">
    A group must be selected for the server to permit uploads.
</div>

<div class="warning">
    Don’t change groups if tasks have been uploaded by this user but not
    finalized; this may lead to incorrect group assignment. (Finalize first,
    then change groups.)
</div>

${ form }

<%include file="to_main_menu.mako"/>
