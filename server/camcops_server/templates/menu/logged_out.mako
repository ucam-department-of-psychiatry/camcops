## logged_out.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<div>
    ${_("You have logged out.")}
</div>
<div>
    ${_("Click")} <a href="${request.route_url(Routes.LOGIN)}">${_("here")}</a> ${_("to log in again")}.
</div>
