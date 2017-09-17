## change_other_password.mako
<%inherit file="base_web_form.mako"/>

<%include file="db_user_info.mako"/>

<h1>Change password for user: ${username}</h1>

%if extra_msg:
    <div class="warning">${extra_msg}</div>
%endif

${form}

<div>
    Minimum password length is ${min_pw_length} characters.
</div>

<%include file="to_view_all_users.mako"/>

<%include file="to_main_menu.mako"/>
