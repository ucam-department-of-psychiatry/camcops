## user_edit_group_membership.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Edit group permissions</h1>

<div>
    User: <b>${ ugm.user.username | h }</b><br>
    Group: <b>${ ugm.group.name | h }</b>
</div>

${ form }

<%include file="to_main_menu.mako"/>
