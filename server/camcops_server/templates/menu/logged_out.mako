## logged_out.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<div>
    You have logged out.
</div>
<div>
    Click <a href="${request.route_url(Routes.LOGIN)}">here</a> to log in again.
</div>
