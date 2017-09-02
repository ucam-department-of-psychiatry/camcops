## change_other_password.mako
<%inherit file="base_web.mako"/>

<h1>Change password for user: ${username}</h1>

%if extra_msg:
    <div class="warning">${extra_msg}</div>
%endif

${form}

<div>
    Minimum password length is ${min_pw_length} characters.
</div>
