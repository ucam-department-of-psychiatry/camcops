## login_failed.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<div class="error">
    Invalid username/password (or user not authorized).
</div>
<div>
    Click <a href="${request.route_url(Routes.LOGIN)}">here</a> to try again.
</div>
