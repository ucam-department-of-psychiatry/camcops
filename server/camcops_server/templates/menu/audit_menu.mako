## audit_menu.mako
<%inherit file="base_web.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes
%>

<h2>${_("Audit options")}</h2>

<h3>${_("Access logs")}</h3>
<ul>
    <li><a href="${request.route_url(Routes.OFFER_AUDIT_TRAIL)}">${_("Audit trail")}</a></li>
</ul>

<h3>${_("Export logs")}</h3>
<ul>
    <li><a href="${request.route_url(Routes.OFFER_EXPORTED_TASK_LIST)}">${_("Exported task log")}</a></li>
</ul>
