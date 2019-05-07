## password_changed.mako
<%inherit file="base_web.mako"/>

<div>${_("Password changed for user")} ${username}.</div>

%if own_password:
    <div class="important">
        ${_("If you store your password in your CamCOPS tablet application, remember to change it there as well.")}
    </div>
%endif

<%include file="to_main_menu.mako"/>
