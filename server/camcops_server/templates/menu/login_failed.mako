## login_failed.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<div class="error">
    ${_("Invalid username/password (or user not authorized).")}
</div>
<div>
    ${_("Click")} <a href="${request.route_url(Routes.LOGIN)}">${_("here")}</a> ${_("to try again.")}
</div>
